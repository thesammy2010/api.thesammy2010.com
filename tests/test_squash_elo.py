"""Tests for rating players from their results."""

import uuid
from types import SimpleNamespace

import pytest

from src.resolvers.squash.elo import START, K, expected, rate

A, B, C, D = (uuid.uuid4() for _ in range(4))


def _match(winning_side, *sides):
    return SimpleNamespace(
        id=uuid.uuid4(),
        played_at=None,
        winning_side=winning_side,
        players=[
            SimpleNamespace(player_id=player, side=side) for player, side in sides
        ],
    )


class TestExpected:
    def test_level_ratings_expect_half(self):
        assert expected(1000, 1000) == 0.5

    def test_400_points_up_expects_ten_to_one(self):
        assert expected(1400, 1000) == pytest.approx(10 / 11)


class TestRate:
    def test_a_first_win_between_newcomers_moves_half_k(self):
        ratings = rate([_match(1, (A, 1), (B, 2))])

        assert ratings[A].rating == START + K / 2
        assert ratings[B].rating == START - K / 2

    def test_a_draw_between_equals_changes_nothing(self):
        ratings = rate([_match(None, (A, 1), (B, 2))])

        assert ratings[A].rating == ratings[B].rating == START

    def test_beating_a_stronger_player_is_worth_more(self):
        # A beats C twice, then B beats A (now stronger) and D beats C (weaker)
        ratings = rate(
            [
                _match(1, (A, 1), (C, 2)),
                _match(1, (A, 1), (C, 2)),
                _match(1, (B, 1), (A, 2)),
                _match(1, (D, 1), (C, 2)),
            ]
        )

        assert ratings[B].rating > ratings[D].rating

    def test_doubles_partners_move_together(self):
        ratings = rate([_match(2, (A, 1), (B, 1), (C, 2), (D, 2))])

        assert ratings[A].rating == ratings[B].rating == START - K / 2
        assert ratings[C].rating == ratings[D].rating == START + K / 2

    def test_points_are_only_moved_around(self):
        ratings = rate(
            [
                _match(1, (A, 1), (B, 2)),
                _match(2, (A, 1), (C, 2)),
                _match(None, (B, 1), (C, 2)),
            ]
        )

        assert sum(r.rating for r in ratings.values()) == pytest.approx(3 * START)

    def test_history_runs_in_order(self):
        first, second = _match(1, (A, 1), (B, 2)), _match(1, (A, 1), (B, 2))
        history = rate([first, second])[A].history

        assert [change.match_id for change in history] == [first.id, second.id]
        assert history[0].after == history[1].before
        assert rate([first, second])[A].peak == history[1].after
