from datetime import date, timedelta
from typing import Iterator


def n_sundays_between(start_date: date, end_date: date) -> int:
    if is_sunday(start_date):
        raise ValueError(f"start date {start_date} cannot be Sunday")

    if is_sunday(end_date):
        raise ValueError(f"end date {end_date} cannot be Sunday")

    days = (end_date - start_date).days
    n_sundays = days // 7

    if (days % 7 + start_date.isoweekday()) >= 7:
        n_sundays += 1

    return n_sundays


# This is open interval that does not include the start or end date
def days_between(start: date, end: date) -> Iterator[date]:
    current = start + timedelta(days=1)
    while current < end:
        yield current
        current += timedelta(days=1)


def is_sunday(d: date) -> bool:
    return d.isoweekday() == 7
