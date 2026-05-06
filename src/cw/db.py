"""
Module for storing all crossword data in a sqlite database

- stores crossword JSON into a sqlite database
"""

import sqlite3
from contextlib import contextmanager
import logging

from cw.config import config
from cw.crossword import Crossword


logger = logging.getLogger(__name__)


@contextmanager
def database():
    db = sqlite3.connect(config.database_file)
    try:
        with db:
            yield db
    finally:
        db.close()


def migrate():
    logger.debug("running database migrations")
    config.database_file.parent.mkdir(exist_ok=True)

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


def add_crossword(crossword: Crossword):
    with database() as db:
        db.execute(
            """
            INSERT INTO crossword
            (style, number, date, name, n_rows, n_columns)
            VALUES
            (:style, :number, :date, :name, :n_rows, :n_columns)
            """,
            {
                "style": crossword.style,
                "number": crossword.number,
                "date": crossword.date,
                "name": crossword.name,
                "n_rows": crossword.n_rows,
                "n_columns": crossword.n_columns,
            },
        )

        db.executemany(
            """
            INSERT INTO clue
            (crossword_style, crossword_number, direction, number, clue, solution, length, position_x, position_y)
            VALUES
            (:crossword_style, :crossword_number, :direction, :number, :clue, :solution, :length, :position_x, :position_y)
            """,
            [
                {
                    "crossword_style": crossword.style,
                    "crossword_number": crossword.number,
                    "direction": clue.direction,
                    "number": clue.number,
                    "clue": clue.clue,
                    "solution": clue.solution,
                    "length": clue.length,
                    "position_x": clue.position_x,
                    "position_y": clue.position_y,
                }
                for clue in crossword.clues
            ],
        )

    logger.debug("Saved crossword to sqlite database")


def has_crossword(crossword: Crossword) -> bool:
    with database() as db:
        res = db.execute(
            "SELECT COUNT(*) FROM crossword WHERE style = ? AND number = ?",
            [crossword.style, crossword.number],
        )
        (count,) = res.fetchone()

        if count >= 1:
            logger.debug("Crossword already in database")
            return True
        else:
            logger.debug("Saved crossword to database")
            return False
