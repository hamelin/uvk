from argparse import ArgumentParser
import json
import logging as lg
from pathlib import Path
import shutil
import subprocess as sp
import sys


LOG = lg.getLogger("uvk")


def main():
    lg.basicConfig(level=lg.DEBUG, format="%(levelname)-10s %(message)s")

    parser = ArgumentParser(
        description="Deploys the UVK kernel",
    )
    parser.add_argument(
        "--name",
        help="Name of the kernelspec. Default is `uvk`.",
        default="uvk",
    )
    displayname_default = (
        f"UVK (Python "
        f"{sys.version_info.major}.{sys.version_info.minor})"
    )
    parser.add_argument(
        "--display-name",
        help=(
            "Pretty name for the kernelspec that will show in Jupyter "
            f"interface. Default is `{displayname_default}`."
        ),
        default=displayname_default,
    )
    parser.add_argument(
        "--tmp",
        help="Location of the temporary directory. Default is the system's.",
        default="",
    )
    args = parser.parse_args()

    path_uv = shutil.which("uv")
    if not path_uv:
        LOG.error("Cannot find jupyter executable. Abort")
        sys.exit(1)

    cp = sp.run(["jupyter", "--paths", "--json"], stdout=sp.PIPE)
    paths_data = list(json.loads(cp.stdout).get("data") or [])
    if not paths_data:
        LOG.error("Cannot interpret the output of jupyter --paths. Abort")
        sys.exit(2)
    for p in paths_data:
        dir = Path(p)
        if dir.is_relative_to(Path.home() / ".local"):
            dir_kernelspecs_user = dir / "kernels"
            break
    else:
        LOG.error(
            "Cannot find the user data path where Jupyter would find "
            "user-specific kernelspecs. Abort"
        )
        sys.exit(3)

    path_kernelspec_resources = (
        Path(sys.prefix) / "share" / "jupyter" / "kernels" / "python3"
    )
    if not path_kernelspec_resources.is_dir():
        LOG.error(
            "The directory we expected to find kernelspec resources in does"
            "not exist. Abort"
        )
        sys.exit(4)
    dir_kernelspec_new = dir_kernelspecs_user / args.name
    if dir_kernelspec_new.is_dir():
        LOG.warn(
            f"Kernel directory {dir_kernelspec_new} already exists. "
            "Since carrying on would overwrite it, "
            "we err on the side of caution and abort. "
            "Delete it yourself and retry if you would rather overwrite."
        )
        sys.exit(5)
    dir_kernelspec_new.mkdir(parents=True, exist_ok=False)
    for p in path_kernelspec_resources.iterdir():
        shutil.copy(p, dir_kernelspec_new / p.name, follow_symlinks=True)

    path_kernel_json = dir_kernelspec_new / "kernel.json"
    if not path_kernel_json.is_file():
        LOG.error("Copying kernelspec resources failed somehow. Abort")
        sys.exit(6)
    kernel_json = json.loads(path_kernel_json.read_text(encoding="utf-8"))
    kernel_json["argv"] = [
        str(path_uv),
        "run",
        "--with",
        "uvk",
        "--isolated",
        "--no-cache",
        "python",
        "-m",
        "ipykernel_launcher",
        "-f",
        "{connection_file}",
    ]
    kernel_json["display_name"] = args.display_name
    if args.tmp:
        kernel_json["env"] = {"TMPDIR": args.tmp}
    path_kernel_json.write_text(json.dumps(kernel_json, indent=2), encoding="utf-8")
    LOG.info(f"UVK kernelspec added at {dir_kernelspec_new}")


if __name__ == "__main__":
    main()
