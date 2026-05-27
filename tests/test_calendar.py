from datetime import date

import pytest

from cw.calendar import days_between
from cw.fetch import n_sundays_between


@pytest.mark.parametrize(
    "start_date, end_date, expected",
    [
        (date(2026, 1, 1), date(2026, 1, 1), 0),
        (date(2026, 1, 1), date(2026, 2, 2), 5),
        (date(2026, 1, 1), date(2026, 4, 1), 13),
        (date(2026, 1, 1), date(2027, 1, 1), 52),
    ],
)
def test_sundays_between(start_date: date, end_date: date, expected: int):
    actual = n_sundays_between(start_date, end_date)
    assert expected == actual


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
    print(actual_days_between)
    actual_days = len(actual_days_between)
    assert expected_days == actual_days, (
        f"start={start}, end={end}, expected={expected_days}, actual={actual_days} days={list(actual_days_between)}"
    )
