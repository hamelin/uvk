from argparse import ArgumentParser, Namespace
from collections.abc import Iterator, Sequence
from contextlib import contextmanager
from importlib.resources import files
from jupyter_client import protocol_version
from jupyter_client.kernelspec import KernelSpec, KernelSpecManager
import logging as lg
from pathlib import Path
import shutil
import sys
from tempfile import TemporaryDirectory

from . import resources
from .util import (
    add_args_quiet_verbose,
    get_uv_permanent,
    log_level,
)


LOG = lg.getLogger(__name__)
Env = Sequence[tuple[str, str]]


def display_name_default() -> str:
    return f"Python {sys.version_info.major} (uvk)"


# class ParametersInstall(Protocol):
#     @property
#     def name(self) -> str: ...

#     @property
#     def display_name(self) -> str: ...

#     @property
#     def user(self) -> bool: ...

#     @property
#     def prefix(self) -> Path | None: ...

#     @property
#     def env(self) -> list[tuple[str, str]] | None: ...

#     @property
#     def quiet(self) -> int: ...


@contextmanager
def prepare_kernelspec(
    name: str,
    display_name: str,
    env: Env = [],
) -> Iterator[Path]:
    with TemporaryDirectory() as dir_:
        dir_kernel = Path(dir_)
        for name_logo in ["logo-32x32.png", "logo-64x64.png", "logo-svg.svg"]:
            with (
                (files(resources) / name_logo).open(mode="rb") as src,
                (dir_kernel / name_logo).open(mode="wb") as dest,
            ):
                shutil.copyfileobj(src, dest)

        LOG.debug(f"Using uv at {get_uv_permanent()}")
        with (dir_kernel / "kernel.json").open(mode="w", encoding="utf-8") as file:
            file.write(
                KernelSpec(
                    argv=[
                        get_uv_permanent(),
                        "run",
                        "--with",
                        "uvk",
                        "--isolated",
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


def install(parser: ArgumentParser) -> None:
    """
    Install the uvk kernel so it can be used with Jupyter.
    """
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
            f"Install the kernel in the current environment; equivalent to --prefix={sys.prefix}."
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
    add_args_quiet_verbose(parser)
    parser.set_defaults(_main_=_main_)


def _main_(params: Namespace) -> None:
    LOG.setLevel(log_level(params))
    try:
        mgr = KernelSpecManager()
        with prepare_kernelspec(
            name=params.name,
            display_name=params.display_name,
            env=params.env or [],
        ) as dir_ks:
            mgr.install_kernel_spec(
                str(dir_ks),
                params.name,
                user=params.user,
                prefix=str(params.prefix) if params.prefix else None,
            )
    except (ValueError, OSError) as err:
        LOG.critical(str(err))
        sys.exit(1)
    except Exception as err:
        LOG.critical(f"{type(err).__name__}: {err}; abort")
        sys.exit(2)
