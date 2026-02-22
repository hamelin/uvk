import pytest  # noqa

from uvk._parse import parse_dependencies


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
