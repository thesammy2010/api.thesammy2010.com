from datetime import datetime, timezone
from uuid import uuid4

import pytest
from pydantic import ValidationError

from src.schemas.go_heavier.session_stats import (
    SessionHighlight,
    SessionStatsRequest,
    SessionStatsResponse,
    WeekdayStats,
)


def _stats(**overrides) -> SessionStatsResponse:
    payload = {
        "sessions": 63,
        "average_sets_per_session": 20.02,
        "average_exercises_per_session": 6.67,
        "average_repetitions_per_session": 203.37,
        "average_volume_kg_per_session": 9039.06,
    }
    payload.update(overrides)
    return SessionStatsResponse(**payload)


def _highlight(**overrides) -> dict:
    payload = {
        "id": uuid4(),
        "workout_time": datetime(2026, 5, 29, 8, 0, tzinfo=timezone.utc),
        "location": "The Gym Wealdstone",
        "sets": 42,
        "volume_kg": 12672.0,
    }
    payload.update(overrides)
    return payload


class TestSessionStatsResponse:
    """Test the shape of the aggregate session stats."""

    def test_naive_times_are_made_timezone_aware(self):
        stats = _stats(
            first_session=datetime(2025, 8, 10, 13, 0),
            last_session=datetime(2026, 8, 20, 21, 20),
        )

        assert stats.first_session == datetime(2025, 8, 10, 13, 0, tzinfo=timezone.utc)
        assert stats.last_session == datetime(2026, 8, 20, 21, 20, tzinfo=timezone.utc)

    def test_gaps_are_absent_rather_than_zero_for_one_session(self):
        """With nothing to measure between, a gap of zero would be a lie."""
        stats = _stats(sessions=1)

        assert stats.average_days_between_sessions is None
        assert stats.longest_gap_days is None

    def test_no_matching_sessions(self):
        stats = _stats(
            sessions=0,
            average_sets_per_session=0.0,
            average_exercises_per_session=0.0,
            average_repetitions_per_session=0.0,
            average_volume_kg_per_session=0.0,
        )

        assert stats.first_session is None
        assert stats.busiest_session is None
        assert stats.heaviest_session is None
        assert stats.by_weekday == []

    def test_the_highlights_are_parsed(self):
        busiest = _highlight()
        stats = _stats(busiest_session=busiest, heaviest_session=_highlight(sets=25))

        assert stats.busiest_session == SessionHighlight(**busiest)
        assert stats.heaviest_session.sets == 25

    def test_a_highlight_time_is_made_timezone_aware(self):
        stats = _stats(
            busiest_session=_highlight(workout_time=datetime(2026, 5, 29, 8, 0))
        )

        assert stats.busiest_session.workout_time.tzinfo is not None

    def test_the_weekday_breakdown_is_parsed(self):
        stats = _stats(
            by_weekday=[
                {
                    "weekday": "Friday",
                    "sessions": 15,
                    "sets": 322,
                    "volume_kg": 143668.4,
                }
            ]
        )

        assert stats.by_weekday == [
            WeekdayStats(weekday="Friday", sessions=15, sets=322, volume_kg=143668.4)
        ]


class TestSessionStatsRequest:
    """Test the query parameters that narrow the session stats."""

    def test_defaults(self):
        request = SessionStatsRequest()

        assert request.location_id is None
        assert request.exercise_id is None
        assert request.after is None
        assert request.before is None

    def test_naive_bounds_are_rejected(self):
        """Bounds must be timezone aware so they can be compared to workout_time."""
        with pytest.raises(ValidationError):
            SessionStatsRequest(after=datetime(2026, 8, 1, 0, 0))

    @pytest.mark.parametrize("field", ["location_id", "exercise_id"])
    def test_malformed_id_filters_are_rejected(self, field: str):
        with pytest.raises(ValidationError):
            SessionStatsRequest(**{field: "not-a-uuid"})
