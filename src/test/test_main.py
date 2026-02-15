from argparse import Namespace
from jupyter_core.paths import jupyter_data_dir
from pathlib import Path  # noqa
import pytest  # noqa
import sys

from uvk.__main__ import display_name_default, parse_args


def ns(
    name: str = "uvk",
    display_name: str = display_name_default(),
    dir_data: str | Path | None = None,
    env: list[tuple[str, str]] | None = None,
) -> Namespace:
    return Namespace(
        name=name,
        display_name=display_name,
        dir_data=Path(dir_data) if dir_data else None,
        env=[list(t) for t in env] if env else None,
    )


@pytest.mark.parametrize(
    "expected,args",
    [
        (ns(), []),
        (ns(name="uvk-test"), ["--name", "uvk-test"]),
        (ns(display_name="heyhey"), ["--display-name", "heyhey"]),
        (ns(dir_data=jupyter_data_dir()), ["--user"]),
        (ns(dir_data="asdf/qwer/zxcv/share/jupyter"), ["--prefix", "asdf/qwer/zxcv"]),
        (ns(dir_data=Path(sys.prefix) / "share" / "jupyter"), ["--sys-prefix"]),
        (ns(env=[("heyhey", "hoho")]), ["--env", "heyhey", "hoho"]),
        (
            ns(env=[("TMPDIR", str(Path.home() / "tmp"))]),
            ["--tmp", str(Path.home() / "tmp")],
        ),
        (
            ns(env=[("asdf", "qwer"), ("TMPDIR", "heyhey"), ("zxcv", "hoho")]),
            ["--env", "asdf", "qwer", "--tmp", "heyhey", "--env", "zxcv", "hoho"],
        ),
        (
            ns(dir_data=jupyter_data_dir(), display_name="nomnom"),
            [
                "--sys-prefix",
                "--prefix",
                "foo/bar",
                "--display-name",
                "nomnom",
                "--user",
            ],
        ),
    ],
)
def test_parse_args(expected: Namespace, args: list[str]) -> None:
    assert expected == parse_args(args)
