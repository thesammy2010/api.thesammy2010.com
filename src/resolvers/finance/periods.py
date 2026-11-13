"""Date ranges for comparing spending between periods.

Kept free of any database import so that it stays unit testable.
"""

import calendar
import datetime
import decimal
from typing import Dict, Optional, Tuple

DAYS_OF_WEEK = [day.lower() for day in calendar.day_name]


def year_earlier(day: datetime.date) -> datetime.date:
    """The same day a year before, the 29th of February becoming the 28th."""
    try:
        return day.replace(year=day.year - 1)
    except ValueError:
        return day.replace(year=day.year - 1, day=28)


def month_period(
    year: int, month: int, today: datetime.date
) -> Tuple[datetime.date, datetime.date]:
    """A month's first day, and its last or today, whichever is earlier.

    Cutting the month in progress off at today is what makes it comparable
    with the same days of the month a year before, rather than with the
    whole of it.
    """
    first = datetime.date(year, month, 1)
    last = first.replace(day=calendar.monthrange(year, month)[1])
    # A month yet to start has no today in it to cut off at
    end = last if today < first else min(last, today)
    return first, end


def year_to_date_period(
    year: int, month: int, today: datetime.date
) -> Tuple[datetime.date, datetime.date]:
    """The 1st of January to the end of the month, or today if earlier."""
    _, end = month_period(year, month, today)
    return datetime.date(year, 1, 1), end


def change_pct(current: decimal.Decimal, previous: decimal.Decimal) -> Optional[float]:
    """How much current is up on previous, in percent, or None from nothing."""
    if not previous:
        return None
    return round(float((current - previous) / previous * 100), 1)


def weekday_counts(start: datetime.date, end: datetime.date) -> Dict[str, int]:
    """How many of each day of the week fall from start to end, both included."""
    days = (end - start).days + 1
    if days <= 0:
        return {day: 0 for day in DAYS_OF_WEEK}
    weeks, extra = divmod(days, 7)
    counts = {day: weeks for day in DAYS_OF_WEEK}
    for offset in range(extra):
        counts[DAYS_OF_WEEK[(start.weekday() + offset) % 7]] += 1
    return counts
