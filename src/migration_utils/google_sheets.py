import uuid
from typing import List, Mapping

import gspread
import pandas
import pendulum

from src.config import Config
from src.models.go_heavier import Exercise, Location, Workout


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
    df = pandas.DataFrame(data[1:], columns=data[0])

    df["id"] = df["id"].map(uuid.UUID)
    df["name"] = df["name"].astype(str)
    df["description"] = df["description"].astype(str)
    df["address_line1"] = df["address_line1"].astype(str)
    df["address_line2"] = df["address_line2"].astype(str)
    df["address_city"] = df["address_city"].astype(str)
    df["address_postal_code"] = df["address_postal_code"].astype(str)
    df["address_country_iso3"] = df["address_country_iso3"].astype(str)
    df["created_at"] = pandas.to_datetime(df["created_at"]).replace("", None)
    df["updated_at"] = pandas.to_datetime(df["updated_at"]).replace("", None)

    for row in df.to_dict(orient="records"):
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

    df = pandas.DataFrame(data[1:], columns=data[0])

    df["id"] = df["id"].map(uuid.UUID)
    df["bipedal"] = df["bipedal"].astype(bool)
    df["free_weights"] = df["free_weights"].astype(bool)
    df["created_at"] = df["created_at"].apply(pendulum.parse)
    df["updated_at"] = df["updated_at"].apply(pendulum.parse)

    for row in df.to_dict(orient="records"):
        try:
            exercise = Exercise(**row)
        except Exception as e:
            print(f"Error creating exercise: {e}")
            raise
        exercises.append(exercise)

    return exercises


def load_workouts_from_sheet(
    cfg: Config = Config(), range_start=0, range_end=100
) -> List[Workout]:
    locations_mapping = get_locations_mapping(cfg=cfg)
    exercise_mapping = get_exercises_mapping(cfg=cfg)
    workouts_sheet = get_workouts(cfg=cfg)
    workouts: List[Workout] = []
    data = workouts_sheet.get_all_values()

    df = pandas.DataFrame(data[1 + range_start : range_end], columns=data[0])
    df = df.replace("", None)
    df["location"] = df["location"].map(locations_mapping)
    df["exercise"] = df["exercise"].map(exercise_mapping)

    df["index"] = pandas.to_numeric(df["index"], errors="coerce")
    df["weight_kg"] = df["weight_kg"].astype(float)
    df["repetitions"] = df["repetitions"].astype(int)
    df["bar_weight_kg"] = df["bar_weight_kg"].astype(float)
    df["supplementary_weight_kg"] = df["supplementary_weight_kg"].astype(float)
    df["notes"] = df["notes"].astype(str)

    df["location"] = df["location"].ffill()
    df["exercise"] = df["exercise"].ffill()
    df["workout_time"] = df["workout_time"].ffill()
    df["index"] = (
        df["index"].ffill() + df.groupby(df["index"].notna().cumsum()).cumcount()
    ).astype(int)

    # Parse workout times as UK local time (Europe/London), then convert to UTC
    # This automatically handles British Summer Time (BST) and GMT
    df["workout_time"] = df["workout_time"].apply(
        lambda x: pendulum.parse(x, tz="Europe/London").in_tz("UTC")
    )

    df["created_at"] = pendulum.now("UTC")
    df["updated_at"] = pendulum.now("UTC")

    df = df.rename({"location": "location_id", "exercise": "exercise_id"}, axis=1)

    for row in df.to_dict(orient="records"):
        try:
            workout = Workout(**row)
        except Exception as e:
            print(f"Error creating workout: {e}")
            raise
        workouts.append(workout)

    return workouts
