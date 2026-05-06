import click
from cw.crossword import Crossword
from cw.fetch import fetch as cw_fetch
from cw import db
from cw.config import CrosswordStyle

import logging

logger = logging.getLogger(__name__)


@click.group()
@click.option("-v", "--verbose", is_flag=True)
def cli(verbose: bool):

    if verbose:
        logging.basicConfig(
            level=logging.DEBUG,
            format="%(levelname)-6s[%(name)-10s]: %(message)s",
        )
        logger.debug("Verbose logging enabled")
    else:
        logging.basicConfig(
            level=logging.INFO,
            format="%(levelname)-4s: %(message)s",
        )

    db.migrate()


@cli.command()
@click.option("--number", type=int)
@click.option(
    "--style", required=True, type=click.Choice(CrosswordStyle, case_sensitive=False)
)
def fetch(number: int, style: CrosswordStyle):
    crossword_json = cw_fetch(number, style)
    crossword = Crossword.from_json(crossword_json)
    if not db.has_crossword(crossword):
        db.add_crossword(crossword)


def start(number, style):
    raise NotImplementedError()
