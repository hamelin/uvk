from argparse import Namespace
from pathlib import Path  # noqa
import pytest  # noqa

from uvk.__main__ import display_name_default, parse_args


def ns(name: str, display_name: str, tmp: str) -> Namespace:
    return Namespace(
        name=name,
        display_name=display_name,
        tmp=tmp,
    )


@pytest.mark.parametrize(
    "expected,args",
    [
        (ns("uvk", display_name_default(), ""), []),
    ],
)
def test_parse_args(expected: Namespace, args: list[str]) -> None:
    assert expected == parse_args(args)
