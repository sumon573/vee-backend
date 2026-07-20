"""
PrivacyGuard — reusable privacy and interaction permission checks.

Purpose:
    Centralises all "can user A do X to user B?" logic so that future features
    (Chat, Voice Room, Stories, Notifications) share a single, consistent
    enforcement surface instead of duplicating block/privacy checks in each
    feature's service layer.

Design:
    - Stateless logic; receives BlockRepository (and future: PrivacySettings repo)
      via constructor injection.
    - All methods are async to allow future DB-backed privacy settings.
    - Stub methods (can_message, can_join_room) are defined now so callers can
      wire them in without future import changes; they return True until the
      relevant feature is implemented.
    - Never raises HTTP exceptions — returns bool / structured result.

Phase 8 coverage:
    - can_view_profile: blocked in either direction → False
    - can_follow:       blocked in either direction → False
    - can_message:      stub → True (Phase 9: Chat)
    - can_join_room:    stub → True (Phase 10: Voice Room)
"""

import logging
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.block_repo import BlockRepository

logger = logging.getLogger(__name__)


class PrivacyGuard:
    """
    Central authority for cross-user interaction permissions.

    Instantiate with an active AsyncSession.
    """

    def __init__(self, session: AsyncSession) -> None:
        """
        Args:
            session: An active SQLAlchemy AsyncSession from get_db().
        """
        self._session = session
        self._block_repo = BlockRepository(session)

    # ------------------------------------------------------------------
    # Profile visibility
    # ------------------------------------------------------------------

    async def can_view_profile(
        self,
        viewer_id: uuid.UUID,
        target_id: uuid.UUID,
    ) -> bool:
        """
        Return True if `viewer_id` is permitted to view `target_id`'s profile.

        Rules (Phase 8):
            - A user can always view their own profile.
            - If either party has blocked the other, viewing is denied.

        Args:
            viewer_id: UUID of the user requesting the profile.
            target_id: UUID of the profile owner.

        Returns:
            True if viewing is permitted, False otherwise.
        """
        if viewer_id == target_id:
            return True

        blocked = await self._block_repo.is_mutually_blocked(viewer_id, target_id)
        if blocked:
            logger.debug(
                "privacy_guard.can_view_profile denied viewer=%s target=%s reason=blocked",
                str(viewer_id),
                str(target_id),
            )
            return False

        return True

    # ------------------------------------------------------------------
    # Follow permission
    # ------------------------------------------------------------------

    async def can_follow(
        self,
        follower_id: uuid.UUID,
        target_id: uuid.UUID,
    ) -> bool:
        """
        Return True if `follower_id` is permitted to follow `target_id`.

        Rules (Phase 8):
            - A user cannot follow themselves (handled by FollowService too).
            - If either party has blocked the other, following is denied.

        Args:
            follower_id: UUID of the user who wants to follow.
            target_id:   UUID of the user to be followed.

        Returns:
            True if following is permitted, False otherwise.
        """
        if follower_id == target_id:
            return False

        blocked = await self._block_repo.is_mutually_blocked(follower_id, target_id)
        if blocked:
            logger.debug(
                "privacy_guard.can_follow denied follower=%s target=%s reason=blocked",
                str(follower_id),
                str(target_id),
            )
            return False

        return True

    # ------------------------------------------------------------------
    # Messaging permission (stub — Phase 9: Chat)
    # ------------------------------------------------------------------

    async def can_message(
        self,
        sender_id: uuid.UUID,
        recipient_id: uuid.UUID,
    ) -> bool:
        """
        Return True if `sender_id` is permitted to message `recipient_id`.

        Phase 8: Stub — returns True for all non-blocked pairs.
        Phase 9 (Chat): Will enforce message privacy settings,
                        mutual-follow requirements, etc.

        Args:
            sender_id:    UUID of the user who wants to send a message.
            recipient_id: UUID of the message recipient.

        Returns:
            True if messaging is permitted, False otherwise.
        """
        if sender_id == recipient_id:
            return False

        blocked = await self._block_repo.is_mutually_blocked(sender_id, recipient_id)
        if blocked:
            return False

        # TODO (Phase 9): Check message privacy settings
        return True

    # ------------------------------------------------------------------
    # Voice room permission (stub — Phase 10: Voice Room)
    # ------------------------------------------------------------------

    async def can_join_room(
        self,
        user_id: uuid.UUID,
        room_owner_id: uuid.UUID,
    ) -> bool:
        """
        Return True if `user_id` is permitted to join a room owned by `room_owner_id`.

        Phase 8: Stub — returns True for all non-blocked pairs.
        Phase 10 (Voice Room): Will enforce room privacy settings,
                               invite-only rooms, etc.

        Args:
            user_id:       UUID of the user who wants to join the room.
            room_owner_id: UUID of the room owner.

        Returns:
            True if joining is permitted, False otherwise.
        """
        if user_id == room_owner_id:
            return True

        blocked = await self._block_repo.is_mutually_blocked(user_id, room_owner_id)
        if blocked:
            return False

        # TODO (Phase 10): Check room privacy settings (public/private/invite-only)
        return True
