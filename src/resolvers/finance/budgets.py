import datetime
import uuid
from typing import List

from src.db import session
from src.migration_utils.finance_rows import budget_id_for
from src.models.finance import Budget as DBBudget
from src.models.finance import Category as DBCategory
from src.resolvers.finance.references import ReferenceNotFound
from src.schemas.finance.budgets import ListBudgetsRequest, PutBudgetRequest


def get_budgets(request: ListBudgetsRequest) -> List[DBBudget]:
    query = session.query(DBBudget)
    if request.year is not None:
        query = query.filter(DBBudget.year == request.year)
    return query.order_by(DBBudget.year.desc(), DBBudget.category_id).all()


def put_budget(year: int, category_id: uuid.UUID, budget: PutBudgetRequest) -> DBBudget:
    """Sets a category's target for a year, creating it if it has none yet."""
    category = session.get(DBCategory, category_id)
    if category is None:
        raise ReferenceNotFound(f"Category {category_id} not found")

    now = datetime.datetime.now(tz=datetime.timezone.utc)
    db_budget = (
        session.query(DBBudget)
        .filter(DBBudget.category_id == category_id, DBBudget.year == year)
        .first()
    )
    if db_budget is None:
        db_budget = DBBudget(
            id=budget_id_for(category.name, year),
            category_id=category_id,
            year=year,
            created_at=now,
        )
        session.add(db_budget)

    db_budget.monthly_target_gbp = budget.monthly_target_gbp
    db_budget.rationale = budget.rationale
    db_budget.updated_at = now

    session.commit()
    return db_budget
