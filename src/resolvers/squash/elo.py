"""Elo ratings, replayed from completed matches in the order they were played.

Kept free of any database import so that it stays unit testable. Worked out
afresh on every request rather than stored: the group plays a few matches a
week, and a match corrected or deleted after the fact then changes every
rating after it, as it should.
"""

import dataclasses
import datetime
import uuid
from collections import defaultdict
from statistics import mean
from typing import Dict, List, Optional

from src.resolvers.squash.scoring import SIDES

START = 1000
# How far one match can move a rating. 32 suits a small group playing often,
# where ratings should settle within a few weeks
K = 32
# Until a player's played this many, their rating is mostly where they started
PROVISIONAL_MATCHES = 5


@dataclasses.dataclass
class Change:
    match_id: uuid.UUID
    played_at: Optional[datetime.datetime]
    before: float
    after: float


@dataclasses.dataclass
class Rating:
    rating: float = START
    history: List[Change] = dataclasses.field(default_factory=list)

    @property
    def matches(self) -> int:
        return len(self.history)

    @property
    def peak(self) -> float:
        return max(change.after for change in self.history)


def expected(rating: float, opponent: float) -> float:
    """The share of the points a side rated rating should take off one rated
    opponent, from 0 to 1."""
    return 1 / (1 + 10 ** ((opponent - rating) / 400))


def rate(matches) -> Dict[uuid.UUID, Rating]:
    """Every player's rating after the matches, which must be completed and in
    the order played.

    A win scores 1, a draw 0.5 and a loss 0. In doubles a pair is rated as
    the average of the two, and both partners gain or lose what the pair
    did, so carrying a weaker partner to a win is worth more.
    """
    ratings: Dict[uuid.UUID, Rating] = defaultdict(Rating)
    for match in matches:
        sides = {
            side: [player.player_id for player in match.players if player.side == side]
            for side in SIDES
        }
        team = {side: mean(ratings[p].rating for p in sides[side]) for side in SIDES}
        for side in SIDES:
            if match.winning_side is None:
                score = 0.5
            else:
                score = float(match.winning_side == side)
            change = K * (score - expected(team[side], team[3 - side]))
            for player_id in sides[side]:
                rating = ratings[player_id]
                rating.history.append(
                    Change(
                        match_id=match.id,
                        played_at=match.played_at,
                        before=rating.rating,
                        after=rating.rating + change,
                    )
                )
                rating.rating += change
    return dict(ratings)
