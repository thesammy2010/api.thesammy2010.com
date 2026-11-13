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
from src.schemas.finance.stats import (
    BreakdownRequest,
    BreakdownResponse,
    MerchantStatsRequest,
    MerchantStatsResponse,
    MonthlyStatsRequest,
    MonthlyStatsResponse,
    UnusualSpendsRequest,
    UnusualSpendsResponse,
    YearlyStatsRequest,
    YearlyStatsResponse,
    YearOnYearRequest,
    YearOnYearResponse,
)

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
    necessary_gbp nor discretionary_gbp.

    For the month in progress, `forecast` projects the month's total: what's
    been spent, plus last month's recurring spends not yet seen this month,
    plus the daily rate of everything else for the days left."""
    return stats.get_monthly_stats(request=request)


@router.get("/stats/yearly", response_model=YearlyStatsResponse)
def get_yearly_stats(
    request: Annotated[YearlyStatsRequest, Query()],
) -> YearlyStatsResponse:
    """A year's spending month by month, for each category and main category,
    with averages and how far over or under target each is so far. Averages
    and targets to date count the month in progress as elapsed."""
    return stats.get_yearly_stats(request=request)


@router.get("/stats/merchants", response_model=MerchantStatsResponse)
def get_merchant_stats(
    request: Annotated[MerchantStatsRequest, Query()],
) -> MerchantStatsResponse:
    """The merchants most spent with and most often spent at, over a range of
    dates and optionally within one category. Spends with no merchant count
    towards total_gbp only."""
    return stats.get_merchant_stats(request=request)


@router.get("/stats/year-on-year", response_model=YearOnYearResponse)
def get_year_on_year(
    request: Annotated[YearOnYearRequest, Query()],
) -> YearOnYearResponse:
    """A month, and January up to it, against the same days a year before,
    in total and by category. While the month is in progress both years are
    cut off at today's date, so they compare like for like."""
    return stats.get_year_on_year(request=request)


@router.get("/stats/unusual", response_model=UnusualSpendsResponse)
def get_unusual_spends(
    request: Annotated[UnusualSpendsRequest, Query()],
) -> UnusualSpendsResponse:
    """Spends at least `times_typical` times their category's median spend,
    and at least `min_amount_gbp`, most unusual first. Good for spotting big
    one-offs and typos in the sheet."""
    return stats.get_unusual_spends(request=request)


@router.get("/stats/breakdown", response_model=BreakdownResponse)
def get_breakdown(
    request: Annotated[BreakdownRequest, Query()],
) -> BreakdownResponse:
    """Spending by payment method, day of the week and time of day. A day of
    the week's average is per occurrence of that day in range, whether
    anything was spent on it or not."""
    return stats.get_breakdown(request=request)
