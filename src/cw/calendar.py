from calendar import Day
from collections.abc import Iterator
from datetime import UTC, date, datetime, timedelta


def n_days_between(day: Day, start: date, end: date) -> int:
    if start > end:
        raise ValueError(f"start date {start} occurs after end date {end}")

    days_until_next = (day - start.weekday()) % 7
    first_day = start + timedelta(days=days_until_next)

    if first_day > end:
        return 0

    return (end - first_day).days // 7 + 1


def n_days_between_slow(day: Day, start: date, end: date) -> int:
    current = start
    count = 0

    while current <= end:
        if current.weekday() == day:
            count += 1

        current += timedelta(days=1)

    return count


# This is open interval that does not include the start or end date
def days_between(start: date, end: date) -> Iterator[date]:
    current = start + timedelta(days=1)
    while current < end:
        yield current
        current += timedelta(days=1)


def today() -> date:
    return datetime.now(tz=UTC).date()
