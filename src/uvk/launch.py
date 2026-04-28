from argparse import ArgumentParser, Namespace
import logging as lg
from nbformat import NotebookNode, reads as as_notebook, NO_CONVERT
from nbformat.reader import NotJSONError
import os
from pathlib import Path
import shlex
import subprocess as sp
import sys
from tempfile import NamedTemporaryFile
from tomllib import TOMLDecodeError
from textwrap import dedent
from uv import find_uv_bin

from .parse import NoMetadata, parse_script_metadata, ScriptMetadataParseError


LOG = lg.getLogger(__name__)


def launch(parser: ArgumentParser) -> None:
    """
    Launch the IPython kernel through uv run.
    """
    parser.add_argument(
        "-f",
        dest="connection_file",
        required=True,
        help="""
            JSON file in which to store connection info. This file will contain the IP, ports,
            and authentication key needed to connect clients to this kernel. By default,
            this file will be created in the security dir of the current profile, but can be
            specified by absolute path.
        """,
    )
    parser.set_defaults(_main_=_main_)


def get_script_metadata() -> str:
    session = os.environ.get("JPY_SESSION_NAME", "")
    if session and (path_notebook := Path(session)).is_file():
        if path_notebook.name.endswith(".ipynb"):
            try:
                metadata_ = extract_script_metadata(
                    as_notebook(path_notebook.read_text("utf-8"), NO_CONVERT)
                )
                if metadata_:
                    LOG.debug(f"Extracted inline metadata from notebook [{path_notebook}]")
                    return str(metadata_)
                else:
                    LOG.debug(
                        f"Notebook [{path_notebook}] does not seem to contain inline metadata."
                    )
                    return ""
            except NotJSONError:
                LOG.error(
                    f"Cannot read notebook file [{path_notebook}] as JSON, so no inline metadata can be extracted"
                )
                return ""
        else:
            LOG.info(
                f"The Jupyter session name [{path_notebook}] maps to a non-notebook file, so we don't attempt at extracting inline metadata"
            )
            return ""
    LOG.info(f"Session named [{session}] does not map to a local file, so no inline metadata")
    return ""


def get_path_project(source: Path) -> Path | None:
    cp = sp.run(
        [find_uv_bin(), "sync", "--check"],
        cwd=source,
        stdin=sp.DEVNULL,
        stdout=sp.PIPE,
        stderr=sp.STDOUT,
        encoding="utf-8",
    )
    for line in cp.stdout.splitlines():
        if line.startswith("Would use project environment at: "):
            prefix, path_raw = line.split(": ")
            path_venv = source / Path(path_raw.strip())
            path_project = path_venv.parent
            if path_project.is_dir():
                if (path_project / "pyproject.toml").is_file():
                    return path_project
                else:
                    LOG.debug(
                        f"Found directory {path_project}, but it does not contain pyproject.toml"
                    )
            else:
                LOG.debug(
                    f"Found directory {path_project} from uv sync output, but it does not exist"
                )
    return None


def get_cmdline_uv(script_metadata: str, path_project: Path | None) -> list[str]:
    try:
        metadata = parse_script_metadata(script_metadata) or {}
    except (ScriptMetadataParseError, TOMLDecodeError):
        metadata = {}

    metadata_uvk = metadata.get("tool", {}).get("uvk", {})
    args_uv = metadata_uvk.get("args_uv", [])
    cmdline = [find_uv_bin(), "run", "--with", "uvk", *args_uv]

    if path_project and script_metadata:
        LOG.warning(f"Since notebook has script metadata, project path {path_project} is ignored")
        path_project = None
    if path_project:
        LOG.info(f"Associating kernel to project in directory {path_project}")
        cmdline += ["--project", str(path_project)]
    else:
        LOG.info("Running kernel in isolated environment")
        cmdline += ["--no-project", "--script"]

    return cmdline


def _main_(params: Namespace) -> None:
    # LOG.setLevel(log_level(params))
    LOG.setLevel(lg.DEBUG)
    script_metadata = get_script_metadata()
    if script_metadata:
        LOG.debug("Notebook carries valid script metadata")
    else:
        LOG.debug("No script metadata found in notebook code cells")

    path_project = get_path_project(Path.cwd())
    if path_project:
        LOG.debug(f"Found project path: {path_project}")
    else:
        LOG.debug("No project found")

    cmdline_uv = get_cmdline_uv(script_metadata, path_project)
    env = compose_env_kernel(cmdline_uv)
    LOG.debug(
        f"uv command line: {env['UVK_CMDLINE_PREFIX']}  # followed with script and connection file"
    )

    with NamedTemporaryFile(mode="w+", encoding="utf-8", suffix=".py") as script_launch:
        print(script_metadata, file=script_launch)
        print(
            dedent(
                """\
                from ipykernel import kernelapp as app
                app.launch_new_instance()
                """
            ),
            file=script_launch,
        )
        script_launch.flush()

        cp = sp.run([*cmdline_uv, script_launch.name, "-f", params.connection_file], env=env)
    sys.exit(cp.returncode)


def extract_script_metadata(notebook: NotebookNode) -> str | None:
    for cell in notebook.cells:
        if cell.cell_type == "code":
            try:
                if parse_script_metadata(cell.source):
                    return cell.source
            except NoMetadata:
                pass
    return None


def compose_env_kernel(cmdline_prefix: list[str]) -> dict[str, str]:
    env = os.environ.copy()
    if "--project" in cmdline_prefix:
        LOG.debug("Having a project dir, we drop VIRTUAL_ENV to avoid uv warning")
        del env["VIRTUAL_ENV"]
    env["UVK_CMDLINE_PREFIX"] = " ".join(shlex.quote(token) for token in cmdline_prefix)
    return env
