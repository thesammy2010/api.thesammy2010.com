from typing import Any, Dict

from fastapi import APIRouter, Depends

from src.common import IsoCountryCode, MuscleGroup, SpecificMuscle
from src.dependencies.auth import require_role
from src.models.user import Role, User

router = APIRouter(tags=["default"])


@router.get("/config")
def get_config(user: User = Depends(require_role(Role.none))) -> Dict[str, Any]:
    return {
        "default": {"IsoCountryCode": [country.value for country in IsoCountryCode]},
        "go-heavier": {
            "MuscleGroup": [group.value for group in MuscleGroup],
            "SpecificMuscle": [group.value for group in SpecificMuscle],
        },
    }
