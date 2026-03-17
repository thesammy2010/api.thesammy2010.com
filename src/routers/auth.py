from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from google.auth.exceptions import GoogleAuthError

from src.common import decode_token
from src.dependencies.auth import require_role
from src.models.user import Role, User
from src.resolvers.users import create_user_in_db, get_current_user, update_user
from src.schemas.auth import UpdateUserRequest, UserResponse

router = APIRouter(prefix="/auth", tags=["auth"])
_bearer = HTTPBearer()


@router.post(
    "/login",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    description="Login with Google ID token",
)
def post_login(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer),
) -> UserResponse:
    try:
        if user := get_current_user(token=credentials.credentials):
            return UserResponse(
                id=user.id, google_account_id=user.google_account_id, role=user.role
            )

        user = create_user_in_db(decode_token(credentials.credentials))
        return UserResponse(
            id=user.id, google_account_id=user.google_account_id, role=user.role
        )
    except GoogleAuthError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid Google ID token: {e}",
        )


@router.get("/me", response_model=UserResponse, status_code=status.HTTP_200_OK)
def get_me(user: User = Depends(require_role(Role.none))) -> UserResponse:
    return UserResponse(
        id=user.id, google_account_id=user.google_account_id, role=user.role
    )


@router.put(
    "/user",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    description="Update a user's role",
)
def put_user(
    request: UpdateUserRequest, user: User = Depends(require_role(Role.admin))
) -> Optional[UserResponse]:
    user = update_user(request=request)
    return UserResponse(
        id=user.id, google_account_id=user.google_account_id, role=user.role
    )
