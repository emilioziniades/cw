from cw.parameters import ClueParamType, ClueArgument
import logging
from datetime import date
from typing import Optional

import click

from cw import db, display
from cw.crossword import Crossword, CrosswordStyle
from cw.fetch import crossword_number_from_date
from cw.fetch import fetch as cw_fetch

logger = logging.getLogger(__name__)

# TODO: standardize error message here e.g. active check and error log


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
    crossword_json = cw_fetch(style, number)
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
    print_current_crossword()


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
    print_current_crossword()


@cli.command()
@click.argument(
    "clue",
    type=ClueParamType(),
    required=True,
)
@click.argument("solution", type=str, required=True)
def solve(clue: ClueArgument, solution: str):
    try:
        active = db.get_active_crossword()
        if active is None:
            raise Exception("No active crossword. Start a crossword with `cw start`")

        db.solve_clue(
            clue.direction, clue.number, active.style, active.number, solution
        )

        print_current_crossword()

    except Exception as ex:
        logger.error(ex)
        exit(1)


@cli.command()
def list():
    crosswords = db.get_all_crosswords()
    display.print_crossword_list(crosswords)


@cli.command()
def check():
    try:
        active = db.get_active_crossword()
        if active is None:
            raise Exception("No active crossword. Start a crossword with `cw start`")

        crossword = db.get_crossword(active.style, active.number)
        if crossword is None:
            raise ValueError("The active crossword does not exist")

        # TODO: if crossword is green, mark it as completed and tell the user
        display.print_crossword(crossword, check=True)

        grid = display.crossword_to_grid(crossword)

        # TODO: this is the second time we calculate is_correct. Obviously performance isn't
        # really an issue but it is a huge code smell that a class from `cw.display` has solving logic
        if grid.is_correct():
            logger.info("SUCCESS! Crossword has been marked as completed")
            db.mark_completed(crossword)
        else:
            logger.info("Puzzle is incomplete or has wrong answers")
            logger.info("Wrong letters are in red")

    except Exception as ex:
        logger.error(ex)
        exit(1)


@cli.command()
def reveal():
    # TODO: fill in missing cells in blue and wrong cells in yellow
    pass


@cli.command()
def clear():
    pass


def print_current_crossword():
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
