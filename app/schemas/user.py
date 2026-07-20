"""
Pydantic v2 schemas for User request / response DTOs.

Naming convention:
    UserBase         — shared fields (no ID, no audit fields)
    UserRead         — full representation returned to the authenticated user (own profile)
    UserPublicRead   — public representation returned for other users' profiles
    UserCreate       — internal creation payload (not exposed directly via HTTP)
    UserUpdate       — partial update payload for PATCH /users/me
    UserDeletedRead  — minimal response after a soft-delete

Validation:
    - Username: 3–30 chars, lowercase alphanumeric + underscore only (^[a-z0-9_]{3,30}$)
    - Reserved usernames are rejected at the schema layer
    - Bio: max 500 chars
    - Display name: 1–100 chars

Rules:
    - Never import SQLAlchemy models or db sessions here.
    - Use `model_config = ConfigDict(...)` — not inner Config class.
"""

import re
import uuid
from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.enums import Gender

# ---------------------------------------------------------------------------
# Username validation
# ---------------------------------------------------------------------------

_USERNAME_REGEX = re.compile(r"^[a-z0-9_]{3,30}$")

# Usernames that are reserved for platform use and cannot be claimed by users.
RESERVED_USERNAMES: frozenset[str] = frozenset(
    {
        "admin",
        "administrator",
        "api",
        "root",
        "system",
        "support",
        "help",
        "info",
        "mail",
        "email",
        "contact",
        "abuse",
        "security",
        "privacy",
        "legal",
        "terms",
        "vee",
        "veeapp",
        "veeofficial",
        "official",
        "staff",
        "mod",
        "moderator",
        "superuser",
        "bot",
        "robot",
        "null",
        "undefined",
        "anonymous",
        "guest",
        "user",
        "users",
        "account",
        "accounts",
        "profile",
        "profiles",
        "settings",
        "dashboard",
        "home",
        "login",
        "logout",
        "signin",
        "signout",
        "signup",
        "register",
        "registration",
        "password",
        "forgot",
        "reset",
        "verify",
        "verification",
        "notification",
        "notifications",
        "message",
        "messages",
        "chat",
        "follow",
        "followers",
        "following",
        "block",
        "blocked",
        "report",
        "explore",
        "search",
        "discover",
        "trending",
        "live",
        "audio",
        "voice",
        "room",
        "rooms",
        "story",
        "stories",
        "wallet",
        "payment",
        "payments",
        "about",
        "team",
        "press",
        "jobs",
        "careers",
        "blog",
        "news",
        "faq",
        "docs",
        "documentation",
        "developer",
        "developers",
        "app",
        "mobile",
        "ios",
        "android",
        "web",
        "download",
        "test",
        "demo",
        "example",
        "sample",
        "delete",
        "deleted",
    }
)


def _validate_username(value: str) -> str:
    """
    Enforce username format rules.

    Raises:
        ValueError: if the username fails regex or is reserved.
    """
    # Normalise to lowercase before validation
    normalized = value.lower()
    if not _USERNAME_REGEX.match(normalized):
        raise ValueError(
            "Username must be 3–30 characters and contain only lowercase "
            "letters (a–z), digits (0–9), or underscores (_)."
        )
    if normalized in RESERVED_USERNAMES:
        raise ValueError(
            f"'{normalized}' is a reserved username and cannot be used."
        )
    return normalized


# ---------------------------------------------------------------------------
# Base
# ---------------------------------------------------------------------------


class UserBase(BaseModel):
    """Fields shared across User schemas."""

    username: str = Field(..., min_length=3, max_length=30)
    display_name: str = Field(..., min_length=1, max_length=100)
    email: Optional[str] = Field(default=None, max_length=255)
    phone: Optional[str] = Field(default=None, max_length=20)
    avatar_url: Optional[str] = Field(default=None)
    bio: Optional[str] = Field(default=None, max_length=500)
    gender: Optional[Gender] = Field(default=None)
    birth_date: Optional[date] = Field(default=None)

    @field_validator("username", mode="before")
    @classmethod
    def validate_username(cls, v: str) -> str:
        return _validate_username(v)


# ---------------------------------------------------------------------------
# Read — own full profile (authenticated user)
# ---------------------------------------------------------------------------


class UserRead(UserBase):
    """
    Full user representation returned to the authenticated owner of the profile.

    Includes private fields (email, phone, birth_date, is_verified, deleted_at).
    ORM instances can be passed directly thanks to `from_attributes=True`.
    """

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    firebase_uid: str
    is_verified: bool
    is_active: bool
    deleted_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    last_seen_at: Optional[datetime] = None


# ---------------------------------------------------------------------------
# Public Read — another user's profile (unauthenticated or third-party)
# ---------------------------------------------------------------------------


class UserPublicRead(BaseModel):
    """
    Public representation of a user profile.

    Excludes: firebase_uid, email, phone, birth_date, deleted_at.
    Returned from GET /api/v1/users/{username}.
    """

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    username: str
    display_name: str
    avatar_url: Optional[str] = None
    bio: Optional[str] = None
    gender: Optional[Gender] = None
    is_verified: bool
    created_at: datetime
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
# Update (partial — PATCH /users/me)
# ---------------------------------------------------------------------------


class UserUpdate(BaseModel):
    """
    Partial update payload for the authenticated user's own profile.

    All fields are optional — only provided fields are applied.
    Username changes are subject to availability and reserved-name checks.
    """

    model_config = ConfigDict(from_attributes=True)

    username: Optional[str] = Field(default=None, min_length=3, max_length=30)
    display_name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    avatar_url: Optional[str] = Field(default=None)
    bio: Optional[str] = Field(default=None, max_length=500)
    gender: Optional[Gender] = Field(default=None)
    birth_date: Optional[date] = Field(default=None)

    @field_validator("username", mode="before")
    @classmethod
    def validate_username(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        return _validate_username(v)


# ---------------------------------------------------------------------------
# Deleted — confirmation response after soft-delete
# ---------------------------------------------------------------------------


class UserDeletedRead(BaseModel):
    """Minimal confirmation payload returned after a soft-delete request."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    username: str
    deleted_at: datetime
    message: str = "Account has been deactivated successfully."
