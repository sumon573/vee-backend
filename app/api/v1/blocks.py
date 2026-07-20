"""
Block / Privacy routes — /api/v1/users/

Endpoints:
    POST   /api/v1/users/{username}/block  — block a user (auth required)
    DELETE /api/v1/users/{username}/block  — unblock a user (auth required)
    GET    /api/v1/users/blocked           — list users the caller has blocked

Architecture:
    - All business logic delegated to BlockService.
    - Domain exceptions caught by FastAPI exception handlers in main.py.
    - Protected endpoints use get_current_user from app.services.auth.dependencies.

IMPORTANT — Router include order:
    This router must be included in app/api/v1/__init__.py BEFORE the users router
    so that GET /users/blocked is matched before GET /users/{username}.
"""

import logging

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.user import User
from app.schemas.block import BlockedListResponse, BlockRead
from app.services.auth.dependencies import get_current_user
from app.services.block_service import BlockService

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/users",
    tags=["blocks"],
)


# ---------------------------------------------------------------------------
# GET /api/v1/users/blocked
# ---------------------------------------------------------------------------
# NOTE: This static route MUST be declared before /{username}/block routes so
# FastAPI matches "blocked" as a literal path segment, not a {username} value.
# Include this router before the users router in app/api/v1/__init__.py.
# ---------------------------------------------------------------------------


@router.get(
    "/blocked",
    response_model=BlockedListResponse,
    status_code=status.HTTP_200_OK,
    summary="List users the authenticated caller has blocked",
    description=(
        "Protected endpoint. Requires `Authorization: Bearer <firebase_id_token>`. "
        "Returns a paginated list of users that the authenticated caller has blocked, "
        "ordered newest-block-first."
    ),
)
async def list_blocked_users(
    skip: int = Query(default=0, ge=0, description="Pagination offset"),
    limit: int = Query(default=20, ge=1, le=100, description="Page size"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> BlockedListResponse:
    """
    Return a paginated list of all users the authenticated caller has blocked.

    Errors:
        401 / 403 — standard auth failures
    """
    block_service = BlockService(db)
    return await block_service.get_blocked_users(
        current_user, skip=skip, limit=limit
    )


# ---------------------------------------------------------------------------
# POST /api/v1/users/{username}/block
# ---------------------------------------------------------------------------


@router.post(
    "/{username}/block",
    response_model=BlockRead,
    status_code=status.HTTP_201_CREATED,
    summary="Block a user",
    description=(
        "Protected endpoint. Requires `Authorization: Bearer <firebase_id_token>`. "
        "Blocks the specified user. Any existing follow relationship between the "
        "two users is automatically removed in both directions."
    ),
)
async def block_user(
    username: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> BlockRead:
    """
    Block the user identified by `username`.

    Side effects:
    - Any follow relationship (in either direction) between the caller and
      the target is automatically removed.

    Errors:
        400 self_block       — cannot block yourself
        404 user_not_found   — no active user with that username
        409 already_blocked  — this user is already blocked
        401 / 403            — standard auth failures
    """
    block_service = BlockService(db)
    block = await block_service.block_user(current_user, username)
    return BlockRead.model_validate(block)


# ---------------------------------------------------------------------------
# DELETE /api/v1/users/{username}/block
# ---------------------------------------------------------------------------


@router.delete(
    "/{username}/block",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Unblock a user",
    description=(
        "Protected endpoint. Requires `Authorization: Bearer <firebase_id_token>`. "
        "Removes the block on the specified user. "
        "Does not restore any previously removed follow relationships."
    ),
)
async def unblock_user(
    username: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """
    Unblock the user identified by `username`.

    Note: Unblocking does not restore any follow relationships that were
    removed when the block was placed.

    Errors:
        404 user_not_found — no active user with that username
        409 not_blocked    — this user is not currently blocked
        401 / 403          — standard auth failures
    """
    block_service = BlockService(db)
    await block_service.unblock_user(current_user, username)
