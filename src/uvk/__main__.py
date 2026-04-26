from argparse import ArgumentParser, Namespace
import logging as lg
import sys

from .install import install
from .launch import launch


def parse_args(args: list[str] | None = None) -> Namespace:
    parser_main = ArgumentParser(
        description="""
            uv-driven IPython kernel with environment setup from inline script metadata embedded
            into notebooks.   
        """,
    )
    subparsers = parser_main.add_subparsers(title="Commands", dest="command", required=True)
    for app in [install, launch]:
        parser_app = subparsers.add_parser(
            app.__name__,
            help=app.__doc__,
            aliases=getattr(app, "aliases", []),
            deprecated=getattr(app, "deprecated", False),
        )
        app(parser_app)
    return parser_main.parse_args(args)


def main():
    lg.basicConfig(level=lg.INFO, format="%(message)s")
    ns = parse_args()
    try:
        ns._main_(ns)
    except AttributeError:
        lg.critical("Argument parsing failure. Abort.")
        sys.exit(11)


if __name__ == "__main__":
    main()
