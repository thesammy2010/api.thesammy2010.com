"""Turning raw Google Sheet values into frames the models can be built from.

Kept free of any database or config import so that it stays unit testable.
"""

import logging
from typing import List

import pandas
import sqlalchemy

logger = logging.getLogger(__name__)

# The sheet row a value came from, tracked so that a rejected row can be named
# in a way that can be found in the spreadsheet. Never passed to a model.
SHEET_ROW = "sheet_row"

# Without any one of these a workout cannot be built: the model requires them
# and pandas cannot cast an empty cell to a number.
REQUIRED_WORKOUT_VALUES = [
    "location",
    "exercise",
    "workout_time",
    "index",
    "repetitions",
    "weight_kg",
]


def to_frame(data: List[List[str]], blanks_as_none: bool = False) -> pandas.DataFrame:
    """Build a frame from raw sheet values, dropping the rows with nothing in them.

    A spreadsheet accumulates blank spacer rows between sessions and blank rows
    off the end of the data. They are not records, and for workouts a blank row
    left in place would inherit the session above it through the forward fill
    and shift the set numbering of the rows below it.

    ``blanks_as_none`` is opt in because a caller that casts a column with
    astype(str) would otherwise turn an empty cell into the string "None".
    """
    df = pandas.DataFrame(data[1:], columns=data[0])
    df[SHEET_ROW] = range(2, len(df) + 2)

    values = df.drop(columns=SHEET_ROW)
    blank = values.map(lambda cell: cell is None or str(cell).strip() == "").all(axis=1)
    if blank.any():
        logger.debug(f"Ignoring {int(blank.sum())} blank sheet rows")
    df = df[~blank].copy()

    return df.replace("", None) if blanks_as_none else df


def drop_unmapped_columns(df: pandas.DataFrame, model) -> pandas.DataFrame:
    """Keep only the columns the model actually has.

    The sheet is edited by hand and grows columns that the database does not
    have, such as a weight recorded in pounds alongside the one in kilograms.
    Passing one of those to a model is a TypeError, so drop them here rather
    than letting a new column break the whole load.
    """
    mapped = {column.key for column in sqlalchemy.inspect(model).mapper.column_attrs}
    unmapped = [column for column in df.columns if column not in mapped]
    if unmapped:
        logger.debug(
            f"Ignoring sheet columns that {model.__name__} does not have: "
            f"{', '.join(unmapped)}"
        )

    return df.drop(columns=unmapped)


def drop_incomplete_workouts(df: pandas.DataFrame) -> pandas.DataFrame:
    """Drop workout rows that are missing a value the model requires.

    Each one is named by its sheet row so the gap can be found and filled in,
    rather than the whole migration failing on the first bad cast.
    """
    incomplete = df[REQUIRED_WORKOUT_VALUES].isna().any(axis=1)
    if not incomplete.any():
        return df

    for row in df[incomplete].to_dict(orient="records"):
        missing = [c for c in REQUIRED_WORKOUT_VALUES if pandas.isna(row[c])]
        logger.warning(
            f"Skipping workouts sheet row {row[SHEET_ROW]}, "
            f"it has no {', '.join(missing)}"
        )

    return df[~incomplete].copy()
