from calendar import SUNDAY
from datetime import date

import pytest

from cw.calendar import days_between, n_days_between, n_days_between_slow


@pytest.mark.parametrize(
    "start_date, end_date, expected",
    [
        (date(2026, 1, 1), date(2026, 1, 1), 0),
        (date(2026, 1, 1), date(2026, 2, 2), 5),
        (date(2026, 1, 1), date(2026, 4, 1), 13),
        (date(2026, 1, 1), date(2027, 1, 1), 52),
        (date(2026, 9, 27), date(2026, 9, 27), 1),
        (date(2026, 9, 20), date(2026, 9, 27), 2),
        (date(2025, 9, 27), date(2026, 9, 27), 53),
    ],
)
def test_sundays_between(start_date: date, end_date: date, expected: int):
    actual = n_days_between(SUNDAY, start_date, end_date)
    actual_slow = n_days_between_slow(SUNDAY, start_date, end_date)

    assert actual == actual_slow, "slow and fast functions match"
    assert expected == actual_slow, "expected matches slow function"
    assert expected == actual, "expected matches fast function"


@pytest.mark.parametrize(
    "start, end, expected_days",
    [
        (date(2026, 1, 1), date(2026, 1, 1), 0),
        (date(2026, 1, 1), date(2026, 1, 2), 0),
        (date(2026, 1, 1), date(2026, 2, 1), 30),
        (date(2026, 1, 1), date(2027, 1, 1), 364),
    ],
)
def test_days_between(start: date, end: date, expected_days: int):
    actual_days_between = list(days_between(start, end))
    actual_days = len(actual_days_between)
    assert expected_days == actual_days, (
        f"start={start}, end={end}, expected={expected_days}, actual={actual_days} days={list(actual_days_between)}"
    )
