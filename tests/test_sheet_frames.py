import logging

import pandas
import pytest

from src.migration_utils.sheet_frames import (
    SHEET_ROW,
    drop_incomplete_workouts,
    drop_unmapped_columns,
    to_frame,
)
from src.models.go_heavier import Workout

HEADER = ["id", "name", "weight_kg", "weight_lb"]


class TestToFrame:
    """Test building a frame from raw sheet values."""

    def test_sheet_rows_are_numbered_from_two(self):
        """Row 1 is the header, so the first record is row 2 in the sheet."""
        df = to_frame([HEADER, ["a", "Bench", "20", ""], ["b", "Squat", "40", ""]])

        assert list(df[SHEET_ROW]) == [2, 3]

    def test_blank_rows_are_dropped(self):
        """A spreadsheet accumulates blank spacer and trailing rows."""
        df = to_frame(
            [
                HEADER,
                ["a", "Bench", "20", ""],
                ["", "", "", ""],
                ["b", "Squat", "40", ""],
                ["  ", "", " ", ""],
            ]
        )

        assert list(df[SHEET_ROW]) == [2, 4]

    def test_a_row_with_only_an_id_is_kept(self):
        """Only a completely empty row is structural; a stray id is a real gap."""
        df = to_frame([HEADER, ["a", "", "", ""]])

        assert list(df[SHEET_ROW]) == [2]

    def test_blanks_are_left_alone_by_default(self):
        """A caller casting with astype(str) would turn None into "None"."""
        df = to_frame([HEADER, ["a", "", "20", ""]])

        assert df["name"].iloc[0] == ""

    def test_blanks_become_missing_when_asked(self):
        """Blank becomes a pandas missing value, which ffill and isna understand."""
        df = to_frame([HEADER, ["a", "", "20", ""]], blanks_as_none=True)

        assert pandas.isna(df["name"].iloc[0])

    def test_an_empty_sheet_gives_an_empty_frame(self):
        assert to_frame([HEADER]).empty


class TestDropUnmappedColumns:
    """Test discarding sheet columns the model does not have."""

    def test_unmapped_columns_are_dropped(self):
        """The sheet grows columns, such as a weight recorded in pounds."""
        df = pandas.DataFrame(
            [{"weight_kg": 20.0, "weight_lb": 44.0, SHEET_ROW: 2, "repetitions": 10}]
        )

        remaining = drop_unmapped_columns(df, Workout)

        assert set(remaining.columns) == {"weight_kg", "repetitions"}

    def test_mapped_columns_are_kept_in_place(self):
        df = pandas.DataFrame([{"weight_kg": 20.0, "repetitions": 10}])

        assert list(drop_unmapped_columns(df, Workout).columns) == [
            "weight_kg",
            "repetitions",
        ]


class TestDropIncompleteWorkouts:
    """Test rejecting workout rows that are missing a required value."""

    @staticmethod
    def _frame(*overrides) -> pandas.DataFrame:
        rows = []
        for i, override in enumerate(overrides):
            row = {
                "location": "gym",
                "exercise": "bench",
                "workout_time": "2026-08-07",
                "index": 1.0,
                "repetitions": 10.0,
                "weight_kg": 20.0,
                SHEET_ROW: i + 2,
            }
            row.update(override)
            rows.append(row)
        return pandas.DataFrame(rows)

    def test_complete_rows_are_kept(self):
        df = self._frame({}, {})

        assert len(drop_incomplete_workouts(df)) == 2

    @pytest.mark.parametrize(
        "column",
        ["location", "exercise", "workout_time", "index", "repetitions", "weight_kg"],
    )
    def test_a_row_missing_any_required_value_is_dropped(self, column: str):
        df = self._frame({}, {column: None})

        remaining = drop_incomplete_workouts(df)

        assert list(remaining[SHEET_ROW]) == [2]

    def test_the_skipped_row_is_named_in_the_warning(self, caplog):
        """The sheet row is logged so the gap can be found and filled in."""
        df = self._frame({}, {"weight_kg": None, "repetitions": None})

        with caplog.at_level(logging.WARNING):
            drop_incomplete_workouts(df)

        assert "sheet row 3" in caplog.text
        assert "repetitions, weight_kg" in caplog.text

    def test_a_zero_weight_is_not_treated_as_missing(self):
        """Bodyweight exercises are logged at 0kg and are perfectly valid."""
        df = self._frame({"weight_kg": 0.0})

        assert len(drop_incomplete_workouts(df)) == 1
