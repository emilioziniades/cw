import logging
import sys

import click

from cw import db, display
from cw.calendar import today
from cw.config import OutputStyle, config
from cw.crossword import Crossword, CrosswordStyle
from cw.db import get_crossword
from cw.fetch import crossword_number_from_date
from cw.fetch import fetch as cw_fetch
from cw.grid import Grid
from cw.parameters import ClueArgument, ClueParamType

logger = logging.getLogger(__name__)

# TODO: standardize error message here e.g. active check and error log


@click.group()
@click.option("-v", "--verbose", is_flag=True)
@click.version_option()
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
def start(style: CrosswordStyle, number: int | None):
    if number is None:
        number = crossword_number_from_date(style, today())
    db.start_crossword(style, number)
    print_current_crossword()


@cli.command()
@click.argument(
    "style",
    type=click.Choice(CrosswordStyle, case_sensitive=False),
    default=CrosswordStyle.MINI,
)
@click.argument("number", type=int, default=None)
def stop(style: CrosswordStyle, number: int | None):
    if number is None:
        number = crossword_number_from_date(style, today())
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
            raise ValueError("No active crossword. Start a crossword with `cw start`")

        db.solve_clue(
            clue.direction, clue.number, active.style, active.number, solution
        )

        crossword = get_crossword(active.style, active.number)
        if crossword is None:
            raise ValueError("The active crossword does not exist")

        grid = Grid.from_crossword(crossword)

        if grid.is_correct():
            print_current_crossword(reveal=True)
            db.mark_completed(crossword)
            logger.info("SUCCESS! Crossword has been marked as completed")
        else:
            print_current_crossword()

    except ValueError as ex:
        logger.error(ex)
        sys.exit(1)


@cli.command()
def list():
    crosswords = db.get_all_crosswords()
    display.print_crossword_list(crosswords)


@cli.command()
@click.option("--reveal", is_flag=True)
def check(reveal):
    try:
        active = db.get_active_crossword()
        if active is None:
            raise ValueError("No active crossword. Start a crossword with `cw start`")

        crossword = db.get_crossword(active.style, active.number)
        if crossword is None:
            raise ValueError("The active crossword does not exist")

        grid = Grid.from_crossword(crossword)

        # TODO: this is the second time we calculate is_correct. Obviously performance isn't
        # really an issue but it is a huge code smell.
        if grid.is_correct():
            display.print_crossword(crossword, reveal=True)
            db.mark_completed(crossword)
            logger.info("SUCCESS! Crossword has been marked as completed")
        elif grid.is_complete():
            if reveal:
                display.print_crossword(crossword, reveal=True)
                logger.info(
                    "Puzzle has wrong answers. Wrong letters are displayed in red"
                )

            else:
                display.print_crossword(crossword)
                logger.info(
                    "Puzzle has wrong answers. Use `--reveal` flag to show wrong letters"
                )
        else:
            display.print_crossword(crossword, reveal=reveal)
            logger.info(
                f"Puzzle is incomplete{'. Wrong letters are displayed in red' if reveal else ''}"
            )

    except ValueError as ex:
        logger.error(ex)
        sys.exit(1)


@cli.command()
def clear():
    try:
        active = db.get_active_crossword()
        if active is None:
            raise ValueError("No active crossword. Start a crossword with `cw start`")
        db.clear_user_answers(active)

        print_current_crossword()

    except ValueError as ex:
        logger.error(ex)
        sys.exit(1)


@cli.command()
@click.option(
    "--output",
    type=click.Choice(OutputStyle, case_sensitive=False),
    help="Output style for crossword and clues",
)
def configure(output: OutputStyle | None):
    user_config = config.user_config

    if output is not None:
        user_config.output = output
        user_config.save()

    logger.info("Configuration saved")


def print_current_crossword(reveal: bool = False):
    active = db.get_active_crossword()
    if active is None:
        logger.fatal(
            "No active crossword. Use `cw start <style> <number>` to start a puzzle"
        )
        sys.exit(1)

    crossword = db.get_crossword(active.style, active.number)
    if crossword is None:
        raise ValueError("The active crossword does not exist")

    display.print_crossword(crossword, reveal=reveal)
