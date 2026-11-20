from typing import Annotated, List

from fastapi import APIRouter, Depends, HTTPException, Path, Response

from src.models.device import Device
from src.models.user import User
from src.resolvers import devices
from src.resolvers.users import provision_current_user
from src.schemas.devices import DeviceRequest, DeviceResponse

# For anyone signed in: what they're told about is up to the features they
# can use, so registering a phone needs no particular role.
router = APIRouter(tags=["devices"])


@router.post("/devices", response_model=DeviceResponse)
def register_device(
    user: Annotated[User, Depends(provision_current_user)], request: DeviceRequest
) -> Device:
    """Registers the caller's phone for notifications. Send it on every
    launch and whenever the token changes; one already registered is
    refreshed, and moves to the caller if it was signed in as someone else."""
    return devices.register_device(user, request)


@router.get("/devices", response_model=List[DeviceResponse])
def get_devices(
    user: Annotated[User, Depends(provision_current_user)],
) -> List[Device]:
    """The caller's registered phones, oldest first."""
    return devices.get_devices(user)


@router.delete("/devices/{token}", status_code=204)
def unregister_device(
    user: Annotated[User, Depends(provision_current_user)],
    token: Annotated[str, Path(pattern=r"^[0-9a-fA-F]{64,200}$")],
) -> Response:
    """Stops notifications to one of the caller's phones, such as when
    they sign out on it. 404 if it isn't one of theirs."""
    if not devices.unregister_device(user, token):
        raise HTTPException(status_code=404, detail="Device not found")
    return Response(status_code=204)
