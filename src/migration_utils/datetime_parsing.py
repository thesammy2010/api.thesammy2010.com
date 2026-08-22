"""Parsing of the datetime strings that come out of the Google Sheet.

Kept free of any database or config import so that it stays unit testable.
"""

import math
from typing import Optional

import pendulum

# A spreadsheet will happily autocorrect a typed hyphen into a typographic dash,
# and pasted values can carry non-breaking spaces. Neither is accepted by any
# date parser, and both are invisible in the cell, so normalise them away.
_CHARACTER_FIXES = str.maketrans(
    {
        "‐": "-",  # hyphen
        "‑": "-",  # non-breaking hyphen
        "‒": "-",  # figure dash
        "–": "-",  # en dash
        "—": "-",  # em dash
        "―": "-",  # horizontal bar
        "−": "-",  # minus sign
        " ": " ",  # no-break space
        " ": " ",  # figure space
        " ": " ",  # narrow no-break space
    }
)


def clean_datetime_string(value) -> str:
    """Normalise the characters a spreadsheet can introduce into a datetime."""
    if value is None:
        return ""
    if isinstance(value, float) and math.isnan(value):
        return ""

    return str(value).translate(_CHARACTER_FIXES).strip()


def parse_sheet_datetime(value, tz: Optional[str] = None) -> pendulum.DateTime:
    """Parse a datetime from the sheet.

    Reports the raw cell if it still cannot be parsed, escaped with ascii() so
    that an invisible character shows up as its code point rather than hiding
    behind an identical looking string.
    """
    cleaned = clean_datetime_string(value)
    try:
        return pendulum.parse(cleaned, tz=tz) if tz else pendulum.parse(cleaned)
    except Exception as e:
        raise ValueError(
            f"Could not parse a datetime from the sheet cell {ascii(value)}: {e}"
        ) from e
