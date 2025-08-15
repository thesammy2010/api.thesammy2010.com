import logging
import uuid
from typing import Annotated, List, Optional

from fastapi import APIRouter, HTTPException, Response

from src.models.go_heavier.location import Location as DBLocation
from src.resolvers.go_heavier import locations
from src.schemas.go_heavier.locations import LocationRequest, LocationResponse

router = APIRouter(prefix="/go-heavier", tags=["go-heavier"])


@router.get("/locations", response_model=List[LocationResponse])
def get_locations() -> List[DBLocation]:
    return locations.get_locations()


@router.get("/locations/{location_id}", response_model=Optional[LocationResponse])
async def get_location(location_id: Annotated[str, uuid.UUID]) -> Optional[DBLocation]:
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


@router.post("/locations", response_model=LocationResponse)
async def create_location(location: LocationRequest) -> Optional[DBLocation]:
    try:
        new_location = locations.create_location(location)
        return new_location
    except Exception as e:
        logging.error(f"Error creating location: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.put("/locations/{location_id}", response_model=LocationResponse)
async def update_location(
    location_id: Annotated[str, uuid.UUID],
    location: LocationRequest,
) -> Optional[DBLocation]:
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


@router.delete("/locations/{location_id}")
def delete_location(location_id: Annotated[str, uuid.UUID]) -> Response:
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
