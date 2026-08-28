from typing import Any, Dict

from fastapi import APIRouter, Depends

from src.common import IsoCountryCode, MuscleGroup, SpecificMuscle
from src.resolvers.users import require_viewer

router = APIRouter(tags=["default"])


@router.get("/config", dependencies=[Depends(require_viewer)])
def get_config() -> Dict[str, Any]:
    """Valid values for the enum-like fields used elsewhere in the API."""
    return {
        "default": {"IsoCountryCode": [country.value for country in IsoCountryCode]},
        "go-heavier": {
            "MuscleGroup": [group.value for group in MuscleGroup],
            "SpecificMuscle": [group.value for group in SpecificMuscle],
        },
    }
