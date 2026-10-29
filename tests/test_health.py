from datetime import date, datetime, timedelta, timezone
from uuid import uuid4

import pytest
from pydantic import ValidationError

from src.resolvers.go_heavier.health import could_match, nearest
from src.schemas.go_heavier.health import (
    LinkHealthWorkoutRequest,
    ListHealthDaysRequest,
    PutHealthDayRequest,
    PutHealthWorkoutRequest,
)

START = datetime(2026, 10, 23, 20, 9, tzinfo=timezone.utc)
END = START + timedelta(minutes=47)


def _workout(**overrides) -> dict:
    payload = {
        "activity_type": "traditional_strength_training",
        "start_time": START,
        "end_time": END,
        "duration_seconds": 47 * 60.0,
        "active_energy_kcal": 405.9,
        "heart_rate_avg": 116.9,
        "effort_score": 8,
        "heart_rate": [[8, 106], [9, 108], [29, 128]],
    }
    payload.update(overrides)
    return payload


class TestCouldMatch:
    """Test which session times a watch workout can be matched to."""

    @pytest.mark.parametrize(
        "offset",
        [
            timedelta(minutes=-9),  # logged a few minutes before the watch started
            timedelta(minutes=-81),  # logged well before
            timedelta(hours=-2),  # the earliest allowed
            timedelta(minutes=30),  # logged partway through
            timedelta(minutes=47),  # the end
        ],
    )
    def test_a_session_from_two_hours_before_to_the_end_matches(self, offset):
        assert could_match(START, END, 47 * 60.0, START + offset)

    @pytest.mark.parametrize(
        "offset", [timedelta(hours=-2, minutes=-1), timedelta(minutes=48)]
    )
    def test_a_session_outside_that_does_not(self, offset):
        assert not could_match(START, END, 47 * 60.0, START + offset)

    def test_a_workout_started_by_accident_never_matches(self):
        """A two minute workout, stopped again, next to the real one."""
        assert not could_match(START, START + timedelta(minutes=2), 110.0, START)


class TestNearest:
    """Test choosing between sessions that could all match."""

    def test_the_session_nearest_the_start_wins(self):
        near, far = uuid4(), uuid4()
        candidates = [
            (far, START - timedelta(minutes=90)),
            (near, START - timedelta(minutes=5)),
        ]

        assert nearest(START, candidates) == near

    def test_a_tie_is_broken_by_id_not_order(self):
        a, b = sorted([uuid4(), uuid4()], key=str)
        before, after = START - timedelta(minutes=5), START + timedelta(minutes=5)

        assert nearest(START, [(b, before), (a, after)]) == a
        assert nearest(START, [(a, after), (b, before)]) == a

    def test_no_candidates(self):
        assert nearest(START, []) is None


class TestPutHealthWorkoutRequest:
    """Test a workout as sent by the app."""

    def test_heart_rate_is_pairs_of_seconds_and_bpm(self):
        request = PutHealthWorkoutRequest(**_workout())

        assert request.heart_rate == [(8, 106), (9, 108), (29, 128)]

    def test_everything_but_the_times_and_type_is_optional(self):
        request = PutHealthWorkoutRequest(
            activity_type="traditional_strength_training",
            start_time=START,
            end_time=END,
            duration_seconds=0,
        )

        assert request.heart_rate is None
        assert request.effort_score is None

    def test_it_cannot_end_before_it_starts(self):
        with pytest.raises(ValidationError):
            PutHealthWorkoutRequest(**_workout(end_time=START - timedelta(seconds=1)))

    def test_times_must_be_timezone_aware(self):
        with pytest.raises(ValidationError):
            PutHealthWorkoutRequest(**_workout(start_time=datetime(2026, 10, 23, 20)))

    @pytest.mark.parametrize("score", [0, 11])
    def test_the_effort_score_is_one_to_ten(self, score):
        with pytest.raises(ValidationError):
            PutHealthWorkoutRequest(**_workout(effort_score=score))

    def test_a_reading_must_be_a_pair(self):
        with pytest.raises(ValidationError):
            PutHealthWorkoutRequest(**_workout(heart_rate=[[8, 106, 1]]))


class TestLinkHealthWorkoutRequest:
    def test_null_unlinks(self):
        assert LinkHealthWorkoutRequest(session_id=None).session_id is None

    def test_the_session_must_be_given_even_if_null(self):
        """An empty body is a mistake, not an unlink."""
        with pytest.raises(ValidationError):
            LinkHealthWorkoutRequest()


class TestHealthDays:
    def test_everything_is_optional(self):
        assert PutHealthDayRequest().model_dump(exclude_none=True) == {}

    def test_body_fat_is_a_percentage(self):
        with pytest.raises(ValidationError):
            PutHealthDayRequest(body_fat_pct=128)

    def test_list_bounds_are_dates(self):
        request = ListHealthDaysRequest(after="2026-10-01")

        assert request.after == date(2026, 10, 1)
