import datetime
import uuid
from typing import List, Mapping, Optional

import gspread
import pandas
import pendulum

from src.config import Config
from src.migration_utils.datetime_parsing import (
    clean_datetime_string,
    parse_sheet_datetime,
)
from src.migration_utils.session_ids import session_id_for
from src.migration_utils.sheet_frames import (
    drop_incomplete_workouts,
    drop_unmapped_columns,
    to_frame,
)
from src.models.go_heavier import Exercise, Location, Session, Workout


def _get_worksheet(
    worksheet_id: str | int, cfg: Config = Config()
) -> gspread.Worksheet:
    client: gspread.Client = gspread.service_account(
        filename=cfg.google_service_account_filepath
    )
    spreadsheet: gspread.Spreadsheet = client.open_by_key(cfg.GOOGLE_SPREADSHEET_ID)
    return spreadsheet.get_worksheet_by_id(worksheet_id)


def get_locations(cfg: Config = Config()) -> gspread.Worksheet:
    return _get_worksheet(worksheet_id=0, cfg=cfg)


def get_workouts(cfg: Config = Config()) -> gspread.Worksheet:
    return _get_worksheet(worksheet_id=1003474616, cfg=cfg)


def get_exercises(cfg: Config = Config()) -> gspread.Worksheet:
    return _get_worksheet(worksheet_id=1892058398, cfg=cfg)


def get_locations_mapping(cfg: Config = Config()) -> Mapping[str, uuid.UUID]:
    return {
        location[1]: uuid.UUID(location[0])
        for location in get_locations(cfg=cfg).get_all_values()[1:]
    }


def get_exercises_mapping(cfg: Config = Config()) -> Mapping[str, uuid.UUID]:
    return {
        exercise[1]: uuid.UUID(exercise[0])
        for exercise in _get_worksheet(
            worksheet_id=1892058398, cfg=cfg
        ).get_all_values()[1:]
    }


def load_locations_from_sheet(cfg: Config = Config()) -> List[Location]:
    locations_sheet = get_locations(cfg=cfg)
    locations: List[Location] = []
    data = locations_sheet.get_all_values()
    df = to_frame(data)

    df["id"] = df["id"].map(uuid.UUID)
    df["name"] = df["name"].astype(str)
    df["description"] = df["description"].astype(str)
    df["address_line1"] = df["address_line1"].astype(str)
    df["address_line2"] = df["address_line2"].astype(str)
    df["address_city"] = df["address_city"].astype(str)
    df["address_postal_code"] = df["address_postal_code"].astype(str)
    df["address_country_iso3"] = df["address_country_iso3"].astype(str)
    df["created_at"] = pandas.to_datetime(
        df["created_at"].map(clean_datetime_string)
    ).replace("", None)
    df["updated_at"] = pandas.to_datetime(
        df["updated_at"].map(clean_datetime_string)
    ).replace("", None)

    for row in drop_unmapped_columns(df, Location).to_dict(orient="records"):
        try:
            location = Location(**row)
        except Exception as e:
            print(f"Error creating location: {e}")
            raise
        locations.append(location)

    return locations


def load_exercises_from_sheet(cfg: Config = Config()) -> List[Exercise]:
    exercises_sheet = get_exercises(cfg=cfg)
    exercises: List[Exercise] = []
    data = exercises_sheet.get_all_values()

    df = to_frame(data)

    df["id"] = df["id"].map(uuid.UUID)
    df["bipedal"] = df["bipedal"].astype(bool)
    df["free_weights"] = df["free_weights"].astype(bool)
    df["created_at"] = df["created_at"].apply(parse_sheet_datetime)
    df["updated_at"] = df["updated_at"].apply(parse_sheet_datetime)

    for row in drop_unmapped_columns(df, Exercise).to_dict(orient="records"):
        try:
            exercise = Exercise(**row)
        except Exception as e:
            print(f"Error creating exercise: {e}")
            raise
        exercises.append(exercise)

    return exercises


def _workout_frame(
    cfg: Config,
    range_start: int,
    range_end: Optional[int],
    after: Optional[datetime.datetime],
    before: Optional[datetime.datetime],
) -> pandas.DataFrame:
    """The workouts sheet, forward filled, narrowed and validated.

    Both the sessions and the sets are built from this, so that they cannot
    disagree about which rows are in range.
    """
    locations_mapping = get_locations_mapping(cfg=cfg)
    exercise_mapping = get_exercises_mapping(cfg=cfg)
    data = get_workouts(cfg=cfg).get_all_values()

    df = to_frame(data, blanks_as_none=True)
    df["location"] = df["location"].map(locations_mapping)
    df["exercise"] = df["exercise"].map(exercise_mapping)

    df["index"] = pandas.to_numeric(df["index"], errors="coerce")

    df["location"] = df["location"].ffill()
    df["exercise"] = df["exercise"].ffill()
    df["workout_time"] = df["workout_time"].ffill()
    df["index"] = (
        df["index"].ffill() + df.groupby(df["index"].notna().cumsum()).cumcount()
    )

    # Parse workout times as UK local time (Europe/London), then convert to UTC
    # This automatically handles British Summer Time (BST) and GMT
    df["workout_time"] = df["workout_time"].apply(
        lambda x: parse_sheet_datetime(x, tz="Europe/London").in_tz("UTC")
    )

    df = df.iloc[range_start : None if range_end is None else max(range_end - 1, 0)]
    if after is not None:
        df = df[df["workout_time"] >= after]
    if before is not None:
        df = df[df["workout_time"] <= before]

    df = drop_incomplete_workouts(df.copy())

    # The sheet has no session id, so derive a stable one from the pair that
    # identifies a session. The same pair gives the same id on every run.
    df["session_id"] = [
        session_id_for(location_id=location, workout_time=workout_time)
        for location, workout_time in zip(df["location"], df["workout_time"])
    ]

    return df


def load_sessions_from_sheet(
    cfg: Config = Config(),
    range_start: int = 0,
    range_end: Optional[int] = None,
    after: Optional[datetime.datetime] = None,
    before: Optional[datetime.datetime] = None,
) -> List[Session]:
    """One session per location and time in the workouts sheet."""
    df = _workout_frame(cfg, range_start, range_end, after, before)

    sessions_frame = df[["session_id", "location", "workout_time"]].drop_duplicates(
        subset="session_id"
    )

    now = pendulum.now("UTC")
    return [
        Session(
            id=row["session_id"],
            location_id=row["location"],
            workout_time=row["workout_time"],
            created_at=now,
            updated_at=now,
        )
        for row in sessions_frame.to_dict(orient="records")
    ]


def load_workouts_from_sheet(
    cfg: Config = Config(),
    range_start: int = 0,
    range_end: Optional[int] = None,
    after: Optional[datetime.datetime] = None,
    before: Optional[datetime.datetime] = None,
) -> List[Workout]:
    """Load the sets from the sheet.

    ``range_start``/``range_end`` slice the sheet rows the same way as the raw
    sheet values, so ``range_end`` counts the header row. ``after``/``before``
    filter on the workout time. The sessions these sets belong to come from
    ``load_sessions_from_sheet`` and must be merged first.
    """
    df = _workout_frame(cfg, range_start, range_end, after, before)
    workouts: List[Workout] = []

    df["index"] = df["index"].astype(int)
    df["weight_kg"] = df["weight_kg"].astype(float)
    df["repetitions"] = df["repetitions"].astype(int)
    df["bar_weight_kg"] = df["bar_weight_kg"].astype(float)
    df["supplementary_weight_kg"] = df["supplementary_weight_kg"].astype(float)
    # Blank cells are None by this point. astype(str) would write them as the
    # literal "None", and Series.map coerces None back to NaN, so build the
    # column from a list to keep the blanks null.
    df["notes"] = pandas.Series(
        [None if pandas.isna(note) else str(note) for note in df["notes"]],
        index=df.index,
        dtype=object,
    )

    df["created_at"] = pendulum.now("UTC")
    df["updated_at"] = pendulum.now("UTC")

    df = drop_unmapped_columns(df, Workout)

    for row in df.to_dict(orient="records"):
        try:
            workout = Workout(**row)
        except Exception as e:
            print(f"Error creating workout: {e}")
            raise
        workouts.append(workout)

    return workouts
