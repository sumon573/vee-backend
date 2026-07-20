"""
UserRepository — data access layer for the User aggregate.

Architecture:
    - Receives an AsyncSession via constructor injection.
    - The only layer permitted to write SQLAlchemy queries for User.
    - Returns ORM model instances (User) or None — never raises HTTP exceptions.
    - Business logic lives in UserService, not here.
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

        Args:
            user: An active (session-tracked) User ORM instance.
            data: Mapping of column name → new value.

        Returns:
            The updated User instance.
        """
        allowed = {
            "display_name", "avatar_url", "bio",
            "gender", "birth_date", "username",
        }
        for field, value in data.items():
            if field in allowed:
                setattr(user, field, value)
        await self._session.flush()
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
