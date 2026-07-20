"""
FollowService — business logic for social graph (follow/unfollow) operations.

Architecture:
    - Orchestrates FollowRepository and UserRepository calls to fulfil use cases.
    - Raises domain exceptions, not HTTP exceptions.
    - Receives AsyncSession from the API layer via dependency injection.
    - Never writes SQL directly; always delegates to repositories.

Business Rules:
    1. A user may not follow themselves.
    2. A user may not follow an inactive (suspended) account.
    3. A user may not follow a soft-deleted account.
    4. Duplicate follows are rejected.
    5. Unfollowing a user you do not follow is rejected.
"""

import logging
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    AlreadyFollowingError,
    InactiveUserError,
    NotFollowingError,
    SelfFollowError,
    UserNotFoundError,
)
from app.models.follow import Follow
from app.models.user import User
from app.repositories.follow_repo import FollowRepository
from app.repositories.user_repo import UserRepository

logger = logging.getLogger(__name__)


class FollowService:
    """
    Orchestrates follow/unfollow business operations.

    Instantiate with an active AsyncSession and delegate to repositories
    for all persistence operations.
    """

    def __init__(self, session: AsyncSession) -> None:
        """
        Args:
            session: An active SQLAlchemy AsyncSession from get_db().
        """
        self._session = session
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

    # ------------------------------------------------------------------
    # Follow / Unfollow
    # ------------------------------------------------------------------

    async def follow_user(
        self,
        current_user: User,
        target_username: str,
    ) -> Follow:
        """
        Follow the user identified by `target_username`.

        Args:
            current_user:    The authenticated caller (session-tracked).
            target_username: Username of the account to follow.

        Returns:
            The created Follow relationship instance.

        Raises:
            UserNotFoundError:    Target user does not exist or is deleted.
            InactiveUserError:    Target user's account is suspended.
            SelfFollowError:      Caller attempted to follow themselves.
            AlreadyFollowingError: Caller already follows the target.
        """
        target = await self._get_active_user_by_username(target_username)

        if current_user.id == target.id:
            raise SelfFollowError()

        already = await self._follow_repo.is_following(current_user.id, target.id)
        if already:
            raise AlreadyFollowingError()

        follow = await self._follow_repo.follow(current_user.id, target.id)
        logger.info(
            "follow_service.followed follower=%s following=%s",
            current_user.username,
            target.username,
        )
        return follow

    async def unfollow_user(
        self,
        current_user: User,
        target_username: str,
    ) -> None:
        """
        Unfollow the user identified by `target_username`.

        Args:
            current_user:    The authenticated caller (session-tracked).
            target_username: Username of the account to unfollow.

        Raises:
            UserNotFoundError:  Target user does not exist or is deleted.
            InactiveUserError:  Target user's account is suspended.
            NotFollowingError:  Caller is not currently following the target.
        """
        target = await self._get_active_user_by_username(target_username)

        removed = await self._follow_repo.unfollow(current_user.id, target.id)
        if not removed:
            raise NotFollowingError()

        logger.info(
            "follow_service.unfollowed follower=%s following=%s",
            current_user.username,
            target.username,
        )

    # ------------------------------------------------------------------
    # List queries
    # ------------------------------------------------------------------

    async def get_followers(
        self,
        username: str,
        skip: int = 0,
        limit: int = 20,
    ) -> tuple[list[User], int]:
        """
        Return paginated list of followers for `username`.

        Args:
            username: The target user's username.
            skip:     Pagination offset.
            limit:    Page size (max 100).

        Returns:
            Tuple of (list of User instances, total count).

        Raises:
            UserNotFoundError: Target user does not exist or is deleted.
            InactiveUserError: Target user's account is suspended.
        """
        target = await self._get_active_user_by_username(username)
        users = await self._follow_repo.list_followers(
            target.id, skip=skip, limit=limit
        )
        total = await self._follow_repo.followers_count(target.id)
        return users, total

    async def get_following(
        self,
        username: str,
        skip: int = 0,
        limit: int = 20,
    ) -> tuple[list[User], int]:
        """
        Return paginated list of users that `username` follows.

        Args:
            username: The target user's username.
            skip:     Pagination offset.
            limit:    Page size (max 100).

        Returns:
            Tuple of (list of User instances, total count).

        Raises:
            UserNotFoundError: Target user does not exist or is deleted.
            InactiveUserError: Target user's account is suspended.
        """
        target = await self._get_active_user_by_username(username)
        users = await self._follow_repo.list_following(
            target.id, skip=skip, limit=limit
        )
        total = await self._follow_repo.following_count(target.id)
        return users, total

    # ------------------------------------------------------------------
    # Relationship status
    # ------------------------------------------------------------------

    async def get_relationship(
        self,
        current_user: User,
        target_username: str,
    ) -> dict:
        """
        Return the mutual follow relationship between the caller and target.

        Args:
            current_user:    The authenticated caller.
            target_username: Username of the target to check against.

        Returns:
            Dict with keys ``is_following`` and ``is_followed_by``.

        Raises:
            UserNotFoundError: Target user does not exist or is deleted.
            InactiveUserError: Target user's account is suspended.
        """
        target = await self._get_active_user_by_username(target_username)
        is_following = await self._follow_repo.is_following(
            current_user.id, target.id
        )
        is_followed_by = await self._follow_repo.is_following(
            target.id, current_user.id
        )
        logger.debug(
            "follow_service.relationship caller=%s target=%s "
            "is_following=%s is_followed_by=%s",
            current_user.username,
            target.username,
            is_following,
            is_followed_by,
        )
        return {
            "is_following": is_following,
            "is_followed_by": is_followed_by,
        }

    # ------------------------------------------------------------------
    # Profile enrichment helpers
    # ------------------------------------------------------------------

    async def get_social_counts(
        self,
        user_id: uuid.UUID,
    ) -> tuple[int, int]:
        """
        Return (followers_count, following_count) for a single user ID.

        Args:
            user_id: UUID of the target user.

        Returns:
            Tuple of (followers_count, following_count).
        """
        followers = await self._follow_repo.followers_count(user_id)
        following = await self._follow_repo.following_count(user_id)
        return followers, following
