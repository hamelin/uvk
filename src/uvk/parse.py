from collections.abc import Sequence
import logging as lg
import re
import tomllib
import warnings as w


Requirements = Sequence[str]
LOG = lg.getLogger(__name__)


def parse_dependencies(deps: str) -> Requirements:
    return [dep.strip() for dep in deps.split()]


class ScriptMetadataParseError(ValueError):
    def __init__(self, msg: str, metadata: str) -> None:
        super().__init__(msg)
        self.metadata = metadata


class NoMetadata(ScriptMetadataParseError):
    def __init__(self, snippet: str) -> None:
        super().__init__("Cannot parse script metadata out of this snippet", snippet)


class NoScriptMetadataEndLine(ScriptMetadataParseError):
    def __init__(self, metadata: str) -> None:
        super().__init__(
            "Cannot find the script metadata closing line `# ///`",
            metadata,
        )


class IllegalLine(ScriptMetadataParseError):
    def __init__(self, snippet: str, num_line: int) -> None:
        super().__init__(
            f"Noncomment line {num_line} is illegal within inline script snippet.",
            snippet,
        )
        self.num_line = num_line


class TrailingLines(Warning):
    pass


def parse_script_metadata(metadata: str) -> dict:
    lines_metadata = iter(enumerate(metadata.splitlines(), start=1))
    try:
        while True:
            num_line, line = next(lines_metadata)
            if re.match(r"# /// script\w*$", line):
                break
    except StopIteration:
        raise NoMetadata(metadata)
    LOG.debug(f"Found script metadata header at line {num_line}")

    lines_toml = []
    for num_line, line in lines_metadata:
        if re.match(r"# ///\w*$", line):
            LOG.debug(f"Found script metadata footer at line {num_line}")
            break
        if not (m := re.match(r"#$|# ", line)):
            raise IllegalLine(metadata, num_line)
        line = line[len(m.group(0)) :]
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
