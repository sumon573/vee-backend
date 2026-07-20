"""
Firebase ID token verification — production implementation.

Architecture:
    - Single entry point for all Firebase token verification.
    - Runs the synchronous firebase-admin SDK call in a thread-pool
      executor so it does not block the asyncio event loop.
    - Maps every firebase-admin error type to a Vee domain exception
      so callers never need to import firebase_admin directly.

Security:
    - Raw token strings are NEVER logged — only masked prefixes.
    - Firebase UID is safe to log (not a secret).
"""

import asyncio
import logging
from functools import partial

from firebase_admin import auth as firebase_auth
from firebase_admin.exceptions import FirebaseError

from app.core.exceptions import (
    AuthTokenExpiredError,
    AuthTokenInvalidError,
    AuthTokenRevokedError,
    FirebaseUnavailableError,
)
from app.schemas.auth import FirebaseTokenPayload
from app.services.auth.firebase_init import get_firebase_app

logger = logging.getLogger(__name__)


async def verify_firebase_token(token: str) -> FirebaseTokenPayload:
    """
    Verify a raw Firebase ID token and return its decoded claims.

    Runs firebase_admin.auth.verify_id_token in a thread-pool executor
    to avoid blocking the async event loop.

    Args:
        token: Raw Bearer token string from the Authorization header.

    Returns:
        FirebaseTokenPayload with verified, trusted claims.

    Raises:
        AuthTokenExpiredError: Token has passed its expiry.
        AuthTokenRevokedError: Token has been explicitly revoked.
        AuthTokenInvalidError: Token is malformed or signature is invalid.
        FirebaseUnavailableError: Firebase SDK is not initialized or unreachable.
    """
    # Log only a safe prefix — never the full token.
    token_prefix = token[:8] + "..." if len(token) > 8 else "***"
    logger.debug("firebase.verify_start token_prefix=%s", token_prefix)

    app = get_firebase_app()

    try:
        loop = asyncio.get_event_loop()
        decoded: dict = await loop.run_in_executor(
            None,
            partial(firebase_auth.verify_id_token, token, app=app),
        )
    except firebase_auth.ExpiredIdTokenError as exc:
        logger.info("firebase.token_expired token_prefix=%s", token_prefix)
        raise AuthTokenExpiredError() from exc
    except firebase_auth.RevokedIdTokenError as exc:
        logger.info("firebase.token_revoked token_prefix=%s", token_prefix)
        raise AuthTokenRevokedError() from exc
    except (
        firebase_auth.InvalidIdTokenError,
        firebase_auth.UserDisabledError,
        ValueError,
    ) as exc:
        logger.info(
            "firebase.token_invalid token_prefix=%s error=%s",
            token_prefix,
            type(exc).__name__,
        )
        raise AuthTokenInvalidError() from exc
    except FirebaseError as exc:
        logger.error(
            "firebase.sdk_error token_prefix=%s error=%s",
            token_prefix,
            type(exc).__name__,
        )
        raise FirebaseUnavailableError() from exc

    payload = FirebaseTokenPayload(
        uid=decoded["uid"],
        email=decoded.get("email"),
        phone_number=decoded.get("phone_number"),
        name=decoded.get("name"),
        picture=decoded.get("picture"),
        email_verified=decoded.get("email_verified", False),
    )

    logger.debug("firebase.verify_success firebase_uid=%s", payload.uid)
    return payload
