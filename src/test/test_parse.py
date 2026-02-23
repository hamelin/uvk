import pytest  # noqa
from textwrap import dedent

from uvk._parse import parse_dependencies, parse_script_metadata


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
    ],
)
def test_parse_script_metadata_correct(metadata_raw: str, expected: dict) -> None:
    assert expected == parse_script_metadata(dedent(metadata_raw.rstrip()))
