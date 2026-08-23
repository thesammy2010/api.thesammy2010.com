"""Schemas for the aggregated view across sessions."""

import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import (
    AwareDatetime,
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
)


class SessionStatsRequest(BaseModel):
    """Query parameters for narrowing the session stats."""

    model_config = ConfigDict(from_attributes=True)

    location_id: Optional[UUID] = Field(
        description="Only count sessions at this location",
        default=None,
    )
    exercise_id: Optional[UUID] = Field(
        description="Only count sessions that included this exercise. The totals "
        "still cover every set in them, not just that exercise",
        default=None,
    )
    after: Optional[AwareDatetime] = Field(
        description="Only count sessions at or after this datetime",
        default=None,
    )
    before: Optional[AwareDatetime] = Field(
        description="Only count sessions at or before this datetime",
        default=None,
    )


class SessionHighlight(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID = Field(description="Unique identifier for the session")
    workout_time: AwareDatetime = Field(description="When the session took place")
    location: str = Field(description="Name of the location")
    sets: int = Field(description="Number of sets logged in the session")
    volume_kg: float = Field(
        description="Total weight moved, the sum of weight_kg multiplied by repetitions"
    )

    @field_validator("workout_time", mode="before")
    @classmethod
    def ensure_timezone_aware(cls, value):
        """Convert naive datetimes to timezone-aware datetimes (UTC)"""
        if isinstance(value, datetime.datetime) and value.tzinfo is None:
            return value.replace(tzinfo=datetime.timezone.utc)
        return value


class WeekdayStats(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    weekday: str = Field(description="Day of the week, in UK local time")
    sessions: int = Field(description="Number of sessions on this day")
    sets: int = Field(description="Number of sets logged on this day")
    volume_kg: float = Field(
        description="Total weight moved, the sum of weight_kg multiplied by repetitions"
    )


class SessionStatsResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    sessions: int = Field(description="Number of sessions counted")
    first_session: Optional[AwareDatetime] = Field(
        description="When the earliest session took place", default=None
    )
    last_session: Optional[AwareDatetime] = Field(
        description="When the most recent session took place", default=None
    )
    average_sets_per_session: float = Field(
        description="Mean number of sets in a session, 0 when there are none"
    )
    average_exercises_per_session: float = Field(
        description="Mean number of different exercises in a session"
    )
    average_repetitions_per_session: float = Field(
        description="Mean number of repetitions in a session"
    )
    average_volume_kg_per_session: float = Field(
        description="Mean weight moved in a session"
    )
    average_days_between_sessions: Optional[float] = Field(
        description="Mean gap between consecutive sessions, null with fewer than two",
        default=None,
    )
    longest_gap_days: Optional[float] = Field(
        description="Longest gap between consecutive sessions, null with fewer than two",
        default=None,
    )
    busiest_session: Optional[SessionHighlight] = Field(
        description="The session with the most sets", default=None
    )
    heaviest_session: Optional[SessionHighlight] = Field(
        description="The session that moved the most weight", default=None
    )
    by_weekday: List[WeekdayStats] = Field(
        description="Breakdown by day of the week, Monday first, omitting days "
        "with no sessions",
        default_factory=list,
    )

    @field_validator("first_session", "last_session", mode="before")
    @classmethod
    def ensure_timezone_aware(cls, value):
        """Convert naive datetimes to timezone-aware datetimes (UTC)"""
        if value is None:
            return None
        if isinstance(value, datetime.datetime) and value.tzinfo is None:
            return value.replace(tzinfo=datetime.timezone.utc)
        return value
