from datetime import datetime, timezone
from uuid import uuid4

import pytest
from pydantic import ValidationError

from src.schemas.go_heavier.location_stats import (
    ExerciseStats,
    LocationStatsRequest,
    LocationStatsResponse,
)


def _stats(**overrides) -> LocationStatsResponse:
    payload = {
        "location_id": uuid4(),
        "name": "The Gym Wealdstone",
        "visits": 35,
        "total_sets": 720,
        "total_repetitions": 7511,
        "total_volume_kg": 332738.0,
        "average_sets_per_visit": 20.57,
        "average_exercises_per_visit": 7.0,
        "distinct_exercises": 39,
    }
    payload.update(overrides)
    return LocationStatsResponse(**payload)


class TestLocationStatsResponse:
    """Test the shape of a location's stats response."""

    def test_naive_visit_times_are_made_timezone_aware(self):
        """Visit times read from the database may be naive and are assumed UTC."""
        stats = _stats(
            first_visit=datetime(2025, 8, 10, 13, 0),
            last_visit=datetime(2026, 5, 29, 8, 0),
        )

        assert stats.first_visit.tzinfo is not None
        assert stats.first_visit == datetime(2025, 8, 10, 13, 0, tzinfo=timezone.utc)
        assert stats.last_visit == datetime(2026, 5, 29, 8, 0, tzinfo=timezone.utc)

    def test_aware_visit_times_are_left_alone(self):
        """Times that already carry a timezone are not shifted."""
        first_visit = datetime(2025, 8, 10, 13, 0, tzinfo=timezone.utc)

        assert _stats(first_visit=first_visit).first_visit == first_visit

    def test_location_with_no_workouts(self):
        """A location with nothing logged reports zeroes rather than nulls."""
        stats = _stats(
            visits=0,
            total_sets=0,
            total_repetitions=0,
            total_volume_kg=0.0,
            average_sets_per_visit=0.0,
            average_exercises_per_visit=0.0,
            distinct_exercises=0,
        )

        assert stats.first_visit is None
        assert stats.last_visit is None
        assert stats.heaviest_weight_kg is None
        assert stats.top_exercises == []

    def test_top_exercises_are_parsed(self):
        """The per exercise breakdown is carried through."""
        exercise_id = uuid4()
        stats = _stats(
            top_exercises=[
                {
                    "exercise_id": exercise_id,
                    "name": "Loaded Abdominal Crunch",
                    "visits": 31,
                    "sets": 88,
                    "repetitions": 1006,
                    "volume_kg": 74264.0,
                }
            ]
        )

        assert stats.top_exercises == [
            ExerciseStats(
                exercise_id=exercise_id,
                name="Loaded Abdominal Crunch",
                visits=31,
                sets=88,
                repetitions=1006,
                volume_kg=74264.0,
            )
        ]


class TestLocationStatsRequest:
    """Test the query parameters that narrow a location's stats."""

    def test_defaults(self):
        request = LocationStatsRequest()

        assert request.after is None
        assert request.before is None
        assert request.top_exercises == 5

    @pytest.mark.parametrize("top_exercises", [0, -1, 26])
    def test_top_exercises_is_bounded(self, top_exercises: int):
        with pytest.raises(ValidationError):
            LocationStatsRequest(top_exercises=top_exercises)

    def test_naive_bounds_are_rejected(self):
        """Bounds must be timezone aware so they can be compared to workout_time."""
        with pytest.raises(ValidationError):
            LocationStatsRequest(after=datetime(2026, 5, 1, 0, 0))
