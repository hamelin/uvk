from argparse import ArgumentParser, Namespace
import logging as lg


LOG = lg.getLogger(__name__)


def launch(parser: ArgumentParser) -> None:
    """
    Launch the IPython kernel through uv run.
    """
    parser.add_argument(
        "-f",
        dest="file",
        required=True,
        help="""
            JSON file in which to store connection info. This file will contain the IP, ports,
            and authentication key needed to connect clients to this kernel. By default,
            this file will be created in the security dir of the current profile, but can be
            specified by absolute path.
        """,
    )
    parser.set_defaults(_main_=_main_)


def _main_(params: Namespace) -> None:
    raise NotImplementedError()
