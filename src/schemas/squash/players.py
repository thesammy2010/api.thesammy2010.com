"""Schemas for the people in the squash group."""

import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class PlayerRequest(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str = Field(description="What they're called", min_length=1, max_length=255)
    user_id: Optional[UUID] = Field(
        description="The user who signs in as them. Without one they can be "
        "put in matches but can't use the API",
        default=None,
    )
    email: Optional[str] = Field(
        description="Their Google account's email. A player with one but no "
        "user_id is linked to the user signed in with it, when they're added "
        "if that user already exists or else the first time they use /squash",
        max_length=255,
        pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$",
        default=None,
    )
    is_active: bool = Field(
        description="Whether they're still in the group. One who isn't keeps "
        "their matches but can no longer use the API",
        default=True,
    )

    @field_validator("email", mode="before")
    @classmethod
    def normalise_email(cls, value: Optional[str]) -> Optional[str]:
        """Google emails aren't case-sensitive, so they're matched lowercased."""
        if value is None or not str(value).strip():
            return None
        return str(value).strip().lower()


class PlayerResponse(PlayerRequest):
    id: UUID
    created_at: datetime.datetime
    updated_at: Optional[datetime.datetime] = None


class PlayerStatsResponse(BaseModel):
    """A player's record across completed matches."""

    player_id: UUID
    matches_played: int
    matches_won: int
    matches_lost: int
    matches_drawn: int = Field(
        description="Matches that ended level, which only those without best_of can"
    )
    games_won: int
    games_lost: int
    points_won: int
    points_lost: int
    win_rate: Optional[float] = Field(
        description="The share of matches won out of those won or lost, from 0 "
        "to 1, so draws don't count either way. Null before any are"
    )


class HeadToHeadResponse(BaseModel):
    """Two players' completed matches against each other."""

    player_id: UUID
    opponent_id: UUID
    matches_played: int
    matches_won: int
    matches_lost: int
    matches_drawn: int
    games_won: int
    games_lost: int
