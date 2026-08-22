from datetime import datetime, timezone
from uuid import uuid4

import pytest
from pydantic import ValidationError

from src.schemas.go_heavier.exercise_stats import (
    ExerciseStatsRequest,
    ExerciseStatsResponse,
    LocationStats,
)


def _stats(**overrides) -> ExerciseStatsResponse:
    payload = {
        "exercise_id": uuid4(),
        "name": "Bench Press",
        "sessions": 12,
        "total_sets": 44,
        "total_repetitions": 321,
        "total_volume_kg": 10580.0,
        "average_sets_per_session": 3.67,
        "average_repetitions_per_set": 7.3,
        "distinct_locations": 3,
    }
    payload.update(overrides)
    return ExerciseStatsResponse(**payload)


class TestExerciseStatsResponse:
    """Test the shape of an exercise's stats response."""

    def test_naive_times_are_made_timezone_aware(self):
        """Times read from the database may be naive and are assumed UTC."""
        stats = _stats(
            first_performed=datetime(2025, 8, 12, 21, 30),
            last_performed=datetime(2026, 5, 29, 8, 0),
        )

        assert stats.first_performed == datetime(
            2025, 8, 12, 21, 30, tzinfo=timezone.utc
        )
        assert stats.last_performed == datetime(2026, 5, 29, 8, 0, tzinfo=timezone.utc)

    def test_aware_times_are_left_alone(self):
        """Times that already carry a timezone are not shifted."""
        first_performed = datetime(2025, 8, 12, 21, 30, tzinfo=timezone.utc)

        assert _stats(first_performed=first_performed).first_performed == (
            first_performed
        )

    def test_exercise_never_performed(self):
        """An exercise with nothing logged reports zeroes rather than nulls."""
        stats = _stats(
            sessions=0,
            total_sets=0,
            total_repetitions=0,
            total_volume_kg=0.0,
            average_sets_per_session=0.0,
            average_repetitions_per_set=0.0,
            distinct_locations=0,
        )

        assert stats.first_performed is None
        assert stats.last_performed is None
        assert stats.heaviest_weight_kg is None
        assert stats.top_locations == []

    def test_top_locations_are_parsed(self):
        """The per location breakdown is carried through."""
        location_id = uuid4()
        stats = _stats(
            top_locations=[
                {
                    "location_id": location_id,
                    "name": "The Gym Wealdstone",
                    "sessions": 10,
                    "sets": 37,
                    "repetitions": 276,
                    "volume_kg": 9180.0,
                }
            ]
        )

        assert stats.top_locations == [
            LocationStats(
                location_id=location_id,
                name="The Gym Wealdstone",
                sessions=10,
                sets=37,
                repetitions=276,
                volume_kg=9180.0,
            )
        ]


class TestExerciseStatsRequest:
    """Test the query parameters that narrow an exercise's stats."""

    def test_defaults(self):
        request = ExerciseStatsRequest()

        assert request.after is None
        assert request.before is None
        assert request.top_locations == 5

    @pytest.mark.parametrize("top_locations", [0, -1, 26])
    def test_top_locations_is_bounded(self, top_locations: int):
        with pytest.raises(ValidationError):
            ExerciseStatsRequest(top_locations=top_locations)

    def test_naive_bounds_are_rejected(self):
        """Bounds must be timezone aware so they can be compared to workout_time."""
        with pytest.raises(ValidationError):
            ExerciseStatsRequest(after=datetime(2026, 5, 1, 0, 0))
