"""Tests for building models out of the Google Sheet.

The loaders are exercised against fake worksheets rather than the real
spreadsheet, so they run without credentials or a database.
"""

import datetime
import logging
import uuid

import pytest

from src.migration_utils import google_sheets
from src.migration_utils.session_ids import session_id_for

GYM = uuid.UUID("62655708-0330-475f-aa28-c4749ded4b9d")
OTHER_GYM = uuid.UUID("97cffa7f-6b99-47a0-9a3f-adbbb7409dea")
BENCH = uuid.UUID("55c2fa3a-789b-4431-a207-018636eec66c")
CRUNCH = uuid.UUID("214b75cd-e331-414e-9189-50bbe4ca5e15")

WORKOUT_HEADER = [
    "id",
    "location",
    "workout_time",
    "exercise",
    "index",
    "weight_kg",
    "repetitions",
    "bar_weight_kg",
    "supplementary_weight_kg",
    "weight_lb",
    "notes",
]


def workout_row(
    location="",
    workout_time="",
    exercise="",
    index="",
    weight_kg="",
    repetitions="",
    bar="",
    supplementary="",
    weight_lb="",
    notes="",
    row_id=None,
) -> list:
    """A workouts sheet row. Blank columns are inherited from the row above."""
    return [
        str(row_id or uuid.uuid4()),
        location,
        workout_time,
        exercise,
        index,
        weight_kg,
        repetitions,
        bar,
        supplementary,
        weight_lb,
        notes,
    ]


class FakeWorksheet:
    def __init__(self, rows: list):
        self._rows = rows

    def get_all_values(self) -> list:
        return self._rows


@pytest.fixture
def workouts_sheet(monkeypatch):
    """Install a fake workouts sheet, returning a setter for its rows."""
    monkeypatch.setattr(
        google_sheets,
        "get_locations_mapping",
        lambda cfg=None: {"Gym": GYM, "Other": OTHER_GYM},
    )
    monkeypatch.setattr(
        google_sheets,
        "get_exercises_mapping",
        lambda cfg=None: {"Bench Press": BENCH, "Crunch": CRUNCH},
    )

    def set_rows(*rows):
        sheet = FakeWorksheet([WORKOUT_HEADER, *rows])
        monkeypatch.setattr(google_sheets, "get_workouts", lambda cfg=None: sheet)

    return set_rows


class TestLoadWorkouts:
    """Test building the sets of a session out of the sheet."""

    def test_a_single_set_is_loaded(self, workouts_sheet):
        workouts_sheet(
            workout_row(
                location="Gym",
                workout_time="2026-08-07T14:30:00",
                exercise="Bench Press",
                index="1",
                weight_kg="50",
                repetitions="10",
            )
        )

        (workout,) = google_sheets.load_workouts_from_sheet(cfg=None)

        assert workout.exercise_id == BENCH
        assert workout.index == 1
        assert workout.repetitions == 10
        assert workout.weight_kg == 50.0

    def test_blank_columns_are_inherited_from_the_row_above(self, workouts_sheet):
        """Only the first row of a session repeats the location and the time."""
        workouts_sheet(
            workout_row(
                location="Gym",
                workout_time="2026-08-07T14:30:00",
                exercise="Bench Press",
                index="1",
                weight_kg="50",
                repetitions="10",
            ),
            workout_row(weight_kg="55", repetitions="8"),
            workout_row(weight_kg="60", repetitions="6"),
        )

        workouts = google_sheets.load_workouts_from_sheet(cfg=None)

        assert [w.exercise_id for w in workouts] == [BENCH, BENCH, BENCH]
        assert len({w.session_id for w in workouts}) == 1

    def test_sets_are_numbered_within_the_exercise(self, workouts_sheet):
        """The index restarts when a new exercise names itself."""
        workouts_sheet(
            workout_row(
                location="Gym",
                workout_time="2026-08-07T14:30:00",
                exercise="Bench Press",
                index="1",
                weight_kg="50",
                repetitions="10",
            ),
            workout_row(weight_kg="55", repetitions="8"),
            workout_row(exercise="Crunch", index="1", weight_kg="20", repetitions="15"),
            workout_row(weight_kg="25", repetitions="12"),
        )

        workouts = google_sheets.load_workouts_from_sheet(cfg=None)

        assert [w.index for w in workouts] == [1, 2, 1, 2]

    def test_a_blank_row_does_not_shift_the_set_numbering(self, workouts_sheet):
        """A spacer row must not be counted as a set of the exercise above it."""
        workouts_sheet(
            workout_row(
                location="Gym",
                workout_time="2026-08-07T14:30:00",
                exercise="Bench Press",
                index="1",
                weight_kg="50",
                repetitions="10",
            ),
            [""] * len(WORKOUT_HEADER),
            workout_row(weight_kg="55", repetitions="8"),
        )

        workouts = google_sheets.load_workouts_from_sheet(cfg=None)

        assert [w.index for w in workouts] == [1, 2]

    @pytest.mark.parametrize("missing", ["weight_kg", "repetitions"])
    def test_a_row_missing_a_required_value_is_skipped(
        self, workouts_sheet, caplog, missing: str
    ):
        complete = {
            "weight_kg": "50",
            "repetitions": "10",
        }
        incomplete = {**complete, missing: ""}
        workouts_sheet(
            workout_row(
                location="Gym",
                workout_time="2026-08-07T14:30:00",
                exercise="Bench Press",
                index="1",
                **complete,
            ),
            workout_row(**incomplete),
        )

        with caplog.at_level(logging.WARNING):
            workouts = google_sheets.load_workouts_from_sheet(cfg=None)

        assert len(workouts) == 1
        assert "sheet row 3" in caplog.text
        assert missing in caplog.text

    def test_a_column_the_model_does_not_have_is_ignored(self, workouts_sheet):
        """The sheet records a weight in pounds that the database does not hold."""
        workouts_sheet(
            workout_row(
                location="Gym",
                workout_time="2026-08-07T14:30:00",
                exercise="Bench Press",
                index="1",
                weight_kg="12.47",
                repetitions="10",
                weight_lb="27.5",
            )
        )

        (workout,) = google_sheets.load_workouts_from_sheet(cfg=None)

        assert workout.weight_kg == 12.47
        assert not hasattr(workout, "weight_lb")

    def test_a_blank_note_is_null_rather_than_the_string_none(self, workouts_sheet):
        workouts_sheet(
            workout_row(
                location="Gym",
                workout_time="2026-08-07T14:30:00",
                exercise="Bench Press",
                index="1",
                weight_kg="50",
                repetitions="10",
                notes="felt good",
            ),
            workout_row(weight_kg="55", repetitions="8"),
        )

        first, second = google_sheets.load_workouts_from_sheet(cfg=None)

        assert first.notes == "felt good"
        assert second.notes is None

    def test_an_assisted_set_keeps_its_negative_weight(self, workouts_sheet):
        workouts_sheet(
            workout_row(
                location="Gym",
                workout_time="2026-08-07T14:30:00",
                exercise="Bench Press",
                index="1",
                weight_kg="-59",
                repetitions="10",
            )
        )

        (workout,) = google_sheets.load_workouts_from_sheet(cfg=None)

        assert workout.weight_kg == -59.0

    def test_a_typographic_dash_in_the_time_still_parses(self, workouts_sheet):
        """A spreadsheet autocorrects a hyphen into an en dash."""
        workouts_sheet(
            workout_row(
                location="Gym",
                workout_time="2026–08-07T14:30:00",
                exercise="Bench Press",
                index="1",
                weight_kg="50",
                repetitions="10",
            )
        )

        (session,) = google_sheets.load_sessions_from_sheet(cfg=None)

        assert session.workout_time.date() == datetime.date(2026, 8, 7)


class TestWorkoutTimeZone:
    """Test that times typed as UK local time are stored as UTC."""

    def test_british_summer_time_shifts_by_an_hour(self, workouts_sheet):
        workouts_sheet(
            workout_row(
                location="Gym",
                workout_time="2026-08-07T14:30:00",
                exercise="Bench Press",
                index="1",
                weight_kg="50",
                repetitions="10",
            )
        )

        (session,) = google_sheets.load_sessions_from_sheet(cfg=None)

        assert session.workout_time.hour == 13

    def test_greenwich_mean_time_does_not_shift(self, workouts_sheet):
        workouts_sheet(
            workout_row(
                location="Gym",
                workout_time="2026-01-07T14:30:00",
                exercise="Bench Press",
                index="1",
                weight_kg="50",
                repetitions="10",
            )
        )

        (session,) = google_sheets.load_sessions_from_sheet(cfg=None)

        assert session.workout_time.hour == 14


@pytest.fixture
def three_sessions(workouts_sheet):
    """Three sessions across two gyms, in January, March and June."""
    workouts_sheet(
        workout_row(
            location="Gym",
            workout_time="2026-01-05T10:00:00",
            exercise="Bench Press",
            index="1",
            weight_kg="50",
            repetitions="10",
        ),
        workout_row(weight_kg="55", repetitions="8"),
        workout_row(
            location="Other",
            workout_time="2026-03-05T10:00:00",
            exercise="Crunch",
            index="1",
            weight_kg="60",
            repetitions="12",
        ),
        workout_row(
            location="Gym",
            workout_time="2026-06-05T10:00:00",
            exercise="Bench Press",
            index="1",
            weight_kg="70",
            repetitions="6",
        ),
    )


class TestLoadSessions:
    """Test building the sessions the sets belong to."""

    def test_one_session_per_location_and_time(self, three_sessions):
        sessions = google_sheets.load_sessions_from_sheet(cfg=None)

        assert len(sessions) == 3
        assert [s.location_id for s in sessions] == [GYM, OTHER_GYM, GYM]

    def test_the_id_is_derived_from_the_location_and_the_time(self, three_sessions):
        """The backfill derives it the same way, which is what makes re-runs merge."""
        sessions = google_sheets.load_sessions_from_sheet(cfg=None)

        for session in sessions:
            assert session.id == session_id_for(
                location_id=session.location_id, workout_time=session.workout_time
            )

    def test_loading_twice_gives_the_same_ids(self, three_sessions):
        first = google_sheets.load_sessions_from_sheet(cfg=None)
        second = google_sheets.load_sessions_from_sheet(cfg=None)

        assert [s.id for s in first] == [s.id for s in second]

    def test_every_set_points_at_a_loaded_session(self, three_sessions):
        sessions = google_sheets.load_sessions_from_sheet(cfg=None)
        workouts = google_sheets.load_workouts_from_sheet(cfg=None)

        assert {w.session_id for w in workouts} <= {s.id for s in sessions}

    def test_the_sets_of_one_session_share_its_id(self, three_sessions):
        workouts = google_sheets.load_workouts_from_sheet(cfg=None)

        assert workouts[0].session_id == workouts[1].session_id
        assert workouts[0].session_id != workouts[2].session_id


class TestNarrowingTheLoad:
    """Test the date and row ranges, which sessions and sets must agree on."""

    def test_loading_after_a_date(self, three_sessions):
        after = datetime.datetime(2026, 2, 1, tzinfo=datetime.timezone.utc)

        sessions = google_sheets.load_sessions_from_sheet(cfg=None, after=after)
        workouts = google_sheets.load_workouts_from_sheet(cfg=None, after=after)

        assert len(sessions) == 2
        assert len(workouts) == 2

    def test_loading_before_a_date(self, three_sessions):
        before = datetime.datetime(2026, 4, 1, tzinfo=datetime.timezone.utc)

        sessions = google_sheets.load_sessions_from_sheet(cfg=None, before=before)

        assert len(sessions) == 2

    def test_loading_between_two_dates(self, three_sessions):
        sessions = google_sheets.load_sessions_from_sheet(
            cfg=None,
            after=datetime.datetime(2026, 2, 1, tzinfo=datetime.timezone.utc),
            before=datetime.datetime(2026, 4, 1, tzinfo=datetime.timezone.utc),
        )

        assert len(sessions) == 1
        assert sessions[0].location_id == OTHER_GYM

    def test_a_row_range_counts_the_header(self, three_sessions):
        """range_end slices the raw sheet values, where row 1 is the header."""
        workouts = google_sheets.load_workouts_from_sheet(cfg=None, range_end=3)

        assert len(workouts) == 2

    def test_a_narrowed_range_still_inherits_from_the_rows_above(self, three_sessions):
        """Starting partway down must not lose the session carried down to it."""
        workouts = google_sheets.load_workouts_from_sheet(cfg=None, range_start=1)

        assert workouts[0].exercise_id == BENCH
        assert workouts[0].session_id == session_id_for(
            location_id=GYM,
            workout_time=datetime.datetime(
                2026, 1, 5, 10, 0, tzinfo=datetime.timezone.utc
            ),
        )

    def test_a_range_matching_nothing_is_empty(self, three_sessions):
        after = datetime.datetime(2030, 1, 1, tzinfo=datetime.timezone.utc)

        assert google_sheets.load_workouts_from_sheet(cfg=None, after=after) == []
        assert google_sheets.load_sessions_from_sheet(cfg=None, after=after) == []
