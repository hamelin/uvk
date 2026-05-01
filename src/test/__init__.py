from collections.abc import Callable, Iterator
from importlib.resources import as_file, files
from importlib.resources.abc import Traversable
from pathlib import Path
import nbformat
import pytest
import subprocess as sp
import sys
from types import FunctionType
from typing import Protocol
from uv import find_uv_bin

from . import notebooks


class Readable(Protocol):
    def read_text(self, encoding: str) -> str: ...


def load_notebook(p: Readable) -> nbformat.NotebookNode:
    return nbformat.reads(p.read_text("utf-8"), nbformat.NO_CONVERT)


def get_notebook_resource(name: str) -> Traversable:
    name_notebook = f"{name}.ipynb"
    p = files(notebooks) / name_notebook
    if not p.is_file():
        raise ValueError(f"No notebook named {name_notebook} exists at expected path {p}")
    return p


def notebook(_fn_: FunctionType) -> Callable[[], Iterator[nbformat.NotebookNode]]:
    def _fixture_notebook() -> Iterator[nbformat.NotebookNode]:
        with as_file(get_notebook_resource(_fn_.__name__)) as path:
            notebook = load_notebook(path)
            notebook.metadata._path_ = str(path)
            yield notebook

    _fixture_notebook.__name__ = _fn_.__name__
    return pytest.fixture(_fixture_notebook)


# def notebook_run(_fn_: FunctionType) -> Callable[[Path, str], nbformat.NotebookNode]:
#     def _fixture_notebook(tmp_path: Path, kernelspec: str) -> nbformat.NotebookNode:
#         source = load_notebook(get_notebook_resource(_fn_.__name__))
#         source["metadata"]["kernelspec"]["name"] = kernelspec
#         path_source = tmp_path / "source.ipynb"
#         path_source.write_text(nbformat.writes(source, nbformat.NO_CONVERT), encoding="utf-8")
#         cp = sp.run(
#             [
#                 find_uv_bin(),
#                 "run",
#                 "--dev",
#                 "jupyter",
#                 "nbconvert",
#                 "--stdout",
#                 "--to",
#                 "notebook",
#                 "--execute",
#                 "--allow-errors",
#                 str(path_source.resolve()),
#             ],
#             encoding="utf-8",
#             stdout=sp.PIPE,
#             env=os.environ | {"JPY_SESSION_NAME": str(path_source.resolve())},
#         )
#         assert cp.returncode == 0
#         return nbformat.reads(cp.stdout, nbformat.NO_CONVERT)

#     _fixture_notebook.__name__ = _fn_.__name__
#     return pytest.fixture(_fixture_notebook)


def make_project(home: Path) -> None:
    sp.run(
        [
            find_uv_bin(),
            "init",
            "--name",
            home.name,
            "--python",
            sys.executable,
            "--lib",
            "--no-description",
            "--author-from",
            "none",
            "--vcs",
            "none",
            "--build-backend",
            "setuptools",
            "--no-readme",
            "--no-pin-python",
            str(home),
        ],
        check=True,
    )
    sp.run([find_uv_bin(), "add", "--project", str(home), "lark"], cwd=home, check=True)
    sp.run([find_uv_bin(), "version", "--project", str(home), "0.0.2"], cwd=home, check=True)
