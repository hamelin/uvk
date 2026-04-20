from collections.abc import Iterable
from dataclasses import dataclass
import re
from pathlib import Path
from psutil import Process
import subprocess as sp
import sys
from uv import find_uv_bin


_VERBS_WITH_AUXILIARIES = {
    "auth": True,
    "run": False,
    "init": False,
    "add": False,
    "remove": False,
    "version": False,
    "sync": False,
    "lock": False,
    "export": False,
    "tree": False,
    "format": False,
    "audit": False,
    "tool": True,
    "python": True,
    "pip": True,
    "venv": False,
    "build": False,
    "publish": False,
    "cache": True,
    "self": True,
    "help": False,
}
_REQUIRES_FLAG_ACTIVE = {
    "auth": False,
    "run": True,
    "init": False,
    "add": True,
    "remove": True,
    "version": True,
    "sync": True,
    "lock": False,
    "export": False,
    "tree": False,
    "format": False,
    "audit": False,
    "tool": False,
    "python": False,
    "pip": False,
    "venv": False,
    "build": False,
    "publish": False,
    "cache": False,
    "self": False,
    "help": False,
}
_UV_HELP = {}


@dataclass
class _DirCacheUv:
    dir: Path | None = None

    def __call__(self) -> Path:
        if self.dir is None:
            cp = sp.run(
                [find_uv_bin(), "cache", "dir"],
                stdout=sp.PIPE,
                stderr=sp.STDOUT,
                stdin=sp.DEVNULL,
                encoding="utf-8",
            )
            cp.check_returncode()
            self.dir = Path(cp.stdout.strip())
        return self.dir


dir_cache_uv = _DirCacheUv()


def get_uv_permanent() -> str:
    uv_bin = find_uv_bin()
    if Path(uv_bin).is_relative_to(dir_cache_uv()):
        # If uv lives under its own cache directory, we must assume it has been set up there
        # by some other running uv. Let's walk up the parent chain to find it.
        process = Process().parent()
        while process is not None:
            exe = process.exe()
            if re.search(r"[/\\]uv(\.exe)?$", exe.lower()):
                if Path(exe).is_relative_to(dir_cache_uv()):
                    continue
                return exe
        raise RuntimeError("Cannot find a permanent uv instance")
    else:
        return uv_bin


def uv_(command: Iterable[str], project: Iterable[str] = []) -> tuple[str, ...]:
    assert not isinstance(command, str)
    command_full = tuple(command)
    if not command_full:
        return (get_uv_permanent(),)
    verb, *tail = command_full
    head = [get_uv_permanent(), verb]
    if verb not in _VERBS_WITH_AUXILIARIES:
        look_up_auxiliaries(verb)
        assert verb in _VERBS_WITH_AUXILIARIES
    if _VERBS_WITH_AUXILIARIES[verb] and tail:
        aux, *tail = tail
        head.append(aux)

    head.extend(["--python", sys.executable])
    head.extend(project)

    if verb not in _REQUIRES_FLAG_ACTIVE:
        look_up_active_flag(verb)
        assert verb in _REQUIRES_FLAG_ACTIVE
    if _REQUIRES_FLAG_ACTIVE[verb]:
        assert verb in _REQUIRES_FLAG_ACTIVE
        head.append("--active")

    return (*head, *tail)


def look_up_auxiliaries(verb: str) -> None:
    _VERBS_WITH_AUXILIARIES[verb] = bool(re.search(r"Commands\b", uv_help(verb)))


def look_up_active_flag(verb: str) -> None:
    _REQUIRES_FLAG_ACTIVE[verb] = bool(re.search("--active\b", uv_help(verb)))


def uv_help(verb: str) -> str:
    if verb not in _UV_HELP:
        cp = sp.run(
            [get_uv_permanent(), verb, "--help"],
            stdin=sp.DEVNULL,
            stdout=sp.PIPE,
            stderr=sp.STDOUT,
            encoding="utf-8",
        )
        _UV_HELP[verb] = cp.stdout if cp.returncode == 0 else ""
    return _UV_HELP[verb]


__all__ = ["uv_"]
