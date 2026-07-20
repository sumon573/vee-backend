"""
UserRepository — data access layer for the User aggregate.

Architecture:
    - Receives an AsyncSession via constructor injection.
    - The only layer permitted to write SQLAlchemy queries for User.
    - Returns ORM model instances (User) or None — never raises HTTP exceptions.
    - Business logic lives in UserService, not here.

Phase 6 additions:
    - soft_delete()              — sets deleted_at + is_active=False
    - search_by_username_prefix() — prefix-match for username search
"""

import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User

logger = logging.getLogger(__name__)


class UserRepository:
    """
    Data access object for the `users` table.

    All queries for User records go through this class.
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

    async def get_by_id(self, user_id: uuid.UUID) -> Optional[User]:
        """
        Fetch a user by primary key.

        Args:
            user_id: UUID primary key.

        Returns:
            User instance or None if not found.
        """
        return await self._session.get(User, user_id)

    async def get_by_firebase_uid(self, firebase_uid: str) -> Optional[User]:
        """
        Fetch a user by their Firebase UID.

        Args:
            firebase_uid: The UID from a verified Firebase ID token.

        Returns:
            User instance or None if not found.
        """
        stmt = select(User).where(User.firebase_uid == firebase_uid)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_username(self, username: str) -> Optional[User]:
        """
        Fetch a user by their unique username.

        Args:
            username: Case-sensitive username string.

        Returns:
            User instance or None if not found.
        """
        stmt = select(User).where(User.username == username)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> Optional[User]:
        """
        Fetch a user by email address.

        Args:
            email: Email address string.

        Returns:
            User instance or None if not found.
        """
        stmt = select(User).where(User.email == email)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def search_by_username_prefix(
        self,
        prefix: str,
        limit: int = 20,
    ) -> list[User]:
        """
        Return users whose username starts with `prefix`.

        Only returns active, non-deleted accounts. Results are ordered
        alphabetically by username. Useful for @-mention auto-complete.

        Args:
            prefix: Leading characters to match (case-insensitive via ILIKE).
            limit:  Maximum number of results to return (default 20, max 100).

        Returns:
            List of matching User instances (may be empty).
        """
        safe_limit = min(max(1, limit), 100)
        stmt = (
            select(User)
            .where(
                User.username.ilike(f"{prefix}%"),
                User.is_active.is_(True),
                User.deleted_at.is_(None),
            )
            .order_by(User.username)
            .limit(safe_limit)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    # ------------------------------------------------------------------
    # Write operations
    # ------------------------------------------------------------------

    async def create(self, user: User) -> User:
        """
        Persist a new User record to the database.

        Args:
            user: An unsaved User ORM instance.

        Returns:
            The saved User instance with server-generated fields populated
            (id, created_at, updated_at).
        """
        self._session.add(user)
        await self._session.flush()
        await self._session.refresh(user)
        logger.info(
            "user_repo.created user_id=%s firebase_uid=%s",
            str(user.id),
            user.firebase_uid,
        )
        return user

    async def update_last_seen(self, user: User) -> None:
        """
        Stamp the user's last_seen_at to the current UTC time.

        Args:
            user: An active (session-tracked) User ORM instance.
        """
        user.last_seen_at = datetime.now(timezone.utc)
        await self._session.flush()

    async def update_profile(self, user: User, data: dict[str, Any]) -> User:
        """
        Apply a dictionary of field updates to an existing User.

        Only updates fields present in `data`; ignores unknown keys.
        Skips None values so callers can pass model.model_dump(exclude_unset=True).

        Args:
            user: An active (session-tracked) User ORM instance.
            data: Mapping of column name → new value.

        Returns:
            The updated User instance.
        """
        allowed: set[str] = {
            "display_name",
            "avatar_url",
            "bio",
            "gender",
            "birth_date",
            "username",
        }
        for field, value in data.items():
            if field in allowed:
                setattr(user, field, value)
        await self._session.flush()
        return user

    async def soft_delete(self, user: User) -> User:
        """
        Soft-delete a user account.

        Sets `deleted_at` to the current UTC time and `is_active` to False.
        The row is NOT removed from the database; it can be restored by
        an admin by clearing `deleted_at` and setting `is_active=True`.

        Args:
            user: An active (session-tracked) User ORM instance.

        Returns:
            The updated User instance with deleted_at and is_active set.
        """
        now = datetime.now(timezone.utc)
        user.deleted_at = now
        user.is_active = False
        await self._session.flush()
        logger.info(
            "user_repo.soft_deleted user_id=%s deleted_at=%s",
            str(user.id),
            now.isoformat(),
        )
        return user

    async def save(self, user: User) -> User:
        """
        Flush pending changes to an existing tracked User to the DB.

        Args:
            user: A modified User ORM instance already in the session.

        Returns:
            The flushed User instance.
        """
        await self._session.flush()
        return user
