from datetime import datetime, timezone
from uuid import uuid4

import pytest
from pydantic import ValidationError

from src.schemas.go_heavier.workout_stats import (
    ExerciseBreakdown,
    LocationBreakdown,
    WorkoutStatsRequest,
    WorkoutStatsResponse,
)


def _stats(**overrides) -> WorkoutStatsResponse:
    payload = {
        "sessions": 39,
        "total_sets": 795,
        "total_repetitions": 8203,
        "total_volume_kg": 357088.2,
        "average_sets_per_session": 20.38,
        "average_exercises_per_session": 6.92,
        "average_repetitions_per_set": 10.32,
        "distinct_locations": 4,
        "distinct_exercises": 39,
    }
    payload.update(overrides)
    return WorkoutStatsResponse(**payload)


class TestWorkoutStatsResponse:
    """Test the shape of the aggregate workout stats response."""

    def test_naive_times_are_made_timezone_aware(self):
        """Times read from the database may be naive and are assumed UTC."""
        stats = _stats(
            first_workout=datetime(2025, 8, 10, 13, 0),
            last_workout=datetime(2026, 5, 29, 8, 0),
        )

        assert stats.first_workout == datetime(2025, 8, 10, 13, 0, tzinfo=timezone.utc)
        assert stats.last_workout == datetime(2026, 5, 29, 8, 0, tzinfo=timezone.utc)

    def test_aware_times_are_left_alone(self):
        """Times that already carry a timezone are not shifted."""
        first_workout = datetime(2025, 8, 10, 13, 0, tzinfo=timezone.utc)

        assert _stats(first_workout=first_workout).first_workout == first_workout

    def test_no_matching_workouts(self):
        """A filter that matches nothing reports zeroes rather than nulls."""
        stats = _stats(
            sessions=0,
            total_sets=0,
            total_repetitions=0,
            total_volume_kg=0.0,
            average_sets_per_session=0.0,
            average_exercises_per_session=0.0,
            average_repetitions_per_set=0.0,
            distinct_locations=0,
            distinct_exercises=0,
        )

        assert stats.first_workout is None
        assert stats.last_workout is None
        assert stats.heaviest_weight_kg is None
        assert stats.top_locations == []
        assert stats.top_exercises == []

    def test_both_breakdowns_are_parsed(self):
        """The location and exercise breakdowns are carried through."""
        location_id, exercise_id = uuid4(), uuid4()
        stats = _stats(
            top_locations=[
                {
                    "location_id": location_id,
                    "name": "The Gym Wealdstone",
                    "sessions": 35,
                    "sets": 720,
                    "repetitions": 7511,
                    "volume_kg": 332738.0,
                }
            ],
            top_exercises=[
                {
                    "exercise_id": exercise_id,
                    "name": "Loaded Abdominal Crunch",
                    "sessions": 34,
                    "sets": 98,
                    "repetitions": 1120,
                    "volume_kg": 81728.0,
                }
            ],
        )

        assert stats.top_locations == [
            LocationBreakdown(
                location_id=location_id,
                name="The Gym Wealdstone",
                sessions=35,
                sets=720,
                repetitions=7511,
                volume_kg=332738.0,
            )
        ]
        assert stats.top_exercises == [
            ExerciseBreakdown(
                exercise_id=exercise_id,
                name="Loaded Abdominal Crunch",
                sessions=34,
                sets=98,
                repetitions=1120,
                volume_kg=81728.0,
            )
        ]


class TestWorkoutStatsRequest:
    """Test the query parameters that narrow the workout stats."""

    def test_defaults(self):
        request = WorkoutStatsRequest()

        assert request.location_id is None
        assert request.exercise_id is None
        assert request.after is None
        assert request.before is None
        assert request.top_locations == 5
        assert request.top_exercises == 5

    @pytest.mark.parametrize("limit", [0, -1, 26])
    def test_breakdown_limits_are_bounded(self, limit: int):
        with pytest.raises(ValidationError):
            WorkoutStatsRequest(top_locations=limit)
        with pytest.raises(ValidationError):
            WorkoutStatsRequest(top_exercises=limit)

    def test_naive_bounds_are_rejected(self):
        """Bounds must be timezone aware so they can be compared to workout_time."""
        with pytest.raises(ValidationError):
            WorkoutStatsRequest(after=datetime(2026, 5, 1, 0, 0))

    def test_malformed_id_filters_are_rejected(self):
        with pytest.raises(ValidationError):
            WorkoutStatsRequest(location_id="not-a-uuid")
