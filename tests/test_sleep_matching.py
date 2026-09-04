"""Tests over matching a stored SleepRecord onto a newly created session.

These run against a real database, since the matching query itself
(comparing UK-local calendar dates in SQL) is exactly what's under test.
"""

import datetime
from typing import Iterator

import pytest

from src.db import session
from src.models.go_heavier import Location, SleepRecord
from src.resolvers.go_heavier import sessions
from src.schemas.go_heavier.sessions import CreateSessionRequest


@pytest.fixture
def location() -> Location:
    return session.query(Location).first()


@pytest.fixture
def cleanup() -> Iterator[dict]:
    """Deletes whatever session/sleep record ids a test registers here.

    Register each id the moment it's created, not just once at the end of
    the test body - a failed assertion partway through must not skip
    cleanup and leak rows into later tests.
    """
    created = {"session_ids": [], "sleep_record_ids": []}
    yield created
    for record_id in created["sleep_record_ids"]:
        record = session.get(SleepRecord, record_id)
        if record:
            session.delete(record)
    for session_id in created["session_ids"]:
        sessions.delete_session(session_id=session_id)
    session.commit()


def _sleep_record(wake_time: datetime.datetime, **overrides) -> SleepRecord:
    defaults = dict(
        bed_time=wake_time - datetime.timedelta(hours=7),
        wake_time=wake_time,
        sleep_hours=7.0,
    )
    defaults.update(overrides)
    record = SleepRecord(**defaults)
    session.add(record)
    session.commit()
    return record


class TestCreateSessionMatchesSleep:
    """Test that create_session picks up a same-UK-day sleep record."""

    def test_a_session_picks_up_a_same_day_sleep_record(
        self, location: Location, cleanup: dict
    ):
        wake_time = datetime.datetime(2026, 9, 1, 8, 6, tzinfo=datetime.timezone.utc)
        record = _sleep_record(wake_time, sleep_hours=7.22, sleep_score=88)
        cleanup["sleep_record_ids"].append(record.id)

        workout_time = datetime.datetime(
            2026, 9, 1, 18, 0, tzinfo=datetime.timezone.utc
        )
        result = sessions.create_session(
            CreateSessionRequest(location_id=location.id, workout_time=workout_time)
        )
        cleanup["session_ids"].append(result.id)

        assert result.sleep_hours == 7.22
        assert result.sleep_score == 88
        assert result.bed_time == record.bed_time

    def test_matching_is_by_uk_local_wake_date_not_utc_date(
        self, location: Location, cleanup: dict
    ):
        """00:45 UTC on Sep 1 is 01:45 BST, still the same UK day as an
        evening session logged in UTC on Sep 1."""
        wake_time = datetime.datetime(2026, 9, 1, 0, 45, tzinfo=datetime.timezone.utc)
        record = _sleep_record(wake_time)
        cleanup["sleep_record_ids"].append(record.id)

        workout_time = datetime.datetime(
            2026, 9, 1, 20, 0, tzinfo=datetime.timezone.utc
        )
        result = sessions.create_session(
            CreateSessionRequest(location_id=location.id, workout_time=workout_time)
        )
        cleanup["session_ids"].append(result.id)

        assert result.sleep_hours == record.sleep_hours

    def test_a_different_day_sleep_record_is_not_matched(
        self, location: Location, cleanup: dict
    ):
        wake_time = datetime.datetime(2026, 8, 30, 8, 0, tzinfo=datetime.timezone.utc)
        record = _sleep_record(wake_time)
        cleanup["sleep_record_ids"].append(record.id)

        workout_time = datetime.datetime(
            2026, 9, 1, 18, 0, tzinfo=datetime.timezone.utc
        )
        result = sessions.create_session(
            CreateSessionRequest(location_id=location.id, workout_time=workout_time)
        )
        cleanup["session_ids"].append(result.id)

        assert result.sleep_hours is None

    def test_an_already_matched_record_is_not_matched_again(
        self, location: Location, cleanup: dict
    ):
        # A real, unrelated session (a different day, so it's not what's
        # under test here) stands in for whatever session the record
        # matched against previously.
        other = sessions.create_session(
            CreateSessionRequest(
                location_id=location.id,
                workout_time=datetime.datetime(
                    2026, 8, 20, 18, 0, tzinfo=datetime.timezone.utc
                ),
            )
        )
        cleanup["session_ids"].append(other.id)

        wake_time = datetime.datetime(2026, 9, 1, 8, 0, tzinfo=datetime.timezone.utc)
        record = _sleep_record(wake_time, matched_session_id=other.id)
        cleanup["sleep_record_ids"].append(record.id)

        workout_time = datetime.datetime(
            2026, 9, 1, 18, 0, tzinfo=datetime.timezone.utc
        )
        result = sessions.create_session(
            CreateSessionRequest(location_id=location.id, workout_time=workout_time)
        )
        cleanup["session_ids"].append(result.id)

        assert result.sleep_hours is None

    def test_the_matched_record_is_marked_so_it_is_not_reused(
        self, location: Location, cleanup: dict
    ):
        wake_time = datetime.datetime(2026, 9, 1, 8, 0, tzinfo=datetime.timezone.utc)
        record = _sleep_record(wake_time)
        cleanup["sleep_record_ids"].append(record.id)

        workout_time = datetime.datetime(
            2026, 9, 1, 18, 0, tzinfo=datetime.timezone.utc
        )
        result = sessions.create_session(
            CreateSessionRequest(location_id=location.id, workout_time=workout_time)
        )
        cleanup["session_ids"].append(result.id)

        assert record.matched_session_id == result.id

    def test_deleting_the_matched_session_unmatches_the_record_rather_than_blocking(
        self, location: Location, cleanup: dict
    ):
        """Deleting a session is a normal action - a sleep record having
        matched it must not prevent that."""
        wake_time = datetime.datetime(2026, 9, 1, 8, 0, tzinfo=datetime.timezone.utc)
        record = _sleep_record(wake_time)
        cleanup["sleep_record_ids"].append(record.id)

        workout_time = datetime.datetime(
            2026, 9, 1, 18, 0, tzinfo=datetime.timezone.utc
        )
        result = sessions.create_session(
            CreateSessionRequest(location_id=location.id, workout_time=workout_time)
        )

        assert sessions.delete_session(session_id=result.id) is True

        session.expire_all()
        assert session.get(SleepRecord, record.id).matched_session_id is None
