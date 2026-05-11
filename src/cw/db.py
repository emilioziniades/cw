"""
Module for storing all crossword data in a sqlite database

- stores crossword JSON into a sqlite database
"""

from typing import Generator, Optional
import sqlite3
from contextlib import contextmanager
import logging


from cw.config import config
from cw.crossword import Crossword, CrosswordStyle, Direction


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
            user_state TEXT NOT NULL,
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
            position_x INTEGER NOT NULL,
            position_y INTEGER NOT NULL,
            solution TEXT NOT NULL,
            user_solution TEXT NOT NULL CHECK(length(user_solution) = length(solution)),
            PRIMARY KEY (direction, number, crossword_style, crossword_number),
            FOREIGN KEY (crossword_style, crossword_number) REFERENCES crossword (style, number)
        );
        """,
        """
        CREATE UNIQUE INDEX only_one_active
        ON crossword (user_state)
        WHERE user_state = 'active'
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
            (style, number, date, name, n_rows, n_columns, user_state)
            VALUES
            (:style, :number, :date, :name, :n_rows, :n_columns, :user_state)
            """,
            {
                "style": crossword.style,
                "number": crossword.number,
                "date": crossword.date,
                "name": crossword.name,
                "n_rows": crossword.n_rows,
                "n_columns": crossword.n_columns,
                "user_state": crossword.user_state,
            },
        )

        db.executemany(
            """
            INSERT INTO clue
            (crossword_style, crossword_number, direction, number, clue, position_x, position_y, solution, user_solution)
            VALUES
            (:crossword_style, :crossword_number, :direction, :number, :clue, :position_x, :position_y, :solution, :user_solution)
            """,
            [
                {
                    "crossword_style": crossword.style,
                    "crossword_number": crossword.number,
                    "direction": clue.direction,
                    "number": clue.number,
                    "clue": clue.clue,
                    "position_x": clue.position_x,
                    "position_y": clue.position_y,
                    "solution": clue.solution,
                    "user_solution": clue.user_solution,
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
                UPDATE crossword
                SET user_state = 'inactive'
                WHERE style = ? AND number = ?
                """,
                (active.style, active.number),
            )
            logger.debug("Set %s #%s as inactive", active.style, active.number)
        db.execute(
            """
            UPDATE crossword
            SET user_state = 'active'
            WHERE style = ? AND number = ?
            """,
            (style, number),
        )
        logger.debug("Set %s #%s as active", style, number)


def get_active_crossword() -> Optional[Crossword]:
    with database() as db:
        res = db.execute(
            "SELECT * FROM crossword WHERE user_state = 'active'"
        ).fetchone()
        return Crossword.from_row(res, []) if res else None


def stop_crossword(style: CrosswordStyle, number: int):
    with database() as db:
        db.execute(
            """
            UPDATE crossword
            SET user_state = 'inactive'
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


def get_all_crosswords() -> list[Crossword]:
    with database() as db:
        res = db.execute(
            """
            SELECT *
            FROM crossword
            """,
        ).fetchall()

        return [Crossword.from_row(row, []) for row in res]


def solve_clue(
    direction: Direction,
    number: int,
    crossword_style: CrosswordStyle,
    crossword_number: int,
    user_solution: str,
):
    with database() as db:
        db.execute(
            """
            UPDATE clue
            SET
            user_solution = upper(:user_solution)
            WHERE
            crossword_style = :crossword_style
            AND
            crossword_number = :crossword_number
            AND
            number = :number
            AND
            direction = :direction
            """,
            {
                "direction": direction,
                "number": number,
                "crossword_style": crossword_style,
                "crossword_number": crossword_number,
                "user_solution": user_solution,
            },
        )
