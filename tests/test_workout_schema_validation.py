from datetime import datetime, timezone
from uuid import uuid4

import pytest

from src.schemas.go_heavier.workouts import WorkoutResponse, _BaseWorkout


class TestFloatValidation:
    """Test validation of optional float fields (bar_weight_kg, supplementary_weight_kg)."""

    def test_nan_values_converted_to_none(self):
        """Test that NaN values are converted to None for optional float fields."""
        workout = WorkoutResponse(
            id=uuid4(),
            location_id=uuid4(),
            exercise_id=uuid4(),
            workout_time=datetime(2026, 6, 3, 10, 0, 0, tzinfo=timezone.utc),
            index=1,
            repetitions=10,
            weight_kg=50.0,
            bar_weight_kg=float("nan"),  # NaN should convert to None
            supplementary_weight_kg=float("nan"),  # NaN should convert to None
            created_at=datetime(2026, 6, 3, 0, 47, 31, tzinfo=timezone.utc),
            updated_at=datetime(2026, 6, 3, 0, 47, 31, tzinfo=timezone.utc),
        )

        assert workout.bar_weight_kg is None
        assert workout.supplementary_weight_kg is None

    def test_zero_values_converted_to_none(self):
        """Test that 0.0 values are converted to None for optional float fields."""
        workout = WorkoutResponse(
            id=uuid4(),
            location_id=uuid4(),
            exercise_id=uuid4(),
            workout_time=datetime(2026, 6, 3, 10, 0, 0, tzinfo=timezone.utc),
            index=1,
            repetitions=10,
            weight_kg=50.0,
            bar_weight_kg=0.0,  # 0.0 should convert to None
            supplementary_weight_kg=0.0,  # 0.0 should convert to None
            created_at=datetime(2026, 6, 3, 0, 47, 31, tzinfo=timezone.utc),
            updated_at=datetime(2026, 6, 3, 0, 47, 31, tzinfo=timezone.utc),
        )

        assert workout.bar_weight_kg is None
        assert workout.supplementary_weight_kg is None

    def test_valid_positive_floats_preserved(self):
        """Test that valid positive float values are preserved."""
        workout = WorkoutResponse(
            id=uuid4(),
            location_id=uuid4(),
            exercise_id=uuid4(),
            workout_time=datetime(2026, 6, 3, 10, 0, 0, tzinfo=timezone.utc),
            index=1,
            repetitions=10,
            weight_kg=50.0,
            bar_weight_kg=20.0,
            supplementary_weight_kg=5.5,
            created_at=datetime(2026, 6, 3, 0, 47, 31, tzinfo=timezone.utc),
            updated_at=datetime(2026, 6, 3, 0, 47, 31, tzinfo=timezone.utc),
        )

        assert workout.bar_weight_kg == 20.0
        assert workout.supplementary_weight_kg == 5.5

    def test_none_values_preserved(self):
        """Test that explicit None values are preserved."""
        workout = WorkoutResponse(
            id=uuid4(),
            location_id=uuid4(),
            exercise_id=uuid4(),
            workout_time=datetime(2026, 6, 3, 10, 0, 0, tzinfo=timezone.utc),
            index=1,
            repetitions=10,
            weight_kg=50.0,
            bar_weight_kg=None,
            supplementary_weight_kg=None,
            created_at=datetime(2026, 6, 3, 0, 47, 31, tzinfo=timezone.utc),
            updated_at=None,
        )

        assert workout.bar_weight_kg is None
        assert workout.supplementary_weight_kg is None
        assert workout.updated_at is None

    def test_float_validation_boundaries(self):
        """Test that float validation boundaries are enforced."""
        # Test valid values within boundaries
        workout = WorkoutResponse(
            id=uuid4(),
            location_id=uuid4(),
            exercise_id=uuid4(),
            workout_time=datetime(2026, 6, 3, 10, 0, 0, tzinfo=timezone.utc),
            index=1,
            repetitions=10,
            weight_kg=50.0,
            bar_weight_kg=99.9,  # Just under 100
            supplementary_weight_kg=0.1,  # Just above 0
            created_at=datetime(2026, 6, 3, 0, 47, 31, tzinfo=timezone.utc),
            updated_at=datetime(2026, 6, 3, 0, 47, 31, tzinfo=timezone.utc),
        )

        assert workout.bar_weight_kg == 99.9
        assert workout.supplementary_weight_kg == 0.1

    def test_zero_weight_kg_allowed(self):
        """Test that 0.0 weight_kg is allowed and preserved."""
        workout = WorkoutResponse(
            id=uuid4(),
            location_id=uuid4(),
            exercise_id=uuid4(),
            workout_time=datetime(2026, 6, 3, 10, 0, 0, tzinfo=timezone.utc),
            index=1,
            repetitions=10,
            weight_kg=0.0,  # Should be allowed
            bar_weight_kg=20.0,
            supplementary_weight_kg=5.0,
            created_at=datetime(2026, 6, 3, 0, 47, 31, tzinfo=timezone.utc),
            updated_at=datetime(2026, 6, 3, 0, 47, 31, tzinfo=timezone.utc),
        )

        assert workout.weight_kg == 0.0  # Should be preserved


class TestDatetimeValidation:
    """Test validation of datetime fields."""

    def test_naive_datetimes_converted_to_aware(self):
        """Test that naive datetimes are converted to timezone-aware (UTC)."""
        workout = WorkoutResponse(
            id=uuid4(),
            location_id=uuid4(),
            exercise_id=uuid4(),
            workout_time=datetime(2026, 6, 3, 10, 0, 0),  # Naive datetime
            index=1,
            repetitions=10,
            weight_kg=50.0,
            bar_weight_kg=20.0,
            supplementary_weight_kg=5.0,
            created_at=datetime(2026, 6, 3, 0, 47, 31, 121404),  # Naive datetime
            updated_at=datetime(2026, 6, 3, 0, 47, 31, 171989),  # Naive datetime
        )

        assert workout.workout_time.tzinfo == timezone.utc
        assert workout.created_at.tzinfo == timezone.utc
        assert workout.updated_at.tzinfo == timezone.utc

    def test_aware_datetimes_preserved(self):
        """Test that timezone-aware datetimes are preserved."""
        workout_time = datetime(2026, 6, 3, 10, 0, 0, tzinfo=timezone.utc)
        created_at = datetime(2026, 6, 3, 0, 47, 31, tzinfo=timezone.utc)
        updated_at = datetime(2026, 6, 3, 0, 47, 31, tzinfo=timezone.utc)

        workout = WorkoutResponse(
            id=uuid4(),
            location_id=uuid4(),
            exercise_id=uuid4(),
            workout_time=workout_time,
            index=1,
            repetitions=10,
            weight_kg=50.0,
            bar_weight_kg=20.0,
            supplementary_weight_kg=5.0,
            created_at=created_at,
            updated_at=updated_at,
        )

        assert workout.workout_time == workout_time
        assert workout.created_at == created_at
        assert workout.updated_at == updated_at

    def test_none_updated_at_allowed(self):
        """Test that updated_at can be None (it's optional)."""
        workout = WorkoutResponse(
            id=uuid4(),
            location_id=uuid4(),
            exercise_id=uuid4(),
            workout_time=datetime(2026, 6, 3, 10, 0, 0, tzinfo=timezone.utc),
            index=1,
            repetitions=10,
            weight_kg=50.0,
            bar_weight_kg=20.0,
            supplementary_weight_kg=5.0,
            created_at=datetime(2026, 6, 3, 0, 47, 31, tzinfo=timezone.utc),
            updated_at=None,
        )

        assert workout.updated_at is None


class TestCombinedValidation:
    """Test combined validation scenarios that mix multiple edge cases."""

    def test_all_edge_cases_combined(self):
        """Test handling of all edge cases in a single workout record."""
        workout = WorkoutResponse(
            id=uuid4(),
            location_id=uuid4(),
            exercise_id=uuid4(),
            workout_time=datetime(2026, 6, 3, 10, 0, 0),  # Naive datetime
            index=1,
            repetitions=10,
            weight_kg=0.0,  # 0.0 is allowed and preserved
            bar_weight_kg=float("nan"),  # NaN converts to None
            supplementary_weight_kg=0.0,  # 0.0 converts to None
            notes="Test workout with edge cases",
            created_at=datetime(2026, 6, 3, 0, 47, 31),  # Naive datetime
            updated_at=None,  # Explicitly None
        )

        # Weight is preserved
        assert workout.weight_kg == 0.0  # Preserved as-is

        # Float conversions
        assert workout.bar_weight_kg is None
        assert workout.supplementary_weight_kg is None

        # Datetime conversions
        assert workout.workout_time.tzinfo == timezone.utc
        assert workout.created_at.tzinfo == timezone.utc
        assert workout.updated_at is None

        # Other fields preserved
        assert workout.notes == "Test workout with edge cases"

    def test_database_like_scenario(self):
        """Test a scenario that mimics actual database output."""
        # Simulating what SQLAlchemy might return from the database
        workout = WorkoutResponse(
            id=uuid4(),
            location_id=uuid4(),
            exercise_id=uuid4(),
            workout_time=datetime(2026, 6, 3, 10, 0, 0),  # DB returns naive
            index=1,
            repetitions=10,
            weight_kg=0.0,  # 0.0 in DB is preserved
            bar_weight_kg=float("nan"),  # NULL in DB returns as NaN
            supplementary_weight_kg=float("nan"),  # NULL in DB returns as NaN
            notes=None,
            created_at=datetime(2026, 6, 3, 0, 47, 31, 121404),  # DB returns naive
            updated_at=datetime(2026, 6, 3, 0, 47, 31, 171989),  # DB returns naive
        )

        # All validations should pass
        assert workout.weight_kg == 0.0  # Preserved from DB
        assert workout.bar_weight_kg is None
        assert workout.supplementary_weight_kg is None
        assert workout.workout_time.tzinfo == timezone.utc
        assert workout.created_at.tzinfo == timezone.utc
        assert workout.updated_at.tzinfo == timezone.utc


class TestBaseWorkoutValidation:
    """Test validation for the base workout model."""

    def test_base_workout_float_validation(self):
        """Test that float validation works in the base workout model."""
        workout = _BaseWorkout(
            location_id=uuid4(),
            exercise_id=uuid4(),
            workout_time=datetime(2026, 6, 3, 10, 0, 0, tzinfo=timezone.utc),
            index=1,
            repetitions=10,
            weight_kg=50.0,
            bar_weight_kg=float("nan"),
            supplementary_weight_kg=0.0,
        )

        assert workout.bar_weight_kg is None
        assert workout.supplementary_weight_kg is None

    def test_base_workout_valid_values(self):
        """Test that valid values work in the base workout model."""
        workout = _BaseWorkout(
            location_id=uuid4(),
            exercise_id=uuid4(),
            workout_time=datetime(2026, 6, 3, 10, 0, 0, tzinfo=timezone.utc),
            index=5,
            repetitions=15,
            weight_kg=75.5,
            bar_weight_kg=25.0,
            supplementary_weight_kg=10.0,
            notes="Heavy set",
        )

        assert workout.index == 5
        assert workout.repetitions == 15
        assert workout.weight_kg == 75.5
        assert workout.bar_weight_kg == 25.0
        assert workout.supplementary_weight_kg == 10.0
        assert workout.notes == "Heavy set"


class TestValidationErrors:
    """Test that proper validation errors are raised for invalid data."""

    def test_invalid_weight_kg_raises_error(self):
        """Test that invalid weight_kg values raise validation errors."""
        with pytest.raises(Exception):  # Pydantic ValidationError
            WorkoutResponse(
                id=uuid4(),
                location_id=uuid4(),
                exercise_id=uuid4(),
                workout_time=datetime(2026, 6, 3, 10, 0, 0, tzinfo=timezone.utc),
                index=1,
                repetitions=10,
                weight_kg=-5.0,  # Invalid: must be > 0
                bar_weight_kg=20.0,
                supplementary_weight_kg=5.0,
                created_at=datetime(2026, 6, 3, 0, 47, 31, tzinfo=timezone.utc),
                updated_at=datetime(2026, 6, 3, 0, 47, 31, tzinfo=timezone.utc),
            )

    def test_bar_weight_too_large_raises_error(self):
        """Test that bar_weight_kg > 100 raises validation error."""
        with pytest.raises(Exception):  # Pydantic ValidationError
            WorkoutResponse(
                id=uuid4(),
                location_id=uuid4(),
                exercise_id=uuid4(),
                workout_time=datetime(2026, 6, 3, 10, 0, 0, tzinfo=timezone.utc),
                index=1,
                repetitions=10,
                weight_kg=50.0,
                bar_weight_kg=150.0,  # Invalid: must be < 100
                supplementary_weight_kg=5.0,
                created_at=datetime(2026, 6, 3, 0, 47, 31, tzinfo=timezone.utc),
                updated_at=datetime(2026, 6, 3, 0, 47, 31, tzinfo=timezone.utc),
            )

    def test_invalid_index_raises_error(self):
        """Test that invalid index values raise validation errors."""
        with pytest.raises(Exception):  # Pydantic ValidationError
            WorkoutResponse(
                id=uuid4(),
                location_id=uuid4(),
                exercise_id=uuid4(),
                workout_time=datetime(2026, 6, 3, 10, 0, 0, tzinfo=timezone.utc),
                index=0,  # Invalid: must be > 0
                repetitions=10,
                weight_kg=50.0,
                bar_weight_kg=20.0,
                supplementary_weight_kg=5.0,
                created_at=datetime(2026, 6, 3, 0, 47, 31, tzinfo=timezone.utc),
                updated_at=datetime(2026, 6, 3, 0, 47, 31, tzinfo=timezone.utc),
            )

    def test_invalid_repetitions_raises_error(self):
        """Test that invalid repetitions values raise validation errors."""
        with pytest.raises(Exception):  # Pydantic ValidationError
            WorkoutResponse(
                id=uuid4(),
                location_id=uuid4(),
                exercise_id=uuid4(),
                workout_time=datetime(2026, 6, 3, 10, 0, 0, tzinfo=timezone.utc),
                index=1,
                repetitions=150,  # Invalid: must be < 100
                weight_kg=50.0,
                bar_weight_kg=20.0,
                supplementary_weight_kg=5.0,
                created_at=datetime(2026, 6, 3, 0, 47, 31, tzinfo=timezone.utc),
                updated_at=datetime(2026, 6, 3, 0, 47, 31, tzinfo=timezone.utc),
            )
