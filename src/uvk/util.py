from collections.abc import Iterable
import re
import subprocess as sp
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


def uv_(command: Iterable[str]) -> tuple[str, ...]:
    assert not isinstance(command, str)
    command_full = tuple(command)
    if not command_full:
        return (find_uv_bin(),)
    verb, *tail = command_full
    head = [find_uv_bin(), verb]
    if verb not in _VERBS_WITH_AUXILIARIES:
        look_up_auxiliaries(verb)
        assert verb in _VERBS_WITH_AUXILIARIES
    if _VERBS_WITH_AUXILIARIES[verb] and tail:
        aux, *tail = tail
        head.append(aux)

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
            [find_uv_bin(), verb, "--help"],
            stdin=sp.DEVNULL,
            stdout=sp.PIPE,
            stderr=sp.STDOUT,
            encoding="utf-8",
        )
        _UV_HELP[verb] = cp.stdout if cp.returncode == 0 else ""
    return _UV_HELP[verb]


__all__ = ["uv_"]
