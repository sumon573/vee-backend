"""
UserRepository — data access layer for the User aggregate.

Architecture:
    - Receives an AsyncSession via constructor injection.
    - The only layer permitted to write SQLAlchemy queries for User.
    - Returns ORM model instances (User) or None — never raises HTTP exceptions.
    - Business logic lives in UserService, not here.

TODO (Phase 5): Implement all method bodies.
"""

import uuid
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


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

    async def get_by_id(self, user_id: uuid.UUID) -> Optional[User]:
        """
        Fetch a user by primary key.

        Args:
            user_id: UUID primary key.

        Returns:
            User instance or None if not found.

        TODO (Phase 5): Implement with session.get(User, user_id).
        """
        raise NotImplementedError

    async def get_by_firebase_uid(self, firebase_uid: str) -> Optional[User]:
        """
        Fetch a user by their Firebase UID.

        Args:
            firebase_uid: The UID from a verified Firebase ID token.

        Returns:
            User instance or None if not found.

        TODO (Phase 5): Implement with select(User).where(...).
        """
        raise NotImplementedError

    async def get_by_username(self, username: str) -> Optional[User]:
        """
        Fetch a user by their unique username.

        Args:
            username: Case-sensitive username string.

        Returns:
            User instance or None if not found.

        TODO (Phase 5): Implement with select(User).where(...).
        """
        raise NotImplementedError

    async def get_by_email(self, email: str) -> Optional[User]:
        """
        Fetch a user by email address.

        Args:
            email: Email address string.

        Returns:
            User instance or None if not found.

        TODO (Phase 5): Implement with select(User).where(...).
        """
        raise NotImplementedError

    async def create(self, user: User) -> User:
        """
        Persist a new User record to the database.

        Args:
            user: An unsaved User ORM instance.

        Returns:
            The saved User instance (with id and timestamps populated).

        TODO (Phase 5): Implement with session.add(user) + flush.
        """
        raise NotImplementedError

    async def save(self, user: User) -> User:
        """
        Persist changes to an existing User record.

        Args:
            user: A modified User ORM instance already tracked by the session.

        Returns:
            The saved User instance.

        TODO (Phase 5): Implement with session.flush().
        """
        raise NotImplementedError
