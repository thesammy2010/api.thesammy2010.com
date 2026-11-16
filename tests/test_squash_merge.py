"""Tests for merging two matches between the same players."""

import datetime
import uuid
from types import SimpleNamespace

import pytest

from src.resolvers.squash.matches import merged_status, played_order, sides_swapped
from src.resolvers.squash.scoring import InvalidScore

A, B, C, D = (uuid.uuid4() for _ in range(4))


def _match(*sides, format="singles", status="completed", games=(), played_at=None):
    return SimpleNamespace(
        format=format,
        status=status,
        games=list(games),
        played_at=played_at,
        created_at=datetime.datetime(2026, 11, 1),
        players=[
            SimpleNamespace(player_id=player, side=side) for player, side in sides
        ],
    )


class TestSidesSwapped:
    def test_same_sides(self):
        assert not sides_swapped(_match((A, 1), (B, 2)), _match((A, 1), (B, 2)))

    def test_ends_swapped(self):
        assert sides_swapped(_match((A, 1), (B, 2)), _match((A, 2), (B, 1)))

    def test_doubles_pairs_swapped(self):
        assert sides_swapped(
            _match((A, 1), (B, 1), (C, 2), (D, 2), format="doubles"),
            _match((A, 2), (B, 2), (C, 1), (D, 1), format="doubles"),
        )

    def test_different_players(self):
        with pytest.raises(InvalidScore, match="same players"):
            sides_swapped(_match((A, 1), (B, 2)), _match((A, 1), (C, 2)))

    def test_doubles_with_different_pairs(self):
        with pytest.raises(InvalidScore, match="paired differently"):
            sides_swapped(
                _match((A, 1), (B, 1), (C, 2), (D, 2), format="doubles"),
                _match((A, 1), (C, 1), (B, 2), (D, 2), format="doubles"),
            )


class TestMergedStatus:
    def test_completed_only_if_both_were(self):
        assert merged_status(_match(), _match()) == "completed"
        in_progress = _match(status="in_progress", games=[(5, 3)])
        assert merged_status(_match(), in_progress) == "in_progress"

    def test_scheduled_without_games(self):
        assert (
            merged_status(_match(status="scheduled"), _match(status="scheduled"))
            == "scheduled"
        )


class TestPlayedOrder:
    def test_undated_counts_as_played_last(self):
        dated = _match(played_at=datetime.datetime(2026, 11, 2))
        undated = _match()
        assert sorted([undated, dated], key=played_order) == [dated, undated]
