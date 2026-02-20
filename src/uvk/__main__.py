from argparse import Action, ArgumentParser, Namespace
from collections import defaultdict
from collections.abc import Iterator, Sequence
from contextlib import contextmanager
from importlib.resources import open_binary
from jupyter_client import protocol_version
from jupyter_client.kernelspec import KernelSpec, KernelSpecManager
import logging as lg
from pathlib import Path
import shutil
import sys
from tempfile import TemporaryDirectory
from typing import Protocol

from . import resources

LOG = lg.getLogger("uvk")
Env = Sequence[tuple[str, str]]


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
    def user(self) -> bool: ...

    @property
    def prefix(self) -> Path | None: ...

    @property
    def env(self) -> list[tuple[str, str]] | None: ...

    @property
    def quiet(self) -> int: ...

    @property
    def python(self) -> str | None: ...


# def dir_data_default() -> Path:
#     return Path(sys.prefix) / "share" / "jupyter"


def parse_args(args: list[str] | None = None) -> ParametersInstall:
    parser = ArgumentParser(
        description=(
            "Deploys the UVK kernel. By default, the kernel is installed in the system "
            "space, and an error is raised if the current user does not have the right "
            "to write in system directories. Various options can change this behavior."
        ),
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
        default=False,
        action="store_true",
        help="Install the kernel in the user's space.",
    )
    parser.add_argument(
        "--prefix",
        default=None,
        type=Path,
        help="Install the kernel in the Python distribution at the given prefix path.",
    )
    parser.add_argument(
        "--sys-prefix",
        dest="prefix",
        action="store_const",
        const=Path(sys.prefix),
        help=(
            f"Install the kernel in the current environment; equivalent to "
            f"--prefix={sys.prefix}."
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
        "--debug",
        dest="quiet",
        action="store_const",
        const=-1,
        help="Debug-level output chatter.",
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
    return parser.parse_args(args)


@contextmanager
def prepare_kernelspec(
    name: str, display_name: str, env: Env = [], python: str = ""
) -> Iterator[Path]:
    with TemporaryDirectory() as dir_:
        dir_kernel = Path(dir_)
        for name_logo in ["logo-32x32.png", "logo-64x64.png", "logo-svg.svg"]:
            with (
                open_binary(resources, name_logo) as src,
                (dir_kernel / name_logo).open(mode="wb") as dest,
            ):
                shutil.copyfileobj(src, dest)

        with (dir_kernel / "kernel.json").open(mode="w", encoding="utf-8") as file:
            file.write(
                KernelSpec(
                    argv=[
                        str(PATH_UV),
                        "run",
                        "--with",
                        "uvk",
                        *([] if not python else ["--python", python]),
                        "--isolated",
                        "--no-cache",
                        "python",
                        "-m",
                        "ipykernel_launcher",
                        "-f",
                        "{connection_file}",
                    ],
                    name=name,
                    display_name=display_name,
                    env=dict(env or []),
                    language="python",
                    metadata={"debugger": True},
                    kernel_protocol_version=protocol_version,
                ).to_json()
            )
        yield dir_kernel


def main():
    lg.basicConfig(level=lg.INFO, format="%(message)s")
    params = parse_args()
    lg.getLogger().setLevel(
        defaultdict(
            lambda: lg.CRITICAL, {-1: lg.DEBUG, 0: lg.INFO, 1: lg.WARN, 2: lg.ERROR}
        )[params.quiet]
    )

    try:
        mgr = KernelSpecManager()
        with prepare_kernelspec(
            name=params.name,
            display_name=params.display_name,
            env=params.env,
            python=params.python,
        ) as dir_ks:
            mgr.install_kernel_spec(
                str(dir_ks), params.name, user=params.user, prefix=params.prefix
            )
    except (ValueError, OSError) as err:
        LOG.critical(str(err))
        sys.exit(1)
    except Exception as err:
        LOG.critical(f"{type(err).__name__}: {err}; abort")
        sys.exit(2)


if __name__ == "__main__":
    main()
