"""Tests for working out a player's record."""

from src.resolvers.squash.stats import win_rate


class TestWinRate:
    def test_draws_count_neither_way(self):
        # 3 won, 1 lost, any number drawn
        assert win_rate(won=3, lost=1) == 0.75

    def test_none_before_a_match_is_won_or_lost(self):
        assert win_rate(won=0, lost=0) is None
