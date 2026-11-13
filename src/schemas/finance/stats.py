import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from src.schemas.finance.money import Money


class MonthlyStatsRequest(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    year: int = Field(description="The year of the month", ge=2000)
    month: int = Field(description="The month, from 1 to 12", ge=1, le=12)


class CategorySpend(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    category_id: UUID
    group: str = Field(description="The main category, such as Food & Drink")
    name: str = Field(description="The category, such as Dinner")
    spent_gbp: Money = Field(description="Total spent in the category that month")
    transactions: int = Field(description="Number of spends in the category")
    target_gbp: Optional[Money] = Field(
        description="The category's monthly target for that year, null when "
        "it has none",
        default=None,
    )


class PendingRecurring(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    merchant_id: Optional[UUID] = None
    merchant: Optional[str] = None
    category_id: Optional[UUID] = None
    description: Optional[str] = None
    amount_gbp: Money = Field(description="What it came to last month")
    expected_on: datetime.date = Field(
        description="The same day of the month it was spent on last month"
    )


class MonthForecast(BaseModel):
    """Where the month is heading, only given for the month in progress."""

    model_config = ConfigDict(from_attributes=True)

    as_of: datetime.date = Field(description="The day the forecast was made")
    days_elapsed: int = Field(description="Days of the month so far, today included")
    days_in_month: int
    average_per_day_gbp: Money = Field(
        description="Spent so far divided by days_elapsed"
    )
    discretionary_per_day_gbp: Money = Field(
        description="Spent so far on things not marked recurring, divided by "
        "days_elapsed. Used to project the rest of the month"
    )
    pending_recurring_gbp: Money = Field(
        description="Recurring spends from last month not yet seen this month"
    )
    pending_recurring: List[PendingRecurring] = Field(
        description="Each recurring spend from last month not yet seen this "
        "month, soonest first"
    )
    projected_total_gbp: Money = Field(
        description="Spent so far, plus pending_recurring_gbp, plus "
        "discretionary_per_day_gbp for each day left"
    )


class MonthlyStatsResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    year: int
    month: int
    total_gbp: Money = Field(description="Everything spent that month")
    transactions: int = Field(description="Number of spends that month")
    necessary_gbp: Money = Field(description="Spent on things marked necessary")
    discretionary_gbp: Money = Field(
        description="Spent on things marked not necessary. Spends with neither "
        "count towards neither this nor necessary_gbp"
    )
    recurring_gbp: Money = Field(description="Spent on things marked recurring")
    with_partner_gbp: Money = Field(description="Spent together with a partner")
    uncategorised_gbp: Money = Field(description="Spent without a category")
    target_gbp: Money = Field(
        description="The sum of every category's monthly target for that year"
    )
    categories: List[CategorySpend] = Field(
        description="Every category with a spend or a target that month, most "
        "spent first"
    )
    forecast: Optional[MonthForecast] = Field(
        description="Where the month is heading. Only given for the month in "
        "progress, null for one that's over or yet to start",
        default=None,
    )


class YearlyStatsRequest(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    year: int = Field(description="The year", ge=2000)


class MonthTotal(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    month: int
    total_gbp: Money
    running_total_gbp: Money = Field(description="Spent from January to this month")


class CategoryYear(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    category_id: UUID
    group: str
    name: str
    months: List[Money] = Field(
        description="Spent in each month, January first, always twelve long"
    )
    total_gbp: Money
    average_gbp: Money = Field(
        description="total_gbp divided by months_elapsed, the month in progress "
        "included"
    )
    target_gbp: Optional[Money] = Field(
        description="The monthly target for the year, null when it has none",
        default=None,
    )
    target_to_date_gbp: Optional[Money] = Field(
        description="target_gbp multiplied by months_elapsed", default=None
    )
    over_target_gbp: Optional[Money] = Field(
        description="total_gbp less target_to_date_gbp, negative while under",
        default=None,
    )


class GroupYear(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    group: str = Field(description="The main category, such as Food & Drink")
    months: List[Money] = Field(description="Spent in each month, January first")
    total_gbp: Money
    target_gbp: Money = Field(description="The sum of its categories' monthly targets")


class YearlyStatsResponse(BaseModel):
    """A year's spending month by month, as the sheet's yearly breakdown has it."""

    model_config = ConfigDict(from_attributes=True)

    year: int
    months_elapsed: int = Field(
        description="Months of the year so far, the one in progress included. "
        "12 for a past year, 0 for a future one"
    )
    total_gbp: Money
    transactions: int
    average_per_month_gbp: Money = Field(
        description="total_gbp divided by months_elapsed"
    )
    target_gbp: Money = Field(description="The sum of every category's monthly target")
    target_to_date_gbp: Money = Field(
        description="target_gbp multiplied by months_elapsed"
    )
    uncategorised_gbp: Money
    months: List[MonthTotal] = Field(description="Each month, January first")
    groups: List[GroupYear] = Field(description="Each main category, most spent first")
    categories: List[CategoryYear] = Field(
        description="Every category with a spend or a target that year, most "
        "spent first"
    )


class MerchantStatsRequest(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    after: Optional[datetime.date] = Field(
        description="Only count spends on or after this date", default=None
    )
    before: Optional[datetime.date] = Field(
        description="Only count spends on or before this date", default=None
    )
    category_id: Optional[UUID] = Field(
        description="Only count spends in this category", default=None
    )
    limit: int = Field(
        description="How many merchants to rank", default=20, ge=1, le=100
    )


class MerchantSpend(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    merchant_id: UUID
    name: str
    total_gbp: Money
    transactions: int
    average_gbp: Money = Field(description="total_gbp divided by transactions")
    last_spent_on: datetime.date


class MerchantStatsResponse(BaseModel):
    """Where the money goes, as the sheet's merchant graphs show it."""

    model_config = ConfigDict(from_attributes=True)

    total_gbp: Money = Field(
        description="Everything spent in range, merchant or not, for comparison"
    )
    by_spend: List[MerchantSpend] = Field(description="The most spent with first")
    by_count: List[MerchantSpend] = Field(description="The most spent at first")


class YearOnYearRequest(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    year: int = Field(description="The year to compare with the one before", ge=2001)
    month: int = Field(
        description="The month to compare, and the last of the year to date",
        ge=1,
        le=12,
    )


class CategoryComparison(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    category_id: UUID
    group: str
    name: str
    total_gbp: Money
    previous_total_gbp: Money = Field(description="The same period a year before")
    change_gbp: Money = Field(description="total_gbp less previous_total_gbp")
    change_pct: Optional[float] = Field(
        description="change_gbp as a percentage of previous_total_gbp, null when "
        "nothing was spent a year before",
        default=None,
    )


class PeriodComparison(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    start: datetime.date
    end: datetime.date = Field(
        description="The period's last day, or today while it's in progress"
    )
    previous_start: datetime.date
    previous_end: datetime.date
    total_gbp: Money
    previous_total_gbp: Money
    change_gbp: Money
    change_pct: Optional[float] = None
    categories: List[CategoryComparison] = Field(
        description="Every category spent in either period, the biggest change "
        "first. Older categories are compared as the ones they were mapped to"
    )


class YearOnYearResponse(BaseModel):
    """A month and the year to date against the same days a year before."""

    model_config = ConfigDict(from_attributes=True)

    year: int
    month: int
    month_comparison: PeriodComparison = Field(
        description="The month against the same month a year before. While it's "
        "in progress, both are cut off at today's day of the month"
    )
    year_to_date: PeriodComparison = Field(
        description="January to the end of the month against the same span a "
        "year before"
    )


class UnusualSpendsRequest(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    after: Optional[datetime.date] = Field(
        description="Only look at spends on or after this date", default=None
    )
    before: Optional[datetime.date] = Field(
        description="Only look at spends on or before this date", default=None
    )
    times_typical: float = Field(
        description="How many times its category's typical spend a spend has to "
        "be to count as unusual",
        default=3.0,
        gt=1,
    )
    min_amount_gbp: Money = Field(
        description="Spends below this are never unusual, so a £6 coffee isn't "
        "flagged for being twice the usual £3",
        default=20,
        ge=0,
    )
    limit: int = Field(description="How many to return", default=50, ge=1, le=200)


class UnusualSpend(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    transaction_id: UUID
    spent_on: datetime.date
    amount_gbp: Money
    merchant: Optional[str] = None
    description: Optional[str] = None
    category_id: UUID
    category: str
    typical_gbp: Money = Field(
        description="The median spend in the category, across every year"
    )
    times_typical: float = Field(description="amount_gbp divided by typical_gbp")


class UnusualSpendsResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    spends: List[UnusualSpend] = Field(
        description="The most unusual first, by how many times typical they are"
    )


class BreakdownRequest(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    after: Optional[datetime.date] = Field(
        description="Only count spends on or after this date. Defaults to the "
        "first spend",
        default=None,
    )
    before: Optional[datetime.date] = Field(
        description="Only count spends on or before this date. Defaults to the "
        "last spend",
        default=None,
    )
    exclude_recurring: bool = Field(
        description="Leave out spends marked recurring, so the mortgage going "
        "out on the 1st doesn't make that weekday look expensive",
        default=False,
    )


class PaymentMethodBreakdown(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    payment_method_id: UUID
    name: str
    kind: str
    total_gbp: Money
    transactions: int
    average_gbp: Money = Field(description="total_gbp divided by transactions")
    share_pct: float = Field(description="Share of everything spent in range")


class DayOfWeekBreakdown(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    day: str = Field(description="monday to sunday")
    total_gbp: Money
    transactions: int
    average_per_day_gbp: Money = Field(
        description="total_gbp divided by how many of that day fall in range"
    )


class TimeOfDayBreakdown(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    time_of_day: Optional[str] = Field(
        description="One of the times of day, or null for spends without one, "
        "which is every spend before August 2026"
    )
    total_gbp: Money
    transactions: int
    average_gbp: Money


class BreakdownResponse(BaseModel):
    """Spending split by how, which day and when it was paid."""

    model_config = ConfigDict(from_attributes=True)

    start: Optional[datetime.date] = Field(
        description="The first day counted, null when there are no spends"
    )
    end: Optional[datetime.date] = None
    total_gbp: Money
    transactions: int
    by_payment_method: List[PaymentMethodBreakdown] = Field(
        description="Most spent first"
    )
    by_day_of_week: List[DayOfWeekBreakdown] = Field(description="Monday first")
    by_time_of_day: List[TimeOfDayBreakdown] = Field(
        description="Morning to night, then online, then unrecorded"
    )
