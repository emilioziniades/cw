"""
Module for displaying crossword in terminal

TODO: this is getting a bit weird, because the logic for checking correctness has
now been mushed into the logic for rendering the grid. ew ew ew.
"""

import os
from dataclasses import dataclass
from itertools import repeat
from typing import Optional

from rich import print
from rich.columns import Columns
from rich.console import Console
from rich.table import Table

from cw.crossword import Crossword, Direction, State
from cw.db import get_letters

TL = "┌"
TR = "┐"
BL = "└"
BR = "┘"
H = "─"
V = "│"
S = " "
B = "█"
CR = "├"
CL = "┤"
CD = "┬"
CU = "┴"
CC = "┼"

SUPERSCRIPTS = {
    "0": "⁰",
    "1": "¹",
    "2": "²",
    "3": "³",
    "4": "⁴",
    "5": "⁵",
    "6": "⁶",
    "7": "⁷",
    "8": "⁸",
    "9": "⁹",
}


@dataclass
class Cell:
    clue_number: Optional[int] = None
    user_letter: Optional[str] = None
    solution_letter: Optional[str] = None
    is_black_square: bool = True

    def display(self, colour: Optional[str] = None):
        def style(inner: str):
            if colour:
                return f"[{colour}]{inner}[/{colour}]"
            else:
                return inner

        if self.is_black_square:
            return B * 4

        letter = style(self.user_letter or S)

        if not self.clue_number:
            return f"{S}{S}{letter}{S}"

        n1 = S
        n2 = S

        digits = str(self.clue_number).split()

        if not 0 < len(digits) < 2:
            raise ValueError(f"Clue number must be 1 or 2-digits: {self.clue_number}")

        if len(digits) == 1:
            n2 = SUPERSCRIPTS[digits[0]]
        elif len(digits) == 2:
            n2 = SUPERSCRIPTS[digits[1]]
            n1 = SUPERSCRIPTS[digits[0]]

        return f"{n1}{n2}{letter}{S}"


@dataclass(frozen=True)
class Grid:
    cells: list[list[Cell]]

    # NOTE: assumes that (1) cell contents are one row high
    # and (2) cell width is 4 characters wide
    def display(self, check: bool = False):
        CELL_WIDTH = 4
        grid = ""

        n_rows = len(self.cells)
        n_cols = len(self.cells[0])

        solved = self.is_correct()

        def get_colour(cell: Cell) -> Optional[str]:
            if check:
                if solved:
                    return "green"
                elif cell.user_letter != cell.solution_letter:
                    return "red"
                else:
                    return None
            else:
                return None

        for r, row in enumerate(self.cells):
            # TOP
            for c, _ in enumerate(row):
                if c == 0 and r == 0:
                    grid += TL
                elif c == 0:
                    grid += CR
                elif r == 0:
                    grid += CD
                elif r == 0 and c == 0:
                    grid += BL
                else:
                    grid += CC

                grid += H * CELL_WIDTH

            if r == 0:
                grid += TR
            else:
                grid += CL

            grid += os.linesep

            # MIDDLE
            for c, col in enumerate(row):
                grid += V
                grid += col.display(colour=get_colour(col))

                if c == n_cols - 1:
                    grid += V

            grid += os.linesep

            # BOTTOM
            # Since each row shares a top and bottom,
            # we only have to print the bottom once
            if r == n_rows - 1:
                for c, _ in enumerate(row):
                    if c == 0:
                        grid += BL
                    else:
                        grid += CU

                    grid += H * CELL_WIDTH

                    if c == n_cols - 1:
                        grid += BR

        return grid

    def is_correct(self):
        return all(
            [c.user_letter == c.solution_letter for cell in self.cells for c in cell]
        )


def print_crossword(cw: Crossword, check: bool = False):
    grid = crossword_to_grid(cw)

    acrosses = ["[b][u]Across[/b][/u]"] + list(
        sorted(
            [str(c) for c in cw.clues if c.direction is Direction.ACROSS],
        )
    )

    downs = ["[b][u]Down[/b][/u]"] + list(
        sorted(
            [str(c) for c in cw.clues if c.direction is Direction.DOWN],
        )
    )

    print(
        Columns(
            [
                grid.display(check=check),
                os.linesep.join(acrosses),
                os.linesep.join(downs),
            ],
            padding=(1, 3),
        )
    )


def crossword_to_grid(cw: Crossword) -> Grid:
    # default all cells to black squares
    grid = [
        [Cell(is_black_square=True) for _ in range(cw.n_columns)]
        for _ in range(cw.n_rows)
    ]

    user_letters = {
        (letter.position_x, letter.position_y): letter.letter
        for letter in get_letters(cw.style, cw.number)
    }

    # paint white cells, letters and numbers
    for clue in cw.clues:
        length = len(clue.solution)

        x0 = clue.position_x
        y0 = clue.position_y

        grid[y0][x0].is_black_square = False
        grid[y0][x0].clue_number = clue.number
        grid[y0][x0].user_letter = user_letters.get((x0, y0))
        grid[y0][x0].solution_letter = clue.solution[0]

        match clue.direction:
            case Direction.ACROSS:
                xs = range(clue.position_x + 1, clue.position_x + length)
                ys = repeat(y0, length - 1)
            case Direction.DOWN:
                xs = repeat(x0, length - 1)
                ys = range(clue.position_y + 1, clue.position_y + length)

        for x, y, letter in zip(xs, ys, clue.solution[1:]):
            grid[y][x].is_black_square = False
            grid[y][x].user_letter = user_letters.get((x, y))
            grid[y][x].solution_letter = letter

    return Grid(grid)


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
            f"{cw.style.capitalize()} #{cw.number}",
            cw.user_state.capitalize(),
            style=style_for(cw),
        )

    Console().print(table)
