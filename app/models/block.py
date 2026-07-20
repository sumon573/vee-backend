"""
Block ORM model — one-directional privacy shield (blocker → blocked).

Architecture:
    - Inherits UUIDMixin → provides `id` (UUID v4 primary key)
    - Does NOT use TimestampMixin — block edges are immutable after creation;
      only `created_at` is needed.
    - Self-block is prevented at the DB level via a CHECK constraint
      (belt-and-suspenders alongside the service-layer guard).
    - Duplicate blocks are prevented via a UNIQUE constraint on
      (blocker_id, blocked_id).
    - Both FK columns cascade DELETE so removing a user automatically
      removes all their block edges.

Indexes:
    ix_blocks_blocker_id  — accelerates "list all users that user X has blocked"
    ix_blocks_blocked_id  — accelerates "list all users that have blocked user X"
    ix_blocks_created_at  — accelerates chronological list queries
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


class Block(UUIDMixin, Base):
    """
    One-directional block relationship between two platform users.

    Primary key : id          (UUID v4 — from UUIDMixin)
    Participants: blocker_id  (the user who initiated the block)
                  blocked_id  (the user who is blocked)
    Audit time  : created_at  (server-generated on INSERT)
    """

    __tablename__ = "blocks"

    __table_args__ = (
        # Prevent duplicate blocks at the DB level
        UniqueConstraint(
            "blocker_id",
            "blocked_id",
            name="uq_blocks_blocker_blocked",
        ),
        # Prevent self-blocks at the DB level
        CheckConstraint(
            "blocker_id != blocked_id",
            name="ck_blocks_no_self_block",
        ),
        # Accelerates: "list everyone user X has blocked"
        Index("ix_blocks_blocker_id", "blocker_id"),
        # Accelerates: "list everyone who has blocked user X"
        Index("ix_blocks_blocked_id", "blocked_id"),
        # Accelerates: chronological ordering in list queries
        Index("ix_blocks_created_at", "created_at"),
    )

    # ------------------------------------------------------------------
    # Participants
    # ------------------------------------------------------------------

    blocker_id: Mapped[uuid.UUID] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        doc="UUID of the user who initiated the block.",
    )

    blocked_id: Mapped[uuid.UUID] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        doc="UUID of the user who is blocked.",
    )

    # ------------------------------------------------------------------
    # Audit
    # ------------------------------------------------------------------

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        doc="UTC timestamp when the block was created (set by DB server).",
    )

    # ------------------------------------------------------------------
    # Dunder
    # ------------------------------------------------------------------

    def __repr__(self) -> str:
        return (
            f"<Block id={self.id!s} "
            f"blocker_id={self.blocker_id!s} "
            f"blocked_id={self.blocked_id!s}>"
        )
