"""
Social graph routes — follow/unfollow endpoints mounted under /api/v1/users/.

Endpoints:
    POST   /api/v1/users/{username}/follow       — follow a user
    DELETE /api/v1/users/{username}/follow       — unfollow a user
    GET    /api/v1/users/{username}/followers    — list a user's followers
    GET    /api/v1/users/{username}/following    — list users a user follows
    GET    /api/v1/users/{username}/relationship — mutual relationship status

Architecture:
    - Delegates all business logic to FollowService.
    - Returns Pydantic response schemas; never returns raw ORM objects.
    - Domain exceptions are caught by FastAPI exception handlers in main.py.
    - Protected endpoints use get_current_user dependency (Phase 5).
"""

import logging

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.user import User
from app.schemas.follow import FollowListResponse, FollowRead, FollowUserRead, RelationshipRead
from app.services.auth.dependencies import get_current_user
from app.services.follow_service import FollowService

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/users",
    tags=["follows"],
)


# ---------------------------------------------------------------------------
# POST /api/v1/users/{username}/follow
# ---------------------------------------------------------------------------


@router.post(
    "/{username}/follow",
    response_model=FollowRead,
    status_code=status.HTTP_201_CREATED,
    summary="Follow a user",
    description=(
        "Protected endpoint. Requires `Authorization: Bearer <firebase_id_token>`. "
        "Creates a follow relationship from the authenticated user to the target. "
        "Self-follow and duplicate follows are rejected."
    ),
)
async def follow_user(
    username: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> FollowRead:
    """
    Follow the user identified by `username`.

    Errors:
        400 self_follow        — attempted to follow yourself
        404 user_not_found     — target user does not exist or is deleted
        403 account_inactive   — target account is suspended
        409 already_following  — you already follow this user
        401 / 403              — standard auth failures
    """
    follow_service = FollowService(db)
    follow = await follow_service.follow_user(current_user, username)
    return FollowRead.model_validate(follow)


# ---------------------------------------------------------------------------
# DELETE /api/v1/users/{username}/follow
# ---------------------------------------------------------------------------


@router.delete(
    "/{username}/follow",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Unfollow a user",
    description=(
        "Protected endpoint. Requires `Authorization: Bearer <firebase_id_token>`. "
        "Removes the follow relationship from the authenticated user to the target."
    ),
)
async def unfollow_user(
    username: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """
    Unfollow the user identified by `username`.

    Errors:
        404 user_not_found   — target user does not exist or is deleted
        403 account_inactive — target account is suspended
        409 not_following    — you are not currently following this user
        401 / 403            — standard auth failures
    """
    follow_service = FollowService(db)
    await follow_service.unfollow_user(current_user, username)


# ---------------------------------------------------------------------------
# GET /api/v1/users/{username}/followers
# ---------------------------------------------------------------------------


@router.get(
    "/{username}/followers",
    response_model=FollowListResponse,
    status_code=status.HTTP_200_OK,
    summary="List a user's followers",
    description=(
        "Public endpoint — no authentication required. "
        "Returns a paginated list of users who follow the given username. "
        "Inactive and soft-deleted accounts are excluded from results."
    ),
)
async def list_followers(
    username: str,
    skip: int = Query(default=0, ge=0, description="Number of records to skip."),
    limit: int = Query(default=20, ge=1, le=100, description="Maximum records to return."),
    db: AsyncSession = Depends(get_db),
) -> FollowListResponse:
    """
    Return a paginated list of followers for `username`.

    Errors:
        404 user_not_found   — target user does not exist or is deleted
        403 account_inactive — target account is suspended
    """
    follow_service = FollowService(db)
    users, total = await follow_service.get_followers(username, skip=skip, limit=limit)
    return FollowListResponse(
        users=[FollowUserRead.model_validate(u) for u in users],
        total=total,
        skip=skip,
        limit=limit,
    )


# ---------------------------------------------------------------------------
# GET /api/v1/users/{username}/following
# ---------------------------------------------------------------------------


@router.get(
    "/{username}/following",
    response_model=FollowListResponse,
    status_code=status.HTTP_200_OK,
    summary="List users a user follows",
    description=(
        "Public endpoint — no authentication required. "
        "Returns a paginated list of users that the given username follows. "
        "Inactive and soft-deleted accounts are excluded from results."
    ),
)
async def list_following(
    username: str,
    skip: int = Query(default=0, ge=0, description="Number of records to skip."),
    limit: int = Query(default=20, ge=1, le=100, description="Maximum records to return."),
    db: AsyncSession = Depends(get_db),
) -> FollowListResponse:
    """
    Return a paginated list of users that `username` follows.

    Errors:
        404 user_not_found   — target user does not exist or is deleted
        403 account_inactive — target account is suspended
    """
    follow_service = FollowService(db)
    users, total = await follow_service.get_following(username, skip=skip, limit=limit)
    return FollowListResponse(
        users=[FollowUserRead.model_validate(u) for u in users],
        total=total,
        skip=skip,
        limit=limit,
    )


# ---------------------------------------------------------------------------
# GET /api/v1/users/{username}/relationship
# ---------------------------------------------------------------------------


@router.get(
    "/{username}/relationship",
    response_model=RelationshipRead,
    status_code=status.HTTP_200_OK,
    summary="Get mutual relationship status with a user",
    description=(
        "Protected endpoint. Requires `Authorization: Bearer <firebase_id_token>`. "
        "Returns whether the authenticated user follows the target, and whether "
        "the target follows them back."
    ),
)
async def get_relationship(
    username: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> RelationshipRead:
    """
    Return the mutual follow relationship between the caller and `username`.

    Errors:
        404 user_not_found   — target user does not exist or is deleted
        403 account_inactive — target account is suspended
        401 / 403            — standard auth failures
    """
    follow_service = FollowService(db)
    rel = await follow_service.get_relationship(current_user, username)
    return RelationshipRead(**rel)
