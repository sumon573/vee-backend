"""
User profile routes — /api/v1/users/

Endpoints:
    GET    /api/v1/users/me            — return the authenticated user's full profile
    PATCH  /api/v1/users/me            — update the authenticated user's profile fields
    DELETE /api/v1/users/me            — soft-delete the authenticated user's account
    GET    /api/v1/users/{username}    — return a public user profile by username

Architecture:
    - Delegates all business logic to UserService.
    - Returns Pydantic response schemas; never returns raw ORM objects.
    - Domain exceptions are caught by FastAPI exception handlers in main.py.
    - Protected endpoints use the get_current_user dependency from Phase 5.
"""

import logging

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.user import User
from app.schemas.user import UserDeletedRead, UserPublicRead, UserRead, UserUpdate
from app.services.auth.dependencies import get_current_user
from app.services.user_service import UserService

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/users",
    tags=["users"],
)


# ---------------------------------------------------------------------------
# GET /api/v1/users/me
# ---------------------------------------------------------------------------


@router.get(
    "/me",
    response_model=UserRead,
    status_code=status.HTTP_200_OK,
    summary="Get the authenticated user's full profile",
    description=(
        "Protected endpoint. Requires `Authorization: Bearer <firebase_id_token>`. "
        "Returns the complete profile of the currently authenticated user, including "
        "private fields such as email, phone, birth_date, and deleted_at."
    ),
)
async def get_me(
    current_user: User = Depends(get_current_user),
) -> UserRead:
    """
    Return the authenticated caller's own profile.

    Uses the `get_current_user` dependency which handles token verification,
    user sync, and presence update automatically.
    """
    return UserRead.model_validate(current_user)


# ---------------------------------------------------------------------------
# PATCH /api/v1/users/me
# ---------------------------------------------------------------------------


@router.patch(
    "/me",
    response_model=UserRead,
    status_code=status.HTTP_200_OK,
    summary="Update the authenticated user's profile",
    description=(
        "Protected endpoint. Requires `Authorization: Bearer <firebase_id_token>`. "
        "Partial update — only include fields you want to change. "
        "Username changes are validated for format, reserved names, and uniqueness."
    ),
)
async def update_me(
    update_data: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> UserRead:
    """
    Partially update the authenticated caller's own profile.

    Accepted fields: username, display_name, avatar_url, bio, gender, birth_date.
    Any fields omitted from the request body are left unchanged.

    Errors:
        422 reserved_username  — attempted username is reserved
        409 username_conflict  — attempted username is already taken
        401 / 403             — standard auth failures
    """
    user_service = UserService(db)
    updated_user = await user_service.update_my_profile(current_user, update_data)
    return UserRead.model_validate(updated_user)


# ---------------------------------------------------------------------------
# DELETE /api/v1/users/me
# ---------------------------------------------------------------------------


@router.delete(
    "/me",
    response_model=UserDeletedRead,
    status_code=status.HTTP_200_OK,
    summary="Soft-delete the authenticated user's account",
    description=(
        "Protected endpoint. Requires `Authorization: Bearer <firebase_id_token>`. "
        "Marks the account as deleted (sets deleted_at, is_active=False). "
        "The account is NOT permanently removed — data is retained for integrity."
    ),
)
async def delete_me(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> UserDeletedRead:
    """
    Soft-delete the authenticated caller's own account.

    After this call:
    - The account's `is_active` is set to False.
    - The account's `deleted_at` is set to the current UTC timestamp.
    - Further authenticated requests from this Firebase token will be rejected.

    This action is reversible by an administrator.
    """
    user_service = UserService(db)
    deleted_user = await user_service.soft_delete_user(current_user)
    return UserDeletedRead.model_validate(deleted_user)


# ---------------------------------------------------------------------------
# GET /api/v1/users/{username}
# ---------------------------------------------------------------------------


@router.get(
    "/{username}",
    response_model=UserPublicRead,
    status_code=status.HTTP_200_OK,
    summary="Get a public user profile by username",
    description=(
        "Public endpoint — no authentication required. "
        "Returns the public profile of the user with the given username. "
        "Private fields (email, phone, birth_date, firebase_uid) are excluded."
    ),
)
async def get_user_by_username(
    username: str,
    db: AsyncSession = Depends(get_db),
) -> UserPublicRead:
    """
    Return the public profile for any active user by username.

    Errors:
        404 user_not_found — no active user with that username exists
    """
    user_service = UserService(db)
    user = await user_service.get_by_username(username)
    return UserPublicRead.model_validate(user)
