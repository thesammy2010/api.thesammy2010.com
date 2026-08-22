import pytest

from src.migration_utils.datetime_parsing import (
    clean_datetime_string,
    parse_sheet_datetime,
)

# A spreadsheet substitutes these for a plain hyphen without showing it.
TYPOGRAPHIC_DASHES = [
    ("hyphen", "2026‐08-07T14:30:00"),
    ("non-breaking hyphen", "2026‑08-07T14:30:00"),
    ("figure dash", "2026‒08-07T14:30:00"),
    ("en dash", "2026–08-07T14:30:00"),
    ("em dash", "2026—08-07T14:30:00"),
    ("horizontal bar", "2026―08-07T14:30:00"),
    ("minus sign", "2026−08-07T14:30:00"),
]
INVISIBLE_SPACES = [
    ("no-break space", "2026-08-07 14:30:00"),
    ("figure space", "2026-08-07 14:30:00"),
    ("narrow no-break space", "2026-08-07 14:30:00"),
]


class TestCleanDatetimeString:
    """Test the normalisation of characters a spreadsheet introduces."""

    @pytest.mark.parametrize("name,value", TYPOGRAPHIC_DASHES, ids=lambda v: str(v))
    def test_dashes_become_hyphens(self, name: str, value: str):
        assert clean_datetime_string(value) == "2026-08-07T14:30:00"

    @pytest.mark.parametrize("name,value", INVISIBLE_SPACES, ids=lambda v: str(v))
    def test_spaces_become_plain_spaces(self, name: str, value: str):
        assert clean_datetime_string(value) == "2026-08-07 14:30:00"

    def test_surrounding_whitespace_is_stripped(self):
        assert clean_datetime_string("  2026-08-07  ") == "2026-08-07"

    def test_a_clean_value_is_untouched(self):
        assert clean_datetime_string("2026-08-07T14:30:00") == "2026-08-07T14:30:00"

    @pytest.mark.parametrize("value", [None, float("nan"), ""])
    def test_missing_values_become_empty(self, value):
        assert clean_datetime_string(value) == ""


class TestParseSheetDatetime:
    """Test parsing of the datetime strings found in the sheet."""

    @pytest.mark.parametrize("name,value", TYPOGRAPHIC_DASHES, ids=lambda v: str(v))
    def test_dashes_are_repaired_before_parsing(self, name: str, value: str):
        parsed = parse_sheet_datetime(value)

        assert (parsed.year, parsed.month, parsed.day) == (2026, 8, 7)
        assert (parsed.hour, parsed.minute) == (14, 30)

    def test_uk_local_time_converts_to_utc(self):
        """Workout times are typed as UK local time, so BST shifts by an hour."""
        parsed = parse_sheet_datetime("2026–08-07T14:30:00", tz="Europe/London").in_tz(
            "UTC"
        )

        assert parsed.hour == 13

    def test_gmt_dates_do_not_shift(self):
        """Outside British Summer Time the local clock already matches UTC."""
        parsed = parse_sheet_datetime("2026-01-07T14:30:00", tz="Europe/London").in_tz(
            "UTC"
        )

        assert parsed.hour == 14

    def test_an_unparseable_cell_names_itself(self):
        """The raw cell is shown so an invisible character is not hidden."""
        with pytest.raises(ValueError, match="not a date"):
            parse_sheet_datetime("not a date")

    def test_the_error_shows_invisible_characters(self):
        with pytest.raises(ValueError) as excinfo:
            parse_sheet_datetime("2026–08-07 the seventh")

        assert "\\u2013" in str(excinfo.value)
