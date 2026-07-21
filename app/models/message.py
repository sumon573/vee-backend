"""
Message ORM model — individual message within a Conversation.

Architecture:
    - Inherits UUIDMixin      → provides `id` (UUID v4 primary key)
    - Inherits TimestampMixin → provides `created_at` and `updated_at`
    - Soft delete via `is_deleted` flag — content is NULLed on delete to
      free storage while preserving the message envelope for ordering.

Design notes:
    - `message_type` uses the MessageType enum; currently only TEXT is supported.
      Future phases can add AUDIO, IMAGE, etc. without a migration break.
    - `is_deleted` is a soft-delete flag; deleted messages are excluded from
      list queries by default.
    - sender_id FK cascades DELETE — if a user is hard-deleted the message
      row is also removed (however, the platform uses soft-delete for users
      so in practice the row is retained).

Indexes:
    ix_messages_conversation_id  — accelerates list_messages() queries
    ix_messages_sender_id        — accelerates "all messages sent by user X"
    ix_messages_created_at       — accelerates chronological ordering
"""

import uuid
from typing import Optional

from sqlalchemy import Boolean, Enum as SAEnum, ForeignKey, Index, Text
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.mixins import TimestampMixin, UUIDMixin
from app.models.enums import MessageType


class Message(UUIDMixin, TimestampMixin, Base):
    """
    A single message within a one-to-one Conversation.

    Primary key    : id              (UUID v4 — from UUIDMixin)
    Parent         : conversation_id (FK → conversations.id CASCADE DELETE)
    Author         : sender_id       (FK → users.id CASCADE DELETE)
    Audit times    : created_at, updated_at (from TimestampMixin)
    Soft delete    : is_deleted flag; deleted content is set to NULL
    """

    __tablename__ = "messages"

    __table_args__ = (
        # Accelerates: list_messages(conversation_id, ...) — most common query
        Index("ix_messages_conversation_id", "conversation_id"),
        # Accelerates: "all messages sent by user X"
        Index("ix_messages_sender_id", "sender_id"),
        # Accelerates: chronological ordering in conversation view
        Index("ix_messages_created_at", "created_at"),
    )

    # ------------------------------------------------------------------
    # Relationships
    # ------------------------------------------------------------------

    conversation_id: Mapped[uuid.UUID] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
        doc="FK → conversations.id; which conversation this message belongs to.",
    )

    sender_id: Mapped[uuid.UUID] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        doc="FK → users.id; the user who sent the message.",
    )

    # ------------------------------------------------------------------
    # Content
    # ------------------------------------------------------------------

    content: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        doc=(
            "Message body text. Nullable — set to NULL when the message is "
            "soft-deleted to free storage while retaining the message envelope."
        ),
    )

    message_type: Mapped[MessageType] = mapped_column(
        SAEnum(MessageType, name="message_type_enum", create_type=True),
        nullable=False,
        default=MessageType.TEXT,
        server_default=MessageType.TEXT.value,
        doc="Message content type. Currently only TEXT; future: AUDIO, IMAGE.",
    )

    # ------------------------------------------------------------------
    # Soft delete
    # ------------------------------------------------------------------

    is_deleted: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
        doc=(
            "True if the sender soft-deleted this message. "
            "Content is set to NULL on delete. "
            "The message row is retained for conversation ordering continuity."
        ),
    )

    # ------------------------------------------------------------------
    # Relationships (lazy — loaded only when explicitly needed)
    # ------------------------------------------------------------------

    sender: Mapped["User"] = relationship("User", lazy="noload")  # noqa: F821

    # ------------------------------------------------------------------
    # Dunder
    # ------------------------------------------------------------------

    def __repr__(self) -> str:
        return (
            f"<Message id={self.id!s} "
            f"conversation_id={self.conversation_id!s} "
            f"sender_id={self.sender_id!s} "
            f"type={self.message_type.value!r} "
            f"deleted={self.is_deleted}>"
        )
