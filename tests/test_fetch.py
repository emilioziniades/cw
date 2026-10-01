from datetime import date

import pytest

from cw.crossword import CrosswordStyle
from cw.fetch import latest_crossword_number


@pytest.mark.parametrize(
    "style, date, expected_number",
    [
        (CrosswordStyle.MINI, date(2026, 5, 18), 152),
        (CrosswordStyle.QUICK, date(2002, 5, 23), 10000),
        (CrosswordStyle.QUICK, date(2002, 5, 29), 10005),
        (CrosswordStyle.QUICK, date(2005, 8, 8), 11000),
        (CrosswordStyle.QUICK, date(2026, 5, 18), 17482),
        (CrosswordStyle.QUICK, date(2015, 3, 24), 14000),
        (CrosswordStyle.QUICK, date(2021, 8, 18), 16000),
        (CrosswordStyle.CRYPTIC, date(2026, 5, 18), 30009),
        (CrosswordStyle.CRYPTIC, date(2000, 9, 11), 22000),
        (CrosswordStyle.CRYPTIC, date(2023, 2, 22), 29000),
        (CrosswordStyle.CRYPTIC, date(2007, 2, 14), 24000),
        (CrosswordStyle.CRYPTIC, date(2026, 10, 25), 30121),
        (CrosswordStyle.CRYPTIC, date(2026, 10, 26), 30121),
        (
            # A Sunday when no puzzle was published
            CrosswordStyle.CRYPTIC,
            date(2026, 9, 27),
            30122,
        ),
        (CrosswordStyle.CRYPTIC, date(2026, 9, 26), 30122),
        (CrosswordStyle.QUICKCRYPTIC, date(2024, 4, 6), 1),
        (CrosswordStyle.QUICKCRYPTIC, date(2025, 4, 19), 55),
        (CrosswordStyle.QUICKCRYPTIC, date(2026, 9, 26), 130),
        (CrosswordStyle.QUICKCRYPTIC, date(2026, 10, 1), 130),
    ],
)
def test_latest_number(style: CrosswordStyle, date: date, expected_number: int):
    actual_number = latest_crossword_number(style, date)
    assert expected_number == actual_number, (
        f"{style} {date}: got {actual_number}, expected {expected_number}"
    )
