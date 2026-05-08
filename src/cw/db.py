"""
Module for storing all crossword data in a sqlite database

- stores crossword JSON into a sqlite database
"""

from typing import Generator, Optional
import sqlite3
from contextlib import contextmanager
import logging

from cw.config import config
from cw.crossword import Crossword, CrosswordStyle, State, UserCrossword


logger = logging.getLogger(__name__)


@contextmanager
def database() -> Generator[sqlite3.Connection]:
    db = sqlite3.connect(config.database_file)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys = ON")
    try:
        with db:
            yield db
    finally:
        db.close()


def get_user_version(db: sqlite3.Connection):
    (user_version,) = db.execute("PRAGMA user_version;").fetchone()
    return user_version


def set_user_version(db: sqlite3.Connection, n: int):
    db.execute(f"PRAGMA user_version = {n}")


def migrate():
    config.database_file.parent.mkdir(exist_ok=True, parents=True)

    migrations = [
        """
        CREATE TABLE IF NOT EXISTS crossword (
            style TEXT NOT NULL,
            number INTEGER NOT NULL,
            date INTEGER NOT NULL,
            name TEXT NOT NULL,
            n_rows INTEGER NOT NULL,
            n_columns INTEGER NOT NULL,
            PRIMARY KEY (style, number),
            UNIQUE (number, style)
        );
        """,
        """
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
            FOREIGN KEY (crossword_style, crossword_number) REFERENCES crossword (style, number)
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS user_crossword (
            style TEXT NOT NULL,
            number INTEGER NOT NULL,
            state TEXT NOT NULL,
            PRIMARY KEY (style, number),
            FOREIGN KEY (style, number) REFERENCES crossword (style, number),
            UNIQUE (number, style)
        );
        """,
        """
        CREATE UNIQUE INDEX only_one_active
        ON user_crossword (state)
        WHERE state = 'active'
        """,
    ]

    with database() as db:
        logger.debug("Current migration version is %s", get_user_version(db))

    for i, migration in enumerate(migrations, start=1):
        with database() as db:
            if i > get_user_version(db):
                logger.debug("Running migration #%s", i)
                db.executescript(migration)
                set_user_version(db, i)

    logger.debug("Database migrations complete")


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

        db.execute(
            """
            INSERT INTO user_crossword
            (style, number, state)
            VALUES
            (:style, :number, :state)
            """,
            {
                "style": crossword.style,
                "number": crossword.number,
                "state": State.INACTIVE,
            },
        )

    logger.debug("Saved crossword to sqlite database")


def has_crossword(crossword: Crossword) -> bool:
    with database() as db:
        res = db.execute(
            "SELECT COUNT(*) FROM crossword WHERE style = ? AND number = ?",
            [crossword.style, crossword.number],
        )
        (count,) = res.fetchone()

        exists = count >= 1

        if exists:
            logger.debug("Crossword already in database")

        return exists


def start_crossword(style: CrosswordStyle, number: int):
    active = get_active_crossword()

    with database() as db:
        if active is not None and (active.style, active.number) != (style, number):
            db.execute(
                """
                UPDATE user_crossword
                SET state = 'inactive'
                WHERE style = ? AND number = ?
                """,
                (active.style, active.number),
            )
            logger.debug("Set %s #%s as inactive", active.style, active.number)
        db.execute(
            """
            UPDATE user_crossword
            SET state = 'active'
            WHERE style = ? AND number = ?
            """,
            (style, number),
        )
        logger.debug("Set %s #%s as active", style, number)


def get_active_crossword() -> Optional[UserCrossword]:
    with database() as db:
        res = db.execute(
            "SELECT * FROM user_crossword WHERE state = 'active'"
        ).fetchone()
        return UserCrossword.from_row(res) if res else None


def stop_crossword(style: CrosswordStyle, number: int):
    with database() as db:
        db.execute(
            """
            UPDATE user_crossword
            SET state = 'inactive'
            WHERE style = ? AND number = ?
            """,
            (style, number),
        )
        logger.debug("Set %s #%s as inactive", style, number)


def get_crossword(style: CrosswordStyle, number: int) -> Optional[Crossword]:
    with database() as db:
        res = db.execute(
            """
            SELECT *
            FROM crossword
            WHERE style = ? AND number = ?
            """,
            (style, number),
        ).fetchone()

        clues_res = db.execute(
            """
            SELECT *
            FROM clue
            WHERE crossword_style = ? AND crossword_number = ?
            """,
            (style, number),
        ).fetchall()

        return Crossword.from_row(res, clues_res) if res else None
