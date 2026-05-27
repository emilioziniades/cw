"""
The purpose for this script is to identify the dates that contain missed Quick crosswords.
"Missed" means (1) it is not Sunday and (2) a Quick crossword was not published that day

The idea is to do a binary search with caching to avoid hammering the Guardian website
"""

import logging
from dataclasses import dataclass
from datetime import date, datetime, timezone
from pprint import pprint
from typing import Generic, Optional, TypeVar

from cw.calendar import days_between, is_sunday
from cw.crossword import CrosswordStyle
from cw.fetch import fetch, n_sundays_between

logging.basicConfig(
    level=logging.DEBUG,
    format="%(levelname)-6s[%(name)-10s]: %(message)s",
)
logger = logging.getLogger(__name__)

T = TypeVar("T")


@dataclass
class Puzzle:
    number: int
    date: date


class Queue(Generic[T]):
    queue: list[T]

    def __init__(self, items: list[T] = []):
        self.queue = items

    def push(self, item: T):
        self.queue.append(item)

    def pop(self) -> Optional[T]:
        try:
            return self.queue.pop(0)
        except IndexError:
            return None


def binary_search(start: Puzzle, end: Puzzle, style: CrosswordStyle) -> list[date]:
    """
    Performs a binary search for dates that should have crossword puzzles but do not
    """
    queue: Queue[tuple[Puzzle, Puzzle]] = Queue()
    all_missing_days = []

    queue.push((start, end))

    while item := queue.pop():
        (start, end) = item
        logger.debug("start: %s, end: %s", start, end)

        expected_end_number = (
            start.number
            + (end.date - start.date).days
            - n_sundays_between(start.date, end.date)
        )

        if expected_end_number == end.number:
            logger.debug("No missing crosswords in this window")

        # We cannot narrow down our search any more, and the non-Sunday days between
        # start.date and end.date are the missed days!
        elif start.number + 1 == end.number:
            missing_days = filter(
                lambda d: not is_sunday(d),
                days_between(start.date, end.date),
            )
            logger.debug("Found days missing puzzles: %s", missing_days)
            all_missing_days += missing_days

        # There is at least one missing quick crossword in this window. Narrow down the search
        # more
        elif expected_end_number > end.number:
            logger.debug(
                "%d missing crosswords in this window", expected_end_number - end.number
            )

            middle_number = (end.number - start.number) // 2 + start.number
            middle_crossword = fetch(middle_number, style)
            middle_date = datetime.fromtimestamp(
                middle_crossword["date"] / 1000.0, tz=timezone.utc
            ).date()

            middle = Puzzle(middle_number, middle_date)
            queue.push((start, middle))
            queue.push((middle, end))

        else:
            raise Exception(f"{start} {end}: reached an impossible state")

    logger.info(
        "Found %d missing days: %s", len(all_missing_days), sorted(all_missing_days)
    )
    return all_missing_days


def main():
    START = Puzzle(10_000, date(2002, 5, 23))
    END = Puzzle(17_489, date(2026, 5, 26))
    STYLE = CrosswordStyle.QUICK

    missing_days = binary_search(START, END, STYLE)
    pprint(missing_days)


if __name__ == "__main__":
    main()
