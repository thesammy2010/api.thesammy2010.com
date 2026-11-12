import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from src.schemas.finance.money import Money


class ListBudgetsRequest(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    year: Optional[int] = Field(
        description="Only list the budgets for this year", default=None, ge=2000
    )


class PutBudgetRequest(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    monthly_target_gbp: Money = Field(
        description="How much the category is meant to cost each month",
        ge=0,
        max_digits=12,
        decimal_places=2,
    )
    rationale: Optional[str] = Field(
        description="How the target was arrived at, such as 5x/month @ £30",
        max_length=255,
        default=None,
    )


class BudgetResponse(PutBudgetRequest):
    id: UUID
    category_id: UUID
    year: int
    created_at: datetime.datetime
    updated_at: datetime.datetime
