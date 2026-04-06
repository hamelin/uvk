from collections.abc import Iterable
import pytest
import shlex
from uv import find_uv_bin
import sys

import uvk.util


@pytest.mark.parametrize(
    "command,expected",
    [
        ("run", (find_uv_bin(), "run", "--python", sys.executable, "--active")),
        ("init", (find_uv_bin(), "init", "--python", sys.executable)),
        ("add", (find_uv_bin(), "add", "--python", sys.executable, "--active")),
        ("remove", (find_uv_bin(), "remove", "--python", sys.executable, "--active")),
        ("version", (find_uv_bin(), "version", "--python", sys.executable, "--active")),
        ("sync", (find_uv_bin(), "sync", "--python", sys.executable, "--active")),
        ("lock", (find_uv_bin(), "lock", "--python", sys.executable)),
        ("export", (find_uv_bin(), "export", "--python", sys.executable)),
        ("tree", (find_uv_bin(), "tree", "--python", sys.executable)),
        ("format", (find_uv_bin(), "format", "--python", sys.executable)),
        ("venv", (find_uv_bin(), "venv", "--python", sys.executable)),
        ("build", (find_uv_bin(), "build", "--python", sys.executable)),
        ("publish", (find_uv_bin(), "publish", "--python", sys.executable)),
        ("help", (find_uv_bin(), "help", "--python", sys.executable)),
        ("auth login", (find_uv_bin(), "auth", "login", "--python", sys.executable)),
        ("auth logout", (find_uv_bin(), "auth", "logout", "--python", sys.executable)),
        ("auth token", (find_uv_bin(), "auth", "token", "--python", sys.executable)),
        ("auth dir", (find_uv_bin(), "auth", "dir", "--python", sys.executable)),
        ("tool run", (find_uv_bin(), "tool", "run", "--python", sys.executable)),
        ("tool install", (find_uv_bin(), "tool", "install", "--python", sys.executable)),
        ("tool upgrade", (find_uv_bin(), "tool", "upgrade", "--python", sys.executable)),
        ("tool list", (find_uv_bin(), "tool", "list", "--python", sys.executable)),
        ("tool uninstall", (find_uv_bin(), "tool", "uninstall", "--python", sys.executable)),
        ("tool update-shell", (find_uv_bin(), "tool", "update-shell", "--python", sys.executable)),
        ("tool dir", (find_uv_bin(), "tool", "dir", "--python", sys.executable)),
        ("python list", (find_uv_bin(), "python", "list", "--python", sys.executable)),
        ("python install", (find_uv_bin(), "python", "install", "--python", sys.executable)),
        ("python upgrade", (find_uv_bin(), "python", "upgrade", "--python", sys.executable)),
        ("python find", (find_uv_bin(), "python", "find", "--python", sys.executable)),
        ("python pin", (find_uv_bin(), "python", "pin", "--python", sys.executable)),
        ("python dir", (find_uv_bin(), "python", "dir", "--python", sys.executable)),
        ("python uninstall", (find_uv_bin(), "python", "uninstall", "--python", sys.executable)),
        (
            "python update-shell",
            (find_uv_bin(), "python", "update-shell", "--python", sys.executable),
        ),
        ("pip compile", (find_uv_bin(), "pip", "compile", "--python", sys.executable)),
        ("pip sync", (find_uv_bin(), "pip", "sync", "--python", sys.executable)),
        ("pip install", (find_uv_bin(), "pip", "install", "--python", sys.executable)),
        ("pip uninstall", (find_uv_bin(), "pip", "uninstall", "--python", sys.executable)),
        ("pip freeze", (find_uv_bin(), "pip", "freeze", "--python", sys.executable)),
        ("pip list", (find_uv_bin(), "pip", "list", "--python", sys.executable)),
        ("pip show", (find_uv_bin(), "pip", "show", "--python", sys.executable)),
        ("pip tree", (find_uv_bin(), "pip", "tree", "--python", sys.executable)),
        ("pip check", (find_uv_bin(), "pip", "check", "--python", sys.executable)),
        ("cache clean", (find_uv_bin(), "cache", "clean", "--python", sys.executable)),
        ("cache prune", (find_uv_bin(), "cache", "prune", "--python", sys.executable)),
        ("cache dir", (find_uv_bin(), "cache", "dir", "--python", sys.executable)),
        ("cache size", (find_uv_bin(), "cache", "size", "--python", sys.executable)),
        ("self update", (find_uv_bin(), "self", "update", "--python", sys.executable)),
        ("self version", (find_uv_bin(), "self", "version", "--python", sys.executable)),
        ("", (find_uv_bin(),)),
        ("-h", (find_uv_bin(), "-h", "--python", sys.executable)),
        ("--version", (find_uv_bin(), "--version", "--python", sys.executable)),
        ("asdf", (find_uv_bin(), "asdf", "--python", sys.executable)),
        ("asdf qwer", (find_uv_bin(), "asdf", "--python", sys.executable, "qwer")),
        (
            "sync --inexact",
            (find_uv_bin(), "sync", "--python", sys.executable, "--active", "--inexact"),
        ),
    ],
)
def test_uv_add_active(expected: tuple[str, ...], command: str) -> None:
    assert expected == uvk.util.uv_(shlex.split(command))


@pytest.mark.parametrize(
    "project,expected",
    [
        ((), (find_uv_bin(), "add", "--python", sys.executable, "--active", "requests")),
        (
            ("--project", "asdf/qwer"),
            (
                find_uv_bin(),
                "add",
                "--python",
                sys.executable,
                "--project",
                "asdf/qwer",
                "--active",
                "requests",
            ),
        ),
    ],
)
def test_uv_project(expected: tuple[str, ...], project: Iterable[str]) -> None:
    assert expected == uvk.util.uv_(("add", "requests"), project)
