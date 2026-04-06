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
import shlex
import subprocess as sp
import sys
from tempfile import NamedTemporaryFile
from typing import Any, cast, overload, Protocol
from uv import find_uv_bin
from warnings import warn

from ._parse import parse_dependencies, parse_script_metadata
from .util import uv_

LOG = lg.getLogger(__name__)


class NamedMagic(Protocol):
    __name__: str

    @overload
    def __call__(self, line_or_cell: str = "") -> Any: ...

    @overload
    def __call__(self, line: str, cell: str = "") -> Any: ...


MAGICS_OVERRIDEN: dict[str, NamedMagic] = {}


def load_ipython_extension(shell: InteractiveShell) -> None:
    for magic_, kind, is_overriding in [
        (require_python, "line", False),
        (script_metadata, "cell", False),
        (dependencies, "line_cell", False),
        (_uv_(shell), "line", True),
        (_restore_uv_(shell), "line", False),
    ]:
        magic = cast(NamedMagic, magic_)
        if is_overriding:
            MAGICS_OVERRIDEN[magic.__name__] = shell.magics_manager.magics[kind][magic.__name__]
        shell.register_magic_function(func=magic, magic_kind=kind, magic_name=magic.__name__)  # type: ignore


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
    dependencies_raw = (f"{line.strip()}\n{cell}" if line and cell else line or cell).strip()
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

        cmd = [find_uv_bin(), "pip", "install", "--requirements", file.name]
        LOG.debug("Run " + " ".join(cmd))
        sp.run(cmd).check_returncode()


def _uv_(shell: InteractiveShell) -> NamedMagic:
    def uv(line: str = "") -> None:
        args = shlex.split(line)
        shell.system(" ".join(shlex.quote(token) for token in uv_(args)))

    return cast(NamedMagic, uv)


def _restore_uv_(shell: InteractiveShell) -> NamedMagic:
    def restore_uv(line: str = "") -> None:
        if "uv" in shell.magics_manager.magics["line"]:
            if "uv" in MAGICS_OVERRIDEN:
                uv_previous = MAGICS_OVERRIDEN.pop("uv")
                if callable(uv_previous):
                    shell.register_magic_function(  # ty: ignore[missing-argument]
                        func=uv_previous,
                        magic_kind="line",
                        magic_name="uv",
                    )
                    print(
                        "Restored the implementation of %uv that the uvk extension had overriden."
                    )
                else:
                    print(
                        "WARNING: the %uv magic that the uvk extension overrode does not look like a Python callable. Will not attempt to restore it."
                    )
            else:
                print(
                    "The current %uv implementation was not registered by the uvk extension. No op."
                )
        else:
            print(
                "Strange: no %uv line magic is present. You may need to restart your kernel to restore this standard IPython functionality."
            )

    return cast(NamedMagic, restore_uv)
