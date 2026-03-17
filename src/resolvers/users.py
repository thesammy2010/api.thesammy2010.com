import logging
from typing import Dict, Optional

import google.auth.exceptions
from fastapi import HTTPException, status

from src.common import decode_token
from src.db import session
from src.models.user import User
from src.schemas.auth import UpdateUserRequest


def get_current_user(token: str) -> Optional[User]:
    try:
        claims = decode_token(token)
        return (
            session.query(User).where(User.google_account_id == claims["sub"]).first()
        )

    except google.auth.exceptions.InvalidValue as e:
        logging.error(f"Failed to decode token: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


def create_user_in_db(claims: Dict[str, str]) -> User:
    existing_user = (
        session.query(User).where(User.google_account_id == claims["sub"]).first()
    )
    if not existing_user:
        user = User(google_account_id=claims["sub"])
        session.add(user)
        session.commit()
        session.refresh(user)
        return user
    return existing_user


def update_user(request: UpdateUserRequest) -> User:
    user: Optional[User] = session.query(User).where(User.id == request.id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.role = request.role
    session.query(User).update({"role": user.role})
    session.commit()
    session.refresh(user)

    return user
