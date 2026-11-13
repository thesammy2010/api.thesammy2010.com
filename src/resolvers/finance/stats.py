import calendar
import datetime
import decimal
import uuid
from collections import defaultdict
from typing import Dict, List, Optional

import pendulum
from sqlalchemy import case, extract, func

from src.db import session
from src.models.finance import Budget as DBBudget
from src.models.finance import Category as DBCategory
from src.models.finance import Merchant as DBMerchant
from src.models.finance import PaymentMethod as DBPaymentMethod
from src.models.finance import Transaction as DBTransaction
from src.resolvers.finance.forecast import (
    RecurringSpend,
    forecast_month,
    months_elapsed,
    pending_recurring,
    previous_month,
)
from src.resolvers.finance.periods import (
    DAYS_OF_WEEK,
    change_pct,
    month_period,
    weekday_counts,
    year_earlier,
    year_to_date_period,
)
from src.schemas.finance.enums import TimeOfDay
from src.schemas.finance.stats import (
    BreakdownRequest,
    BreakdownResponse,
    CategoryComparison,
    CategorySpend,
    CategoryYear,
    DayOfWeekBreakdown,
    GroupYear,
    MerchantSpend,
    MerchantStatsRequest,
    MerchantStatsResponse,
    MonthlyStatsRequest,
    MonthlyStatsResponse,
    MonthTotal,
    PaymentMethodBreakdown,
    PeriodComparison,
    TimeOfDayBreakdown,
    UnusualSpend,
    UnusualSpendsRequest,
    UnusualSpendsResponse,
    YearlyStatsRequest,
    YearlyStatsResponse,
    YearOnYearRequest,
    YearOnYearResponse,
)

ZERO = decimal.Decimal("0")


def _today() -> datetime.date:
    """Today where the spending happens, rather than wherever the server is."""
    return pendulum.today("Europe/London").date()


def _month_range(year: int, month: int):
    first = datetime.date(year, month, 1)
    last = first.replace(day=calendar.monthrange(year, month)[1])
    return [DBTransaction.spent_on >= first, DBTransaction.spent_on <= last]


def _recurring_spends(year: int, month: int) -> List[RecurringSpend]:
    return [
        RecurringSpend(
            merchant_id=row.merchant_id,
            merchant=row.merchant,
            category_id=row.category_id,
            description=row.description,
            amount_gbp=row.amount_gbp,
            spent_on=row.spent_on,
        )
        for row in session.query(
            DBTransaction.merchant_id,
            DBMerchant.name.label("merchant"),
            DBTransaction.category_id,
            DBTransaction.description,
            DBTransaction.amount_gbp,
            DBTransaction.spent_on,
        )
        .outerjoin(DBMerchant, DBMerchant.id == DBTransaction.merchant_id)
        .filter(*_month_range(year, month), DBTransaction.is_recurring.is_(True))
        .all()
    ]


def _sum_where(condition):
    return func.coalesce(
        func.sum(case((condition, DBTransaction.amount_gbp), else_=ZERO)), ZERO
    )


def get_monthly_stats(request: MonthlyStatsRequest) -> MonthlyStatsResponse:
    """A month's spending, in total and by category against its target."""
    in_month = _month_range(request.year, request.month)

    (
        total,
        transactions,
        necessary,
        discretionary,
        recurring,
        with_partner,
        uncategorised,
        not_recurring,
    ) = (
        session.query(
            func.coalesce(func.sum(DBTransaction.amount_gbp), ZERO),
            func.count(DBTransaction.id),
            _sum_where(DBTransaction.is_necessary.is_(True)),
            _sum_where(DBTransaction.is_necessary.is_(False)),
            _sum_where(DBTransaction.is_recurring.is_(True)),
            _sum_where(DBTransaction.with_partner.is_(True)),
            _sum_where(DBTransaction.category_id.is_(None)),
            _sum_where(DBTransaction.is_recurring.is_not(True)),
        )
        .filter(*in_month)
        .one()
    )

    spent = {
        row.category_id: row
        for row in session.query(
            DBTransaction.category_id,
            func.sum(DBTransaction.amount_gbp).label("spent"),
            func.count(DBTransaction.id).label("transactions"),
        )
        .filter(*in_month, DBTransaction.category_id.is_not(None))
        .group_by(DBTransaction.category_id)
        .all()
    }
    targets: Dict = dict(
        session.query(DBBudget.category_id, DBBudget.monthly_target_gbp)
        .filter(DBBudget.year == request.year)
        .all()
    )

    categories = [
        CategorySpend(
            category_id=category.id,
            group=category.group,
            name=category.name,
            spent_gbp=spent[category.id].spent if category.id in spent else ZERO,
            transactions=(
                spent[category.id].transactions if category.id in spent else 0
            ),
            target_gbp=targets.get(category.id),
        )
        for category in session.query(DBCategory)
        .filter(DBCategory.id.in_(set(spent) | set(targets)))
        .all()
    ]
    categories.sort(key=lambda category: (-category.spent_gbp, category.name))

    today = _today()
    forecast = None
    if (today.year, today.month) == (request.year, request.month):
        forecast = forecast_month(
            year=request.year,
            month=request.month,
            today=today,
            spent=total,
            spent_not_recurring=not_recurring,
            pending=pending_recurring(
                last_month=_recurring_spends(
                    *previous_month(request.year, request.month)
                ),
                this_month=_recurring_spends(request.year, request.month),
                year=request.year,
                month=request.month,
            ),
        )

    return MonthlyStatsResponse(
        year=request.year,
        month=request.month,
        total_gbp=total,
        transactions=transactions,
        necessary_gbp=necessary,
        discretionary_gbp=discretionary,
        recurring_gbp=recurring,
        with_partner_gbp=with_partner,
        uncategorised_gbp=uncategorised,
        target_gbp=sum(targets.values(), ZERO),
        categories=categories,
        forecast=forecast,
    )


def get_yearly_stats(request: YearlyStatsRequest) -> YearlyStatsResponse:
    """A year's spending by month and category, against each category's target."""
    in_year = [
        DBTransaction.spent_on >= datetime.date(request.year, 1, 1),
        DBTransaction.spent_on <= datetime.date(request.year, 12, 31),
    ]
    elapsed = months_elapsed(request.year, _today())
    month = extract("month", DBTransaction.spent_on)

    by_category: Dict = defaultdict(lambda: [ZERO] * 12)
    by_month = [ZERO] * 12
    uncategorised = ZERO
    transactions = 0
    for row in (
        session.query(
            DBTransaction.category_id,
            month.label("month"),
            func.sum(DBTransaction.amount_gbp).label("spent"),
            func.count(DBTransaction.id).label("transactions"),
        )
        .filter(*in_year)
        .group_by(DBTransaction.category_id, month)
        .all()
    ):
        index = int(row.month) - 1
        by_month[index] += row.spent
        transactions += row.transactions
        if row.category_id is None:
            uncategorised += row.spent
        else:
            by_category[row.category_id][index] += row.spent

    targets: Dict = dict(
        session.query(DBBudget.category_id, DBBudget.monthly_target_gbp)
        .filter(DBBudget.year == request.year)
        .all()
    )

    def per_month(amount: decimal.Decimal) -> decimal.Decimal:
        return round(amount / elapsed, 2) if elapsed else ZERO

    categories: List[CategoryYear] = []
    groups: Dict[str, GroupYear] = {}
    for category in (
        session.query(DBCategory)
        .filter(DBCategory.id.in_(set(by_category) | set(targets)))
        .all()
    ):
        months = by_category.get(category.id, [ZERO] * 12)
        total = sum(months, ZERO)
        target = targets.get(category.id)
        target_to_date = None if target is None else target * elapsed
        categories.append(
            CategoryYear(
                category_id=category.id,
                group=category.group,
                name=category.name,
                months=months,
                total_gbp=total,
                average_gbp=per_month(total),
                target_gbp=target,
                target_to_date_gbp=target_to_date,
                over_target_gbp=(
                    None if target_to_date is None else total - target_to_date
                ),
            )
        )

        group = groups.setdefault(
            category.group,
            GroupYear(
                group=category.group,
                months=[ZERO] * 12,
                total_gbp=ZERO,
                target_gbp=ZERO,
            ),
        )
        group.months = [a + b for a, b in zip(group.months, months)]
        group.total_gbp += total
        group.target_gbp += target or ZERO

    total = sum(by_month, ZERO)
    target = sum(targets.values(), ZERO)
    running = ZERO
    month_totals: List[MonthTotal] = []
    for index, spent in enumerate(by_month):
        running += spent
        month_totals.append(
            MonthTotal(month=index + 1, total_gbp=spent, running_total_gbp=running)
        )

    return YearlyStatsResponse(
        year=request.year,
        months_elapsed=elapsed,
        total_gbp=total,
        transactions=transactions,
        average_per_month_gbp=per_month(total),
        target_gbp=target,
        target_to_date_gbp=target * elapsed,
        uncategorised_gbp=uncategorised,
        months=month_totals,
        groups=sorted(groups.values(), key=lambda group: -group.total_gbp),
        categories=sorted(
            categories, key=lambda category: (-category.total_gbp, category.name)
        ),
    )


def get_merchant_stats(request: MerchantStatsRequest) -> MerchantStatsResponse:
    """The merchants most spent with, and most spent at, over a range of dates."""
    conditions = []
    if request.after:
        conditions.append(DBTransaction.spent_on >= request.after)
    if request.before:
        conditions.append(DBTransaction.spent_on <= request.before)
    if request.category_id:
        conditions.append(DBTransaction.category_id == request.category_id)

    total = (
        session.query(func.coalesce(func.sum(DBTransaction.amount_gbp), ZERO))
        .filter(*conditions)
        .scalar()
    )

    spent = func.sum(DBTransaction.amount_gbp)
    count = func.count(DBTransaction.id)
    query = (
        session.query(
            DBMerchant.id,
            DBMerchant.name,
            spent.label("spent"),
            count.label("transactions"),
            func.max(DBTransaction.spent_on).label("last_spent_on"),
        )
        .join(DBMerchant, DBMerchant.id == DBTransaction.merchant_id)
        .filter(*conditions)
        .group_by(DBMerchant.id, DBMerchant.name)
    )

    def ranked(*order_by) -> List[MerchantSpend]:
        return [
            MerchantSpend(
                merchant_id=row.id,
                name=row.name,
                total_gbp=row.spent,
                transactions=row.transactions,
                average_gbp=round(row.spent / row.transactions, 2),
                last_spent_on=row.last_spent_on,
            )
            for row in query.order_by(*order_by).limit(request.limit).all()
        ]

    return MerchantStatsResponse(
        total_gbp=total,
        by_spend=ranked(spent.desc(), DBMerchant.name),
        by_count=ranked(count.desc(), spent.desc(), DBMerchant.name),
    )


def _category_totals(
    start: datetime.date, end: datetime.date
) -> Dict[Optional[uuid.UUID], decimal.Decimal]:
    return dict(
        session.query(DBTransaction.category_id, func.sum(DBTransaction.amount_gbp))
        .filter(DBTransaction.spent_on >= start, DBTransaction.spent_on <= end)
        .group_by(DBTransaction.category_id)
        .all()
    )


def _compare(
    start: datetime.date,
    end: datetime.date,
    previous_start: datetime.date,
    previous_end: datetime.date,
) -> PeriodComparison:
    current = _category_totals(start, end)
    previous = _category_totals(previous_start, previous_end)
    total = sum(current.values(), ZERO)
    previous_total = sum(previous.values(), ZERO)

    ids = (set(current) | set(previous)) - {None}
    categories = [
        CategoryComparison(
            category_id=category.id,
            group=category.group,
            name=category.name,
            total_gbp=current.get(category.id, ZERO),
            previous_total_gbp=previous.get(category.id, ZERO),
            change_gbp=current.get(category.id, ZERO) - previous.get(category.id, ZERO),
            change_pct=change_pct(
                current.get(category.id, ZERO), previous.get(category.id, ZERO)
            ),
        )
        for category in session.query(DBCategory).filter(DBCategory.id.in_(ids)).all()
    ]
    categories.sort(key=lambda category: (-abs(category.change_gbp), category.name))

    return PeriodComparison(
        start=start,
        end=end,
        previous_start=previous_start,
        previous_end=previous_end,
        total_gbp=total,
        previous_total_gbp=previous_total,
        change_gbp=total - previous_total,
        change_pct=change_pct(total, previous_total),
        categories=categories,
    )


def get_year_on_year(request: YearOnYearRequest) -> YearOnYearResponse:
    """A month, and the year up to it, against the same days a year before."""
    today = _today()
    # A year before today, so a month in progress is matched with the same
    # days of that month last year rather than all of it
    then = year_earlier(today)

    return YearOnYearResponse(
        year=request.year,
        month=request.month,
        month_comparison=_compare(
            *month_period(request.year, request.month, today),
            *month_period(request.year - 1, request.month, then),
        ),
        year_to_date=_compare(
            *year_to_date_period(request.year, request.month, today),
            *year_to_date_period(request.year - 1, request.month, then),
        ),
    )


def get_unusual_spends(request: UnusualSpendsRequest) -> UnusualSpendsResponse:
    """Spends far above what's typical for their category.

    Typical is the median rather than the mean, so the outliers being looked
    for don't drag up the bar they're measured against.
    """
    typical = (
        session.query(
            DBTransaction.category_id.label("category_id"),
            func.percentile_cont(0.5)
            .within_group(DBTransaction.amount_gbp)
            .label("typical"),
        )
        .filter(DBTransaction.category_id.is_not(None), DBTransaction.amount_gbp > 0)
        .group_by(DBTransaction.category_id)
        .subquery()
    )
    ratio = DBTransaction.amount_gbp / typical.c.typical

    conditions = [
        typical.c.typical > 0,
        DBTransaction.amount_gbp >= request.min_amount_gbp,
        ratio >= request.times_typical,
    ]
    if request.after:
        conditions.append(DBTransaction.spent_on >= request.after)
    if request.before:
        conditions.append(DBTransaction.spent_on <= request.before)

    rows = (
        session.query(
            DBTransaction,
            DBCategory.name.label("category"),
            DBMerchant.name.label("merchant"),
            typical.c.typical,
            ratio.label("ratio"),
        )
        .join(typical, typical.c.category_id == DBTransaction.category_id)
        .join(DBCategory, DBCategory.id == DBTransaction.category_id)
        .outerjoin(DBMerchant, DBMerchant.id == DBTransaction.merchant_id)
        .filter(*conditions)
        .order_by(ratio.desc(), DBTransaction.spent_on.desc())
        .limit(request.limit)
        .all()
    )

    return UnusualSpendsResponse(
        spends=[
            UnusualSpend(
                transaction_id=row.Transaction.id,
                spent_on=row.Transaction.spent_on,
                amount_gbp=row.Transaction.amount_gbp,
                merchant=row.merchant,
                description=row.Transaction.description,
                category_id=row.Transaction.category_id,
                category=row.category,
                typical_gbp=round(decimal.Decimal(str(row.typical)), 2),
                times_typical=round(float(row.ratio), 1),
            )
            for row in rows
        ]
    )


# Morning to night, then online, then spends with no time recorded
TIME_OF_DAY_ORDER = [time.value for time in TimeOfDay] + [None]


def get_breakdown(request: BreakdownRequest) -> BreakdownResponse:
    """Spending by payment method, day of the week and time of day."""
    conditions = []
    if request.after:
        conditions.append(DBTransaction.spent_on >= request.after)
    if request.before:
        conditions.append(DBTransaction.spent_on <= request.before)
    if request.exclude_recurring:
        conditions.append(DBTransaction.is_recurring.is_not(True))

    total, transactions, first, last = (
        session.query(
            func.coalesce(func.sum(DBTransaction.amount_gbp), ZERO),
            func.count(DBTransaction.id),
            func.min(DBTransaction.spent_on),
            func.max(DBTransaction.spent_on),
        )
        .filter(*conditions)
        .one()
    )
    start = request.after or first
    end = request.before or last

    spent = func.sum(DBTransaction.amount_gbp)
    count = func.count(DBTransaction.id)

    by_payment_method = [
        PaymentMethodBreakdown(
            payment_method_id=row.id,
            name=row.name,
            kind=row.kind,
            total_gbp=row.spent,
            transactions=row.transactions,
            average_gbp=round(row.spent / row.transactions, 2),
            share_pct=round(float(row.spent / total * 100), 1) if total else 0.0,
        )
        for row in session.query(
            DBPaymentMethod.id,
            DBPaymentMethod.name,
            DBPaymentMethod.kind,
            spent.label("spent"),
            count.label("transactions"),
        )
        .join(DBPaymentMethod, DBPaymentMethod.id == DBTransaction.payment_method_id)
        .filter(*conditions)
        .group_by(DBPaymentMethod.id, DBPaymentMethod.name, DBPaymentMethod.kind)
        .order_by(spent.desc())
        .all()
    ]

    # ISO day of the week, Monday being 1
    weekday = extract("isodow", DBTransaction.spent_on)
    by_weekday = {
        int(row.weekday): row
        for row in session.query(
            weekday.label("weekday"), spent.label("spent"), count.label("transactions")
        )
        .filter(*conditions)
        .group_by(weekday)
        .all()
    }
    days = weekday_counts(start, end) if start and end else {}
    by_day_of_week = []
    for index, day in enumerate(DAYS_OF_WEEK, start=1):
        row = by_weekday.get(index)
        day_total = row.spent if row else ZERO
        by_day_of_week.append(
            DayOfWeekBreakdown(
                day=day,
                total_gbp=day_total,
                transactions=row.transactions if row else 0,
                average_per_day_gbp=(
                    round(day_total / days[day], 2) if days.get(day) else ZERO
                ),
            )
        )

    by_time = {
        row.time_of_day: row
        for row in session.query(
            DBTransaction.time_of_day,
            spent.label("spent"),
            count.label("transactions"),
        )
        .filter(*conditions)
        .group_by(DBTransaction.time_of_day)
        .all()
    }
    by_time_of_day = [
        TimeOfDayBreakdown(
            time_of_day=time,
            total_gbp=by_time[time].spent,
            transactions=by_time[time].transactions,
            average_gbp=round(by_time[time].spent / by_time[time].transactions, 2),
        )
        for time in TIME_OF_DAY_ORDER
        if time in by_time
    ]

    return BreakdownResponse(
        start=start,
        end=end,
        total_gbp=total,
        transactions=transactions,
        by_payment_method=by_payment_method,
        by_day_of_week=by_day_of_week,
        by_time_of_day=by_time_of_day,
    )
