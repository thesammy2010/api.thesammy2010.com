"""Tests for validating a spend sent to the API."""

import datetime
import uuid

import pytest
from pydantic import ValidationError

from src.schemas.finance.enums import TransactionRelation
from src.schemas.finance.transactions import TransactionRequest

CARD = uuid.UUID("13cd5cda-03ae-5971-abdc-1d449069dcb0")


def request(**kwargs) -> TransactionRequest:
    return TransactionRequest(
        spent_on=datetime.date(2026, 11, 12),
        amount_gbp="0.16",
        payment_method_id=CARD,
        **kwargs,
    )


class TestRelation:
    def test_a_fee_for_another_spend_is_valid(self):
        fee = request(related_to_id=uuid.uuid4(), relation="fee")

        assert fee.relation == TransactionRelation.FEE

    def test_neither_is_valid(self):
        assert request().related_to_id is None

    def test_a_link_needs_a_relation(self):
        with pytest.raises(ValidationError, match="must be set together"):
            request(related_to_id=uuid.uuid4())

    def test_a_relation_needs_a_link(self):
        with pytest.raises(ValidationError, match="must be set together"):
            request(relation="fee")

    def test_an_unknown_relation_is_rejected(self):
        with pytest.raises(ValidationError):
            request(related_to_id=uuid.uuid4(), relation="tip")
