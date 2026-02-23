"""
The uvk IPython extension provides magicks to manage the dependencies
of an isolated kernel. It also ensures that the uv executable is visible
by the IPython process, as shelling out to uv is how most of the kernel's
specific functionalities are delivered.
"""

from collections.abc import Iterable
from IPython.core.interactiveshell import InteractiveShell
from IPython.display import display, Markdown
import logging as lg
from packaging.requirements import Requirement
from packaging.specifiers import SpecifierSet
import shutil
import subprocess as sp
import sys
from tempfile import NamedTemporaryFile
from typing import cast
from warnings import warn

from ._parse import parse_dependencies, parse_script_metadata

_PATH_UV = shutil.which("uv")
LOG = lg.getLogger(__name__)


class CannotFindUV(Exception):

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(
            (
                "uv executable cannot be found; "
                "it is critical for the features provided by "
                f"extension {__name__}."
            ),
            *args,
            **kwargs,
        )


def load_ipython_extension(shell: InteractiveShell) -> None:
    if not _PATH_UV:
        raise CannotFindUV()
    for magic, kind in [
        (require_python, "line"),
        (script_metadata, "cell"),
        (dependencies, "line_cell"),
    ]:
        shell.register_magic_function(  # type: ignore
            func=magic, magic_kind=kind, magic_name=magic.__name__
        )


def script_metadata(line: str, cell: str) -> None:
    if line:
        warn(
            "Non-empty line argument (on the right of %%script_metadata) is ignored",
            category=RuntimeWarning,
        )
    sm = parse_script_metadata(str(cell))
    if "require-python" in sm:
        _require_python(sm["require-python"])
    if "dependencies" in sm:
        _install_requirements(sm["dependencies"])


class PythonRequirementNotSatisfied(Exception):

    def __init__(self, spec: str, version: str) -> None:
        super().__init__(
            (
                f"Python version specification {spec} not satisfied: "
                f"current interpreter is version {version}"
            )
        )
        self.spec = spec
        self.version = version


def _require_python(spec: str) -> None:
    version, *_ = sys.version.split()
    if version not in SpecifierSet(spec):
        raise PythonRequirementNotSatisfied(spec, version)
    LOG.info(f"Current Python version {version} satisfies specification {spec}")


def require_python(line: str = "") -> None:
    _require_python(str(line))


def dependencies(line: str, cell: str = "") -> None:
    dependencies_raw = (
        f"{line.strip()}\n{cell}" if line and cell else line or cell
    ).strip()
    dependencies_normalized = list(parse_dependencies(dependencies_raw))
    if cell:
        if line or dependencies_normalized != [
            line.strip() for line in dependencies_raw.split("\n")
        ]:
            LOG.debug("Dependencies are irregular")
            display(
                Markdown(
                    "\n".join(
                        [
                            (
                                "Requirement specifications are irregular. "
                                "They will be processed as if they had been supplied "
                                "in the following form:"
                            ),
                            "",
                            "```",
                            "%%dependencies",
                            *dependencies_normalized,
                            "```",
                        ]
                    )
                )
            )

    _install_requirements(dependencies_normalized)


def _install_requirements(requirements: Iterable[str]) -> None:
    with NamedTemporaryFile("wt", encoding="utf-8") as file:
        for dep in requirements:
            Requirement(dep)  # Will raise an exception on invalid requirements.
            print(dep, file=file)
        file.flush()

        cmd = [cast(str, _PATH_UV), "pip", "install", "--requirements", file.name]
        LOG.debug("Run " + " ".join(cmd))
        sp.run(cmd).check_returncode()
