from collections.abc import Mapping
from dataclasses import dataclass, field
import pytest
import sys
from textwrap import dedent
from typing import Protocol

from uvk import (
    Add,
    Arguments,
    as_script_metadata,
    Command,
    current_looks_like_name_argument,
    Metadata,
    parse_args,
    Remove,
    SetPython,
    UvArgs,
    uvk,
    UvkArgumentError,
    UvkHelp,
)
from uvk.parse import parse_script_metadata


@pytest.mark.parametrize("args,expected", [(Arguments(["asdf"]), False), (Arguments([]), True)])
def test_arguments_at_end(expected: bool, args: Arguments) -> None:
    assert expected == args.at_end


def test_arguments_current() -> None:
    assert Arguments(["asdf", "qwerty"]).current == "asdf"


def test_arguments_current_at_end() -> None:
    with pytest.raises(ValueError):
        print(Arguments([]).current)


@pytest.mark.parametrize(
    "args,expected",
    [
        (Arguments(["asdf", "qwer"]), Arguments(["qwer"])),
        (Arguments(["asdf"]), Arguments([])),
    ],
)
def test_arguments_advance(expected: Arguments, args: Arguments) -> None:
    assert expected == args.advance()


def test_arguments_advance_at_end() -> None:
    with pytest.raises(ValueError):
        Arguments(["asdf"]).advance().advance()


@pytest.mark.parametrize(
    "args,expected",
    [
        (Arguments(["asdf"]), False),
        (Arguments(["-p"]), True),
        (Arguments(["--asdf"]), True),
    ],
)
def test_current_looks_like_name_argument(expected: bool, args: Arguments) -> None:
    assert expected == current_looks_like_name_argument(args)


@pytest.mark.parametrize(
    "args,expected",
    [
        ("--python >=3.11", [SetPython(">=3.11")]),
        ('-p ">= 3.11, < 3.13, != 3.12.2"', [SetPython("!=3.12.2,<3.13,>=3.11")]),
        ("-a requests", [Add(["requests"])]),
        (
            '--add requests==2.33.1 "lark >1.0"',
            [Add(["requests==2.33.1", "lark>1.0"])],
        ),
        ("-a -p >=3.13", [Add([]), SetPython(">=3.13")]),
        ("-r asdf", [Remove(["asdf"])]),
        ("--remove asdf qwerty>2.2", [Remove(["asdf", "qwerty"])]),
        ("-r", [Remove([])]),
        ("-r -a", [Remove([]), Add([])]),
        ("--remove zxcv -p >=3.13", [Remove(["zxcv"]), SetPython(">=3.13")]),
        ("-A --isolated -p 3.11", [UvArgs(["--isolated", "-p", "3.11"])]),
        (
            "--uv-args --no-cache-dir -- --python >=3.11",
            [UvArgs(["--no-cache-dir"]), SetPython(">=3.11")],
        ),
        ("-A", [UvArgs([])]),
        ("-A -- -a", [UvArgs([]), Add([])]),
        ("-a asdf -A -Z", [Add(["asdf"]), UvArgs(["-Z"])]),
    ],
)
def test_parse_args_success(expected: list[Command], args: str) -> None:
    assert expected == parse_args(args)


@pytest.mark.parametrize(
    "args",
    [
        "--asdf",
        "--python",
        "--python asdf",
        "--python --add",
        "--add asdf <5",
        "-a asdf -Z",
    ],
)
def test_commands_parse_error(args: str) -> None:
    with pytest.raises(UvkArgumentError):
        parse_args(args)


@pytest.mark.parametrize("args", ["-h", "--help", "-a asdf -h -p >=3.11"])
def test_commands_parse_help(args: str) -> None:
    with pytest.raises(UvkHelp):
        parse_args(args)


@pytest.mark.parametrize(
    "metadata,expected",
    [
        (
            {},
            """\
            # /// script
            # ///
            """,
        ),
        (
            {"require-python": ">=3.11"},
            """\
            # /// script
            # require-python = ">=3.11"
            # ///
            """,
        ),
        (
            {"require-python": "<3.13", "dependencies": []},
            """\
            # /// script
            # require-python = "<3.13"
            # dependencies = []
            # ///
            """,
        ),
        (
            {"dependencies": ["asdf"]},
            """\
            # /// script
            # dependencies = ["asdf"]
            # ///
            """,
        ),
        (
            {"dependencies": ["asdf", "qwer"]},
            """\
            # /// script
            # dependencies = ["asdf", "qwer"]
            # ///
            """,
        ),
        (
            {"tool": {"uvk": {"uv-args": ["--no-cache-dir", "--compile-bytecode"]}}},
            """\
            # /// script
            # [tool.uvk]
            # uv-args = ["--no-cache-dir", "--compile-bytecode"]
            # ///
            """,
        ),
        (
            {
                "require-python": ">=3.11",
                "tool": {"uvk": {"uv-args": []}},
            },
            """\
            # /// script
            # require-python = ">=3.11"
            # 
            # [tool.uvk]
            # uv-args = []
            # ///
            """,
        ),
    ],
)
def test_as_script_metadata(expected: str, metadata: Metadata) -> None:
    assert dedent(expected).rstrip() == as_script_metadata(metadata)


@pytest.fixture
def meta1() -> Metadata:
    return {
        "require-python": ">=3.14",
        "dependencies": [
            "numpy",
            "pandas<3",
        ],
    }


@pytest.mark.parametrize(
    "command,expected",
    [
        (
            SetPython(">=3.11"),
            {"require-python": ">=3.11", "dependencies": ["numpy", "pandas<3"]},
        ),
        (
            Add(["requests", "pandas<=2.3", "matplotlib"]),
            {
                "require-python": ">=3.14",
                "dependencies": ["matplotlib", "numpy", "pandas<=2.3", "requests"],
            },
        ),
        (
            Remove(["pandas", "requests"]),
            {"require-python": ">=3.14", "dependencies": ["numpy"]},
        ),
        (
            UvArgs(["--no-cache-dir"]),
            {
                "require-python": ">=3.14",
                "dependencies": ["numpy", "pandas<3"],
                "tool": {"uvk": {"uv-args": ["--no-cache-dir"]}},
            },
        ),
    ],
)
def test_command_exec(expected: Metadata, meta1: Metadata, command: Command) -> None:
    command.execute(meta1)
    assert expected == meta1


@dataclass
class MockShell:
    next_inputs: list[tuple[str, bool]] = field(default_factory=list)

    def set_next_input(self, ni: str, replace: bool = False) -> None:
        self.next_inputs.append((ni, replace))

    def check_inputs(
        self, expected: Mapping[int, tuple[Metadata, bool]], num: int | None = None
    ) -> None:
        if num is not None:
            assert num == len(self.next_inputs)
        for i, (metadata_expected, replace_expected) in expected.items():
            assert i < len(self.next_inputs)
            metadata_, replace = self.next_inputs[i]
            assert metadata_expected == parse_script_metadata(metadata_)
            assert replace_expected == replace


@pytest.fixture
def shell() -> MockShell:
    return MockShell()


class MagicUvk(Protocol):
    def __call__(self, line: str, cell: str | None = None) -> None: ...


@pytest.fixture
def magic_uvk(shell: MockShell) -> MagicUvk:
    return uvk(shell)  # type: ignore


def test_uvk_alone(magic_uvk: MagicUvk, shell: MockShell) -> None:
    magic_uvk("")
    shell.check_inputs(
        {
            0: (
                {
                    "require-python": f">={sys.version_info.major}.{sys.version_info.minor}",
                    "dependencies": [],
                },
                False,
            )
        },
    )


def test_uvk_line(magic_uvk: MagicUvk, shell: MockShell) -> None:
    magic_uvk('-a numpy requests -p "== 3.12" --uv-args --no-cache-dir')
    shell.check_inputs(
        {
            0: (
                {
                    "require-python": "==3.12",
                    "dependencies": ["numpy", "requests"],
                    "tool": {"uvk": {"uv-args": ["--no-cache-dir"]}},
                },
                False,
            ),
        }
    )


def test_uvk_cell(magic_uvk: MagicUvk, shell: MockShell) -> None:
    magic_uvk(
        "-r pandas -a polars duckdb",
        dedent(
            """\
            # /// script
            # require-python = ">=3.13"
            # dependencies = [
            #     "numpy",
            #     "pandas",
            #     "requests",
            # ]
            # 
            # [tool.uvk]
            # uv-args = ["--index", "asdf"]
            # ///
            """,
        ).rstrip(),
    )
    shell.check_inputs(
        {
            0: (
                {
                    "require-python": ">=3.13",
                    "dependencies": ["duckdb", "numpy", "polars", "requests"],
                    "tool": {"uvk": {"uv-args": ["--index", "asdf"]}},
                },
                True,
            )
        }
    )


def test_uvk_composition(magic_uvk: MagicUvk, shell: MockShell) -> None:
    magic_uvk('-p ">= 3.11"')
    magic_uvk(
        "-A --no-cache-dir -- -a numpy scikit-learn",
        dedent("""\
            # /// script
            # require-python = ">=3.11"
            # ///
        """).rstrip(),
    )
    magic_uvk(
        "-A",
        dedent("""\
            # /// script
            # require-python = ">=3.11"
            # dependencies = ["numpy", "scikit-learn"]
            # [tool.uvk]
            # uv-args = ["--no-cache-dir"]
            # ///
        """).rstrip(),
    )
    shell.check_inputs(
        {
            0: ({"require-python": ">=3.11", "dependencies": []}, False),
            1: (
                {
                    "require-python": ">=3.11",
                    "dependencies": ["numpy", "scikit-learn"],
                    "tool": {"uvk": {"uv-args": ["--no-cache-dir"]}},
                },
                True,
            ),
            2: (
                {
                    "require-python": ">=3.11",
                    "dependencies": ["numpy", "scikit-learn"],
                    "tool": {"uvk": {"uv-args": []}},
                },
                True,
            ),
        }
    )
