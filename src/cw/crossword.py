from dataclasses import dataclass
from enum import StrEnum, auto
import sqlite3
from typing import assert_never


class CrosswordStyle(StrEnum):
    MINI = auto()
    QUICK = auto()
    CRYPTIC = auto()


class Direction(StrEnum):
    ACROSS = auto()
    DOWN = auto()


class State(StrEnum):
    ACTIVE = auto()
    INACTIVE = auto()
    COMPLETE = auto()


@dataclass(frozen=True)
class Clue:
    direction: Direction
    number: int
    clue: str
    solution: str
    length: int
    position_x: int
    position_y: int

    @staticmethod
    def from_json(data: dict) -> "Clue":
        return Clue(
            direction=Direction(data["direction"]),
            number=data["number"],
            clue=data["clue"],
            solution=data["solution"],
            length=data["length"],
            position_x=data["position"]["x"],
            position_y=data["position"]["y"],
        )

    @staticmethod
    def from_row(row: sqlite3.Row) -> "Clue":
        data = dict(row)
        return Clue(
            direction=Direction(data["direction"]),
            number=data["number"],
            clue=data["clue"],
            solution=data["solution"],
            length=data["length"],
            position_x=data["position_x"],
            position_y=data["position_y"],
        )

    def __post_init__(self):
        if len(self.solution) != self.length:
            raise ValueError("Solution length does not match supplied length")

    def __str__(self):
        clue = (
            self.clue.replace("<span>", "")
            .replace("</span>", "")
            .replace("<i>", "[italic]")
            .replace("</i>", "[/italic]")
        )
        return f"{self.number}. {clue}"


@dataclass(frozen=True)
class Crossword:
    style: CrosswordStyle
    number: int
    date: int
    name: str
    n_rows: int
    n_columns: int
    clues: list[Clue]

    @staticmethod
    def from_json(data: dict) -> "Crossword":
        return Crossword(
            style=CrosswordStyle(data["crosswordType"]),
            number=data["number"],
            date=data["date"],
            name=data["name"],
            n_rows=data["dimensions"]["rows"],
            n_columns=data["dimensions"]["cols"],
            clues=[Clue.from_json(c) for c in data["entries"]],
        )

    @staticmethod
    def from_row(row: sqlite3.Row, clues_rows: list[sqlite3.Row]) -> "Crossword":
        data = dict(row)
        return Crossword(
            style=CrosswordStyle(data["style"]),
            number=data["number"],
            date=data["date"],
            name=data["name"],
            n_rows=data["n_rows"],
            n_columns=data["n_columns"],
            clues=[Clue.from_row(c) for c in clues_rows],
        )

    def __post_init__(self):
        for clue in self.clues:
            max_x = self.n_columns - 1
            max_y = self.n_rows - 1

            start_x = clue.position_x
            start_y = clue.position_y

            if clue.direction is Direction.ACROSS:
                end_x = start_x + clue.length - 1
                end_y = start_y
            elif clue.direction is Direction.DOWN:
                end_x = start_x
                end_y = start_y + clue.length - 1
            else:
                assert_never(clue.direction)

            if not (0 <= start_x <= end_x <= max_x and 0 <= start_y <= end_y <= max_y):
                raise ValueError(
                    f"Clue {clue.number}-{clue.direction} does not fit in crossword {self.n_columns}x{self.n_rows}"
                )


@dataclass(frozen=True)
class UserCrossword:
    style: CrosswordStyle
    number: int
    state: State

    @staticmethod
    def from_row(row: sqlite3.Row) -> "UserCrossword":
        data = dict(row)
        return UserCrossword(
            style=data["style"],
            number=data["number"],
            state=State(data["state"]),
        )
