import pytest  # noqa
from textwrap import dedent
from typing import Type
from warnings import catch_warnings

from uvk._parse import (
    IllegalLine,
    NoScriptMetadataEndLine,
    NoScriptMetadataStartLine,
    parse_dependencies,
    parse_script_metadata,
    TrailingLines,
)


@pytest.mark.parametrize(
    "line,expected",
    [
        ("", []),
        ("numpy", ["numpy"]),
        ("numpy scipy>1.11", ["numpy", "scipy>1.11"]),
        (
            "numpy scipy>=1.12,<1.15,!=1.13.1 scikit-learn==1.8.0",
            ["numpy", "scipy>=1.12,<1.15,!=1.13.1", "scikit-learn==1.8.0"],
        ),
        (
            """
            numpy
            scipy>=1.12
            scikit-learn==1.8.0
            """,
            ["numpy", "scipy>=1.12", "scikit-learn==1.8.0"],
        ),
        (
            """\
            numpy scipy>=1.12
                scikit-learn==1.8.0
            pandas pyarrow
            """,
            ["numpy", "scipy>=1.12", "scikit-learn==1.8.0", "pandas", "pyarrow"],
        ),
    ],
)
def test_parse_dependencies(line: str, expected: list[str]) -> None:
    assert expected == parse_dependencies(line)


def cook_metadata(metadata_raw: str) -> str:
    """
    Transforms metadata string made to fit Python indent structure into unindented
    paragraphs as expected in the wild.
    """
    return dedent(metadata_raw.rstrip())


@pytest.mark.parametrize(
    "metadata_raw,expected",
    [
        (
            """\
            # /// script
            # requires-python = ">=3.11,!=3.12.2"
            # ///
            """,
            {"requires-python": ">=3.11,!=3.12.2"},
        ),
        (
            """\
            # /// script
            # dependencies = []
            # ///
            """,
            {"dependencies": []},
        ),
        (
            """\
            # /// script
            # dependencies = ["numpy", "requests>=3"]
            # ///
            """,
            {"dependencies": ["numpy", "requests>=3"]},
        ),
        (
            """\
            # /// script
            # dependencies = [
            #     "pandas",
            #     "pyarrow",
            #     "scipy",
            #     "scikit-learn",
            # ]
            # ///
            """,
            {"dependencies": ["pandas", "pyarrow", "scipy", "scikit-learn"]},
        ),
        (
            """\
            # /// script
            # dependencies = [
            #     "duckdb",
            #     "requests",
            # ]
            # requires-python = "==3.11"
            # ///
            """,
            {"dependencies": ["duckdb", "requests"], "requires-python": "==3.11"},
        ),
        (
            """\
            # /// script
            #    dependencies = [  "lesspass",
            #     "requests",
            #            "jupyter-core"]
            # requires-python = ">3.10"
            # ///
            """,
            {
                "dependencies": ["lesspass", "requests", "jupyter-core"],
                "requires-python": ">3.10",
            },
        ),
        (
            """\
            # /// script
            # dependencies = ["datamapplot"]

            # [tool.uv.sources]
            # datamapplot = { git = "https://github.com/TutteInstitute/datamapplot.git" }
            # ///
            """,  # noqa  -- Gotta endure this long line.
            {
                "dependencies": ["datamapplot"],
                "tool": {
                    "uv": {
                        "sources": {
                            "datamapplot": {
                                "git": (
                                    "https://github.com/TutteInstitute/datamapplot.git"
                                ),
                            },
                        },
                    },
                },
            },
        ),
        (
            """\
            # Here is the script metadata
            #
            # /// script
            # requires-python = ">3.10"
            # ///
            """,
            {"requires-python": ">3.10"},
        ),
    ],
)
def test_parse_script_metadata_correct(metadata_raw: str, expected: dict) -> None:
    assert expected == parse_script_metadata(cook_metadata(metadata_raw))


@pytest.mark.parametrize(
    "metadata_raw,expected",
    [
        (
            "",
            NoScriptMetadataStartLine,
        ),
        (
            """\
            # dependencies = [
            #     "numpy",
            #     "requests",
            # ]
            """,
            NoScriptMetadataStartLine,
        ),
        (
            """\
            #/// script
            # requires-python = ">3.10"
            # ///
            """,
            IllegalLine,
        ),
        (
            """\
            # ///script
            # requires-python = ">3.10"
            # ///
            """,
            NoScriptMetadataStartLine,
        ),
        (
            """\
            # ///  script
            # requires-python = ">3.10"
            # ///
            """,
            NoScriptMetadataStartLine,
        ),
        (
            """\
            # /// script
            # requires-python = ">3.10"
            """,
            NoScriptMetadataEndLine,
        ),
        (
            """\
            # /// script
            # requires-python = ">3.10"
            #///
            """,
            IllegalLine,
        ),
        (
            """\
            # /// script
            # requires-python = ">3.10"
            # /// end
            """,
            NoScriptMetadataEndLine,
        ),
        (
            """\
            # /// script
            requires-python = ">3.10"
            # /// end
            """,
            IllegalLine,
        ),
        (
            """\
            /// script
            # requires-python = ">3.10"
            # ///
            """,
            IllegalLine,
        ),
    ],
)
def test_parse_script_metadata_break_convention(
    metadata_raw: str, expected: Type[ValueError]
) -> None:
    with pytest.raises(expected):
        parse_script_metadata(cook_metadata(metadata_raw))


def test_parse_script_metadata_warn_trailing_lines():
    with catch_warnings(record=True, category=TrailingLines) as ws:
        parse_script_metadata(
            cook_metadata(
                """\
                # /// script
                # requires-python = ">3.10"
                # ///
                # asdf
                """,
            )
        )
    assert len(ws) == 1
