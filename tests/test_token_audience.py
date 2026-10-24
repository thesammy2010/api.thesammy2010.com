"""Tests over which OAuth clients' ID tokens decode_token accepts."""

import pytest

from src import common
from src.config import Config

WEB_CLIENT = "web.apps.googleusercontent.com"
IOS_CLIENT = "ios.apps.googleusercontent.com"


@pytest.fixture
def clients(monkeypatch):
    monkeypatch.setattr(Config, "GOOGLE_CLIENT_ID", WEB_CLIENT)
    monkeypatch.setattr(Config, "GOOGLE_IOS_CLIENT_ID", IOS_CLIENT)


def test_accepts_web_and_ios_clients(clients):
    assert common.accepted_audiences() == [WEB_CLIENT, IOS_CLIENT]


def test_ios_client_is_optional(clients, monkeypatch):
    monkeypatch.setattr(Config, "GOOGLE_IOS_CLIENT_ID", None)
    assert common.accepted_audiences() == [WEB_CLIENT]


def test_decode_token_verifies_against_every_audience(clients, monkeypatch):
    seen = {}

    def fake_verify(token, request, audience):
        seen["audience"] = audience
        return {"aud": IOS_CLIENT}

    monkeypatch.setattr(common.id_token, "verify_oauth2_token", fake_verify)

    assert common.decode_token("token") == {"aud": IOS_CLIENT}
    assert seen["audience"] == [WEB_CLIENT, IOS_CLIENT]
