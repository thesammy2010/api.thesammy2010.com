import logging
import uuid
from typing import Annotated, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Response

from src.models.go_heavier.location import Location as DBLocation
from src.resolvers.go_heavier import locations
from src.resolvers.users import require_editor, require_viewer
from src.schemas.go_heavier.location_stats import (
    LocationStatsRequest,
    LocationStatsResponse,
)
from src.schemas.go_heavier.locations import LocationRequest, LocationResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/go-heavier", tags=["locations"])


@router.get(
    "/locations",
    response_model=List[LocationResponse],
    dependencies=[Depends(require_viewer)],
)
def get_locations() -> List[DBLocation]:
    """Every tracked location."""
    return locations.get_locations()


@router.get(
    "/locations/{location_id}",
    response_model=Optional[LocationResponse],
    dependencies=[Depends(require_viewer)],
)
async def get_location(location_id: Annotated[str, uuid.UUID]) -> Optional[DBLocation]:
    """A single location by id."""
    try:
        location_uuid = uuid.UUID(location_id)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail={"detail": "Invalid format for location id"},
        )
    location = locations.get_location(location_uuid)
    if not location:
        raise HTTPException(status_code=404, detail="Location not found")
    return location


@router.get(
    "/locations/{location_id}/stats",
    response_model=LocationStatsResponse,
    dependencies=[Depends(require_viewer)],
)
async def get_location_stats(
    location_id: Annotated[str, uuid.UUID],
    request: Annotated[LocationStatsRequest, Query()],
) -> LocationStatsResponse:
    """Aggregates a location's workout history.

    A visit is one distinct `workout_time`, since every set logged in a
    session shares that session's timestamp. `total_volume_kg` is the sum
    of `weight_kg * repetitions` (bar/supplementary weight excluded).
    `average_exercises_per_visit` is averaged across visits, not
    `distinct_exercises` divided by `visits`.
    """
    try:
        location_uuid = uuid.UUID(location_id)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail={"detail": "Invalid format for location id"},
        )
    stats = locations.get_location_stats(location_id=location_uuid, request=request)
    if not stats:
        raise HTTPException(status_code=404, detail="Location not found")
    return stats


@router.post(
    "/locations",
    response_model=LocationResponse,
    dependencies=[Depends(require_editor)],
)
async def create_location(location: LocationRequest) -> Optional[DBLocation]:
    """Creates a location."""
    try:
        new_location = locations.create_location(location)
        return new_location
    except Exception as e:
        logger.error(f"Error creating location: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.put(
    "/locations/{location_id}",
    response_model=LocationResponse,
    dependencies=[Depends(require_editor)],
)
async def update_location(
    location_id: Annotated[str, uuid.UUID],
    location: LocationRequest,
) -> Optional[DBLocation]:
    """Replaces a location's fields."""
    try:
        location_uuid = uuid.UUID(location_id)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail={"detail": "Invalid format for location id"},
        )
    updated_location = locations.update_location(
        location_id=location_uuid, location=location
    )
    if not updated_location:
        raise HTTPException(status_code=404, detail="Location not found")
    return updated_location


@router.delete(
    "/locations/{location_id}",
    status_code=204,
    dependencies=[Depends(require_editor)],
)
def delete_location(location_id: Annotated[str, uuid.UUID]) -> Response:
    """Deletes a location."""
    try:
        location_uuid = uuid.UUID(location_id)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail={"detail": "Invalid format for location id"},
        )
    if not locations.delete_location(location_uuid):
        raise HTTPException(status_code=404, detail="Location not found")
    return Response(status_code=204)
