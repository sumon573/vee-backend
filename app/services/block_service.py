"""
BlockService — business logic for privacy/blocking operations.

Architecture:
    - Orchestrates BlockRepository and FollowRepository calls to fulfil use cases.
    - Raises domain exceptions, not HTTP exceptions.
    - Receives AsyncSession from the API layer via dependency injection.
    - Never writes SQL directly; always delegates to repositories.
    - Designed as a reusable foundation for Chat, Voice Room, and any future
      feature that must respect block relationships.

Business Rules:
    1. A user may not block themselves.
    2. A user may not block a soft-deleted account.
    3. A user may not block an inactive (suspended) account.
    4. Blocking a user automatically removes any follow relationship between
       them in both directions (blocker→blocked and blocked→blocker).
    5. Unblocking a user who was never blocked is rejected.
"""

import logging
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    AlreadyBlockedError,
    InactiveUserError,
    NotBlockedError,
    SelfBlockError,
    UserNotFoundError,
)
from app.models.block import Block
from app.models.user import User
from app.repositories.block_repo import BlockRepository
from app.repositories.follow_repo import FollowRepository
from app.repositories.user_repo import UserRepository
from app.schemas.block import BlockedListResponse, BlockedUserRead

logger = logging.getLogger(__name__)


class BlockService:
    """
    Orchestrates block/unblock business operations.

    Instantiate with an active AsyncSession and delegate to repositories
    for all persistence operations.
    """

    def __init__(self, session: AsyncSession) -> None:
        """
        Args:
            session: An active SQLAlchemy AsyncSession from get_db().
        """
        self._session = session
        self._block_repo = BlockRepository(session)
        self._follow_repo = FollowRepository(session)
        self._user_repo = UserRepository(session)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    async def _get_active_user_by_username(self, username: str) -> User:
        """
        Fetch an active, non-deleted user by username.

        Args:
            username: The username to look up.

        Returns:
            The matching User instance.

        Raises:
            UserNotFoundError: if the user does not exist or is soft-deleted.
            InactiveUserError: if the account is suspended (is_active=False).
        """
        user = await self._user_repo.get_by_username(username)
        if user is None or user.deleted_at is not None:
            raise UserNotFoundError(
                f"No active user found with username '{username}'."
            )
        if not user.is_active:
            raise InactiveUserError(
                f"The user '{username}' account is not active."
            )
        return user

    async def _remove_follow_relationship(
        self,
        user_a_id: uuid.UUID,
        user_b_id: uuid.UUID,
    ) -> None:
        """
        Remove follow edges in both directions between two users (if they exist).

        Called automatically when a block is placed. Follow edges are silently
        removed; non-existence is not an error here.

        Args:
            user_a_id: UUID of the first user (typically the blocker).
            user_b_id: UUID of the second user (typically the blocked user).
        """
        # A follows B
        await self._follow_repo.unfollow(user_a_id, user_b_id)
        # B follows A
        await self._follow_repo.unfollow(user_b_id, user_a_id)

    # ------------------------------------------------------------------
    # Block / Unblock
    # ------------------------------------------------------------------

    async def block_user(
        self,
        current_user: User,
        target_username: str,
    ) -> Block:
        """
        Block the user identified by `target_username`.

        Blocking also removes any follow relationship between the two users
        in both directions.

        Args:
            current_user:    The authenticated caller (session-tracked).
            target_username: Username of the account to block.

        Returns:
            The created Block record.

        Raises:
            UserNotFoundError:  Target user does not exist or is deleted.
            InactiveUserError:  Target user's account is suspended.
            SelfBlockError:     Caller attempted to block themselves.
            AlreadyBlockedError: Caller has already blocked this user.
        """
        target = await self._get_active_user_by_username(target_username)

        if current_user.id == target.id:
            raise SelfBlockError()

        already = await self._block_repo.is_blocked(current_user.id, target.id)
        if already:
            raise AlreadyBlockedError()

        # Remove follow relationships in both directions before blocking
        await self._remove_follow_relationship(current_user.id, target.id)

        block = await self._block_repo.block_user(current_user.id, target.id)
        logger.info(
            "block_service.blocked blocker=%s blocked=%s",
            current_user.username,
            target.username,
        )
        return block

    async def unblock_user(
        self,
        current_user: User,
        target_username: str,
    ) -> None:
        """
        Unblock the user identified by `target_username`.

        Args:
            current_user:    The authenticated caller (session-tracked).
            target_username: Username of the account to unblock.

        Raises:
            UserNotFoundError: Target user does not exist or is deleted.
            InactiveUserError: Target user's account is suspended.
            NotBlockedError:   Caller has not blocked this user.
        """
        target = await self._get_active_user_by_username(target_username)

        removed = await self._block_repo.unblock_user(current_user.id, target.id)
        if not removed:
            raise NotBlockedError()

        logger.info(
            "block_service.unblocked blocker=%s blocked=%s",
            current_user.username,
            target.username,
        )

    # ------------------------------------------------------------------
    # List queries
    # ------------------------------------------------------------------

    async def get_blocked_users(
        self,
        current_user: User,
        skip: int = 0,
        limit: int = 20,
    ) -> BlockedListResponse:
        """
        Return the paginated list of users that `current_user` has blocked.

        Args:
            current_user: The authenticated caller.
            skip:         Pagination offset.
            limit:        Page size (max 100).

        Returns:
            BlockedListResponse with total count and item list.
        """
        rows = await self._block_repo.blocked_users(
            current_user.id, skip=skip, limit=limit
        )
        total = await self._block_repo.blocked_count(current_user.id)

        items = [
            BlockedUserRead(
                id=user.id,
                username=user.username,
                display_name=user.display_name,
                avatar_url=user.avatar_url,
                bio=user.bio,
                is_verified=user.is_verified,
                blocked_at=block.created_at,
            )
            for user, block in rows
        ]

        return BlockedListResponse(
            total=total,
            skip=skip,
            limit=limit,
            items=items,
        )

    # ------------------------------------------------------------------
    # Status helpers (reusable by PrivacyGuard and other services)
    # ------------------------------------------------------------------

    async def is_blocked_in_any_direction(
        self,
        user_a_id: uuid.UUID,
        user_b_id: uuid.UUID,
    ) -> bool:
        """
        Return True if either user has blocked the other.

        Convenience wrapper around BlockRepository.is_mutually_blocked()
        for use in PrivacyGuard and other services.

        Args:
            user_a_id: UUID of the first user.
            user_b_id: UUID of the second user.

        Returns:
            True if any block exists in either direction.
        """
        return await self._block_repo.is_mutually_blocked(user_a_id, user_b_id)
