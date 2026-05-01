"""
This IPython extension provides the `%%uvk` [cell magic](https://ipython.readthedocs.io/en/stable/interactive/magics.html)
to edit a notebook's [inline script metadata](https://packaging.python.org/en/latest/specifications/inline-script-metadata/).

```ipython
%load_ext uvk
```
"""

# from collections.abc import Iterable
from collections.abc import Callable, MutableMapping
from dataclasses import dataclass
from IPython.core.interactiveshell import InteractiveShell

from IPython.display import display, Markdown
import logging as lg
from packaging.requirements import Requirement
from packaging.specifiers import SpecifierSet
import shlex
import sys
import tomlkit
from textwrap import dedent
from typing import Protocol, Self, Union

from .parse import parse_script_metadata

LOG = lg.getLogger(__name__)
Metadata = MutableMapping[str, Union[str, int, "Metadata"]]


def load_ipython_extension(shell: InteractiveShell) -> None:
    shell.register_magic_function(func=uvk(shell), magic_kind="line_cell", magic_name="uvk")  # type: ignore


@dataclass
class Arguments:
    _args: list[str]

    @property
    def at_end(self) -> bool:
        return not self._args

    @property
    def current(self) -> str:
        if self.at_end:
            raise ValueError()
        return self._args[0]

    def advance(self) -> Self:
        if self.at_end:
            raise ValueError()
        return type(self)(self._args[1:])


def current_looks_like_name_argument(args: Arguments) -> bool:
    return args.current.startswith("-")


class Command(Protocol):
    @classmethod
    def parse(cls, args: Arguments) -> tuple[Self | None, Arguments]: ...

    def execute(self, metadata: Metadata) -> None: ...


class UvkArgumentError(Exception):
    pass


class UvkHelp(Exception):
    pass


@dataclass
class SetPython:
    spec: str

    @classmethod
    def parse(cls, args: Arguments) -> tuple[Self | None, Arguments]:
        if args.current not in {"-p", "--python"}:
            return None, args
        args = args.advance()
        if args.at_end:
            raise UvkArgumentError("Argument --python missing version constraint.")
        try:
            return cls(spec=str(SpecifierSet(args.current))), args.advance()
        except ValueError as err:
            raise UvkArgumentError(f"Error with --python version constraint: {err}")

    def execute(self, metadata: Metadata) -> None:
        metadata["require-python"] = self.spec


@dataclass
class Add:
    requirements: list[str]

    @classmethod
    def parse(cls, args: Arguments) -> tuple[Self | None, Arguments]:
        if args.current not in {"-a", "--add"}:
            return None, args
        args = args.advance()
        requirements = []
        while not (args.at_end or current_looks_like_name_argument(args)):
            try:
                requirements.append(str(Requirement(args.current)))
                args = args.advance()
            except ValueError as err:
                raise UvkArgumentError(f"Problem with package requirement {args.current}: {err}")
        return cls(requirements), args

    def execute(self, metadata: Metadata) -> None:
        metadata.setdefault("dependencies", [])
        for req_ in self.requirements:
            req = Requirement(req_)
            try:
                i = [Requirement(r).name for r in metadata["dependencies"]].index(req.name)
                metadata["dependencies"][i] = req_
            except ValueError:
                metadata["dependencies"].append(req_)
        metadata["dependencies"].sort()


@dataclass
class Remove:
    packages: list[str]

    @classmethod
    def parse(cls, args: Arguments) -> tuple[Self | None, Arguments]:
        if args.current not in ["-r", "--remove"]:
            return None, args
        args = args.advance()
        packages = []
        while not (args.at_end or current_looks_like_name_argument(args)):
            packages.append(Requirement(args.current).name)
            args = args.advance()
        return cls(packages), args

    def execute(self, metadata: Metadata) -> None:
        if "dependencies" in metadata:
            for package in self.packages:
                try:
                    i = [Requirement(dep).name for dep in metadata["dependencies"]].index(package)
                    del metadata["dependencies"][i]
                except ValueError:
                    pass


@dataclass
class UvArgs:
    uv_args: list[str]

    @classmethod
    def parse(cls, args: Arguments) -> tuple[Self | None, Arguments]:
        if args.current not in ["-A", "--uv-args"]:
            return None, args
        args = args.advance()
        uv_args = []
        while not (args.at_end or args.current == "--"):
            uv_args.append(args.current)
            args = args.advance()
        if not args.at_end:
            args = args.advance()
        return cls(uv_args), args

    def execute(self, metadata: Metadata) -> None:
        metadata.setdefault("tool", {})
        metadata["tool"].setdefault("uvk", {})
        metadata["tool"]["uvk"]["uv-args"] = self.uv_args


class Help:
    @classmethod
    def parse(cls, args: Arguments) -> tuple[Self | None, Arguments]:
        if args.current not in {"-h", "--help"}:
            return None, args
        raise UvkHelp()

    def execute(self, metadata: Metadata) -> None:
        raise RuntimeError("Wrong way")


def parse_args(args: str) -> list[Command]:
    arguments = Arguments(shlex.split(args))
    commands = []
    while not arguments.at_end:
        for type_command in [SetPython, Add, Remove, UvArgs, Help]:
            command, arguments = type_command.parse(arguments)
            if command is not None:
                commands.append(command)
                break
        else:
            raise UvkArgumentError(f"Unknown command: {arguments.current}")
    return commands


def as_script_metadata(metadata: Metadata) -> str:
    return "\n".join(
        [
            "# /// script",
            *[f"# {line}" for line in tomlkit.dumps(metadata).splitlines()],
            "# ///",
        ]
    )


def uvk(shell: InteractiveShell) -> Callable[[str, str], None]:
    def _uvk(line: str, cell: str | None = None) -> None:
        """
        Script metadata editor. Invoke

        %uvk --help

        for gorgeous Markdown documentation.
        """
        metadata = (
            parse_script_metadata(cell)
            if cell
            else {
                "require-python": f">={sys.version_info.major}.{sys.version_info.minor}",
                "dependencies": [],
            }
        )
        try:
            for command in parse_args(line):
                command.execute(metadata)
            shell.set_next_input(as_script_metadata(metadata), replace=bool(cell))
        except UvkHelp:
            display(
                Markdown(
                    dedent(
                        """\
                        # <span style="font-family: sans-serif;">uvk<span> &mdash; Editor for script metadata

                        Assist in the editing of various aspects of a cell containing inline script
                        metadata. It is not strictly necessary to use this cell magic to change the
                        metadata, but since uvk's logic for detecting and parsing script metadata is
                        strict, and since comment lines and TOML syntax can be tedious to wrangle,
                        this tool might help.

                        This magic can be used either as `%uvk` line magic or as `%%cell` magic.
                        The difference is that the former puts out a new code cell with blank
                        metadata altered by the given options; the latter takes in script metadata
                        in the cell underneath it and *modifies it in place* according to the
                        given options, removing the top `%%uvk` line.

                        The simplest usage of this magic is all by itself as a line magic to
                        add a cell of blank script metadata, with a Python version constraint
                        requiring an interpreter version corresponding to the running interpreter's
                        or newer.

                        ```ipython
                        %uvk
                        -------------------------------------------------------------------------
                        # /// script
                        # require-python = ">=3.13"
                        # dependencies = []
                        # ///
                        ```

                        ## Options

                        ### `-p`, `--python` *version-constraints*

                        Set the `require-python` field of the script metadata so that the Python
                        interpreter that will be chosen to run the kernel satisfies the given
                        constraints. Quote the specifier to use spaces.

                        Example:

                        ```ipython
                        %uvk -p ">= 3.11, < 3.13, != 3.12.2"
                        -------------------------------------------------------------------------
                        # /// script
                        # require-python = "!=3.12.2,<3.13,>=3.11"
                        # dependencies = []
                        # ///
                        ```

                        ### `-a`, `--add` *requirement* ...

                        Add the given package requirements to the `dependencies` field of the
                        metadata. The requirements are package names that one may suffix with
                        version constraints. If one of the specifications refers to a package that
                        is already required amongst the notebook's dependencies, the new
                        requirement clobbers the old one.

                        One can any number of requirements following the option; the listing
                        ends at the end of the line, of when another option leader is encountered.

                        Example:

                        ```ipython
                        %%uvk -a requests "lark >1"
                        # /// script
                        # require-python = ">=3.11"
                        # dependencies = []
                        # ///
                        -------------------------------------------------------------------------
                        # /// script
                        # require-python = ">=3.11"
                        # dependencies = [
                        #     "requests",
                        #     "lark>1",
                        # ]
                        # ///
                        ```

                        ### `-r`, `--remove` *package* ...

                        Remove the named packages from the `dependencies` list. While only
                        package names are required, one may also suffix constraints, but these
                        will be ignored (they still will cause errors if they are incorrectly
                        formatted). Named packages not already part of the dependencies are
                        silently ignored. Like the `--add` option, any number of packages can be
                        named. The list stops at the next option leader, or at the end of the
                        line.

                        Example:

                        ```ipython
                        %%uvk -r lark
                        # /// script
                        # require-python = ">=3.11"
                        # dependencies = [
                        #     "requests",
                        #     "lark>1",
                        # ]
                        # ///
                        -------------------------------------------------------------------------
                        # /// script
                        # require-python = ">=3.11"
                        # dependencies = [
                        #     "requests",
                        # ]
                        # ///
                        ```

                        ### `-A`, `--uv-args` *option* ... `--`

                        Specifies command-line arguments to add to the invocation of `uv`
                        that starts the IPython kernel for this notebook. Quoted arguments
                        are taken as is, not split as if unquoted. Any number of arguments can
                        be provided. The enumeration is presumed to stop at the `--` token, or at
                        the end of the line.

                        Example:

                        ```ipython
                        %%uvk --uv-args --isolated --no-cache-dir -- --add numpy
                        # /// script
                        # require-python = ">=3.11"
                        # dependencies = []
                        # ///
                        -------------------------------------------------------------------------
                        # /// script
                        # require-python = ">=3.11"
                        # dependencies = [
                        #     "numpy",
                        # ]
                        #
                        # [tool.uvk]
                        # uv_args = [
                        #     "--isolated",
                        #     "--no-cache-dir",
                        # ]
                        # ///
                        ```

                        ## Notes
                        
                        Multiple options can be provided on the top line. One may fully
                        specify their metadata in a single operation:

                        ```ipython
                        %uvk -p ">=3.11" -a requests numpy pandas<3 -A --index https://myindex.home/simple
                        ----------------------------------------------------------------------------------
                        # /// script
                        # require-python = ">=3.11"
                        # dependencies = [
                        #     "requests",
                        #     "numpy",
                        #     "pandas<3",
                        # ]
                        #
                        # [tool.uvk]
                        # uv_args = [
                        #     "--index",
                        #     "https://myindex.home/simple",
                        # ]
                        # ///
                        ```

                        This tool is not strictly necessary to edit the notebook's script
                        metadata so that <span style="font-family: sans-serif;">uvk</span>
                        takes it into account when starting the kernel. It is offered as a
                        mean of convenience. Script metadata typos might prevent the kernel
                        from starting, and Jupyterhub platform, no feedback is provided anywhere
                        visible when such difficulties occur.

                        Complete documentation is available on [ReadTheDocs](https://uvk.readthedocs.io/reference/uvk_ext/).
                        """
                    )
                )
            )

    return _uvk
