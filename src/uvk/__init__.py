"""
The uvk IPython extension provides magicks to manage the dependencies
of an isolated kernel. It also ensures that the uv executable is visible
by the IPython process, as shelling out to uv is how most of the kernel's
specific functionalities are delivered.
"""


from IPython.core.magic import cell_magic, line_magic, line_cell_magic
import subprocess as sp


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


def load_ipython_extension(ipython) -> None:
    try:
        sp.run(["uv"], stdout=sp.DEVNULL, stderr=sp.DEVNULL)
    except OSError:
        raise CannotFindUV()


@cell_magic
def script_metadata(cell: str) -> None:
    print("TBD")


@line_magic
def python_version(line: str) -> None:
    print("TBD")


@line_cell_magic
def dependencies(line: str) -> None:
    print("TBD")
