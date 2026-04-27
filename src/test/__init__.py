from collections.abc import Callable, Iterator
from dataclasses import dataclass
from importlib.resources import as_file, files
from pathlib import Path
import nbformat
import pytest
import subprocess as sp
import sys
from types import FunctionType
from uv import find_uv_bin

from . import notebooks


@dataclass
class NotebookOnDisk:
    path: Path
    notebook: nbformat.NotebookNode


def notebook(_fn_: FunctionType) -> Callable[[], Iterator[NotebookOnDisk]]:
    name_notebook = f"{_fn_.__name__}.ipynb"
    p = files(notebooks) / name_notebook
    if not p.is_file():
        raise ValueError(f"No notebook named {name_notebook} exists at expected path {p}")
    notebook = nbformat.reads(p.read_text("utf-8"), nbformat.NO_CONVERT)

    def _fixture_notebook() -> Iterator[NotebookOnDisk]:
        with as_file(p) as path:
            yield NotebookOnDisk(path=path, notebook=notebook)

    _fixture_notebook.__name__ = _fn_.__name__
    return pytest.fixture(_fixture_notebook)


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
