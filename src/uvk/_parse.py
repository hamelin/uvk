from collections.abc import Sequence

Requirements = Sequence[str]


def parse_dependencies(deps: str) -> Requirements:
    return [dep.strip() for dep in deps.split()]
