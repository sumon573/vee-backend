"""
IdentityService — authentication and identity orchestration.

Responsibilities:
    1. Verify Firebase ID token and extract identity claims.
    2. Sync the caller's identity with the local user database
       (get-or-create pattern).
    3. Update presence (last_seen_at) on every authenticated request.
    4. Provide a single entry point for the login flow.

Architecture:
    - Sits between the API layer and (UserService + Firebase).
    - Raises domain exceptions (AuthError, InactiveUserError) — never HTTP.
    - Designed for future provider extension: Google, Apple, Phone, Email,
      Admin impersonation can each be added as new `login_with_*` methods
      without changing the interface consumed by route handlers.

Future providers (example extension points):
    async def login_with_google(id_token: str) -> User: ...
    async def login_with_apple(identity_token: str) -> User: ...
    async def login_with_phone(firebase_token: str) -> User: ...
"""

import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import InactiveUserError
from app.models.user import User
from app.schemas.auth import FirebaseTokenPayload
from app.services.auth.firebase import verify_firebase_token
from app.services.user_service import UserService

logger = logging.getLogger(__name__)


class IdentityService:
    """
    Orchestrates the full authentication login flow.

    Args:
        session: An active AsyncSession from get_db().
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._user_service = UserService(session)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def login_with_firebase(self, raw_token: str) -> User:
        """
        Full login flow: verify token → sync user → update presence.

        Args:
            raw_token: Raw Firebase ID token string from the client.

        Returns:
            The resolved (existing or newly created) active User.

        Raises:
            AuthTokenInvalidError: Token is malformed or signature invalid.
            AuthTokenExpiredError: Token has expired.
            AuthTokenRevokedError: Token has been revoked.
            FirebaseUnavailableError: Firebase service is unreachable.
            InactiveUserError: The resolved user account is not active.
        """
        # Step 1 — Verify token with Firebase (raises AuthError subclasses)
        payload: FirebaseTokenPayload = await verify_firebase_token(raw_token)

        # Step 2 — Sync with local DB (get or create)
        user: User = await self._user_service.sync_firebase_user(payload)

        # Step 3 — Guard against suspended accounts
        if not user.is_active:
            logger.warning(
                "identity.login_rejected_inactive firebase_uid=%s",
                payload.uid,
            )
            raise InactiveUserError()

        # Step 4 — Update last_seen_at (best-effort; non-fatal)
        await self._user_service.update_last_seen(user)

        logger.info(
            "identity.login_success user_id=%s firebase_uid=%s",
            str(user.id),
            payload.uid,
        )
        return user

    async def get_identity(self, raw_token: str) -> FirebaseTokenPayload:
        """
        Verify a token and return the raw Firebase claims.

        Lower-level than login_with_firebase — does not touch the DB.
        Useful for lightweight token introspection.

        Args:
            raw_token: Raw Firebase ID token string.

        Returns:
            Verified FirebaseTokenPayload.

        Raises:
            AuthError subclasses on any verification failure.
        """
        return await verify_firebase_token(raw_token)
