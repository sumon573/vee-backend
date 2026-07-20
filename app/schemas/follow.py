"""
Pydantic v2 schemas for Follow / Social Graph request and response DTOs.

Schemas:
    FollowRead          — response after a successful follow action
    FollowUserRead      — minimal user card returned inside followers/following lists
    FollowListResponse  — paginated list of followers or following users
    RelationshipRead    — mutual relationship status between two users

Rules:
    - Never import SQLAlchemy models or db sessions here.
    - Use `model_config = ConfigDict(...)` — not the inner Config class.
"""

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


# ---------------------------------------------------------------------------
# Follow action response
# ---------------------------------------------------------------------------


class FollowRead(BaseModel):
    """
    Response body returned immediately after a successful POST .../follow.

    Confirms that the follow relationship was created.
    """

    model_config = ConfigDict(from_attributes=True)

    follower_id: uuid.UUID
    following_id: uuid.UUID
    created_at: datetime


# ---------------------------------------------------------------------------
# User card used inside follower / following lists
# ---------------------------------------------------------------------------


class FollowUserRead(BaseModel):
    """
    Minimal public user representation for use inside followers/following lists.

    Deliberately lightweight — callers who need full profile data should use
    GET /api/v1/users/{username}.
    """

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    username: str
    display_name: str
    avatar_url: Optional[str] = None
    bio: Optional[str] = None
    is_verified: bool


# ---------------------------------------------------------------------------
# Paginated list response
# ---------------------------------------------------------------------------


class FollowListResponse(BaseModel):
    """Paginated list of followers or following users."""

    users: list[FollowUserRead]
    total: int
    skip: int
    limit: int


# ---------------------------------------------------------------------------
# Relationship status
# ---------------------------------------------------------------------------


class RelationshipRead(BaseModel):
    """
    Mutual relationship status between the authenticated caller and a target user.

    Returned by GET /api/v1/users/{username}/relationship.
    """

    is_following: bool
    is_followed_by: bool
