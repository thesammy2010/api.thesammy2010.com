import enum
from typing import List, Optional

from pydantic import (
    AwareDatetime,
    BaseModel,
    ConfigDict,
    Field,
    model_validator,
)


class MigrationTable(str, enum.Enum):
    LOCATIONS = "locations"
    EXERCISES = "exercises"
    SESSIONS = "sessions"
    WORKOUTS = "workouts"


class RunMigrationRequest(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    tables: List[MigrationTable] = Field(
        description="The tables to load from the Google Sheet. Tables are always "
        "migrated in dependency order (locations, exercises, then workouts), "
        "regardless of the order given here",
        default_factory=lambda: list(MigrationTable),
        min_length=1,
    )
    dry_run: bool = Field(
        description="Read and parse the sheet but do not write anything to the database",
        default=False,
    )
    workouts_after: Optional[AwareDatetime] = Field(
        description="Only migrate workouts performed at or after this datetime",
        default=None,
    )
    workouts_before: Optional[AwareDatetime] = Field(
        description="Only migrate workouts performed at or before this datetime",
        default=None,
    )
    workouts_row_start: Optional[int] = Field(
        description="Index of the first workouts sheet row to migrate, excluding the header",
        default=None,
        ge=0,
    )
    workouts_row_end: Optional[int] = Field(
        description="Index of the last workouts sheet row to migrate, including the header. "
        "Defaults to the end of the sheet",
        default=None,
        ge=1,
    )

    @model_validator(mode="after")
    def validate_workout_ranges(self) -> "RunMigrationRequest":
        if (
            self.workouts_after
            and self.workouts_before
            and self.workouts_after > self.workouts_before
        ):
            raise ValueError("workouts_after must not be later than workouts_before")
        if (
            self.workouts_row_start is not None
            and self.workouts_row_end is not None
            and self.workouts_row_start >= self.workouts_row_end
        ):
            raise ValueError("workouts_row_start must be less than workouts_row_end")
        return self


class TableMigrationResult(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    table: MigrationTable = Field(description="The table that was migrated")
    rows: int = Field(
        description="Number of rows read from the sheet that matched the request"
    )
    written: int = Field(
        description="Number of rows written to the database. Always 0 for a dry run"
    )


class RunMigrationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    dry_run: bool = Field(description="Whether the migration ran without writing")
    results: List[TableMigrationResult] = Field(
        description="Per table outcome, in the order the tables were migrated"
    )
