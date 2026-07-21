"""
MessageService — business logic layer for Direct Messaging (Phase 9).

Business rules enforced here:
    1. A user cannot message themselves.
    2. A user cannot message a blocked or mutually-blocking user (PrivacyGuard).
    3. A user cannot message an inactive (suspended) or soft-deleted user.
    4. A conversation between the same pair cannot be created twice.
    5. Only participants may read or write in a conversation.
    6. Only the original sender may delete a message.

Design (per ARCHITECTURE.md):
    - Stateless: receives AsyncSession from the API dependency.
    - Raises domain exceptions (app/core/exceptions.py) — never HTTPException.
    - Calls ConversationRepository and MessageRepository — no direct SQL.
    - PrivacyGuard used for block enforcement (can_message).
"""

import logging
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    ConversationNotFoundError,
    InactiveUserError,
    MessagePermissionError,
    SelfMessageError,
    UserNotFoundError,
)
from app.models.user import User
from app.repositories.conversation_repo import ConversationRepository
from app.repositories.message_repo import MessageRepository
from app.repositories.user_repo import UserRepository
from app.schemas.message import (
    ConversationListResponse,
    ConversationRead,
    MessageCreate,
    MessageListResponse,
    MessageRead,
)
from app.services.privacy_guard import PrivacyGuard

logger = logging.getLogger(__name__)


class MessageService:
    """
    Orchestrates all Direct Messaging use cases.

    Instantiate with an active AsyncSession from get_db().
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._conv_repo = ConversationRepository(session)
        self._msg_repo = MessageRepository(session)
        self._user_repo = UserRepository(session)
        self._privacy = PrivacyGuard(session)

    # ------------------------------------------------------------------
    # Conversations
    # ------------------------------------------------------------------

    async def get_or_create_conversation(
        self,
        current_user: User,
        recipient_username: str,
    ) -> ConversationRead:
        """
        Return the existing conversation with recipient, or create a new one.

        Business rules:
            - Cannot message yourself.
            - Recipient must be active and not soft-deleted.
            - Blocked in any direction → MessagePermissionError.
            - Duplicate conversations between the same pair are prevented.

        Args:
            current_user:       The authenticated requesting user.
            recipient_username: Username of the intended recipient.

        Returns:
            ConversationRead with the other participant populated.

        Raises:
            UserNotFoundError:      Recipient username not found or deleted.
            SelfMessageError:       Attempted to start a conversation with self.
            InactiveUserError:      Recipient account is suspended.
            MessagePermissionError: Blocked in any direction.
        """
        # Resolve recipient
        recipient = await self._user_repo.get_by_username(recipient_username)
        if recipient is None:
            raise UserNotFoundError()

        # Rule 1: no self-messaging
        if recipient.id == current_user.id:
            raise SelfMessageError()

        # Rule 2: recipient must be active
        if not recipient.is_active or recipient.deleted_at is not None:
            raise InactiveUserError()

        # Rule 3: block check via PrivacyGuard
        allowed = await self._privacy.can_message(current_user.id, recipient.id)
        if not allowed:
            raise MessagePermissionError()

        # Check for existing conversation
        existing = await self._conv_repo.get_conversation_between(
            current_user.id, recipient.id
        )
        if existing is not None:
            logger.debug(
                "message_service.get_or_create_conversation "
                "existing conversation_id=%s",
                str(existing.id),
            )
            return ConversationRead.from_orm_for_viewer(existing, current_user.id)

        # Create new conversation
        conversation = await self._conv_repo.create_conversation(
            [current_user.id, recipient.id]
        )
        await self._session.commit()
        await self._session.refresh(conversation)

        logger.info(
            "message_service.get_or_create_conversation created "
            "conversation_id=%s user_id=%s recipient_id=%s",
            str(conversation.id),
            str(current_user.id),
            str(recipient.id),
        )
        return ConversationRead.from_orm_for_viewer(conversation, current_user.id)

    async def list_conversations(
        self,
        current_user: User,
    ) -> ConversationListResponse:
        """
        List all conversations for the authenticated user, newest first.

        Args:
            current_user: The authenticated requesting user.

        Returns:
            ConversationListResponse with all conversations populated.
        """
        conversations = await self._conv_repo.list_conversations(current_user.id)
        total = await self._conv_repo.count_conversations(current_user.id)

        reads = [
            ConversationRead.from_orm_for_viewer(c, current_user.id)
            for c in conversations
        ]

        return ConversationListResponse(conversations=reads, total=total)

    # ------------------------------------------------------------------
    # Messages
    # ------------------------------------------------------------------

    async def send_message(
        self,
        current_user: User,
        conversation_id: uuid.UUID,
        body: MessageCreate,
    ) -> MessageRead:
        """
        Send a message in an existing conversation.

        Business rules:
            - Conversation must exist.
            - Current user must be a participant.
            - Recipient must still be active and unblocked.

        Args:
            current_user:    The authenticated sender.
            conversation_id: UUID of the target conversation.
            body:            MessageCreate payload with content.

        Returns:
            MessageRead representing the saved message.

        Raises:
            ConversationNotFoundError: Conversation does not exist or user is not a participant.
            InactiveUserError:         Recipient account is suspended/deleted.
            MessagePermissionError:    Blocked in any direction.
        """
        conversation = await self._conv_repo.get_conversation(conversation_id)
        if conversation is None:
            raise ConversationNotFoundError()

        # Verify current user is a participant
        participant_ids = [p.user_id for p in conversation.participants]
        if current_user.id not in participant_ids:
            raise ConversationNotFoundError()

        # Identify recipient
        recipient_id = next(pid for pid in participant_ids if pid != current_user.id)

        # Recipient must still be active
        recipient = await self._user_repo.get_by_id(recipient_id)
        if recipient is None or not recipient.is_active or recipient.deleted_at is not None:
            raise InactiveUserError()

        # Block check
        allowed = await self._privacy.can_message(current_user.id, recipient_id)
        if not allowed:
            raise MessagePermissionError()

        message = await self._msg_repo.send_message(
            conversation_id=conversation_id,
            sender_id=current_user.id,
            content=body.content,
        )
        await self._session.commit()
        await self._session.refresh(message)

        logger.info(
            "message_service.send_message message_id=%s conversation_id=%s sender_id=%s",
            str(message.id),
            str(conversation_id),
            str(current_user.id),
        )
        return MessageRead.model_validate(message)

    async def list_messages(
        self,
        current_user: User,
        conversation_id: uuid.UUID,
        limit: int = 50,
        offset: int = 0,
    ) -> MessageListResponse:
        """
        List messages in a conversation the current user participates in.

        Args:
            current_user:    The authenticated requesting user.
            conversation_id: UUID of the conversation.
            limit:           Page size (max 100).
            offset:          Pagination offset.

        Returns:
            MessageListResponse with messages ordered newest-first.

        Raises:
            ConversationNotFoundError: Conversation not found or user not a participant.
        """
        conversation = await self._conv_repo.get_conversation(conversation_id)
        if conversation is None:
            raise ConversationNotFoundError()

        participant_ids = [p.user_id for p in conversation.participants]
        if current_user.id not in participant_ids:
            raise ConversationNotFoundError()

        # Clamp limit
        limit = min(limit, 100)

        messages = await self._msg_repo.list_messages(
            conversation_id=conversation_id,
            limit=limit,
            offset=offset,
        )
        total = await self._msg_repo.count_messages(conversation_id)

        return MessageListResponse(
            messages=[MessageRead.model_validate(m) for m in messages],
            total=total,
            limit=limit,
            offset=offset,
        )
