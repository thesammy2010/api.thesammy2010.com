"""The phones each user gets notifications on."""

import datetime
from typing import List

from src.db import session
from src.models.device import Device
from src.models.user import User
from src.schemas.devices import DeviceRequest


def register_device(user: User, request: DeviceRequest) -> Device:
    """Records the phone for the user, or refreshes it if it's already
    known. A token registered to someone else moves to this user: it's the
    same install, now signed in as them."""
    fields = {
        "user_id": user.id,
        "app": request.app,
        "environment": request.environment.value,
        "last_registered_at": datetime.datetime.now(),
    }
    device = session.query(Device).filter(Device.token == request.token).one_or_none()
    if device is None:
        # Added whole, so a flush can't send it half filled in
        device = Device(token=request.token, **fields)
        session.add(device)
    else:
        for field, value in fields.items():
            setattr(device, field, value)
    session.commit()
    return device


def get_devices(user: User) -> List[Device]:
    return (
        session.query(Device)
        .filter(Device.user_id == user.id)
        .order_by(Device.created_at)
        .all()
    )


def unregister_device(user: User, token: str) -> bool:
    """Forgets one of the user's phones, such as on signing out. False if
    it isn't one of theirs."""
    device = (
        session.query(Device)
        .filter(Device.token == token.lower(), Device.user_id == user.id)
        .one_or_none()
    )
    if device is None:
        return False
    session.delete(device)
    session.commit()
    return True
