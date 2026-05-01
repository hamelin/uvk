from nbformat import NotebookNode
import os
from pathlib import Path
import pytest  # noqa
from textwrap import dedent
from tomllib import TOMLDecodeError
from typing import Type
from unittest.mock import patch
from uv import find_uv_bin

from uvk.launch import (
    get_cmdline_uv,
    get_path_project,
    get_script_metadata,
    extract_script_metadata,
)
from uvk.parse import ScriptMetadataParseError

from . import make_project, notebook


@notebook
def no_metadata(): ...


@notebook
def no_dependency_311(): ...


@notebook
def typical(): ...


@notebook
def last_cell_with_uv_args(): ...


@notebook
def metadata_multiple(): ...


@notebook
def metadata_unparsable(): ...


@notebook
def bad_toml(): ...


@notebook
def metadata_multiple_top_skipped(): ...


@notebook
def metadata_multiple_top_broken(): ...


@notebook
def metadata_in_raw_cell(): ...


@notebook
def metadata_after_raw_cell(): ...


@pytest.fixture
def name2notebook(
    no_metadata: NotebookNode,
    no_dependency_311: NotebookNode,
    typical: NotebookNode,
    last_cell_with_uv_args: NotebookNode,
    metadata_multiple: NotebookNode,
    metadata_unparsable: NotebookNode,
    bad_toml: NotebookNode,
    metadata_multiple_top_skipped: NotebookNode,
    metadata_multiple_top_broken: NotebookNode,
    metadata_in_raw_cell: NotebookNode,
    metadata_after_raw_cell: NotebookNode,
) -> dict[str, NotebookNode]:
    return {
        "no_metadata": no_metadata,
        "no_dependency_311": no_dependency_311,
        "typical": typical,
        "last_cell_with_uv_args": last_cell_with_uv_args,
        "metadata_multiple": metadata_multiple,
        "metadata_unparsable": metadata_unparsable,
        "bad_toml": bad_toml,
        "metadata_multiple_top_skipped": metadata_multiple_top_skipped,
        "metadata_multiple_top_broken": metadata_multiple_top_broken,
        "metadata_in_raw_cell": metadata_in_raw_cell,
        "metadata_after_raw_cell": metadata_after_raw_cell,
    }


@pytest.mark.parametrize(
    "name,expected",
    [
        (
            "no_metadata",
            None,
        ),
        (
            "no_dependency_311",
            """\
            # /// script
            # requires-python = ">=3.11"
            # dependencies = []
            # ///
            """,
        ),
        (
            "typical",
            """\
            # /// script
            # requires-python = ">=3.13"
            # dependencies = [
            #     "lark>=1.3.1",
            #     "requests>=2.33.1",
            # ]
            # ///
            """,
        ),
        (
            "last_cell_with_uv_args",
            """\
            # /// script
            # requires-python = ">=3.13"
            # dependencies = [
            #     "lark>=1.3.1",
            #     "requests>=2.33.1",
            # ]
            #
            # [tool.uvk]
            # uv_args = ["--with-editable", "../my-package"]
            # ///
            """,
        ),
        (
            "metadata_multiple",
            """\
            # This is the metadata.
            # /// script
            # requires-python = ">=3.11"
            # dependencies = []
            # ///
            """,
        ),
        (
            "metadata_multiple_top_skipped",
            """\
            # /// script
            # dependencies = [
            #     "requests>=2.33.1",
            # ]
            #
            # ///
            """,
        ),
        (
            "metadata_in_raw_cell",
            None,
        ),
        (
            "metadata_after_raw_cell",
            """\
            # /// script
            # requires-python = ">=3.13"
            # dependencies = [
            #     "requests>=2.33.1",
            # ]
            #
            # [tool.uvk]
            # uv_args = ["--with-editable", "../my-package"]
            # ///
            """,
        ),
    ],
)
def test_extract_script_metadata_valid(
    expected: str, name: str, name2notebook: dict[str, NotebookNode]
) -> None:
    if isinstance(expected, str):
        expected = dedent(expected).rstrip()
    assert expected == extract_script_metadata(name2notebook[name])


@pytest.mark.parametrize(
    "name,expected",
    [
        ("metadata_unparsable", ScriptMetadataParseError),
        ("bad_toml", TOMLDecodeError),
        ("metadata_multiple_top_broken", ScriptMetadataParseError),
    ],
)
def test_extract_script_metadata_error(
    expected: Type[Exception], name: str, name2notebook: dict[str, NotebookNode]
) -> None:
    with pytest.raises(expected):
        extract_script_metadata(name2notebook[name])


@pytest.fixture
def no_session_name() -> None:
    assert "JPY_SESSION_NAME" not in os.environ
    return None


@pytest.fixture
def name2path(metadata_multiple: NotebookNode, no_metadata: NotebookNode) -> dict[str, str]:
    return {
        "": "",
        "does not exist": "does not exist",
        "metadata_multiple": str(metadata_multiple.metadata._path_),
        "no_metadata": str(no_metadata.metadata._path_),
    }


@pytest.mark.parametrize(
    "name,expected",
    [
        ("", ""),
        ("does not exist", ""),
        (
            "metadata_multiple",
            dedent(
                """\
                # This is the metadata.
                # /// script
                # requires-python = ">=3.11"
                # dependencies = []
                # ///
                """
            ).rstrip(),
        ),
        ("no_metadata", ""),
    ],
)
def test_get_script_metadata(expected, name, name2path) -> None:
    try:
        if "JPY_SESSION_NAME" in os.environ:
            del os.environ["JPY_SESSION_NAME"]
        path = name2path[name]
        if path:
            os.environ["JPY_SESSION_NAME"] = path
            print(os.environ["JPY_SESSION_NAME"])
        metadata = get_script_metadata()
        assert expected == metadata
    finally:
        if "JPY_SESSION_NAME" in os.environ:
            del os.environ["JPY_SESSION_NAME"]


@pytest.mark.parametrize(
    "script_metadata,path_project,expected",
    [
        (
            "",
            None,
            [find_uv_bin(), "run", "--with", "uvk", "--no-project", "--script"],
        ),
        (
            dedent(
                """\
                # /// script
                # requires-python = ">=3.13"
                # dependencies = [
                #     "lark>=1.3.1",
                #     "requests>=2.33.1",
                # ]
                # ///
                """,
            ),
            None,
            [find_uv_bin(), "run", "--with", "uvk", "--no-project", "--script"],
        ),
        (
            "",
            Path("asdf/qwerty"),
            [find_uv_bin(), "run", "--with", "uvk", "--project", "asdf/qwerty"],
        ),
        (
            dedent(
                """\
                # /// script
                # requires-python = ">=3.11"
                # dependencies = []
                # ///
                """,
            ),
            Path("asdf/qwerty"),
            [find_uv_bin(), "run", "--with", "uvk", "--no-project", "--script"],
        ),
        (
            dedent(
                """\
                # /// script
                # requires-python = ">=3.13"
                # dependencies = [
                #     "lark>=1.3.1",
                #     "requests>=2.33.1",
                # ]
                #
                # [tool.uvk]
                # args_uv = ["--cache-dir", "/cache"]
                # ///
                """,
            ),
            None,
            [
                find_uv_bin(),
                "run",
                "--with",
                "uvk",
                "--cache-dir",
                "/cache",
                "--no-project",
                "--script",
            ],
        ),
    ],
)
def test_cmdline_uv_(expected: list[str], script_metadata: str, path_project: Path | None) -> None:
    with patch("uvk.launch.with_uvk", return_value=["--with", "uvk"]):
        assert expected == get_cmdline_uv(script_metadata, path_project)


@pytest.fixture
def path_no_project(tmp_path: Path) -> Path:
    assert not tmp_path.is_relative_to(Path.cwd())
    return tmp_path


def test_path_no_project(path_no_project: Path):
    assert get_path_project(path_no_project) is None


@pytest.fixture
def project_haha(tmp_path: Path) -> Path:
    make_project(tmp_path / "haha")
    return tmp_path / "haha"


def test_path_with_project(project_haha: Path) -> None:
    assert project_haha == get_path_project(project_haha)


@pytest.fixture
def dir_under_haha(project_haha: Path) -> Path:
    p = project_haha / "asdf" / "qwer" / "zxcv"
    p.mkdir(parents=True, exist_ok=True)
    return p


def test_path_under_project(dir_under_haha: Path, project_haha: Path) -> None:
    assert project_haha == get_path_project(dir_under_haha)
