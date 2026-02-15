from argparse import Action, ArgumentParser, Namespace
from collections import defaultdict
from collections.abc import Iterator, Sequence
from contextlib import contextmanager
from jupyter_core.paths import jupyter_data_dir
import json
import logging as lg
from pathlib import Path
import shutil
import sys
from typing import Protocol

LOG = lg.getLogger("uvk")
KernelSpec = dict


try:
    PATH_UV = Path(shutil.which("uv"))  # type: ignore
except TypeError:
    raise OSError(
        "Cannot find the uv executable in the current environment; "
        "consider reinstalling uvk."
    )


def display_name_default() -> str:
    return f"UVK (Python " f"{sys.version_info.major}.{sys.version_info.minor})"


class DefineTMPDIR(Action):

    def __init__(self, option_strings, dest, nargs=None, **kwargs) -> None:
        if nargs is not None:
            raise ValueError("nargs not allowed")
        super().__init__(option_strings, dest, **kwargs)

    def __call__(
        self,
        parser: ArgumentParser,
        ns: Namespace,
        values: str | Sequence | None,
        option_string: str | None = None,
    ) -> None:
        assert isinstance(values, str)
        if not ns.env:
            ns.env = []
        ns.env.append(["TMPDIR", values])


class ParametersInstall(Protocol):

    @property
    def name(self) -> str: ...

    @property
    def display_name(self) -> str: ...

    @property
    def dir_data(self) -> Path: ...

    @property
    def env(self) -> list[tuple[str, str]] | None: ...

    @property
    def quiet(self) -> int: ...

    @property
    def python(self) -> str | None: ...


def dir_data_default() -> Path:
    return Path(sys.prefix) / "share" / "jupyter"


def parse_args(args: list[str] | None = None) -> ParametersInstall:
    parser = ArgumentParser(
        description="Deploys the UVK kernel",
    )
    parser.add_argument(
        "--name",
        help="Name of the kernelspec. Default is `uvk`.",
        default="uvk",
    )
    parser.add_argument(
        "--display-name",
        help=(
            "Pretty name for the kernelspec that will show in Jupyter "
            f"interface. Default is `{display_name_default()}`."
        ),
        default=display_name_default(),
    )
    parser.add_argument(
        "--user",
        dest="dir_data",
        action="store_const",
        const=Path(jupyter_data_dir()),
        help="Install the kernel in user's space.",
    )
    parser.add_argument(
        "--prefix",
        dest="dir_data",
        type=lambda d: Path(d) / "share" / "jupyter",
        help="Install the kernel in the Python distribution at the given prefix path.",
    )
    parser.add_argument(
        "--sys-prefix",
        dest="dir_data",
        action="store_const",
        const=dir_data_default(),
        help=(
            f"Install the kernel in the current environment; equivalent to "
            f"--prefix={sys.prefix}. This is the default."
        ),
    )
    parser.add_argument(
        "--env",
        dest="env",
        action="append",
        nargs=2,
        metavar="VARIABLE VALUE",
        help="Define the given environment variable as the kernel is started.",
    )
    parser.add_argument(
        "--tmp",
        dest="env",
        action=DefineTMPDIR,
        help=(
            "Set the temporary directory where the kernel's environment will be "
            "instantiated."
        ),
    )
    parser.add_argument(
        "-q",
        "--quiet",
        action="count",
        default=0,
        help=(
            "Quiets out the output chatter. Use up to three times to quiet down to "
            "critical errors."
        ),
    )
    parser.add_argument(
        "-p",
        "--python",
        dest="python",
        default=None,
        help=(
            "Set the Python interpreter to use as kernel engine. "
            "Convention for this parameter mirrors uv's --python option. "
            "This can be just a Python version number, such as `3.12` or "
            "`3.13.3`, or the full path to an Python executable, such "
            f"as {sys.executable}."
        ),
    )
    params = parser.parse_args(args)
    if not params.dir_data:
        params.dir_data = dir_data_default()
    return params


class KernelSpecAlreadyExists(Exception):

    def __init__(self, path_kernelspec: Path) -> None:
        self.path_kernelspec = path_kernelspec
        super().__init__(f"Kernelspec already exists at path {path_kernelspec}")


@contextmanager
def install_kernelspec(params: ParametersInstall) -> Iterator[tuple[Path, KernelSpec]]:
    path_kernelspec = params.dir_data / "kernels" / params.name
    path_kernel_json = path_kernelspec / "kernel.json"
    if path_kernelspec.is_dir() and path_kernel_json.is_file():
        raise KernelSpecAlreadyExists(path_kernelspec)

    try:
        path_kernelspec.mkdir(parents=True, exist_ok=False)

        path_resources_kernelspec = (
            Path(sys.prefix) / "share" / "jupyter" / "kernels" / "python3"
        )
        assert path_resources_kernelspec.is_dir()
        for p in path_resources_kernelspec.iterdir():
            # TBD: use own icons
            shutil.copy(p, path_kernelspec / p.name)

        assert path_kernel_json.is_file()
        kernelspec = json.loads(path_kernel_json.read_text(encoding="utf-8"))
        assert "argv" in kernelspec
        kernelspec["argv"] = [
            str(PATH_UV),
            "run",
            "--with",
            "uvk",
            *([] if params.python is None else ["--python", params.python]),
            "--isolated",
            "--no-cache",
            "python",
            "-m",
            "ipykernel_launcher",
            "-f",
            "{connection_file}",
        ]
        kernelspec["display_name"] = params.display_name
        if params.env:
            kernelspec.setdefault("env", {}).update(dict(params.env))

        yield path_kernelspec, kernelspec

        path_kernel_json.write_text(json.dumps(kernelspec), encoding="utf-8")
    except Exception as err:
        LOG.warning(
            f"Following {type(err).__name__} {err}, incipient kernelspec at "
            f"{path_kernelspec} is destroyed"
        )
        shutil.rmtree(path_kernelspec, ignore_errors=True)
        raise


def main():
    lg.basicConfig(level=lg.WARNING, format="%(message)s")
    params = parse_args()
    LOG.setLevel(
        defaultdict(lambda: lg.CRITICAL, {0: lg.INFO, 1: lg.WARN, 2: lg.ERROR})[
            params.quiet
        ]
    )

    try:
        with install_kernelspec(params) as (dir_kernelspec, _):
            LOG.info(f"UVK kernelspec added at {dir_kernelspec}")
    except KernelSpecAlreadyExists as err:
        LOG.warn(
            f"Kernelspec already exists at path {err.path_kernelspec}. "
            "Erring on the side of caution, we refuse to clobber it. "
            "If you mean to replace it, first remove it with "
            "`jupyter kernelspec remove` before attempting this command again."
        )
        sys.exit(2)
    except Exception as err:
        LOG.critical(f"{type(err).__name__}: {err}; abort")
        sys.exit(1)


if __name__ == "__main__":
    main()
