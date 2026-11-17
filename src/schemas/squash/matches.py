"""Schemas for matches and the games in them."""

import datetime
from collections import Counter
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from src.schemas.squash.enums import (
    PLAYERS_PER_SIDE,
    MatchFormat,
    MatchStatus,
    RallyDecision,
)
from src.schemas.utils import PaginationParams


class ListMatchesRequest(PaginationParams):
    """Query parameters for listing matches, most recent first."""

    model_config = ConfigDict(from_attributes=True)

    player_id: Optional[UUID] = Field(
        description="Only list matches this player played in", default=None
    )
    status: Optional[MatchStatus] = Field(
        description="Only list matches in this state", default=None
    )
    format: Optional[MatchFormat] = Field(
        description="Only list singles or only doubles", default=None
    )
    venue_id: Optional[UUID] = Field(
        description="Only list matches played at this venue", default=None
    )
    after: Optional[datetime.datetime] = Field(
        description="Only list matches played at or after this", default=None
    )
    before: Optional[datetime.datetime] = Field(
        description="Only list matches played at or before this", default=None
    )

    @model_validator(mode="after")
    def validate_range(self) -> "ListMatchesRequest":
        if self.after and self.before and self.after > self.before:
            raise ValueError("after must not be later than before")
        return self


class MatchPlayerRequest(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    player_id: UUID
    side: int = Field(description="Which side they played on, 1 or 2", ge=1, le=2)


class MatchRequest(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    format: MatchFormat
    status: MatchStatus = Field(
        description="Where the match is up to. It can only be completed once "
        "its games decide it",
        default=MatchStatus.SCHEDULED,
    )
    played_at: Optional[datetime.datetime] = Field(
        description="When it's arranged for, or was played", default=None
    )
    venue_id: Optional[UUID] = Field(
        description="Where it's played, one of /squash/venues", default=None
    )
    points_to: int = Field(
        description="What a game is played to. It goes on past this from one "
        "point short all until a side is two clear",
        ge=1,
        le=50,
        default=11,
    )
    best_of: Optional[int] = Field(
        description="How many games the match is the best of, such as 3 or 5. "
        "Null when games are just played until people stop, the side that "
        "won more of them winning, or a draw on level games",
        ge=1,
        le=9,
        default=None,
    )
    notes: Optional[str] = Field(max_length=512, default=None)
    players: List[MatchPlayerRequest] = Field(
        description="One player a side for singles, two for doubles"
    )

    @model_validator(mode="after")
    def validate_best_of(self) -> "MatchRequest":
        if self.best_of is not None and self.best_of % 2 == 0:
            raise ValueError("best_of must be odd, so that a side can win it")
        return self

    @model_validator(mode="after")
    def validate_players(self) -> "MatchRequest":
        player_ids = [player.player_id for player in self.players]
        if len(set(player_ids)) != len(player_ids):
            raise ValueError("A player can only be in a match once")
        per_side = Counter(player.side for player in self.players)
        expected = PLAYERS_PER_SIDE[self.format]
        if per_side[1] != expected or per_side[2] != expected:
            raise ValueError(
                f"{self.format.value.capitalize()} needs {expected} player(s) "
                "on each side"
            )
        return self


class GameRequest(BaseModel):
    """A game's score so far, or its final score."""

    side1_points: int = Field(ge=0, le=99)
    side2_points: int = Field(ge=0, le=99)


class GameResponse(GameRequest):
    model_config = ConfigDict(from_attributes=True)

    number: int = Field(description="1 for the first game of the match")
    winning_side: Optional[int] = Field(
        description="The side that won it, or null while it's still being played"
    )
    rallies: int = Field(
        description="How many rallies were recorded for it, lets included. 0 "
        "for a game whose score was set directly"
    )


class MergeMatchesRequest(BaseModel):
    """Another match between the same players, to fold into one."""

    match_id: UUID = Field(description="The match to merge with this one")


class RallyRequest(BaseModel):
    won_by_side: Optional[int] = Field(
        description="The side that won the point. Null for a let, which no one wins",
        ge=1,
        le=2,
        default=None,
    )
    decision: Optional[RallyDecision] = Field(
        description="The referee's call, when a player appealed. A let is "
        "replayed, with no point and the same server. A stroke is the point "
        "to the player who appealed, so `won_by_side` is their side, and a "
        "no let the point to their opponent. Null for a rally played out",
        default=None,
    )
    appealed_by_side: Optional[int] = Field(
        description="The side that appealed for a let. Worked out from "
        "`won_by_side` for a stroke or no let",
        ge=1,
        le=2,
        default=None,
    )
    version: int = Field(
        description="The match's version the point was scored against, from the "
        "last response or poll. 409 if it's since changed"
    )
    server_id: Optional[UUID] = Field(
        description="The player who served it. They must be on the side "
        "whose serve it was, when that's known",
        default=None,
    )

    @model_validator(mode="after")
    def validate_decision(self) -> "RallyRequest":
        if self.decision == RallyDecision.LET:
            if self.won_by_side is not None:
                raise ValueError("A let is replayed, so no side wins it")
            return self
        if self.won_by_side is None:
            raise ValueError("won_by_side is needed for anything but a let")
        if self.appealed_by_side is not None and self.decision is None:
            raise ValueError("appealed_by_side needs a decision")
        if self.appealed_by_side is not None and (
            self.appealed_by_side != self.appealing_side
        ):
            raise ValueError(
                f"A {self.decision.value.replace('_', ' ')} for side "
                f"{self.won_by_side} means side {self.appealing_side} appealed"
            )
        return self

    @property
    def appealing_side(self) -> Optional[int]:
        if self.decision == RallyDecision.STROKE:
            return self.won_by_side
        if self.decision == RallyDecision.NO_LET:
            return 3 - self.won_by_side
        return self.appealed_by_side


class RallyResponse(BaseModel):
    game: int = Field(description="The game it was in")
    number: int = Field(description="1 for the first rally of the game")
    won_by_side: Optional[int] = Field(description="Null for a let")
    decision: Optional[RallyDecision]
    appealed_by_side: Optional[int]
    server_id: Optional[UUID]
    side1_points: int = Field(description="Side 1's score after it")
    side2_points: int = Field(description="Side 2's score after it")
    created_at: datetime.datetime


class MatchResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    format: MatchFormat
    status: MatchStatus
    played_at: Optional[datetime.datetime]
    venue_id: Optional[UUID]
    venue: Optional[str] = Field(description="The venue's name, for showing")
    points_to: int
    best_of: Optional[int]
    notes: Optional[str]
    players: List[MatchPlayerRequest]
    games: List[GameResponse]
    side1_games: int = Field(description="Games won by side 1")
    side2_games: int = Field(description="Games won by side 2")
    winning_side: Optional[int] = Field(
        description="The side that won, once the match is completed. Null "
        "for a draw, which only a match without best_of can end in"
    )
    serving_side: Optional[int] = Field(
        description="The side to serve next: whoever won the last rally, or "
        "the last game. Null when that isn't known"
    )
    version: int = Field(
        description="Goes up by one on every change. Send it back when scoring "
        "or undoing a rally, and poll with since_version"
    )
    created_by_id: UUID
    created_at: datetime.datetime
    updated_at: Optional[datetime.datetime] = None
