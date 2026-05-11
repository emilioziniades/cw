from datetime import date
from typing import Optional
import click
from cw.crossword import Crossword
from cw.fetch import fetch as cw_fetch, crossword_number_from_date
from cw import db, display
from cw.crossword import CrosswordStyle

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
@click.argument(
    "style",
    type=click.Choice(CrosswordStyle, case_sensitive=False),
    default=CrosswordStyle.MINI,
)
@click.argument("number", type=int, default=None)
def fetch(style: CrosswordStyle, number: int):
    crossword_json = cw_fetch(number, style)
    crossword = Crossword.from_json(crossword_json)
    if not db.has_crossword(crossword):
        db.add_crossword(crossword)


@cli.command()
@click.argument(
    "style",
    type=click.Choice(CrosswordStyle, case_sensitive=False),
    default=CrosswordStyle.MINI,
)
@click.argument("number", type=int, default=None)
def start(style: CrosswordStyle, number: Optional[int]):
    if number is None:
        number = crossword_number_from_date(style, date.today())
    db.start_crossword(style, number)


@cli.command()
@click.argument(
    "style",
    type=click.Choice(CrosswordStyle, case_sensitive=False),
    default=CrosswordStyle.MINI,
)
@click.argument("number", type=int, default=None)
def stop(style: CrosswordStyle, number: Optional[int]):
    if number is None:
        number = crossword_number_from_date(style, date.today())
    db.stop_crossword(style, number)


@cli.command()
def show():
    active = db.get_active_crossword()
    if active is None:
        logger.fatal(
            "No active crossword. Use `cw start <style> <number>` to start a puzzle"
        )
        exit(1)

    crossword = db.get_crossword(active.style, active.number)
    if crossword is None:
        raise ValueError("The active crossword does not exist")

    display.print_crossword(crossword)


def list():
    crosswords = db.get_all_user_crosswords()
    display.print_crossword_list(crosswords)
