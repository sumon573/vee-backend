"""
User ORM model — core identity record for the Vee platform.

Every authenticated user has exactly one row in the `users` table.
The `firebase_uid` column is the authoritative link to Firebase Authentication.

Architecture:
    - Inherits UUIDMixin  → provides `id` (UUID v4 primary key)
    - Inherits TimestampMixin → provides `created_at` and `updated_at`
    - Inherits Base       → registers with SQLAlchemy metadata for Alembic

Adding relationships (future phases):
    - Phase 5: followers / following (self-referential many-to-many)
    - Phase 6: voice_room_memberships
    - Phase 7: audio_stories
    - Phase 8: messages
"""

import uuid
from datetime import date, datetime
from typing import Optional

from sqlalchemy import Boolean, Date, DateTime, Enum as SAEnum, String, Text, Index
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.mixins import TimestampMixin, UUIDMixin
from app.models.enums import Gender


class User(UUIDMixin, TimestampMixin, Base):
    """
    Platform user identity and public profile.

    Primary key : id           (UUID v4 — from UUIDMixin)
    External key: firebase_uid (Firebase Authentication UID)
    Audit times : created_at, updated_at (from TimestampMixin)
    """

    __tablename__ = "users"

    __table_args__ = (
        # Composite index for profile look-ups by active status
        Index("ix_users_is_active_created_at", "is_active", "created_at"),
    )

    # ------------------------------------------------------------------
    # Identity
    # ------------------------------------------------------------------

    firebase_uid: Mapped[str] = mapped_column(
        String(128),
        unique=True,
        nullable=False,
        index=True,
        doc="Firebase Authentication UID — stable external identifier.",
    )

    # ------------------------------------------------------------------
    # Public profile
    # ------------------------------------------------------------------

    username: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
        doc="URL-safe unique handle chosen by the user (e.g. @alice).",
    )

    display_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        doc="Friendly display name shown in the UI.",
    )

    email: Mapped[Optional[str]] = mapped_column(
        String(255),
        unique=True,
        nullable=True,
        index=True,
        doc="Email address — nullable; not all users authenticate via email.",
    )

    phone: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
        doc="E.164 phone number — nullable; not all users authenticate via phone.",
    )

    avatar_url: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        doc="URL to the user's profile picture (stored in MinIO/S3 in Phase 7).",
    )

    bio: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        doc="Short user bio shown on the profile page.",
    )

    # ------------------------------------------------------------------
    # Demographics (optional, user-controlled)
    # ------------------------------------------------------------------

    gender: Mapped[Optional[Gender]] = mapped_column(
        SAEnum(Gender, name="gender_enum", create_type=True),
        nullable=True,
        doc="Self-declared gender identity.",
    )

    birth_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
        doc="Date of birth — used for age verification, never exposed publicly.",
    )

    # ------------------------------------------------------------------
    # Account status
    # ------------------------------------------------------------------

    is_verified: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
        doc="True once the user has completed phone/email verification.",
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true",
        doc="False if the account is suspended or soft-deleted.",
    )

    # ------------------------------------------------------------------
    # Presence
    # ------------------------------------------------------------------

    last_seen_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="UTC timestamp of the user's most recent authenticated request.",
    )

    # ------------------------------------------------------------------
    # Dunder
    # ------------------------------------------------------------------

    def __repr__(self) -> str:
        return (
            f"<User id={self.id!s} username={self.username!r} "
            f"firebase_uid={self.firebase_uid!r}>"
        )
