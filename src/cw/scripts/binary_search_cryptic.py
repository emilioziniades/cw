import logging
from datetime import date
from pprint import pprint

from cw.binary_search import Puzzle, binary_search
from cw.crossword import CrosswordStyle


def main():
    logging.basicConfig(level=logging.DEBUG)
    START = Puzzle(22_000, date(2000, 9, 11))
    END = Puzzle(30_016, date(2026, 5, 26))
    STYLE = CrosswordStyle.CRYPTIC
    KNOWN_DATES = {
        # Cryptic 26,759 cannot be represented in the standard UI because it
        # has some idiosyncrasies. Therefore it is not available at its usual URL.
        # So we just hardcode the date here. See below URL for more information.
        # https://www.theguardian.com/crosswords/2015/dec/19/prize-crossword-no-26759
        26_759: date(2015, 12, 19),
        # Similar to above, the puzzle can't be represented in the standard interactive
        # grid so it does not appear at the regular URL
        # https://www.theguardian.com/crosswords/2024/dec/28/prize-crossword-no-29577
        29_577: date(2024, 12, 28),
        # Same as above.
        # https://www.theguardian.com/crosswords/2017/dec/23/prize-crossword-no-27388
        27_388: date(2017, 12, 23),
        # Same as above.
        # https://www.theguardian.com/crosswords/2023/dec/23/prize-crossword-no-29261
        29_261: date(2023, 12, 23),
        # Cryptic 22,375 is a Saturday prize puzzle, but /prize/22375 (and
        # /cryptic/22375) 404s. The numbering is continuous around it
        # (22374 = Fri 23 Nov 2001, 22376 = Mon 26 Nov 2001), so it exists on
        # Sat 24 Nov 2001 - the URL is just broken. Hardcode its date.
        22_375: date(2001, 11, 24),
    }

    missing_days, extra_days = binary_search(START, END, STYLE, KNOWN_DATES)
    pprint(missing_days)
    pprint({"missing": missing_days, "extra": extra_days})


if __name__ == "__main__":
    main()
