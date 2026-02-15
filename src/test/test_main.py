from argparse import Namespace
from jupyter_core.paths import jupyter_data_dir
from pathlib import Path  # noqa
import pytest  # noqa
import sys

from uvk.__main__ import (
    dir_data_default,
    display_name_default,
    install_kernelspec,
    KernelSpecAlreadyExists,
    ParametersInstall,
    parse_args,
    PATH_UV,
)


def ns(
    name: str = "uvk",
    display_name: str = display_name_default(),
    dir_data: str | Path = dir_data_default(),
    env: list[tuple[str, str]] | None = None,
) -> Namespace:
    return Namespace(
        name=name,
        display_name=display_name,
        dir_data=Path(dir_data),
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
def test_parse_args(expected: ParametersInstall, args: list[str]) -> None:
    assert expected == parse_args(args)


@pytest.mark.parametrize(
    "display_name,env",
    [
        ("Test UVK", []),
        ("UVK test hey", [("TMPDIR", "/disk/alt/tmp")]),
    ],
)
def test_kernelspec(
    tmp_path: Path, display_name: str, env: list[tuple[str, str]]
) -> None:
    params = Namespace(
        name="test-uvk",
        display_name=display_name,
        dir_data=tmp_path / "kernels",
        env=env,
    )
    with install_kernelspec(params) as (dir_kernelspec, kernelspec):
        assert dir_kernelspec.relative_to(params.dir_data)
        assert dir_kernelspec.name == params.name
        assert list(dir_kernelspec.glob("logo*.png"))
        assert kernelspec.get("argv", [None])[0] == str(PATH_UV)
        assert kernelspec.get("display_name", "") == params.display_name
        if params.env:
            assert dict(params.env) == kernelspec.get("env", {})
        else:
            assert "env" not in kernelspec


def test_fail_on_overwriting_kernelspec(tmp_path):
    params = Namespace(
        name="uvktest", display_name="UVK test", dir_data=tmp_path, env=[]
    )
    with install_kernelspec(params):
        pass
    with pytest.raises(KernelSpecAlreadyExists):
        with install_kernelspec(params):
            pass
