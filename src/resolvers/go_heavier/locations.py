import datetime
import uuid
from typing import List, Optional

from fastapi import HTTPException

from src.db import session
from src.models.go_heavier.location import Location as DBLocation
from src.schemas.go_heavier.locations import LocationRequest


def get_location(location_id: uuid.UUID) -> Optional[DBLocation]:
    return session.query(DBLocation).filter(DBLocation.id == location_id).first()


def get_locations() -> List[DBLocation]:
    return session.query(DBLocation).all()


def update_location(
    location_id: uuid.UUID, location: LocationRequest
) -> Optional[DBLocation]:
    db_location = get_location(location_id)
    if not location:
        raise HTTPException(status_code=404, detail="Location not found")

    for field, value in location.model_dump().items():
        if value is not None:
            setattr(db_location, field, value)

    db_location.updated_at = datetime.datetime.now(tz=datetime.timezone.utc)

    session.commit()
    return db_location


def create_location(location: LocationRequest) -> DBLocation:
    new_location = DBLocation(
        id=uuid.uuid4(),
        name=location.name,
        description=location.description,
        address_line1=location.address_line1,
        address_line2=location.address_line2,
        address_city=location.address_city,
        address_country_iso3=location.address_country_iso3,
        created_at=datetime.datetime.now(tz=datetime.timezone.utc),
        updated_at=datetime.datetime.now(tz=datetime.timezone.utc),
    )
    session.add(new_location)
    session.commit()
    return new_location


def delete_location(location_id: uuid.UUID) -> bool:
    location = get_location(location_id)
    if not location:
        return False
    session.delete(location)
    session.commit()
    return True
