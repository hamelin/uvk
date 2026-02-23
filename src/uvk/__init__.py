"""
The uvk IPython extension provides magicks to manage the dependencies
of an isolated kernel. It also ensures that the uv executable is visible
by the IPython process, as shelling out to uv is how most of the kernel's
specific functionalities are delivered.
"""

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

from ._parse import parse_dependencies

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
        (python_version, "line"),
        (script_metadata, "cell"),
        (dependencies, "line_cell"),
    ]:
        shell.register_magic_function(  # type: ignore
            func=magic, magic_kind=kind, magic_name=magic.__name__
        )


def script_metadata(cell: str) -> None:
    raise NotImplementedError()


class PythonVersionNotSatisfied(Exception):

    def __init__(self, constraint: str, version: str) -> None:
        super().__init__(
            (
                f"Python version constraint {constraint} not satisfied: "
                f"current interpreter is version {version}"
            )
        )
        self.constraint = constraint
        self.version = version


def python_version(line: str = "") -> None:
    version, *_ = sys.version.split()
    if version not in SpecifierSet(str(line)):
        raise PythonVersionNotSatisfied(str(line), version)
    LOG.info(f"Current Python version {version} satisfies constraint {line}")


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

    with NamedTemporaryFile("wt", encoding="utf-8") as file:
        for dep in dependencies_normalized:
            Requirement(dep)  # Will raise an exception on invalid requirements.
            print(dep, file=file)
        file.flush()

        cmd = [cast(str, _PATH_UV), "pip", "install", "--requirements", file.name]
        LOG.debug("Run " + " ".join(cmd))
        sp.run(cmd).check_returncode()
