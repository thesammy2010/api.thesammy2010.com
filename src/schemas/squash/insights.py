"""Schemas for Elo ratings and what live-scored rallies show."""

import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field

from src.schemas.squash.enums import MatchFormat


def rate(won: int, played: int) -> Optional[float]:
    return round(won / played, 3) if played else None


class RatingsRequest(BaseModel):
    format: Optional[MatchFormat] = Field(
        description="Rate only singles or only doubles, each its own ladder. "
        "Without it, every match counts towards one rating",
        default=None,
    )
    include_inactive: bool = Field(
        description="Also list players no longer in the group", default=False
    )


class RatingFormatRequest(BaseModel):
    format: Optional[MatchFormat] = Field(
        description="Only singles or only doubles, as for /squash/ratings",
        default=None,
    )


class RatingResponse(BaseModel):
    """Where a player stands on the ladder."""

    rank: int = Field(description="1 for the highest rated")
    player_id: UUID
    name: str
    rating: int = Field(description="Their Elo rating. Everyone starts on 1000")
    matches_rated: int
    provisional: bool = Field(
        description="Whether they've played too few matches for it to mean much yet"
    )
    peak: int = Field(description="The highest it's been")
    last_change: int = Field(description="What their latest match moved it by")


class RatingChangeResponse(BaseModel):
    """What one match did to a player's rating."""

    match_id: UUID
    played_at: Optional[datetime.datetime]
    rating_before: int
    rating_after: int
    change: int


class RallyInsightsResponse(BaseModel):
    """A side's rallies in games scored live."""

    side: Optional[int] = Field(
        description="Which side of the match, when it's for one", default=None
    )
    rallies_played: int
    rallies_won: int
    rally_win_rate: Optional[float]
    serves_played: int = Field(
        description="Rallies they served, where who served is known: recorded "
        "with the rally, or the winner of the one before"
    )
    serves_won: int
    serve_win_rate: Optional[float]
    receives_played: int
    receives_won: int
    receive_win_rate: Optional[float]
    longest_run: int = Field(description="The most points won in a row in a game")
    biggest_lead: int = Field(description="The furthest ahead they got in a game")
    game_points: int = Field(description="Rallies that would have won them the game")
    game_points_won: int
    game_point_win_rate: Optional[float]

    @classmethod
    def from_tally(cls, tally, side: Optional[int] = None) -> "RallyInsightsResponse":
        return cls(
            side=side,
            rallies_played=tally.rallies_played,
            rallies_won=tally.rallies_won,
            rally_win_rate=rate(tally.rallies_won, tally.rallies_played),
            serves_played=tally.serves_played,
            serves_won=tally.serves_won,
            serve_win_rate=rate(tally.serves_won, tally.serves_played),
            receives_played=tally.receives_played,
            receives_won=tally.receives_won,
            receive_win_rate=rate(tally.receives_won, tally.receives_played),
            longest_run=tally.longest_run,
            biggest_lead=tally.biggest_lead,
            game_points=tally.game_points,
            game_points_won=tally.game_points_won,
            game_point_win_rate=rate(tally.game_points_won, tally.game_points),
        )


class PlayerInsightsResponse(BaseModel):
    """How a player's completed matches went, point by point."""

    player_id: UUID
    games_scored_live: int = Field(
        description="Games with their rallies recorded, which the rally figures "
        "come from"
    )
    rallies: RallyInsightsResponse
    comebacks: int = Field(
        description="Games scored live they won from 3 or more points down"
    )
    biggest_comeback: int = Field(
        description="The furthest behind they've been in a game they won"
    )
    leads_lost: int = Field(
        description="Games scored live they lost from 3 or more points up"
    )
    deuce_games_won: int = Field(
        description="Games that reached 10-all, or one short all, that they won. "
        "Counts every game, live or not"
    )
    deuce_games_lost: int


class GameInsightsResponse(BaseModel):
    number: int
    scored_live: bool
    went_to_deuce: bool
    comeback_by_side: Optional[int] = Field(
        description="The side that won it from 3 or more points down, if one did"
    )
    deepest_deficit: Optional[int] = Field(
        description="The most the game's winner was behind by, for a game "
        "scored live and finished"
    )
    sides: List[RallyInsightsResponse] = Field(
        description="Each side's rallies, empty for a game not scored live"
    )


class MatchInsightsResponse(BaseModel):
    """A match point by point, so far if it's still being played."""

    match_id: UUID
    sides: List[RallyInsightsResponse] = Field(
        description="Each side over every game scored live"
    )
    games: List[GameInsightsResponse]
