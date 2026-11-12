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
