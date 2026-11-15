"""Tests for validating a match before it reaches the database."""

import uuid

import pytest
from pydantic import ValidationError

from src.schemas.squash.matches import MatchRequest, RallyRequest

A, B, C, D = (uuid.uuid4() for _ in range(4))


def match(format, *sides, **kwargs) -> MatchRequest:
    return MatchRequest(
        format=format,
        players=[{"player_id": player, "side": side} for player, side in sides],
        **kwargs,
    )


class TestMatchRequest:
    def test_singles_is_one_a_side(self):
        request = match("singles", (A, 1), (B, 2))

        assert request.points_to == 11
        assert request.status == "scheduled"

    def test_doubles_is_two_a_side(self):
        match("doubles", (A, 1), (B, 1), (C, 2), (D, 2))

    @pytest.mark.parametrize(
        "format,sides",
        [
            ("singles", [(A, 1), (B, 1)]),
            ("singles", [(A, 1)]),
            ("doubles", [(A, 1), (B, 2)]),
            ("doubles", [(A, 1), (B, 1), (C, 1), (D, 2)]),
        ],
    )
    def test_the_sides_must_fit_the_format(self, format, sides):
        with pytest.raises(ValidationError, match="on each side"):
            match(format, *sides)

    def test_a_player_cant_play_on_both_sides(self):
        with pytest.raises(ValidationError, match="only be in a match once"):
            match("doubles", (A, 1), (B, 1), (A, 2), (D, 2))

    def test_best_of_must_be_odd(self):
        match("singles", (A, 1), (B, 2), best_of=5)
        with pytest.raises(ValidationError, match="odd"):
            match("singles", (A, 1), (B, 2), best_of=4)


class TestRallyRequest:
    def test_a_rally_says_which_version_it_was_scored_against(self):
        """Without it, two phones scoring the same rally would add two points."""
        assert RallyRequest(won_by_side=1, version=7).version == 7
        with pytest.raises(ValidationError, match="version"):
            RallyRequest(won_by_side=1)
