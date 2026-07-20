"""
UserService — business logic for User domain operations.

Architecture:
    - Orchestrates UserRepository calls to fulfil use cases.
    - Raises domain exceptions, not HTTP exceptions.
    - Receives AsyncSession from the API layer via dependency injection.
    - Never writes SQL directly; always delegates to UserRepository.

TODO (Phase 5): Implement all method bodies.
"""

import uuid
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.repositories.user_repo import UserRepository
from app.schemas.auth import FirebaseTokenPayload


class UserService:
    """
    Orchestrates user-related business operations.

    Instantiate with an active AsyncSession and delegate to UserRepository
    for all persistence operations.

    Example:
        service = UserService(session)
        user = await service.get_or_create_from_firebase(payload)
    """

    def __init__(self, session: AsyncSession) -> None:
        """
        Args:
            session: An active SQLAlchemy AsyncSession from get_db().
        """
        self._session = session
        self._repo = UserRepository(session)

    async def get_or_create_from_firebase(
        self,
        payload: FirebaseTokenPayload,
    ) -> User:
        """
        Resolve a User from a verified Firebase token payload.

        Looks up the user by firebase_uid. If no record exists, creates
        a new one using the claims from the token.

        Args:
            payload: Verified Firebase token claims.

        Returns:
            Existing or newly created User instance.

        TODO (Phase 5): Implement lookup-or-create logic.
        """
        raise NotImplementedError

    async def get_by_id(self, user_id: uuid.UUID) -> Optional[User]:
        """
        Retrieve a user by primary key.

        Args:
            user_id: UUID primary key.

        Returns:
            User instance or None.

        TODO (Phase 5): Delegate to UserRepository.get_by_id().
        """
        raise NotImplementedError

    async def update_last_seen(self, user: User) -> None:
        """
        Record the current timestamp as the user's last_seen_at.

        Called on every authenticated request to keep presence data fresh.

        Args:
            user: The authenticated User ORM instance.

        TODO (Phase 5): Update user.last_seen_at and persist via repository.
        """
        raise NotImplementedError
