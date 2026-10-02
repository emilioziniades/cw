"""
Module for fetching crossword data from the Guardian website.

- fetches html from guardian website
- caches html locally
- transforms html into crossword json
"""

import json
import logging
from calendar import SATURDAY, SUNDAY
from datetime import date

import requests
from bs4 import BeautifulSoup

from cw.calendar import n_days_between, today
from cw.config import config
from cw.crossword import CrosswordStyle

logger = logging.getLogger(__name__)

BASE_URL = "https://www.theguardian.com/crosswords"


def fetch(style: CrosswordStyle, number: int | None):
    if number is None:
        logger.info("No puzzle number specified, fetching today's puzzle")
        number = latest_crossword_number(style, today())
    logger.info("Fetching %s crossword #%s", style, number)

    cached_file = config.cache_dir / "crosswords" / style / f"{number}.html"
    url = f"{BASE_URL}/{style}/{number}"

    if cached_file.exists():
        logger.debug("Found cached crossword at %s", cached_file)
        html = cached_file.read_text()
    else:
        logger.debug("Fetching crossword from %s", url)
        response = requests.get(url)
        if (
            response.status_code == requests.codes.not_found
            and style is CrosswordStyle.CRYPTIC
        ):
            # Saturday cryptics are at /prize/{number}, not /cryptic/{number},
            # so in this special case we have to try both
            url = f"{BASE_URL}/prize/{number}"
            logger.debug("Fetching crossword from %s", url)
            response = requests.get(url)

        response.raise_for_status()
        html = response.text

        cached_file.parent.mkdir(parents=True, exist_ok=True)
        cached_file.write_text(html)

        logger.debug("Saved crossword html to %s", cached_file)

    puzzle_json = puzzle_json_from_html(html)
    return puzzle_json["data"]


def puzzle_json_from_html(html: str) -> dict:
    soup = BeautifulSoup(html, "html.parser")

    crossword_component = soup.find("gu-island", attrs={"name": "CrosswordComponent"})
    if crossword_component is None:
        raise ValueError(
            'Could not find <gu-island name="CrosswordComponent"> in Guardian html'
        )

    crossword_props = crossword_component.get("props")
    if crossword_props is None:
        raise ValueError(
            '<gu-island name="CrosswordComponent"> did not have `props` attribute'
        )

    data = json.loads(str(crossword_props))
    return data


def latest_crossword_number(style: CrosswordStyle, d: date) -> int:
    MINI_START_DATE = date(2025, 12, 17)

    QUICK_START_DATE = date(2002, 5, 23)
    QUICK_START_NUMBER = 10_000
    QUICK_DATES_MISSING_PUZZLES = [
        date(2002, 12, 25),
        date(2002, 12, 26),
        date(2003, 12, 25),
        date(2003, 12, 26),
        date(2004, 12, 25),
        date(2005, 12, 26),
        date(2006, 12, 25),
        date(2006, 12, 26),
        date(2007, 12, 25),
        date(2007, 12, 26),
        date(2008, 12, 25),
        date(2008, 12, 26),
        date(2009, 12, 25),
        date(2009, 12, 26),
        date(2010, 12, 21),
        date(2012, 12, 25),
        date(2013, 12, 25),
        date(2014, 12, 25),
        date(2015, 12, 25),
        date(2017, 12, 25),
        date(2018, 12, 25),
        date(2019, 12, 25),
        date(2020, 12, 25),
        date(2021, 12, 25),
        date(2023, 12, 25),
        date(2024, 12, 25),
        date(2025, 12, 25),
    ]

    CRYPTIC_START_DATE = date(2000, 9, 11)
    CRYPTIC_START_NUMBER = 22000
    CRYPTIC_DATES_MISSING_PUZZLES = [
        date(2000, 12, 25),
        date(2000, 12, 26),
        date(2001, 12, 25),
        date(2001, 12, 26),
        date(2002, 12, 25),
        date(2002, 12, 26),
        date(2003, 12, 25),
        date(2003, 12, 26),
        date(2004, 12, 25),
        date(2005, 12, 26),
        date(2006, 12, 25),
        date(2006, 12, 26),
        date(2007, 12, 25),
        date(2007, 12, 26),
        date(2008, 12, 25),
        date(2008, 12, 26),
        date(2009, 12, 25),
        date(2009, 12, 26),
        date(2009, 7, 18),
        date(2010, 12, 25),
        date(2012, 12, 25),
        date(2013, 12, 25),
        date(2014, 12, 25),
        date(2015, 12, 25),
        date(2017, 12, 25),
        date(2018, 12, 25),
        date(2019, 12, 25),
        date(2020, 12, 25),
        date(2021, 12, 25),
        date(2023, 12, 25),
        date(2024, 12, 25),
        date(2025, 12, 25),
    ]
    CRYPTIC_DATES_EXTRA_PUZZLE = [
        date(2009, 7, 20),
    ]

    QUICKCRYPTIC_START_DATE = date(2024, 4, 6)
    QUICKCRYPTIC_START_NUMBER = 1

    def dates_lte(d: date, ds: list[date]) -> int:
        return len([i for i in ds if d >= i])

    # Mini crosswords are released every day
    if style is CrosswordStyle.MINI:
        duration = d - MINI_START_DATE
        return duration.days

    # Quick crosswords are not published on a Sunday
    elif style is CrosswordStyle.QUICK:
        duration = d - QUICK_START_DATE
        return (
            duration.days
            + QUICK_START_NUMBER
            - n_days_between(SUNDAY, QUICK_START_DATE, d)
            - dates_lte(d, QUICK_DATES_MISSING_PUZZLES)
        )

    # Cryptic crosswords are not published on a Sunday
    elif style is CrosswordStyle.CRYPTIC:
        duration = d - CRYPTIC_START_DATE
        return (
            duration.days
            + CRYPTIC_START_NUMBER
            - n_days_between(SUNDAY, CRYPTIC_START_DATE, d)
            - dates_lte(d, CRYPTIC_DATES_MISSING_PUZZLES)
            + dates_lte(d, CRYPTIC_DATES_EXTRA_PUZZLE)
        )

    # Quick Cryptic crosswords are only published on a Saturday
    elif style is CrosswordStyle.QUICKCRYPTIC:
        return (
            QUICKCRYPTIC_START_NUMBER
            + n_days_between(SATURDAY, QUICKCRYPTIC_START_DATE, d)
            - 1
        )
