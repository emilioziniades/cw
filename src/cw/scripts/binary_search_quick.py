import logging
from datetime import date
from pprint import pprint

from cw.binary_search import Puzzle, binary_search
from cw.crossword import CrosswordStyle


def main():
    logging.basicConfig(level=logging.DEBUG)
    START = Puzzle(10_000, date(2002, 5, 23))
    END = Puzzle(17_489, date(2026, 5, 26))
    STYLE = CrosswordStyle.QUICK

    missing_days = binary_search(START, END, STYLE)
    pprint(missing_days)


if __name__ == "__main__":
    main()
