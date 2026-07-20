"""
UserService — business logic for User domain operations.

Architecture:
    - Orchestrates UserRepository calls to fulfil use cases.
    - Raises domain exceptions, not HTTP exceptions.
    - Receives AsyncSession from the API layer via dependency injection.
    - Never writes SQL directly; always delegates to UserRepository.
"""

import logging
import uuid
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.repositories.user_repo import UserRepository
from app.schemas.auth import FirebaseTokenPayload

logger = logging.getLogger(__name__)

# Prefix used when auto-generating a username from a Firebase UID.
_USERNAME_PREFIX = "vee_"
# Max characters from firebase_uid used in auto-generated username.
_UID_SLUG_LEN = 16


def _generate_username(firebase_uid: str) -> str:
    """
    Derive a deterministic, URL-safe initial username from a Firebase UID.

    Firebase UIDs are alphanumeric (A-Z, a-z, 0-9) so they are already
    safe for use in a username slug.

    Args:
        firebase_uid: The Firebase UID string.

    Returns:
        A username like ``vee_abc123def456789``.
    """
    slug = firebase_uid[:_UID_SLUG_LEN].lower()
    return f"{_USERNAME_PREFIX}{slug}"


class UserService:
    """
    Orchestrates user-related business operations.

    Instantiate with an active AsyncSession and delegate to UserRepository
    for all persistence operations.
    """

    def __init__(self, session: AsyncSession) -> None:
        """
        Args:
            session: An active SQLAlchemy AsyncSession from get_db().
        """
        self._session = session
        self._repo = UserRepository(session)

    # ------------------------------------------------------------------
    # Core sync
    # ------------------------------------------------------------------

    async def sync_firebase_user(self, payload: FirebaseTokenPayload) -> User:
        """
        Get-or-create a User from a verified Firebase token payload.

        If the user already exists (matched by firebase_uid), the existing
        record is returned unchanged.

        If no record exists, a new User is created using available claims
        from the Firebase token (display_name, email, phone, avatar_url).
        An initial username is auto-generated from the firebase_uid and
        can be updated by the user later.

        Args:
            payload: Verified Firebase token claims.

        Returns:
            Existing or newly created User instance.
        """
        existing = await self._repo.get_by_firebase_uid(payload.uid)
        if existing is not None:
            logger.debug(
                "user_service.sync_found user_id=%s", str(existing.id)
            )
            return existing

        # Build a new user from Firebase claims.
        display_name = payload.name or "Vee User"
        username = _generate_username(payload.uid)

        new_user = User(
            firebase_uid=payload.uid,
            username=username,
            display_name=display_name,
            email=payload.email if payload.email_verified else None,
            phone=payload.phone_number,
            avatar_url=payload.picture,
            is_verified=payload.email_verified,
            is_active=True,
        )

        created = await self._repo.create(new_user)
        logger.info(
            "user_service.created user_id=%s username=%s",
            str(created.id),
            created.username,
        )
        return created

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    async def get_profile(self, user_id: uuid.UUID) -> Optional[User]:
        """
        Retrieve a user's full profile by primary key.

        Args:
            user_id: UUID primary key.

        Returns:
            User instance or None.
        """
        return await self._repo.get_by_id(user_id)

    async def get_by_id(self, user_id: uuid.UUID) -> Optional[User]:
        """Alias for get_profile — backward compatible."""
        return await self._repo.get_by_id(user_id)

    # ------------------------------------------------------------------
    # Presence
    # ------------------------------------------------------------------

    async def update_last_seen(self, user: User) -> None:
        """
        Stamp the user's last_seen_at to now (UTC).

        Non-fatal — callers should not crash if this fails.

        Args:
            user: The authenticated User ORM instance.
        """
        try:
            await self._repo.update_last_seen(user)
        except Exception as exc:  # noqa: BLE001
            # Presence update failure must never block the login response.
            logger.warning(
                "user_service.update_last_seen_failed user_id=%s error=%s",
                str(user.id),
                type(exc).__name__,
            )
