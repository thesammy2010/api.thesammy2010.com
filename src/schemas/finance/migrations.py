import datetime
import enum
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator


class FinanceTable(str, enum.Enum):
    CATEGORIES = "categories"
    PAYMENT_METHODS = "payment_methods"
    MERCHANTS = "merchants"
    TRANSACTIONS = "transactions"
    BUDGETS = "budgets"


class RunFinanceMigrationRequest(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    dry_run: bool = Field(
        description="Read and parse the sheet but write nothing, neither to "
        "the database nor ids back to the sheet",
        default=False,
    )
    after: Optional[datetime.date] = Field(
        description="Only import spends on or after this date", default=None
    )
    before: Optional[datetime.date] = Field(
        description="Only import spends on or before this date. Spends dated "
        "after today, the sheet's estimates of what's still to come, are never "
        "imported",
        default=None,
    )

    @model_validator(mode="after")
    def validate_range(self) -> "RunFinanceMigrationRequest":
        if self.after and self.before and self.after > self.before:
            raise ValueError("after must not be later than before")
        return self


class FinanceTableResult(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    table: FinanceTable = Field(description="The table that was migrated")
    rows: int = Field(description="Number of rows read that matched the request")
    written: int = Field(
        description="Number of rows written to the database. Always 0 for a dry run"
    )


class RunFinanceMigrationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    dry_run: bool = Field(description="Whether the migration ran without writing")
    ids_assigned: int = Field(
        description="Number of spends that had no id in the sheet. Unless this "
        "was a dry run, each now has one written into its row"
    )
    uncategorised: int = Field(
        description="Number of imported spends left without a category, either "
        "because the sheet has none or because it couldn't be mapped"
    )
    results: List[FinanceTableResult] = Field(
        description="Per table outcome, in the order the tables were migrated"
    )
