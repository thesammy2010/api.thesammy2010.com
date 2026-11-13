"""Working out where a month or a year is heading.

Kept free of any database import so that it stays unit testable: the stats
resolver queries the spends and hands them over as plain rows.
"""

import calendar
import dataclasses
import datetime
import decimal
import uuid
from collections import defaultdict
from typing import Dict, List, Optional, Tuple

from src.schemas.finance.stats import MonthForecast, PendingRecurring

ZERO = decimal.Decimal("0")


@dataclasses.dataclass
class RecurringSpend:
    merchant_id: Optional[uuid.UUID]
    merchant: Optional[str]
    category_id: Optional[uuid.UUID]
    description: Optional[str]
    amount_gbp: decimal.Decimal
    spent_on: datetime.date


def months_elapsed(year: int, today: datetime.date) -> int:
    """Months of the year so far, the one in progress included."""
    if year < today.year:
        return 12
    if year > today.year:
        return 0
    return today.month


def previous_month(year: int, month: int) -> Tuple[int, int]:
    return (year - 1, 12) if month == 1 else (year, month - 1)


def _same_day_in(day: int, year: int, month: int) -> datetime.date:
    """The day of the month in another month, the 31st becoming its last day."""
    return datetime.date(year, month, min(day, calendar.monthrange(year, month)[1]))


def pending_recurring(
    last_month: List[RecurringSpend],
    this_month: List[RecurringSpend],
    year: int,
    month: int,
) -> List[PendingRecurring]:
    """Last month's recurring spends that haven't come round yet this month.

    Spends are matched on merchant and category, so the mortgage and the
    building insurance paid to the same lender count separately. When last
    month had more of one than this month has so far, the extra ones from
    last month are taken to be still to come, the latest of them first left.
    """

    def key(spend: RecurringSpend):
        return (spend.merchant_id, spend.category_id)

    seen: Dict = defaultdict(int)
    for spend in this_month:
        seen[key(spend)] += 1

    expected: Dict = defaultdict(list)
    for spend in sorted(last_month, key=lambda spend: spend.spent_on):
        expected[key(spend)].append(spend)

    pending = [
        PendingRecurring(
            merchant_id=spend.merchant_id,
            merchant=spend.merchant,
            category_id=spend.category_id,
            description=spend.description,
            amount_gbp=spend.amount_gbp,
            expected_on=_same_day_in(spend.spent_on.day, year, month),
        )
        for spends_key, spends in expected.items()
        for spend in spends[seen[spends_key] :]
    ]
    return sorted(pending, key=lambda spend: (spend.expected_on, -spend.amount_gbp))


def forecast_month(
    year: int,
    month: int,
    today: datetime.date,
    spent: decimal.Decimal,
    spent_not_recurring: decimal.Decimal,
    pending: List[PendingRecurring],
) -> Optional[MonthForecast]:
    """Where the month in progress is heading, or None for any other month.

    The rest of the month is projected from what's been spent so far on
    things that don't recur, since the recurring ones are counted from last
    month instead and a mortgage early in the month would otherwise inflate
    every day after it.
    """
    if (today.year, today.month) != (year, month):
        return None

    days_in_month = calendar.monthrange(year, month)[1]
    days_elapsed = today.day
    per_day = spent / days_elapsed
    discretionary_per_day = spent_not_recurring / days_elapsed
    pending_total = sum((spend.amount_gbp for spend in pending), ZERO)

    return MonthForecast(
        as_of=today,
        days_elapsed=days_elapsed,
        days_in_month=days_in_month,
        average_per_day_gbp=round(per_day, 2),
        discretionary_per_day_gbp=round(discretionary_per_day, 2),
        pending_recurring_gbp=pending_total,
        pending_recurring=pending,
        projected_total_gbp=round(
            spent
            + pending_total
            + discretionary_per_day * (days_in_month - days_elapsed),
            2,
        ),
    )
