from dataclasses import dataclass
from typing import Self


# TODO: add sanitization
# TODO: add sanity checks like does the length of the solution match the specified length, does it fit into the crossword, etc


@dataclass
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
        # "crossword_style": d["crosswordType"],
        # "crossword_number": d["number"],
        return Clue(
            direction=data["direction"],
            number=data["number"],
            clue=data["clue"],
            solution=data["solution"],
            length=data["length"],
            position_x=data["position"]["x"],
            position_y=data["position"]["y"],
        )


@dataclass
class Crossword:
    style: str
    number: str
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
