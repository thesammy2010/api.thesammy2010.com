from datetime import datetime, timezone
from uuid import uuid4

import pytest
from pydantic import ValidationError

from src.schemas.go_heavier.sessions import (
    ListSessionsRequest,
    SessionExerciseStats,
    SessionResponse,
    SessionSummary,
)


def _payload(**overrides) -> dict:
    payload = {
        "id": uuid4(),
        "workout_time": datetime(2026, 8, 20, 21, 20, tzinfo=timezone.utc),
        "location_id": uuid4(),
        "location": "The Gym Greenford",
        "sets": 17,
        "exercises": 6,
        "repetitions": 158,
        "volume_kg": 8069.9,
        "heaviest_weight_kg": 100.0,
    }
    payload.update(overrides)
    return payload


class TestSessionSummary:
    """Test a session as it appears in the listing."""

    def test_a_naive_workout_time_is_made_timezone_aware(self):
        """The column is read back naive in places and is assumed UTC."""
        summary = SessionSummary(**_payload(workout_time=datetime(2026, 8, 20, 21, 20)))

        assert summary.workout_time == datetime(
            2026, 8, 20, 21, 20, tzinfo=timezone.utc
        )

    def test_an_aware_workout_time_is_left_alone(self):
        workout_time = datetime(2026, 8, 20, 21, 20, tzinfo=timezone.utc)

        assert SessionSummary(**_payload()).workout_time == workout_time

    def test_the_session_is_identified_by_its_own_id(self):
        """The id is stable, unlike the time it was previously keyed on."""
        session_id = uuid4()

        assert SessionSummary(**_payload(id=session_id)).id == session_id

    def test_an_assisted_session_can_be_heaviest_negative(self):
        """A session of only assisted work has a negative heaviest weight."""
        summary = SessionSummary(**_payload(heaviest_weight_kg=-14.0))

        assert summary.heaviest_weight_kg == -14.0


class TestSessionResponse:
    """Test a single session with its breakdown."""

    def test_the_breakdown_is_parsed(self):
        exercise_id = uuid4()
        response = SessionResponse(
            **_payload(),
            by_exercise=[
                {
                    "exercise_id": exercise_id,
                    "name": "Cable Fly",
                    "sets": 3,
                    "repetitions": 25,
                    "volume_kg": 327.9,
                    "heaviest_weight_kg": 14.7,
                }
            ],
        )

        assert response.by_exercise == [
            SessionExerciseStats(
                exercise_id=exercise_id,
                name="Cable Fly",
                sets=3,
                repetitions=25,
                volume_kg=327.9,
                heaviest_weight_kg=14.7,
            )
        ]

    def test_the_breakdown_defaults_to_empty(self):
        assert SessionResponse(**_payload()).by_exercise == []


class TestListSessionsRequest:
    """Test the query parameters for listing sessions."""

    def test_defaults(self):
        request = ListSessionsRequest()

        assert request.page == 1
        assert request.location_id is None
        assert request.exercise_id is None
        assert request.after is None
        assert request.before is None

    def test_pages_are_offset_by_the_page_size(self):
        assert ListSessionsRequest(page=1).offset == 0
        assert ListSessionsRequest(page=3).offset > 0

    @pytest.mark.parametrize("page", [0, -1])
    def test_the_page_must_be_positive(self, page: int):
        with pytest.raises(ValidationError):
            ListSessionsRequest(page=page)

    def test_naive_bounds_are_rejected(self):
        """Bounds must be timezone aware so they can be compared to workout_time."""
        with pytest.raises(ValidationError):
            ListSessionsRequest(after=datetime(2026, 8, 1, 0, 0))

    def test_malformed_id_filters_are_rejected(self):
        with pytest.raises(ValidationError):
            ListSessionsRequest(exercise_id="not-a-uuid")
