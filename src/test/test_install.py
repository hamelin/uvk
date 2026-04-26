from argparse import Namespace
from collections.abc import Iterator
import json
from jupyter_client.kernelspec import KernelSpec, KernelSpecManager
import os
from pathlib import Path
import pytest  # noqa
import subprocess as sp
import sys
from uuid import uuid4
from uv import find_uv_bin

from uvk.__main__ import parse_args
from uvk.install import (
    _main_,
    display_name_default,
    Env,
    prepare_kernelspec,
)
from uvk.util import dir_cache_uv, get_uv_permanent


def ns(
    name: str = "uvk",
    display_name: str = display_name_default(),
    user: bool = False,
    prefix: Path | None = None,
    env: list[tuple[str, str]] | None = None,
    quiet: int = 0,
) -> Namespace:
    return Namespace(
        command="install",
        name=name,
        display_name=display_name,
        user=user,
        prefix=prefix,
        env=[list(t) for t in env] if env else None,
        quiet=quiet,
        _main_=_main_,
    )


@pytest.mark.parametrize(
    "expected,args",
    [
        (ns(), []),
        (ns(name="uvk-test"), ["--name", "uvk-test"]),
        (ns(display_name="heyhey"), ["--display-name", "heyhey"]),
        (ns(user=True, prefix=None), ["--user"]),
        (
            ns(user=False, prefix=Path("asdf/qwer/zxcv")),
            ["--prefix", "asdf/qwer/zxcv"],
        ),
        (ns(user=False, prefix=Path(sys.prefix)), ["--sys-prefix"]),
        (ns(env=[("heyhey", "hoho")]), ["--env", "heyhey", "hoho"]),
        (
            ns(env=[("asdf", "qwer"), ("zxcv", "hoho")]),
            ["--env", "asdf", "qwer", "--env", "zxcv", "hoho"],
        ),
        (
            ns(display_name="nomnom", user=True, prefix=Path("foo/bar")),
            [
                "--sys-prefix",
                "--prefix",
                "foo/bar",
                "--display-name",
                "nomnom",
                "--user",
            ],
        ),
        (ns(quiet=1), ["--quiet"]),
        (ns(quiet=4), ["-qqq", "--quiet"]),
    ],
)
def test_parse_args_install(expected: Namespace, args: list[str]) -> None:
    assert expected == parse_args(["install", *args])


@pytest.mark.parametrize(
    "display_name,env",
    [
        ("Test uvk", []),
        ("uvk test hey", [("ANYWIDGET_HMR", "1")]),
        ("Test uvk", []),
        ("Test uvk", []),
    ],
)
def test_prepare_kernelspec(
    tmp_path: Path,
    display_name: str,
    env: Env,
) -> None:
    with prepare_kernelspec("TEST-uvk-TEST", display_name=display_name, env=env) as dir_kernel:
        for logo in ["logo-32x32.png", "logo-64x64.png", "logo-svg.svg"]:
            assert (dir_kernel / logo).is_file()

        assert (dir_kernel / "kernel.json").is_file()
        kernelspec = KernelSpec.from_resource_dir(str(dir_kernel))
        assert len(kernelspec.argv) >= 4
        assert kernelspec.argv[0] == get_uv_permanent()
        assert kernelspec.display_name == display_name
        assert kernelspec.env == dict(env or {})


@pytest.fixture
def path_tmp_jupyter(tmp_path: Path) -> Iterator[Path]:
    jupyter_path = os.environ.get("JUPYTER_PATH", None)
    try:
        dir_jupyter = tmp_path / "share" / "jupyter"
        dir_jupyter.mkdir(parents=True, exist_ok=False)
        os.environ["JUPYTER_PATH"] = str(dir_jupyter)
        yield dir_jupyter
    finally:
        del os.environ["JUPYTER_PATH"]
        if jupyter_path:
            os.environ["JUPYTER_PATH"] = jupyter_path


@pytest.fixture
def name_kernel() -> str:
    return f"uvk-{uuid4()}"


def test_path_tmp_jupyter(path_tmp_jupyter: Path) -> None:
    mgr = KernelSpecManager()
    assert str(path_tmp_jupyter / "kernels") in mgr.kernel_dirs


def install_kernelspec(name: str, prefix: str, display_name: str = "uvk unit test") -> None:
    with prepare_kernelspec(name, display_name=display_name) as dir:
        KernelSpecManager().install_kernel_spec(str(dir), name, prefix=prefix)


@pytest.fixture
def prefix_install(tmp_path: Path) -> str:
    return str(tmp_path)


@pytest.fixture
def installed_kernel(prefix_install: str, path_tmp_jupyter: Path) -> str:
    name_kernel = f"uvk-{uuid4()}"
    install_kernelspec(name_kernel, prefix_install)
    return name_kernel


def test_install_kernelspec(installed_kernel: str) -> None:
    mgr = KernelSpecManager()
    specs = mgr.get_all_specs()
    assert installed_kernel in mgr.get_all_specs()
    assert specs[installed_kernel]["spec"]["display_name"] == "uvk unit test"


def test_clobber_existing_kernelspec(installed_kernel: str, prefix_install: str) -> None:
    assert installed_kernel in KernelSpecManager().get_all_specs()
    install_kernelspec(installed_kernel, prefix_install, display_name="ALT")
    assert KernelSpecManager().get_all_specs()[installed_kernel]["spec"]["display_name"] == "ALT"


def test_uvx_uvk(tmp_path: Path) -> None:
    dir_env = tmp_path / "myenv"
    sp.run([find_uv_bin(), "venv", str(dir_env)]).check_returncode()
    sp.run(
        [
            find_uv_bin(),
            "tool",
            "run",
            "--isolated",
            "--with-editable",
            ".",
            "uvk",
            "install",
            "--prefix",
            dir_env,
            "--debug",
        ]
    )
    dir_kernel = dir_env / "share" / "jupyter" / "kernels" / "uvk"
    assert dir_kernel.is_dir()
    kernel_json = dir_kernel / "kernel.json"
    assert kernel_json.is_file()
    kernel = json.loads(kernel_json.read_text("utf-8"))
    assert "argv" in kernel
    assert not Path(kernel["argv"][0]).is_relative_to(dir_cache_uv())
