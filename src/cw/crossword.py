from dataclasses import dataclass
from enum import StrEnum, auto


# TODO: add sanitization
# TODO: add sanity checks like does the length of the solution match the specified length, does it fit into the crossword, etc


class CrosswordStyle(StrEnum):
    MINI = auto()
    QUICK = auto()
    CRYPTIC = auto()


@dataclass(frozen=True)
class Clue:
    direction: str
    number: int
    clue: str
    solution: str
    length: int
    position_x: int
    position_y: int

    @staticmethod
    def from_json(data: dict) -> "Clue":
        return Clue(
            direction=data["direction"],
            number=data["number"],
            clue=data["clue"],
            solution=data["solution"],
            length=data["length"],
            position_x=data["position"]["x"],
            position_y=data["position"]["y"],
        )

    def __post_init__(self):
        if len(self.solution) != self.length:
            raise ValueError("Solution length does not match supplied length")


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
        d = data["data"]
        return Crossword(
            style=d["crosswordType"],
            number=d["number"],
            date=d["date"],
            name=d["name"],
            n_rows=d["dimensions"]["rows"],
            n_columns=d["dimensions"]["cols"],
            clues=[Clue.from_json(c) for c in d["entries"]],
        )
