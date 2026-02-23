from textwrap import dedent


def cook(raw: str) -> str:
    """
    Converts a string of content typeset for prettiness in Python code to
    a string paragraph that is not indented and is right-stripped of whitespace.
    """
    return dedent(raw.rstrip())
