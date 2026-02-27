import datetime
import uuid
from typing import Dict, List, Mapping

import gspread
import pendulum

from src.config import Config
from src.models.go_heavier import Workout


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


def get_workout_from_sheet(cfg: Config = Config()) -> List[Workout]:
    locations_mapping = get_locations_mapping(cfg=cfg)
    exercise_mapping = get_exercises_mapping(cfg=cfg)
    workouts_sheet = get_workouts(cfg=cfg)
    workouts: List[Workout] = []
    header: List[str] = workouts_sheet.get_all_values()[0]

    for idx, line in enumerate(workouts_sheet.get_all_values()[1:]):
        row: Dict[str, str] = dict(zip(header, line))
        id_ = uuid.UUID(row["id"]) if row["id"] else uuid.uuid4()
        location_id = locations_mapping[row["location"]] if row["location"] else None
        exercise_id = exercise_mapping[row["exercise"]] if row["exercise"] else None

        if idx == 0:  # first row
            workout = Workout(
                id=id_,
                location_id=location_id,
                exercise_id=exercise_id,
                workout_time=pendulum.instance(
                    datetime.datetime.fromisoformat(row["workout_time"]).replace(
                        tzinfo=datetime.timezone.utc
                    )
                ),
                index=int(row["index"]),
                weight_kg=float(row["weight_kg"]),
                repetitions=int(row["repetitions"]),
                bar_weight_kg=float(row["bar_weight_kg"])
                if row["bar_weight_kg"]
                else None,
                supplementary_weight_kg=float(row["supplementary_weight_kg"])
                if row["supplementary_weight_kg"]
                else None,
                notes=row["notes"] or None,
                created_at=pendulum.now(),
                updated_at=pendulum.now(),
            )
        else:  # allow for using previous value for certain fields
            workout = Workout(
                id=id_,
                location_id=location_id or workouts[-1].location_id,
                exercise_id=exercise_id or workouts[-1].exercise_id,
                workout_time=pendulum.instance(
                    datetime.datetime.fromisoformat(row["workout_time"]).replace(
                        tzinfo=datetime.timezone.utc
                    )
                )
                if row["workout_time"]
                else workouts[-1].workout_time,
                index=int(row["index"]) if row["index"] else workouts[-1].index + 1,
                weight_kg=float(row["weight_kg"]),
                repetitions=int(row["repetitions"]),
                bar_weight_kg=float(row["bar_weight_kg"])
                if row["bar_weight_kg"]
                else None,
                supplementary_weight_kg=float(row["supplementary_weight_kg"])
                if row["supplementary_weight_kg"]
                else None,
                notes=row["notes"] or None,
                created_at=pendulum.now(),
                updated_at=pendulum.now(),
            )
        workouts.append(workout)

    return workouts
