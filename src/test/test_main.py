from argparse import Namespace
from collections.abc import Iterator
from jupyter_client.kernelspec import KernelSpec, KernelSpecManager
import os
from pathlib import Path
import pytest  # noqa
import sys
from uuid import uuid4

from uvk.__main__ import (
    display_name_default,
    Env,
    ParametersInstall,
    prepare_kernelspec,
    parse_args,
    PATH_UV,
)


def ns(
    name: str = "uvk",
    display_name: str = display_name_default(),
    user: bool = False,
    prefix: Path | None = None,
    env: list[tuple[str, str]] | None = None,
    quiet: int = 0,
    python: str | None = None,
) -> Namespace:
    return Namespace(
        name=name,
        display_name=display_name,
        user=user,
        prefix=prefix,
        env=[list(t) for t in env] if env else None,
        quiet=quiet,
        python=python,
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
            ns(env=[("TMPDIR", str(Path.home() / "tmp"))]),
            ["--tmp", str(Path.home() / "tmp")],
        ),
        (
            ns(env=[("asdf", "qwer"), ("TMPDIR", "heyhey"), ("zxcv", "hoho")]),
            ["--env", "asdf", "qwer", "--tmp", "heyhey", "--env", "zxcv", "hoho"],
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
        (ns(python="3.11"), ["-p", "3.11"]),
        (ns(python="3.13.3"), ["--python", "3.13.3"]),
        (ns(python=sys.executable), ["-p", sys.executable]),
    ],
)
def test_parse_args(expected: ParametersInstall, args: list[str]) -> None:
    assert expected == parse_args(args)


@pytest.mark.parametrize(
    "display_name,env,python",
    [
        ("Test UVK", [], None),
        ("UVK test hey", [("TMPDIR", "/disk/alt/tmp")], None),
        ("Test UVK", [], "3.12"),
        ("Test UVK", [], sys.executable),
    ],
)
def test_prepare_kernelspec(
    tmp_path: Path,
    display_name: str,
    env: Env,
    python: str | None,
) -> None:
    with prepare_kernelspec(
        "TEST-uvk-TEST", display_name=display_name, env=env, python=python or ""
    ) as dir_kernel:
        for logo in ["logo-32x32.png", "logo-64x64.png", "logo-svg.svg"]:
            assert (dir_kernel / logo).is_file()

        assert (dir_kernel / "kernel.json").is_file()
        kernelspec = KernelSpec.from_resource_dir(str(dir_kernel))
        assert len(kernelspec.argv) >= 4
        assert kernelspec.argv[0] == str(PATH_UV)
        assert kernelspec.display_name == display_name
        assert kernelspec.env == dict(env or {})

        if python:
            try:
                i = kernelspec.argv.index("--python")
                assert kernelspec.argv[i + 1] == python
            except ValueError:
                pytest.fail("No --python in kernelspec arguments")
        else:
            assert "--python" not in kernelspec.argv


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


def install_kernelspec(
    name: str, prefix: str, display_name: str = "UVK unit test"
) -> None:
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
    assert specs[installed_kernel]["spec"]["display_name"] == "UVK unit test"


def test_clobber_existing_kernelspec(
    installed_kernel: str, prefix_install: str
) -> None:
    assert installed_kernel in KernelSpecManager().get_all_specs()
    install_kernelspec(installed_kernel, prefix_install, display_name="ALT")
    assert (
        KernelSpecManager().get_all_specs()[installed_kernel]["spec"]["display_name"]
        == "ALT"
    )
