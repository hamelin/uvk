"""
The uvk IPython extension provides magicks to manage the dependencies
of an isolated kernel. It also ensures that the uv executable is visible
by the IPython process, as shelling out to uv is how most of the kernel's
specific functionalities are delivered.
"""

from IPython.core.interactiveshell import InteractiveShell
import logging as lg
from packaging.specifiers import SpecifierSet
import shutil
import sys

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
    print("TBD")


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


def dependencies(line: str) -> None:
    print("TBD")
