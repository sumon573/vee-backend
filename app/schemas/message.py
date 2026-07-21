"""
Pydantic schemas for Direct Messaging (Phase 9).

Schema hierarchy:
    ConversationCreate       — request body to start/get a conversation
    ParticipantRead          — embedded participant info in ConversationRead
    ConversationRead         — response for a single conversation
    ConversationListResponse — paginated list of conversations
    MessageCreate            — request body to send a message
    MessageRead              — response for a single message
    MessageListResponse      — paginated list of messages in a conversation

Design rules (per ARCHITECTURE.md):
    - Pure Pydantic v2 models; no SQLAlchemy imports.
    - Naming: <Resource>Create, <Resource>Read, <Resource>ListResponse.
    - model_config = ConfigDict(from_attributes=True) for ORM → schema conversion.
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import MessageType


# ---------------------------------------------------------------------------
# Participants
# ---------------------------------------------------------------------------


class ParticipantRead(BaseModel):
    """
    Minimal public profile of a conversation participant.

    Excludes private fields (email, phone, birth_date, firebase_uid).
    Mirrors the shape of UserPublicRead for consistency.
    """

    id: uuid.UUID
    username: str
    display_name: str
    avatar_url: str | None = None
    is_verified: bool

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# Conversations
# ---------------------------------------------------------------------------


class ConversationCreate(BaseModel):
    """
    Request body for POST /api/v1/messages/conversations.

    The caller supplies the recipient's username.  The service layer resolves
    the user, enforces business rules, and returns the existing or newly
    created conversation.
    """

    recipient_username: str = Field(
        ...,
        min_length=3,
        max_length=30,
        description="Username of the user to start a conversation with.",
    )


class ConversationRead(BaseModel):
    """
    Response schema for a single one-to-one conversation.

    `other_participant` is populated by the service layer (not directly from
    ORM attributes) by finding the participant whose user_id differs from
    the requesting user's id.
    """

    id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    other_participant: ParticipantRead

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def from_orm_for_viewer(
        cls,
        conversation: object,
        viewer_id: uuid.UUID,
    ) -> "ConversationRead":
        """
        Build a ConversationRead by identifying the other participant.

        Args:
            conversation: Conversation ORM instance with participants loaded.
            viewer_id:    UUID of the requesting user (excluded from result).

        Returns:
            ConversationRead with other_participant populated.
        """
        other = next(
            p for p in conversation.participants if p.user_id != viewer_id  # type: ignore[attr-defined]
        )
        return cls(
            id=conversation.id,  # type: ignore[attr-defined]
            created_at=conversation.created_at,  # type: ignore[attr-defined]
            updated_at=conversation.updated_at,  # type: ignore[attr-defined]
            other_participant=ParticipantRead.model_validate(other.user),
        )


class ConversationListResponse(BaseModel):
    """Response schema for GET /api/v1/messages/conversations."""

    conversations: list[ConversationRead]
    total: int


# ---------------------------------------------------------------------------
# Messages
# ---------------------------------------------------------------------------


class MessageCreate(BaseModel):
    """Request body for POST /api/v1/messages/{conversation_id}."""

    content: str = Field(
        ...,
        min_length=1,
        max_length=4000,
        description="Message text content (1–4000 characters).",
    )


class MessageRead(BaseModel):
    """Response schema for a single message."""

    id: uuid.UUID
    conversation_id: uuid.UUID
    sender_id: uuid.UUID
    content: str | None
    message_type: MessageType
    is_deleted: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MessageListResponse(BaseModel):
    """
    Response schema for GET /api/v1/messages/{conversation_id}.

    Messages are returned newest-first (descending created_at).
    Use `offset` for pagination.
    """

    messages: list[MessageRead]
    total: int
    limit: int
    offset: int
