"""
Module for fetching crossword data from the Guardian website.

- fetches html from guardian website
- caches html locally
- transforms html into crossword json
"""

import json
import logging
from datetime import date
from typing import Optional

import requests
from bs4 import BeautifulSoup

from cw.calendar import n_sundays_between
from cw.config import config
from cw.crossword import CrosswordStyle

logger = logging.getLogger(__name__)


def fetch(number: Optional[int], style: CrosswordStyle):
    if number is None:
        logger.info("No puzzle number specified, fetching today's puzzle")
        number = crossword_number_from_date(style, date.today())
    logger.info("Fetching %s crossword #%s", style, number)

    cached_file = config.cache_dir / "crosswords" / style / f"{number}.html"
    url = f"https://www.theguardian.com/crosswords/{style}/{number}"

    if cached_file.exists():
        logger.debug("Found cached crossword at %s", cached_file)
        html = cached_file.read_text()
    else:
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


def crossword_number_from_date(style: CrosswordStyle, d: date) -> int:
    MINI_NUMBER_ONE = date(2025, 12, 17)
    QUICK_NUMBER_TEN_THOUSAND = date(2002, 5, 23)

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

    if style is CrosswordStyle.MINI:
        duration = d - MINI_NUMBER_ONE
        return duration.days
    elif style is CrosswordStyle.QUICK:
        duration = d - QUICK_NUMBER_TEN_THOUSAND
        days_missing_puzzles = [i for i in QUICK_DATES_MISSING_PUZZLES if d >= i]
        return (
            duration.days
            + 10_000
            - n_sundays_between(QUICK_NUMBER_TEN_THOUSAND, d)
            - len(days_missing_puzzles)
        )
    elif style is CrosswordStyle.CRYPTIC:
        raise NotImplementedError()
