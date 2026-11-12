import calendar
import datetime
import decimal
from typing import Dict

from sqlalchemy import case, func

from src.db import session
from src.models.finance import Budget as DBBudget
from src.models.finance import Category as DBCategory
from src.models.finance import Transaction as DBTransaction
from src.schemas.finance.stats import (
    CategorySpend,
    MonthlyStatsRequest,
    MonthlyStatsResponse,
)

ZERO = decimal.Decimal("0")


def _sum_where(condition):
    return func.coalesce(
        func.sum(case((condition, DBTransaction.amount_gbp), else_=ZERO)), ZERO
    )


def get_monthly_stats(request: MonthlyStatsRequest) -> MonthlyStatsResponse:
    """A month's spending, in total and by category against its target."""
    first = datetime.date(request.year, request.month, 1)
    last = first.replace(day=calendar.monthrange(request.year, request.month)[1])
    in_month = [DBTransaction.spent_on >= first, DBTransaction.spent_on <= last]

    (
        total,
        transactions,
        necessary,
        discretionary,
        recurring,
        with_partner,
        uncategorised,
    ) = (
        session.query(
            func.coalesce(func.sum(DBTransaction.amount_gbp), ZERO),
            func.count(DBTransaction.id),
            _sum_where(DBTransaction.is_necessary.is_(True)),
            _sum_where(DBTransaction.is_necessary.is_(False)),
            _sum_where(DBTransaction.is_recurring.is_(True)),
            _sum_where(DBTransaction.with_partner.is_(True)),
            _sum_where(DBTransaction.category_id.is_(None)),
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
    )
