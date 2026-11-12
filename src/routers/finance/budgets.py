import uuid
from typing import Annotated, List

from fastapi import APIRouter, Depends, HTTPException, Path, Query

from src.models.finance import Budget as DBBudget
from src.resolvers.finance import budgets, stats
from src.resolvers.finance.references import ReferenceNotFound
from src.resolvers.users import require_admin
from src.routers.finance import parse_uuid
from src.schemas.finance.budgets import (
    BudgetResponse,
    ListBudgetsRequest,
    PutBudgetRequest,
)
from src.schemas.finance.stats import MonthlyStatsRequest, MonthlyStatsResponse

router = APIRouter(
    prefix="/finance",
    tags=["budgets"],
    dependencies=[Depends(require_admin)],
)


@router.get("/budgets", response_model=List[BudgetResponse])
def get_budgets(request: Annotated[ListBudgetsRequest, Query()]) -> List[DBBudget]:
    """Every category's monthly target, most recent year first."""
    return budgets.get_budgets(request=request)


@router.put("/budgets/{year}/{category_id}", response_model=BudgetResponse)
def put_budget(
    year: Annotated[int, Path(ge=2000)],
    category_id: Annotated[str, uuid.UUID],
    budget: PutBudgetRequest,
) -> DBBudget:
    """Sets a category's monthly target for a year, creating it if needed.
    404 if the category doesn't exist."""
    try:
        return budgets.put_budget(
            year=year, category_id=parse_uuid(category_id, "category"), budget=budget
        )
    except ReferenceNotFound as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/stats/monthly", response_model=MonthlyStatsResponse)
def get_monthly_stats(
    request: Annotated[MonthlyStatsRequest, Query()],
) -> MonthlyStatsResponse:
    """A month's spending, in total and by category against that year's
    targets. Spends with no answer for necessary are in neither
    necessary_gbp nor discretionary_gbp."""
    return stats.get_monthly_stats(request=request)
