"""
Follow ORM model — directed social graph edge (follower → following).

Architecture:
    - Inherits UUIDMixin → provides `id` (UUID v4 primary key)
    - Does NOT use TimestampMixin — only `created_at` is needed; follow
      relationships are immutable after creation.
    - Self-follow is blocked at the DB level via a CHECK constraint
      (belt-and-suspenders alongside the service-layer guard).
    - Duplicate follow is blocked via UNIQUE constraint on
      (follower_id, following_id).
    - Both FK columns cascade DELETE so that removing a user automatically
      removes all their follow edges.

Indexes:
    ix_follows_follower_id  — accelerates "who does user X follow?"
    ix_follows_following_id — accelerates "who follows user X?"
    ix_follows_created_at   — accelerates chronological list queries
"""

import uuid
from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.mixins import UUIDMixin


class Follow(UUIDMixin, Base):
    """
    Directed follow relationship between two platform users.

    Primary key : id           (UUID v4 — from UUIDMixin)
    Participants: follower_id  (the user who initiated the follow)
                  following_id (the user being followed)
    Audit time  : created_at  (server-generated on INSERT)
    """

    __tablename__ = "follows"

    __table_args__ = (
        # Prevent duplicate follows at the DB level
        UniqueConstraint(
            "follower_id",
            "following_id",
            name="uq_follows_follower_following",
        ),
        # Prevent self-follows at the DB level
        CheckConstraint(
            "follower_id != following_id",
            name="ck_follows_no_self_follow",
        ),
        # Accelerates: "list everyone user X follows"
        Index("ix_follows_follower_id", "follower_id"),
        # Accelerates: "list everyone who follows user X"
        Index("ix_follows_following_id", "following_id"),
        # Accelerates: chronological ordering in list queries
        Index("ix_follows_created_at", "created_at"),
    )

    # ------------------------------------------------------------------
    # Participants
    # ------------------------------------------------------------------

    follower_id: Mapped[uuid.UUID] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        doc="UUID of the user who is following (the initiator).",
    )

    following_id: Mapped[uuid.UUID] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        doc="UUID of the user being followed (the target).",
    )

    # ------------------------------------------------------------------
    # Audit
    # ------------------------------------------------------------------

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        doc="UTC timestamp when the follow relationship was created (set by DB server).",
    )

    # ------------------------------------------------------------------
    # Dunder
    # ------------------------------------------------------------------

    def __repr__(self) -> str:
        return (
            f"<Follow id={self.id!s} "
            f"follower_id={self.follower_id!s} "
            f"following_id={self.following_id!s}>"
        )
