"""
MessageRepository — data access layer for individual messages.

Responsibilities:
    - All SQL for the `messages` table.
    - Returns ORM model instances; raises no business logic exceptions.
    - Pagination via limit/offset is supported on list_messages().
    - Soft delete: mark_deleted() sets is_deleted=True and clears content.

Rules (per ARCHITECTURE.md):
    - No business logic — belongs in MessageService.
    - No HTTP exceptions — callers handle domain errors.
    - Receives AsyncSession via constructor injection.
"""

import logging
import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import MessageType
from app.models.message import Message

logger = logging.getLogger(__name__)


class MessageRepository:
    """Data access layer for the Message model."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # ------------------------------------------------------------------
    # Reads
    # ------------------------------------------------------------------

    async def get_message(self, message_id: uuid.UUID) -> Message | None:
        """
        Fetch a single message by primary key.

        Args:
            message_id: UUID of the message.

        Returns:
            Message ORM instance, or None if not found.
        """
        result = await self._session.execute(
            select(Message).where(Message.id == message_id)
        )
        return result.scalar_one_or_none()

    async def list_messages(
        self,
        conversation_id: uuid.UUID,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Message]:
        """
        List non-deleted messages in a conversation, newest first.

        Pagination is supported via limit and offset.  Deleted messages are
        included in the result but with content=None and is_deleted=True,
        preserving conversation ordering continuity.

        Args:
            conversation_id: UUID of the parent conversation.
            limit:           Maximum number of messages to return (default 50).
            offset:          Number of messages to skip (for pagination).

        Returns:
            List of Message ORM instances ordered by created_at DESC.
        """
        stmt = (
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def count_messages(self, conversation_id: uuid.UUID) -> int:
        """Return total message count for a conversation (including deleted)."""
        stmt = (
            select(func.count())
            .select_from(Message)
            .where(Message.conversation_id == conversation_id)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one()

    # ------------------------------------------------------------------
    # Writes
    # ------------------------------------------------------------------

    async def send_message(
        self,
        conversation_id: uuid.UUID,
        sender_id: uuid.UUID,
        content: str,
        message_type: MessageType = MessageType.TEXT,
    ) -> Message:
        """
        Persist a new message and return the saved instance.

        Args:
            conversation_id: UUID of the target conversation.
            sender_id:       UUID of the sending user.
            content:         Message body text.
            message_type:    Content type (default TEXT).

        Returns:
            Freshly created Message ORM instance.
        """
        message = Message(
            conversation_id=conversation_id,
            sender_id=sender_id,
            content=content,
            message_type=message_type,
            is_deleted=False,
        )
        self._session.add(message)
        await self._session.flush()
        await self._session.refresh(message)

        logger.debug(
            "message_repo.send_message id=%s conversation_id=%s sender_id=%s",
            str(message.id),
            str(conversation_id),
            str(sender_id),
        )
        return message

    async def mark_deleted(
        self,
        message_id: uuid.UUID,
        sender_id: uuid.UUID,
    ) -> Message | None:
        """
        Soft-delete a message sent by sender_id.

        Sets is_deleted=True and clears content to free storage.
        Only the original sender may delete their own message; if the
        message does not exist or belongs to a different sender, returns None.

        Args:
            message_id: UUID of the message to delete.
            sender_id:  UUID of the requesting user (must be the sender).

        Returns:
            Updated Message ORM instance, or None if not found / not authorized.
        """
        result = await self._session.execute(
            select(Message).where(
                Message.id == message_id,
                Message.sender_id == sender_id,
                Message.is_deleted.is_(False),
            )
        )
        message = result.scalar_one_or_none()
        if message is None:
            return None

        message.is_deleted = True
        message.content = None
        await self._session.flush()
        await self._session.refresh(message)

        logger.debug(
            "message_repo.mark_deleted message_id=%s sender_id=%s",
            str(message_id),
            str(sender_id),
        )
        return message
