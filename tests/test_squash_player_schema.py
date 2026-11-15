"""Tests for validating a player before it reaches the database."""

import pytest
from pydantic import ValidationError

from src.schemas.squash.players import PlayerRequest


class TestPlayerRequest:
    def test_an_email_is_matched_lowercased(self):
        player = PlayerRequest(name="Alex", email="  Alex.Smith@Gmail.com ")

        assert player.email == "alex.smith@gmail.com"

    def test_a_blank_email_is_none(self):
        assert PlayerRequest(name="Alex", email="").email is None

    def test_an_email_needs_an_at_and_a_domain(self):
        with pytest.raises(ValidationError):
            PlayerRequest(name="Alex", email="alex")
