"""Tests for the date ranges spending is compared over."""

import datetime
import decimal

import pytest

from src.resolvers.finance.periods import (
    change_pct,
    month_period,
    weekday_counts,
    year_earlier,
    year_to_date_period,
)

TODAY = datetime.date(2026, 11, 12)


class TestYearEarlier:
    def test_the_same_day_a_year_before(self):
        assert year_earlier(TODAY) == datetime.date(2025, 11, 12)

    def test_a_leap_day_becomes_the_28th(self):
        assert year_earlier(datetime.date(2028, 2, 29)) == datetime.date(2027, 2, 28)


class TestMonthPeriod:
    def test_a_past_month_is_the_whole_month(self):
        assert month_period(2026, 10, TODAY) == (
            datetime.date(2026, 10, 1),
            datetime.date(2026, 10, 31),
        )

    def test_the_month_in_progress_ends_today(self):
        assert month_period(2026, 11, TODAY) == (
            datetime.date(2026, 11, 1),
            TODAY,
        )

    def test_the_same_month_a_year_before_is_cut_at_the_same_day(self):
        assert month_period(2025, 11, year_earlier(TODAY)) == (
            datetime.date(2025, 11, 1),
            datetime.date(2025, 11, 12),
        )

    def test_a_month_yet_to_start_is_the_whole_month(self):
        assert month_period(2026, 12, TODAY)[1] == datetime.date(2026, 12, 31)

    def test_the_year_to_date_starts_in_january(self):
        assert year_to_date_period(2026, 11, TODAY) == (
            datetime.date(2026, 1, 1),
            TODAY,
        )


class TestChangePct:
    @pytest.mark.parametrize(
        "current,previous,expected",
        [("150", "100", 50.0), ("75", "100", -25.0), ("10", "0", None)],
    )
    def test_change_pct(self, current, previous, expected):
        assert (
            change_pct(decimal.Decimal(current), decimal.Decimal(previous)) == expected
        )


class TestWeekdayCounts:
    def test_a_whole_number_of_weeks_has_one_of_each_per_week(self):
        counts = weekday_counts(datetime.date(2026, 11, 2), datetime.date(2026, 11, 15))

        assert set(counts.values()) == {2}

    def test_the_extra_days_start_from_the_first_days_weekday(self):
        # Sunday the 1st to Tuesday the 10th: ten days, so an extra Sunday,
        # Monday and Tuesday
        counts = weekday_counts(datetime.date(2026, 11, 1), datetime.date(2026, 11, 10))

        assert counts["sunday"] == counts["monday"] == counts["tuesday"] == 2
        assert counts["wednesday"] == counts["saturday"] == 1
        assert sum(counts.values()) == 10

    def test_an_empty_range_has_none(self):
        assert set(
            weekday_counts(TODAY, TODAY - datetime.timedelta(days=1)).values()
        ) == {0}
