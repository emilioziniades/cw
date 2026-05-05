"""
Module for storing all crossword data in a sqlite database

- stores crossword JSON into a sqlite database
"""

import sqlite3
from contextlib import contextmanager

import click
from platformdirs import user_data_path

APP_NAME = "cw"
DATA_DIR = user_data_path(APP_NAME)
DB_FILE = DATA_DIR / "cw.sqlite"


@contextmanager
def database():
    db = sqlite3.connect(DB_FILE)
    try:
        with db:
            yield db
    finally:
        db.close()


def migrate():
    DB_FILE.parent.mkdir(exist_ok=True)

    migration = """
    CREATE TABLE IF NOT EXISTS crossword (
        style TEXT NOT NULL,
        number INTEGER NOT NULL,
        date INTEGER NOT NULL,
        name TEXT NOT NULL,
        n_rows INTEGER NOT NULL,
        n_columns INTEGER NOT NULL,
        PRIMARY KEY (style, number),
        UNIQUE(number, style)
    );

    CREATE TABLE IF NOT EXISTS clue (
        crossword_style TEXT NOT NULL,
        crossword_number INTEGER NOT NULL,
        direction TEXT NOT NULL,
        number INTEGER NOT NULL,
        clue TEXT NOT NULL,
        solution TEXT NOT NULL,
        length INTEGER NOT NULL,
        position_x INTEGER NOT NULL,
        position_y INTEGER NOT NULL,
        PRIMARY KEY (direction, number, crossword_style, crossword_number),
        FOREIGN KEY(crossword_style, crossword_number) REFERENCES crossword(style, number)
    );
    """

    with database() as db:
        db.executescript(migration)


def add_crossword(data: dict):
    d = data["data"]

    with database() as db:
        db.execute(
            "INSERT INTO crossword(style, number, date, name, n_rows, n_columns) VALUES (:style, :number, :date, :name, :n_rows, :n_columns)",
            {
                "style": d["crosswordType"],
                "number": d["number"],
                "date": d["date"],
                "name": d["name"],
                "n_rows": d["dimensions"]["rows"],
                "n_columns": d["dimensions"]["cols"],
            },
        )

        clues = [
            {
                "crossword_style": d["crosswordType"],
                "crossword_number": d["number"],
                "direction": clue["direction"],
                "number": clue["number"],
                "clue": clue["clue"],
                "solution": clue["solution"],
                "length": clue["length"],
                "position_x": clue["position"]["x"],
                "position_y": clue["position"]["y"],
            }
            for clue in d["entries"]
        ]
        db.executemany(
            "INSERT INTO clue (crossword_style, crossword_number, direction, number, clue, solution, length, position_x, position_y) VALUES (:crossword_style, :crossword_number, :direction, :number, :clue, :solution, :length, :position_x, :position_y)",
            clues,
        )

    click.echo("Saved crossword")


def has_crossword(data: dict) -> bool:
    style = data["data"]["crosswordType"]
    number = data["data"]["number"]

    with database() as db:
        res = db.execute(
            "SELECT COUNT(*) FROM crossword WHERE style = ? AND number = ?",
            [style, number],
        )
        (count,) = res.fetchone()

        return count >= 1
