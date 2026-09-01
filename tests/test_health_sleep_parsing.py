import datetime

from src.routers.health import parse_sleep_summary

FULL_SUMMARY = (
    "1 Sep 2026 at 01:45-1 Sep 2026 at 09:06\n"
    "Total Time Asleep:7.22 hours\n"
    "\n"
    "Awake for 1 hours and 17 minutes\n"
    "Core for 2 hours and 47 minutes\n"
    "Deep for 0 hours and 58 minutes\n"
    "REM for 2 hours and 11 minutes"
)


class TestParseSleepSummary:
    """Test parsing Shortcuts' free-text summary of a Sleep Analysis sample."""

    def test_bed_time_and_wake_time_are_read_as_uk_local_and_converted_to_utc(self):
        """01:45 BST (UTC+1) becomes 00:45 UTC."""
        result = parse_sleep_summary(FULL_SUMMARY)

        assert result["bed_time"] == datetime.datetime(
            2026, 9, 1, 0, 45, tzinfo=datetime.timezone.utc
        )
        assert result["wake_time"] == datetime.datetime(
            2026, 9, 1, 8, 6, tzinfo=datetime.timezone.utc
        )

    def test_total_asleep_hours_is_parsed(self):
        assert parse_sleep_summary(FULL_SUMMARY)["sleep_hours"] == 7.22

    def test_every_stage_is_converted_to_minutes(self):
        assert parse_sleep_summary(FULL_SUMMARY)["stages_minutes"] == {
            "Awake": 77,
            "Core": 167,
            "Deep": 58,
            "REM": 131,
        }

    def test_a_missing_stage_is_simply_absent_rather_than_failing(self):
        without_rem = FULL_SUMMARY.replace("\nREM for 2 hours and 11 minutes", "")

        assert "REM" not in parse_sleep_summary(without_rem)["stages_minutes"]

    def test_unparseable_text_returns_all_none_rather_than_raising(self):
        result = parse_sleep_summary("not a sleep summary at all")

        assert result["bed_time"] is None
        assert result["wake_time"] is None
        assert result["sleep_hours"] is None
        assert result["stages_minutes"] == {}
