import uuid
from typing import List, Optional

from sqlalchemy import func

from src.db import session
from src.models.squash import Venue as DBVenue
from src.resolvers.squash.players import Conflict
from src.schemas.squash.venues import VenueRequest


def get_venues(include_inactive: bool) -> List[DBVenue]:
    query = session.query(DBVenue)
    if not include_inactive:
        query = query.filter(DBVenue.is_active.is_(True))
    return query.order_by(DBVenue.name, DBVenue.id).all()


def get_venue(venue_id: uuid.UUID) -> Optional[DBVenue]:
    return session.get(DBVenue, venue_id)


def _check_name(venue: VenueRequest, venue_id: Optional[uuid.UUID]) -> None:
    taken = (
        session.query(DBVenue)
        .filter(func.lower(DBVenue.name) == venue.name.lower())
        .one_or_none()
    )
    if taken is not None and taken.id != venue_id:
        raise Conflict(f"{venue.name} is already venue {taken.id}")


def create_venue(venue: VenueRequest) -> DBVenue:
    _check_name(venue, None)
    new_venue = DBVenue(id=uuid.uuid4(), **venue.model_dump())
    session.add(new_venue)
    session.commit()
    return new_venue


def update_venue(venue_id: uuid.UUID, venue: VenueRequest) -> Optional[DBVenue]:
    existing = get_venue(venue_id)
    if not existing:
        return None
    _check_name(venue, venue_id)
    for field, value in venue.model_dump().items():
        setattr(existing, field, value)
    session.commit()
    return existing
