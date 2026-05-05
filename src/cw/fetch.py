"""
Module for fetching crossword data from the Guardian website.

TODO:
    - fetch html from guardian website
    - cache html locally
    - transform html into crossword json
    - then store that locally in a sqlite database
"""

# TODO: create enum for crossword styles

from typing import Any, Optional
from datetime import date
import json

from bs4 import BeautifulSoup
import requests
from platformdirs import user_cache_path
from pprint import pprint

APP_NAME = "cw"
CACHE_DIR = user_cache_path(APP_NAME)


def fetch(number: Optional[int], style: str):
    if number is None:
        number = puzzle_number_from_date(style)
        print(CACHE_DIR)
        print(number)

    cached_file = CACHE_DIR / "crosswords" / style / f"{number}.html"
    url = f"https://www.theguardian.com/crosswords/{style}/{number}"

    if cached_file.exists():
        print("cached")
        html = cached_file.read_text()
    else:
        print("uncached, fetching")
        response = requests.get(url)
        response.raise_for_status()
        html = response.text

        cached_file.parent.mkdir(parents=True, exist_ok=True)
        cached_file.write_text(html)

    puzzle_json = puzzle_json_from_html(html)
    pprint(puzzle_json)


def puzzle_json_from_html(html: str) -> dict[Any, Any]:
    soup = BeautifulSoup(html, "html.parser")

    crossword_component = soup.find("gu-island", attrs={"name": "CrosswordComponent"})
    assert crossword_component is not None

    crossword_props = crossword_component.get("props")
    assert crossword_props is not None

    data = json.loads(str(crossword_props))
    return data


def puzzle_number_from_date(style: str, d: date = date.today()) -> int:
    MINI_NUMBER_ONE = date(2025, 12, 17)

    if style == "mini":
        duration = d - MINI_NUMBER_ONE
        return duration.days
    elif style == "quick":
        raise NotImplementedError()
    elif style == "cryptic":
        raise NotImplementedError()
    else:
        raise Exception(f"Unknown crossword style: {style}")
