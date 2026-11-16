"""Tests for working out a player's record."""

import uuid
from types import SimpleNamespace

from src.resolvers.squash.stats import record, win_rate


class TestWinRate:
    def test_draws_count_neither_way(self):
        # 3 won, 1 lost, any number drawn
        assert win_rate(won=3, lost=1) == 0.75

    def test_none_before_a_match_is_won_or_lost(self):
        assert win_rate(won=0, lost=0) is None


def _match(format, winning_side, *games, side=1):
    return SimpleNamespace(
        format=format,
        winning_side=winning_side,
        points_to=11,
        players=[SimpleNamespace(player_id=ME, side=side)],
        games=[SimpleNamespace(side1_points=a, side2_points=b) for a, b in games],
    )


ME = uuid.uuid4()


class TestRecord:
    def test_counts_from_the_players_side(self):
        played = record(
            [
                _match("singles", 1, (11, 5), (11, 9)),
                _match("doubles", 1, (11, 3), (7, 11), (11, 8), side=2),
            ],
            ME,
        )
        assert (played.matches_won, played.matches_lost) == (1, 1)
        assert (played.games_won, played.games_lost) == (3, 2)
        assert (played.points_won, played.points_lost) == (22 + 22, 14 + 29)
        assert played.win_rate == 0.5

    def test_none_played(self):
        played = record([], ME)
        assert played.matches_played == 0
        assert played.win_rate is None
