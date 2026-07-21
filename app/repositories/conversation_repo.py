"""
ConversationRepository — data access layer for direct messaging conversations.

Responsibilities:
    - All SQL for the `conversations` and `conversation_participants` tables.
    - Returns ORM model instances; raises no business logic exceptions.
    - N+1 avoided: list_conversations uses selectin loading (configured on the
      Conversation.participants relationship) so participants are fetched in a
      single IN query, not per-row.

Rules (per ARCHITECTURE.md):
    - No business logic — that belongs in MessageService.
    - No HTTP exceptions — callers handle domain errors.
    - Receives AsyncSession via constructor injection.
"""

import logging
import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.conversation import Conversation, ConversationParticipant

logger = logging.getLogger(__name__)


class ConversationRepository:
    """Data access layer for Conversation and ConversationParticipant."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # ------------------------------------------------------------------
    # Reads
    # ------------------------------------------------------------------

    async def get_conversation(
        self,
        conversation_id: uuid.UUID,
    ) -> Conversation | None:
        """
        Fetch a conversation by its primary key.

        Participants are loaded via the selectin relationship configured on
        Conversation.participants — no extra query needed.

        Args:
            conversation_id: UUID of the conversation to fetch.

        Returns:
            Conversation ORM instance with participants loaded, or None.
        """
        result = await self._session.execute(
            select(Conversation).where(Conversation.id == conversation_id)
        )
        return result.scalar_one_or_none()

    async def get_conversation_between(
        self,
        user_a_id: uuid.UUID,
        user_b_id: uuid.UUID,
    ) -> Conversation | None:
        """
        Find the existing one-to-one conversation between two users.

        Strategy: find conversations where user_a is a participant AND the
        same conversation_id also has user_b as a participant.

        Args:
            user_a_id: UUID of the first user.
            user_b_id: UUID of the second user.

        Returns:
            Conversation ORM instance if found, or None.
        """
        # Subquery: conversation IDs where user_b participates
        user_b_conversations = (
            select(ConversationParticipant.conversation_id)
            .where(ConversationParticipant.user_id == user_b_id)
            .scalar_subquery()
        )

        stmt = (
            select(Conversation)
            .join(
                ConversationParticipant,
                Conversation.id == ConversationParticipant.conversation_id,
            )
            .where(ConversationParticipant.user_id == user_a_id)
            .where(Conversation.id.in_(user_b_conversations))
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_conversations(
        self,
        user_id: uuid.UUID,
    ) -> list[Conversation]:
        """
        List all conversations for a given user, newest first.

        Participants are loaded via selectin on the relationship — one extra
        IN query total, not one per conversation row.

        Args:
            user_id: UUID of the requesting user.

        Returns:
            List of Conversation ORM instances (may be empty).
        """
        # Subquery: conversation IDs where user participates
        user_conversations = (
            select(ConversationParticipant.conversation_id)
            .where(ConversationParticipant.user_id == user_id)
            .scalar_subquery()
        )

        stmt = (
            select(Conversation)
            .where(Conversation.id.in_(user_conversations))
            .order_by(Conversation.updated_at.desc())
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def count_conversations(self, user_id: uuid.UUID) -> int:
        """Return the total number of conversations for user_id."""
        stmt = (
            select(func.count())
            .select_from(ConversationParticipant)
            .where(ConversationParticipant.user_id == user_id)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one()

    # ------------------------------------------------------------------
    # Writes
    # ------------------------------------------------------------------

    async def create_conversation(
        self,
        participant_ids: list[uuid.UUID],
    ) -> Conversation:
        """
        Create a new conversation and add exactly two participants.

        Args:
            participant_ids: List of exactly two user UUIDs.

        Returns:
            Freshly created and flushed Conversation ORM instance.
        """
        conversation = Conversation()
        self._session.add(conversation)
        await self._session.flush()  # Populate conversation.id before inserting participants

        for user_id in participant_ids:
            participant = ConversationParticipant(
                conversation_id=conversation.id,
                user_id=user_id,
            )
            self._session.add(participant)

        await self._session.flush()
        await self._session.refresh(conversation)

        logger.debug(
            "conversation_repo.create_conversation id=%s participants=%s",
            str(conversation.id),
            [str(uid) for uid in participant_ids],
        )
        return conversation
