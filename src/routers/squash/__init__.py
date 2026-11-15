import uuid

from fastapi import HTTPException


def parse_uuid(value: str, label: str) -> uuid.UUID:
    try:
        return uuid.UUID(value)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail={"detail": f"Invalid format for {label} id"},
        )
