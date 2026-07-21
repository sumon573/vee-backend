"""
Conversation and ConversationParticipant ORM models — Direct Messaging foundation.

Architecture:
    - Conversation: a shared channel between exactly two users.
    - ConversationParticipant: junction table linking a conversation to its participants.
      Uses a composite primary key (conversation_id, user_id) — no separate UUID needed.
    - Participants are loaded with selectin strategy to avoid N+1 on list queries.

Constraints:
    - Exactly two participants per conversation is enforced at the service layer.
    - Duplicate conversations between the same pair are prevented at the service layer
      via get_conversation_between() before create_conversation().
    - CASCADE DELETE on both FK columns removes participants and messages when a
      conversation is deleted.

Indexes:
    ix_conversation_participants_user_id — accelerates "list all conversations for user X"
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, func
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.mixins import TimestampMixin, UUIDMixin


class Conversation(UUIDMixin, TimestampMixin, Base):
    """
    A one-to-one messaging channel between two platform users.

    Primary key  : id          (UUID v4 — from UUIDMixin)
    Audit times  : created_at, updated_at (from TimestampMixin)
    Participants : loaded via ConversationParticipant junction table (selectin)
    """

    __tablename__ = "conversations"

    participants: Mapped[list["ConversationParticipant"]] = relationship(
        "ConversationParticipant",
        lazy="selectin",
        cascade="all, delete-orphan",
    )

    messages: Mapped[list["Message"]] = relationship(  # noqa: F821 — resolved at runtime
        "Message",
        lazy="noload",
        cascade="all, delete-orphan",
        order_by="Message.created_at",
    )

    def __repr__(self) -> str:
        return f"<Conversation id={self.id!s}>"


class ConversationParticipant(Base):
    """
    Junction table: maps a conversation to one of its two participants.

    Primary key  : composite (conversation_id, user_id)
    Relationship : user is eagerly loaded with joined strategy so that
                   ConversationRead.other_participant can be populated without
                   an extra query.
    """

    __tablename__ = "conversation_participants"

    __table_args__ = (
        # Accelerates: "list all conversations for user X"
        Index("ix_conversation_participants_user_id", "user_id"),
    )

    conversation_id: Mapped[uuid.UUID] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey("conversations.id", ondelete="CASCADE"),
        primary_key=True,
        doc="FK → conversations.id; part of composite PK.",
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
        doc="FK → users.id; part of composite PK.",
    )

    joined_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        doc="UTC timestamp when the participant joined the conversation.",
    )

    # Eagerly loaded so ORM objects carry full user data without extra queries
    user: Mapped["User"] = relationship("User", lazy="joined")  # noqa: F821

    def __repr__(self) -> str:
        return (
            f"<ConversationParticipant "
            f"conversation_id={self.conversation_id!s} "
            f"user_id={self.user_id!s}>"
        )
