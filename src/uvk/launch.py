from argparse import ArgumentParser, Namespace
import logging as lg


LOG = lg.getLogger(__name__)


def launch(parser: ArgumentParser) -> None:
    """
    Launch the IPython kernel through uv run.
    """
    parser.set_defaults(_main_=_main_)


def _main_(params: Namespace) -> None:
    raise NotImplementedError()
