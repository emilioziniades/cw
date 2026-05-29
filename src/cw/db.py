"""
Module for storing all crossword data in a sqlite database

- stores crossword JSON into a sqlite database

#TODO: alot of functions with many parameters where we could just pass the Crossword/Clue object
"""

import logging
import sqlite3
from contextlib import contextmanager
from itertools import repeat
from typing import Generator, Optional

from cw.config import config
from cw.crossword import Clue, Crossword, CrosswordStyle, Direction, Letter

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
            user_state TEXT NOT NULL CHECK(user_state IN ('active', 'inactive', 'complete')),
            PRIMARY KEY (style, number),
            UNIQUE (style, number)
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
            PRIMARY KEY (direction, number, crossword_style, crossword_number),
            FOREIGN KEY (crossword_style, crossword_number) REFERENCES crossword (style, number)
        );
        """,
        """
        CREATE UNIQUE INDEX only_one_active
        ON crossword (user_state)
        WHERE user_state = 'active';
        """,
        """
        CREATE TABLE IF NOT EXISTS user_input (
            crossword_style TEXT NOT NULL,
            crossword_number INTEGER NOT NULL,
            position_x INTEGER NOT NULL,
            position_y INTEGER NOT NULL,
            letter TEXT NOT NULL CHECK(length(letter) = 1 AND letter = UPPER(letter)),
            PRIMARY KEY (position_x, position_y, crossword_style, crossword_number),
            FOREIGN KEY (crossword_style, crossword_number) REFERENCES crossword (style, number)
        );
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
            (crossword_style, crossword_number, direction, number, clue, position_x, position_y, solution)
            VALUES
            (:crossword_style, :crossword_number, :direction, :number, :clue, :position_x, :position_y, :solution)
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


def get_clue(
    direction: Direction,
    number: int,
    crossword_style: CrosswordStyle,
    crossword_number: int,
) -> Optional[Clue]:
    with database() as db:
        res = db.execute(
            """
            SELECT *
            FROM clue
            WHERE crossword_style = ?
            AND crossword_number = ?
            AND number = ?
            AND direction = ?
            """,
            (crossword_style, crossword_number, number, direction),
        ).fetchone()

        if res:
            return Clue.from_row(res)
        else:
            return None


def add_letter(
    crossword_style: CrosswordStyle,
    crossword_number: int,
    position_x: int,
    position_y: int,
    letter: str,
):
    with database() as db:
        db.execute(
            """
            INSERT INTO user_input
            (crossword_style, crossword_number, position_x, position_y, letter)
            VALUES
            (:crossword_style, :crossword_number, :position_x, :position_y, :letter)
            ON CONFLICT
            DO UPDATE
            SET letter = :letter;
            """,
            {
                "crossword_style": crossword_style,
                "crossword_number": crossword_number,
                "position_x": position_x,
                "position_y": position_y,
                "letter": letter,
            },
        )


def get_letter(
    crossword_style: CrosswordStyle,
    crossword_number: int,
    position_x: int,
    position_y: int,
) -> Letter:
    with database() as db:
        res = db.execute(
            """
            SELECT * 
            FROM user_input
            WHERE crossword_style = :crossword_style
            AND crossword_number = :crossword_number
            AND position_x = :position_x
            AND position_y = :position_y
            """,
            {
                "crossword_style": crossword_style,
                "crossword_number": crossword_number,
                "position_x": position_x,
                "position_y": position_y,
            },
        ).fetchone()

        return Letter.from_row(res)


def get_letters(
    crossword_style: CrosswordStyle,
    crossword_number: int,
) -> list[Letter]:
    with database() as db:
        res = db.execute(
            """
            SELECT * 
            FROM user_input
            WHERE crossword_style = :crossword_style
            AND crossword_number = :crossword_number
            """,
            {
                "crossword_style": crossword_style,
                "crossword_number": crossword_number,
            },
        ).fetchall()

        return [Letter.from_row(row) for row in res]


def solve_clue(
    direction: Direction,
    number: int,
    crossword_style: CrosswordStyle,
    crossword_number: int,
    user_solution: str,
):
    clue = get_clue(direction, number, crossword_style, crossword_number)
    if clue is None:
        raise ValueError(
            f"Clue {number}{direction[0]} does not exist on {crossword_style} #{crossword_number}"
        )

    length = len(clue.solution)

    if len(user_solution) != length:
        raise ValueError(f"'{user_solution}' should be {length} characters")

    match clue.direction:
        case Direction.ACROSS:
            xs = range(clue.position_x, clue.position_x + length)
            ys = repeat(clue.position_y, length)
        case Direction.DOWN:
            xs = repeat(clue.position_x, length)
            ys = range(clue.position_y, clue.position_y + length)

    for x, y, letter in zip(xs, ys, user_solution):
        # this inserts in multiple transactions. it should be one
        add_letter(crossword_style, crossword_number, x, y, letter.upper())


def mark_completed(crossword: Crossword):
    with database() as db:
        db.execute(
            """
                UPDATE crossword
                SET user_state = 'complete'
                WHERE style = ? AND number = ?
            """,
            (crossword.style, crossword.number),
        )
    pass
