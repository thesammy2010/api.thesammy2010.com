"""Tests for projecting where a month and a year are heading."""

import datetime
import decimal
import uuid

import pytest

from src.resolvers.finance.forecast import (
    RecurringSpend,
    forecast_month,
    months_elapsed,
    pending_recurring,
    previous_month,
)

NATIONWIDE = uuid.UUID("0b1e9c4e-34a4-4a58-8f8e-4c5d1f3b8a01")
MORTGAGE = uuid.UUID("0b1e9c4e-34a4-4a58-8f8e-4c5d1f3b8a02")
UTILITY = uuid.UUID("0b1e9c4e-34a4-4a58-8f8e-4c5d1f3b8a03")
TFL = uuid.UUID("0b1e9c4e-34a4-4a58-8f8e-4c5d1f3b8a04")
TRANSPORT = uuid.UUID("0b1e9c4e-34a4-4a58-8f8e-4c5d1f3b8a05")


def spend(merchant_id, category_id, amount, on) -> RecurringSpend:
    return RecurringSpend(
        merchant_id=merchant_id,
        merchant=None,
        category_id=category_id,
        description=None,
        amount_gbp=decimal.Decimal(amount),
        spent_on=on,
    )


class TestMonthsElapsed:
    @pytest.mark.parametrize("year,expected", [(2025, 12), (2026, 11), (2027, 0)])
    def test_months_elapsed(self, year, expected):
        assert months_elapsed(year, datetime.date(2026, 11, 12)) == expected

    def test_the_month_before_january_is_last_december(self):
        assert previous_month(2026, 1) == (2025, 12)
        assert previous_month(2026, 11) == (2026, 10)


class TestPendingRecurring:
    def test_one_not_seen_yet_this_month_is_pending(self):
        pending = pending_recurring(
            last_month=[
                spend(NATIONWIDE, MORTGAGE, "1800", datetime.date(2026, 10, 1))
            ],
            this_month=[],
            year=2026,
            month=11,
        )

        assert [(p.amount_gbp, p.expected_on) for p in pending] == [
            (decimal.Decimal("1800"), datetime.date(2026, 11, 1))
        ]

    def test_one_already_seen_this_month_is_not(self):
        assert (
            pending_recurring(
                last_month=[
                    spend(NATIONWIDE, MORTGAGE, "1800", datetime.date(2026, 10, 1))
                ],
                this_month=[
                    spend(NATIONWIDE, MORTGAGE, "1800", datetime.date(2026, 11, 1))
                ],
                year=2026,
                month=11,
            )
            == []
        )

    def test_the_same_merchant_in_another_category_counts_separately(self):
        """The mortgage and the insurance are both paid to Nationwide."""
        pending = pending_recurring(
            last_month=[
                spend(NATIONWIDE, MORTGAGE, "1800", datetime.date(2026, 10, 1)),
                spend(NATIONWIDE, UTILITY, "18", datetime.date(2026, 10, 2)),
            ],
            this_month=[
                spend(NATIONWIDE, MORTGAGE, "1800", datetime.date(2026, 11, 1))
            ],
            year=2026,
            month=11,
        )

        assert [p.amount_gbp for p in pending] == [decimal.Decimal("18")]

    def test_only_the_ones_beyond_this_months_count_are_pending(self):
        pending = pending_recurring(
            last_month=[
                spend(TFL, TRANSPORT, "20", datetime.date(2026, 10, day))
                for day in (3, 10, 17)
            ],
            this_month=[spend(TFL, TRANSPORT, "20", datetime.date(2026, 11, 4))],
            year=2026,
            month=11,
        )

        assert [p.expected_on.day for p in pending] == [10, 17]

    def test_the_31st_becomes_the_last_day_of_a_shorter_month(self):
        (pending,) = pending_recurring(
            last_month=[
                spend(NATIONWIDE, MORTGAGE, "1800", datetime.date(2026, 10, 31))
            ],
            this_month=[],
            year=2026,
            month=11,
        )

        assert pending.expected_on == datetime.date(2026, 11, 30)


class TestForecastMonth:
    def forecast(self, today, **kwargs):
        defaults = dict(
            year=2026,
            month=11,
            today=today,
            spent=decimal.Decimal("2100"),
            spent_not_recurring=decimal.Decimal("300"),
            pending=[],
        )
        defaults.update(kwargs)
        return forecast_month(**defaults)

    def test_only_the_month_in_progress_has_one(self):
        assert self.forecast(datetime.date(2026, 12, 1)) is None
        assert self.forecast(datetime.date(2026, 10, 31)) is None

    def test_the_rest_of_the_month_is_projected_from_what_doesnt_recur(self):
        forecast = self.forecast(datetime.date(2026, 11, 10))

        assert forecast.days_elapsed == 10
        assert forecast.average_per_day_gbp == decimal.Decimal("210.00")
        assert forecast.discretionary_per_day_gbp == decimal.Decimal("30.00")
        # 2100 so far, plus 30 a day for the 20 days left
        assert forecast.projected_total_gbp == decimal.Decimal("2700.00")

    def test_pending_recurring_spends_are_added(self):
        pending = pending_recurring(
            last_month=[spend(NATIONWIDE, UTILITY, "18", datetime.date(2026, 10, 20))],
            this_month=[],
            year=2026,
            month=11,
        )

        forecast = self.forecast(datetime.date(2026, 11, 30), pending=pending)

        assert forecast.pending_recurring_gbp == decimal.Decimal("18")
        assert forecast.projected_total_gbp == decimal.Decimal("2118.00")
