"""
Pydantic v2 schemas for User request / response DTOs.

Naming convention:
    UserBase    — shared fields (no ID, no audit fields)
    UserRead    — full public representation returned to clients
    UserCreate  — internal creation payload (not exposed directly via HTTP yet)
    UserUpdate  — partial update payload (future profile-edit endpoint)

Rules:
    - Never import SQLAlchemy models or db sessions here.
    - Use `model_config = ConfigDict(...)` — not inner Config class.
"""

import uuid
from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import Gender


# ---------------------------------------------------------------------------
# Base
# ---------------------------------------------------------------------------


class UserBase(BaseModel):
    """Fields shared across User schemas."""

    username: str = Field(..., min_length=3, max_length=50)
    display_name: str = Field(..., min_length=1, max_length=100)
    email: Optional[str] = Field(default=None, max_length=255)
    phone: Optional[str] = Field(default=None, max_length=20)
    avatar_url: Optional[str] = Field(default=None)
    bio: Optional[str] = Field(default=None, max_length=500)
    gender: Optional[Gender] = Field(default=None)
    birth_date: Optional[date] = Field(default=None)


# ---------------------------------------------------------------------------
# Read (response)
# ---------------------------------------------------------------------------


class UserRead(UserBase):
    """
    Full user representation returned to API clients.

    ORM instances can be passed directly thanks to `from_attributes=True`.
    """

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    firebase_uid: str
    is_verified: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime
    last_seen_at: Optional[datetime] = None


# ---------------------------------------------------------------------------
# Create (internal)
# ---------------------------------------------------------------------------


class UserCreate(UserBase):
    """
    Internal payload for creating a new user record.

    Not exposed as an HTTP request body directly — the API layer
    constructs this from verified Firebase token data.
    """

    firebase_uid: str = Field(..., min_length=1, max_length=128)


# ---------------------------------------------------------------------------
# Update (partial, future)
# ---------------------------------------------------------------------------


class UserUpdate(BaseModel):
    """
    Partial update payload for profile-edit endpoint (future Phase 5).

    All fields are optional — only provided fields are applied.
    """

    model_config = ConfigDict(from_attributes=True)

    display_name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    avatar_url: Optional[str] = Field(default=None)
    bio: Optional[str] = Field(default=None, max_length=500)
    gender: Optional[Gender] = Field(default=None)
    birth_date: Optional[date] = Field(default=None)
