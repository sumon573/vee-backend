"""
Pydantic v2 schemas for Block request / response DTOs.

Schemas:
    BlockRead        — representation of a block record (for internal use / confirm)
    BlockedUserRead  — public user card embedded in the blocked-list response
    BlockedListResponse — paginated list of blocked users

Rules:
    - Never import SQLAlchemy models or db sessions here.
    - Use `model_config = ConfigDict(...)` — not inner Config class.
"""

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


# ---------------------------------------------------------------------------
# Block record
# ---------------------------------------------------------------------------


class BlockRead(BaseModel):
    """Representation of a block relationship record."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    blocker_id: uuid.UUID
    blocked_id: uuid.UUID
    created_at: datetime


# ---------------------------------------------------------------------------
# User card inside the blocked-list response
# ---------------------------------------------------------------------------


class BlockedUserRead(BaseModel):
    """
    Minimal public user profile returned inside the blocked-users list.

    Excludes all private fields.
    """

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    username: str
    display_name: str
    avatar_url: Optional[str] = None
    bio: Optional[str] = None
    is_verified: bool
    blocked_at: datetime  # when the current user blocked this person


# ---------------------------------------------------------------------------
# Paginated list response
# ---------------------------------------------------------------------------


class BlockedListResponse(BaseModel):
    """Paginated response for GET /api/v1/users/blocked."""

    total: int
    skip: int
    limit: int
    items: list[BlockedUserRead]
