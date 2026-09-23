"""
Module for representing the crossword as a grid.
Acts as the sort of glue between the `crossword` table and the `user_input` table
"""

import os
from dataclasses import dataclass
from itertools import repeat
from typing import Self

from rich.text import Text

from cw.config import OutputStyle
from cw.crossword import Crossword, Direction
from cw.db import get_letters


@dataclass
class Cell:
    clue_number: int | None = None
    user_letter: str | None = None
    solution_letter: str | None = None
    is_black_square: bool = True


@dataclass(frozen=True)
class Grid:
    cells: list[list[Cell]]

    @classmethod
    def from_crossword(cls, cw: Crossword) -> Self:
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

        return cls(grid)

    def display(self, output: OutputStyle, reveal: bool = False) -> Text:

        LEFT_ONE_QUARTER = "\u258e"  # ▎
        BODY_WIDTH = 4
        BLACK = "#000000"
        WHITE = "#ffffff"
        GRAY = "#666666"
        CADMIUM_GREEN = "#097969"
        CADMIUM_RED = "#EE4B2B"

        if output is OutputStyle.PRETTY:
            text_colour = BLACK
            border_colour = BLACK
            correct_text_colour = CADMIUM_GREEN
            wrong_text_colour = CADMIUM_RED
            number_colour = GRAY
            background_colour = WHITE

        elif output is OutputStyle.PLAIN:
            text_colour = "white"
            border_colour = "white"
            correct_text_colour = "green"
            wrong_text_colour = "red"
            number_colour = "dim white"
            background_colour = "default"

        is_correct = self.is_correct()

        def background(cell: Cell) -> str:
            return border_colour if cell.is_black_square else background_colour

        def number_row(row: list[Cell]) -> Text:
            text = Text()
            for cell in row:
                style = f"{border_colour} on {background(cell)} overline"
                text.append(LEFT_ONE_QUARTER, style=style)
                if cell.is_black_square:
                    text.append(" " * BODY_WIDTH, style=style)
                else:
                    number = str(cell.clue_number) if cell.clue_number else ""
                    text.append(
                        number.ljust(BODY_WIDTH),
                        style=f"{number_colour} on {background(cell)} overline",
                    )
            text.append(LEFT_ONE_QUARTER, style=border_colour)
            return text

        def letter_row(row: list[Cell]) -> Text:
            text = Text()
            for cell in row:
                style = f"{border_colour} on {background(cell)}"
                text.append(LEFT_ONE_QUARTER, style=style)
                body = (
                    " " * BODY_WIDTH
                    if cell.is_black_square
                    else (cell.user_letter or " ".strip()).center(BODY_WIDTH)
                )

                letter_colour = text_colour
                if reveal:
                    if is_correct:
                        # only print green when the whole crossword is correct
                        letter_colour = correct_text_colour
                    elif cell.user_letter != cell.solution_letter:
                        letter_colour = wrong_text_colour
                    else:
                        letter_colour = text_colour

                style = f"{letter_colour} on {background(cell)}"
                text.append(body, style=f"bold {style}")
            text.append(LEFT_ONE_QUARTER, style=border_colour)
            return text

        width = len(self.cells[0]) * (BODY_WIDTH + 1) + 1
        rows = []
        for row in self.cells:
            rows.append(number_row(row))
            rows.append(letter_row(row))
        rows.append(Text(" " * (width - 1), style=f"{border_colour} overline"))

        return Text(os.linesep).join(rows)

    def is_correct(self) -> bool:
        return all(
            c.user_letter == c.solution_letter for cell in self.cells for c in cell
        )

    def is_correct_so_far(self) -> bool:
        return all(
            c.user_letter == c.solution_letter
            for cell in self.cells
            for c in cell
            if not c.is_black_square and c.user_letter
        )

    def is_complete(self) -> bool:
        return all(
            c.user_letter is not None
            for cell in self.cells
            for c in cell
            if not c.is_black_square
        )
