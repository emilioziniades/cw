import logging
from dataclasses import dataclass
from datetime import date
from typing import Optional
import re

import click

from cw import db, display
from cw.crossword import Crossword, CrosswordStyle, Direction
from cw.fetch import crossword_number_from_date
from cw.fetch import fetch as cw_fetch

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

    # TODO: use user solution to populate crossword
    display.print_crossword(crossword)


@dataclass
class ClueArgument:
    direction: Direction
    number: int


class ClueParamType(click.ParamType):
    def convert(self, value, param, ctx):
        match = re.match("^(\\d*)([a-zA-Z]*)$", value)
        if match is None:
            self.fail(
                f"Failed to parse {value} as clue number + direction. Expected 1d or 22a"
            )

        groups = match.groups()
        if len(groups) != 2:
            self.fail(
                f"Failed to parse {value} as clue number + direction. Expected 1d or 22a"
            )

        number = groups[0]
        direction = groups[1]

        try:
            number = int(number)

            if direction.lower() == "d":
                direction = Direction.DOWN
            elif direction.lower() == "a":
                direction = Direction.ACROSS
            else:
                self.fail(f"Unrecognized direction: {direction}. Expected a or d")

            return ClueArgument(number=number, direction=direction)

        except Exception as ex:
            self.fail(str(ex))


@cli.command()
@click.argument(
    "clue",
    type=ClueParamType(),
    required=True,
)
@click.argument("solution", type=str, required=True)
def solve(clue: ClueArgument, solution: str):
    active = db.get_active_crossword()
    if active is None:
        raise Exception("No active crossword. Start a crossword with `cw start`")

    print(clue)
    print(solution)

    db.solve_clue(clue.direction, clue.number, active.style, active.number, solution)
    pass


@cli.command()
def check():
    pass


@cli.command()
def list():
    crosswords = db.get_all_user_crosswords()
    display.print_crossword_list(crosswords)
