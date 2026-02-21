import datetime
import uuid
from typing import List, Mapping

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

    for idx, row in enumerate(workouts_sheet.get_all_values()[1:]):
        row: List[str]
        location_id = locations_mapping[row[1]] if row[1] else None
        exercise_id = exercise_mapping[row[2]] if row[2] else None
        if idx == 0:  # first row
            workout = Workout(
                id=uuid.uuid4(),
                location_id=location_id,
                exercise_id=exercise_id,
                workout_time=pendulum.instance(
                    datetime.datetime.fromisoformat(row[3]).replace(
                        tzinfo=datetime.timezone.utc
                    )
                ),
                index=int(row[4]),
                weight_kg=float(row[5]),
                repetitions=int(row[6]),
                bar_weight_kg=float(row[7]) if row[7] else None,
                created_at=pendulum.now(),
                updated_at=pendulum.now(),
            )
        else:  # allow for using previous value for certain fields
            workout = Workout(
                id=uuid.uuid4(),
                location_id=location_id or workouts[-1].location_id,
                exercise_id=exercise_id or workouts[-1].exercise_id,
                workout_time=pendulum.instance(
                    datetime.datetime.fromisoformat(row[3]).replace(
                        tzinfo=datetime.timezone.utc
                    )
                )
                if row[3]
                else workouts[-1].workout_time,
                index=int(row[4]),
                weight_kg=float(row[5]),
                repetitions=int(row[6]),
                bar_weight_kg=float(row[7]) if row[7] else None,
                created_at=pendulum.now(),
                updated_at=pendulum.now(),
            )
        workouts.append(workout)

    return workouts
