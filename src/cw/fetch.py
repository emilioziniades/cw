"""
Module for fetching crossword data from the Guardian website.

- fetches html from guardian website
- caches html locally
- transforms html into crossword json
"""

# TODO: create enum for crossword styles

from typing import Optional
from datetime import date
import json

from bs4 import BeautifulSoup
import click
import requests
from platformdirs import user_cache_path

APP_NAME = "cw"
CACHE_DIR = user_cache_path(APP_NAME)


def fetch(number: Optional[int], style: str):
    if number is None:
        click.echo("No puzzle number specified, fetching today's puzzle")
        number = puzzle_number_from_date(style, date.today())
    click.echo(f"Fetching {style} crossword number {number}")

    cached_file = CACHE_DIR / "crosswords" / style / f"{number}.html"
    url = f"https://www.theguardian.com/crosswords/{style}/{number}"

    if cached_file.exists():
        print("Found cached crossword")
        html = cached_file.read_text()
    else:
        click.echo(f"Fetching crossword from {url}")
        response = requests.get(url)
        response.raise_for_status()
        html = response.text

        cached_file.parent.mkdir(parents=True, exist_ok=True)
        cached_file.write_text(html)

    puzzle_json = puzzle_json_from_html(html)
    return puzzle_json


def puzzle_json_from_html(html: str) -> dict:
    soup = BeautifulSoup(html, "html.parser")

    crossword_component = soup.find("gu-island", attrs={"name": "CrosswordComponent"})
    assert crossword_component is not None

    crossword_props = crossword_component.get("props")
    assert crossword_props is not None

    data = json.loads(str(crossword_props))
    return data


def puzzle_number_from_date(style: str, d: date) -> int:
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
