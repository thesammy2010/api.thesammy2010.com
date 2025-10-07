from typing import Any, Dict

from fastapi import APIRouter

from src.common import IsoCountryCode, MuscleGroup, SpecificMuscle

router = APIRouter(tags=["default"])


@router.get("/config")
def get_config() -> Dict[str, Any]:
    return {
        "default": {"IsoCountryCode": [country.value for country in IsoCountryCode]},
        "go-heavier": {
            "MuscleGroup": [group.value for group in MuscleGroup],
            "SpecificMuscle": [group.value for group in SpecificMuscle],
        },
    }
