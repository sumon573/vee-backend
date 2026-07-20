"""
UserService — business logic for User domain operations.

Architecture:
    - Orchestrates UserRepository calls to fulfil use cases.
    - Raises domain exceptions, not HTTP exceptions.
    - Receives AsyncSession from the API layer via dependency injection.
    - Never writes SQL directly; always delegates to UserRepository.

Phase 6 additions:
    - update_my_profile()  — validate + apply partial profile updates
    - soft_delete_user()   — initiate user-requested account deletion
    - get_by_username()    — public profile look-up by username
"""

import logging
import uuid
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    InactiveUserError,
    ReservedUsernameError,
    UserNotFoundError,
    UsernameConflictError,
)
from app.models.user import User
from app.repositories.user_repo import UserRepository
from app.schemas.auth import FirebaseTokenPayload
from app.schemas.user import RESERVED_USERNAMES, UserUpdate

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

    async def get_by_username(self, username: str) -> User:
        """
        Look up a public user profile by username.

        Only returns active, non-deleted accounts.

        Args:
            username: The username to look up (case-sensitive).

        Returns:
            The matching User instance.

        Raises:
            UserNotFoundError: if no active user with that username exists.
        """
        user = await self._repo.get_by_username(username)
        if user is None or not user.is_active or user.deleted_at is not None:
            raise UserNotFoundError(f"No active user found with username '{username}'.")
        return user

    # ------------------------------------------------------------------
    # Profile update
    # ------------------------------------------------------------------

    async def update_my_profile(
        self,
        current_user: User,
        update_data: UserUpdate,
    ) -> User:
        """
        Apply a partial update to the authenticated user's own profile.

        Validates that:
        - A requested username is not reserved.
        - A requested username is not already taken by another user.

        Args:
            current_user: The authenticated User ORM instance (session-tracked).
            update_data:  Validated UserUpdate schema with fields to change.

        Returns:
            The updated User instance.

        Raises:
            ReservedUsernameError:  if the new username is reserved.
            UsernameConflictError:  if the new username is taken by another user.
        """
        data = update_data.model_dump(exclude_unset=True, exclude_none=True)

        new_username: Optional[str] = data.get("username")
        if new_username is not None and new_username != current_user.username:
            # Reserved-name check (belt-and-suspenders alongside schema validator)
            if new_username.lower() in RESERVED_USERNAMES:
                raise ReservedUsernameError()

            # Uniqueness check
            existing = await self._repo.get_by_username(new_username)
            if existing is not None and existing.id != current_user.id:
                raise UsernameConflictError()

        updated = await self._repo.update_profile(current_user, data)
        logger.info(
            "user_service.profile_updated user_id=%s fields=%s",
            str(current_user.id),
            list(data.keys()),
        )
        return updated

    # ------------------------------------------------------------------
    # Soft delete
    # ------------------------------------------------------------------

    async def soft_delete_user(self, user: User) -> User:
        """
        Soft-delete the authenticated user's own account.

        Sets deleted_at to UTC now and is_active to False.
        The record is retained in the database for data integrity.

        Args:
            user: The authenticated User ORM instance (session-tracked).

        Returns:
            The updated User instance with deleted_at populated.
        """
        deleted = await self._repo.soft_delete(user)
        logger.info(
            "user_service.soft_deleted user_id=%s",
            str(user.id),
        )
        return deleted

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
