import re
from dataclasses import dataclass

import click

from cw.crossword import Direction


@dataclass
class ClueArgument:
    direction: Direction
    number: int


class ClueParamType(click.ParamType):
    """
    Parse shorthand representations of a clue identifier from the commandline, e.g. 1d or 23a
    into a `(direction: Direction, number: int)` tuple.
    `"""

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
