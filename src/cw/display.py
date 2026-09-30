"""
Module for displaying data in terminal
"""

import os
from dataclasses import dataclass

from rich import print
from rich.columns import Columns
from rich.console import Console
from rich.table import Table
from rich.text import Text

from cw.config import config
from cw.crossword import Crossword, Direction, State
from cw.grid import Grid


@dataclass
class Cell:
    clue_number: int | None = None
    user_letter: str | None = None
    solution_letter: str | None = None
    is_black_square: bool = True


def print_crossword(cw: Crossword, reveal: bool = False):
    grid = Grid.from_crossword(cw)

    output_style = config.user_config.output

    acrosses = [Text("Across", style="bold underline")] + [
        Text(str(c), style="dim strike" if grid.is_clue_complete(c) else "")
        for c in sorted(cw.clues, key=lambda c: c.number)
        if c.direction is Direction.ACROSS
    ]

    downs = [Text("Down", style="bold underline")] + [
        Text(str(c), style="dim strike" if grid.is_clue_complete(c) else "")
        for c in sorted(cw.clues, key=lambda c: c.number)
        if c.direction is Direction.DOWN
    ]

    print(
        Columns(
            [
                grid.display(reveal=reveal, output=output_style),
                Text(os.linesep).join(acrosses + [Text("")] + downs),
            ],
            padding=(1, 3),
        )
    )


def print_crossword_list(cws: list[Crossword]):
    table = Table(title="Crosswords")
    table.add_column("Puzzle")
    table.add_column("Status")

    def sort_fn(cw: Crossword):
        match cw.user_state:
            case State.ACTIVE:
                return 0
            case State.INACTIVE:
                return 1
            case State.COMPLETE:
                return 2

    def style_for(cw: Crossword):
        match cw.user_state:
            case State.ACTIVE:
                return "green bold"
            case State.INACTIVE:
                return "yellow"
            case State.COMPLETE:
                return "bright_black"

    for cw in sorted(cws, key=sort_fn):
        table.add_row(
            f"{cw.style.capitalize():7} #{cw.number}",
            cw.user_state.capitalize(),
            style=style_for(cw),
        )

    Console().print(table)
