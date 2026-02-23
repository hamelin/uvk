from collections.abc import Iterator, Sequence
import logging as lg
import re
import tomllib
import warnings as w

Requirements = Sequence[str]
LOG = lg.getLogger(__name__.split(".")[0])


def parse_dependencies(deps: str) -> Requirements:
    return [dep.strip() for dep in deps.split()]


class ScriptMetadataParseError(ValueError):

    def __init__(self, msg: str, metadata: str) -> None:
        super().__init__(msg)
        self.metadata = metadata


class NoScriptMetadataStartLine(ScriptMetadataParseError):

    def __init__(self, metadata: str) -> None:
        super().__init__(
            "Cannot find the script metadata opening line `# /// script`",
            metadata,
        )


class NoScriptMetadataEndLine(ScriptMetadataParseError):

    def __init__(self, metadata: str) -> None:
        super().__init__(
            "Cannot find the script metadata closing line `# ///`",
            metadata,
        )


class IllegalLine(ScriptMetadataParseError):

    def __init__(self, metadata: str) -> None:
        super().__init__(
            (
                "An illegal line (neither `#` nor starting with `# `) appears among "
                "the script metadata"
            ),
            metadata,
        )


def iter_lines_metadata(metadata: str) -> Iterator[str]:
    for line in metadata.split("\n"):
        line = line.strip()
        if line in {"", "#"}:
            pass
        elif re.match(r"# ", line):
            yield line[2:]
        else:
            raise IllegalLine(metadata)


class TrailingLines(Warning):
    pass


def parse_script_metadata(metadata: str) -> dict:
    lines_metadata = iter_lines_metadata(metadata)
    try:
        while not re.match(r"/// script\w*$", next(lines_metadata)):
            pass
    except StopIteration:
        raise NoScriptMetadataStartLine(metadata)

    lines_toml = []
    for line in lines_metadata:
        if re.match(r"///\w*$", line):
            break
        lines_toml.append(line)
    else:
        raise NoScriptMetadataEndLine(metadata)

    try:
        next(lines_metadata)
        w.warn(
            message=(
                "The script metadata has trailing lines after the closing line "
                "`# ///`; these are ignored"
            ),
            category=TrailingLines,
        )
    except StopIteration:
        pass

    return tomllib.loads("\n".join(lines_toml))
