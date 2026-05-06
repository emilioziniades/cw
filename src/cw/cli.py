import click
from cw.fetch import fetch as cw_fetch
from cw import db
from cw.config import CrosswordStyle

import logging

logger = logging.getLogger(__name__)

db.migrate()


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


@cli.command()
@click.option("--number", type=int)
@click.option(
    "--style", required=True, type=click.Choice(CrosswordStyle, case_sensitive=False)
)
def fetch(number: int, style: CrosswordStyle):
    puzzle_json = cw_fetch(number, style)
    if not db.has_crossword(puzzle_json):
        db.add_crossword(puzzle_json)


def start(number, style):
    raise NotImplementedError()
