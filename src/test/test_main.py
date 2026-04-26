import pytest  # noqa

from uvk.__main__ import parse_args


def test_fail_no_subcommand() -> None:
    with pytest.raises(SystemExit):
        parse_args([])
