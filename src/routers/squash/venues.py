import uuid
from typing import Annotated, List

from fastapi import APIRouter, Depends, HTTPException, Query

from src.models.squash import Venue as DBVenue
from src.resolvers.squash import venues
from src.resolvers.squash.players import (
    Conflict,
    require_squash_admin,
    require_squash_player,
)
from src.routers.squash import parse_uuid
from src.schemas.squash.venues import VenueRequest, VenueResponse

router = APIRouter(
    prefix="/squash",
    tags=["squash venues"],
    dependencies=[Depends(require_squash_player)],
)


@router.get("/venues", response_model=List[VenueResponse])
def get_venues(
    include_inactive: Annotated[bool, Query()] = False,
) -> List[DBVenue]:
    """Where the group plays, by name."""
    return venues.get_venues(include_inactive=include_inactive)


@router.get("/venues/{venue_id}", response_model=VenueResponse)
def get_venue(venue_id: Annotated[str, uuid.UUID]) -> DBVenue:
    venue = venues.get_venue(parse_uuid(venue_id, "venue"))
    if not venue:
        raise HTTPException(status_code=404, detail="Venue not found")
    return venue


@router.post(
    "/venues",
    response_model=VenueResponse,
    dependencies=[Depends(require_squash_admin)],
)
def create_venue(venue: VenueRequest) -> DBVenue:
    """Adds somewhere the group plays. Admin-only. 409 if one already has the
    name, ignoring case."""
    try:
        return venues.create_venue(venue)
    except Conflict as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.put(
    "/venues/{venue_id}",
    response_model=VenueResponse,
    dependencies=[Depends(require_squash_admin)],
)
def update_venue(venue_id: Annotated[str, uuid.UUID], venue: VenueRequest) -> DBVenue:
    """Replaces a venue's fields, such as to stop offering it once the group
    no longer plays there. Admin-only."""
    try:
        updated = venues.update_venue(parse_uuid(venue_id, "venue"), venue)
    except Conflict as e:
        raise HTTPException(status_code=409, detail=str(e))
    if not updated:
        raise HTTPException(status_code=404, detail="Venue not found")
    return updated
