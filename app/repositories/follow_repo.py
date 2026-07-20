"""
FollowRepository — data access layer for the Follow aggregate.

Architecture:
    - Receives an AsyncSession via constructor injection.
    - The only layer permitted to write SQLAlchemy queries for Follow.
    - Returns ORM model instances or primitives — never raises HTTP exceptions.
    - Business logic lives in FollowService, not here.

Performance:
    - Batch count helpers (followers_count_batch, following_count_batch) allow
      callers to resolve counts for multiple users in a single query, avoiding
      N+1 patterns when rendering lists of user cards.
"""

import logging
import uuid
from typing import Optional

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.follow import Follow
from app.models.user import User

logger = logging.getLogger(__name__)


class FollowRepository:
    """
    Data access object for the `follows` table.

    All queries for Follow records go through this class.
    Instantiate with an active AsyncSession obtained from get_db().
    """

    def __init__(self, session: AsyncSession) -> None:
        """
        Args:
            session: An active SQLAlchemy AsyncSession.
        """
        self._session = session

    # ------------------------------------------------------------------
    # Read operations
    # ------------------------------------------------------------------

    async def get_follow(
        self,
        follower_id: uuid.UUID,
        following_id: uuid.UUID,
    ) -> Optional[Follow]:
        """
        Fetch a specific follow relationship by participant IDs.

        Args:
            follower_id:  UUID of the follower.
            following_id: UUID of the user being followed.

        Returns:
            Follow instance or None if the relationship does not exist.
        """
        stmt = select(Follow).where(
            Follow.follower_id == follower_id,
            Follow.following_id == following_id,
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def is_following(
        self,
        follower_id: uuid.UUID,
        following_id: uuid.UUID,
    ) -> bool:
        """
        Return True if `follower_id` currently follows `following_id`.

        Args:
            follower_id:  UUID of the potential follower.
            following_id: UUID of the potential followee.

        Returns:
            True if the follow relationship exists, False otherwise.
        """
        follow = await self.get_follow(follower_id, following_id)
        return follow is not None

    async def followers_count(self, user_id: uuid.UUID) -> int:
        """
        Return the total number of users who follow `user_id`.

        Args:
            user_id: UUID of the target user.

        Returns:
            Integer count of followers.
        """
        stmt = (
            select(func.count())
            .select_from(Follow)
            .where(Follow.following_id == user_id)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one()

    async def following_count(self, user_id: uuid.UUID) -> int:
        """
        Return the total number of users that `user_id` follows.

        Args:
            user_id: UUID of the target user.

        Returns:
            Integer count of users being followed.
        """
        stmt = (
            select(func.count())
            .select_from(Follow)
            .where(Follow.follower_id == user_id)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one()

    async def list_followers(
        self,
        user_id: uuid.UUID,
        skip: int = 0,
        limit: int = 20,
    ) -> list[User]:
        """
        Return User objects for accounts that follow `user_id`.

        Only active, non-deleted accounts are returned.
        Results are ordered newest-follow-first.

        Args:
            user_id: UUID of the target user.
            skip:    Number of records to skip (for pagination).
            limit:   Maximum number of records to return.

        Returns:
            List of User instances (may be empty).
        """
        safe_limit = min(max(1, limit), 100)
        stmt = (
            select(User)
            .join(Follow, Follow.follower_id == User.id)
            .where(
                Follow.following_id == user_id,
                User.is_active.is_(True),
                User.deleted_at.is_(None),
            )
            .order_by(Follow.created_at.desc())
            .offset(skip)
            .limit(safe_limit)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def list_following(
        self,
        user_id: uuid.UUID,
        skip: int = 0,
        limit: int = 20,
    ) -> list[User]:
        """
        Return User objects for accounts that `user_id` follows.

        Only active, non-deleted accounts are returned.
        Results are ordered newest-follow-first.

        Args:
            user_id: UUID of the target user.
            skip:    Number of records to skip (for pagination).
            limit:   Maximum number of records to return.

        Returns:
            List of User instances (may be empty).
        """
        safe_limit = min(max(1, limit), 100)
        stmt = (
            select(User)
            .join(Follow, Follow.following_id == User.id)
            .where(
                Follow.follower_id == user_id,
                User.is_active.is_(True),
                User.deleted_at.is_(None),
            )
            .order_by(Follow.created_at.desc())
            .offset(skip)
            .limit(safe_limit)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def followers_count_batch(
        self,
        user_ids: list[uuid.UUID],
    ) -> dict[uuid.UUID, int]:
        """
        Return follower counts for a list of user IDs in a single query.

        Avoids N+1 queries when rendering lists of user cards.

        Args:
            user_ids: List of UUIDs to resolve counts for.

        Returns:
            Mapping of user_id → follower count (missing keys = 0).
        """
        if not user_ids:
            return {}
        stmt = (
            select(Follow.following_id, func.count().label("cnt"))
            .where(Follow.following_id.in_(user_ids))
            .group_by(Follow.following_id)
        )
        result = await self._session.execute(stmt)
        return {row.following_id: row.cnt for row in result}

    async def following_count_batch(
        self,
        user_ids: list[uuid.UUID],
    ) -> dict[uuid.UUID, int]:
        """
        Return following counts for a list of user IDs in a single query.

        Avoids N+1 queries when rendering lists of user cards.

        Args:
            user_ids: List of UUIDs to resolve counts for.

        Returns:
            Mapping of user_id → following count (missing keys = 0).
        """
        if not user_ids:
            return {}
        stmt = (
            select(Follow.follower_id, func.count().label("cnt"))
            .where(Follow.follower_id.in_(user_ids))
            .group_by(Follow.follower_id)
        )
        result = await self._session.execute(stmt)
        return {row.follower_id: row.cnt for row in result}

    # ------------------------------------------------------------------
    # Write operations
    # ------------------------------------------------------------------

    async def follow(
        self,
        follower_id: uuid.UUID,
        following_id: uuid.UUID,
    ) -> Follow:
        """
        Persist a new follow relationship.

        Pre-conditions (enforced by FollowService before this call):
            - follower_id != following_id
            - the relationship does not already exist

        Args:
            follower_id:  UUID of the user who is following.
            following_id: UUID of the user being followed.

        Returns:
            The newly created Follow instance with server-generated fields.
        """
        new_follow = Follow(follower_id=follower_id, following_id=following_id)
        self._session.add(new_follow)
        await self._session.flush()
        await self._session.refresh(new_follow)
        logger.info(
            "follow_repo.followed follower_id=%s following_id=%s",
            str(follower_id),
            str(following_id),
        )
        return new_follow

    async def unfollow(
        self,
        follower_id: uuid.UUID,
        following_id: uuid.UUID,
    ) -> bool:
        """
        Remove a follow relationship.

        Args:
            follower_id:  UUID of the unfollowing user.
            following_id: UUID of the user being unfollowed.

        Returns:
            True if a row was deleted; False if the relationship did not exist.
        """
        stmt = delete(Follow).where(
            Follow.follower_id == follower_id,
            Follow.following_id == following_id,
        )
        result = await self._session.execute(stmt)
        removed = result.rowcount > 0
        if removed:
            logger.info(
                "follow_repo.unfollowed follower_id=%s following_id=%s",
                str(follower_id),
                str(following_id),
            )
        return removed
