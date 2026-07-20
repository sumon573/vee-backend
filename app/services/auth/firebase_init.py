"""
Firebase Admin SDK — production-safe singleton initializer.

Architecture:
    - Initialized exactly once per process via get_firebase_app().
    - Credentials are read from environment variables — never from disk
      (no service account JSON file required in production).
    - Private key newlines are normalized: hosting platforms often store
      the PEM key with literal \\n — this module converts them to real
      newlines before passing to the SDK.

Security:
    - Private key value is NEVER logged.
    - Only project_id and client_email appear in log output.

Usage:
    from app.services.auth.firebase_init import get_firebase_app
    app = get_firebase_app()
    decoded = firebase_auth.verify_id_token(token, app=app)
"""

import logging

import firebase_admin
from firebase_admin import credentials

from app.core.config import settings
from app.core.exceptions import FirebaseUnavailableError

logger = logging.getLogger(__name__)

# Module-level singleton — set once and reused for the process lifetime.
_firebase_app: firebase_admin.App | None = None


def get_firebase_app() -> firebase_admin.App:
    """
    Return the initialized Firebase Admin App singleton.

    On first call: reads credentials from environment variables and
    initializes the Firebase Admin SDK.
    On subsequent calls: returns the cached app instance immediately.

    Returns:
        An initialized firebase_admin.App.

    Raises:
        FirebaseUnavailableError: If credentials are missing or the SDK
            fails to initialize.
    """
    global _firebase_app

    if _firebase_app is not None:
        return _firebase_app

    # Attempt to reuse an existing app (e.g. if tests or other code
    # already called firebase_admin.initialize_app).
    try:
        _firebase_app = firebase_admin.get_app()
        logger.info(
            "firebase.reused_existing_app project_id=%s",
            settings.FIREBASE_PROJECT_ID,
        )
        return _firebase_app
    except ValueError:
        pass  # No existing app — initialize below.

    if not all([
        settings.FIREBASE_PROJECT_ID,
        settings.FIREBASE_CLIENT_EMAIL,
        settings.FIREBASE_PRIVATE_KEY,
    ]):
        raise FirebaseUnavailableError(
            "Firebase credentials are not configured. "
            "Set FIREBASE_PROJECT_ID, FIREBASE_CLIENT_EMAIL, and "
            "FIREBASE_PRIVATE_KEY environment variables."
        )

    # Normalize private key: hosting platforms often store PEM with literal \\n.
    private_key = settings.FIREBASE_PRIVATE_KEY.replace("\\n", "\n")

    try:
        cred = credentials.Certificate(
            {
                "type": "service_account",
                "project_id": settings.FIREBASE_PROJECT_ID,
                "client_email": settings.FIREBASE_CLIENT_EMAIL,
                "private_key": private_key,
                "token_uri": "https://oauth2.googleapis.com/token",
            }
        )
        _firebase_app = firebase_admin.initialize_app(cred)
        logger.info(
            "firebase.initialized project_id=%s client_email=%s",
            settings.FIREBASE_PROJECT_ID,
            settings.FIREBASE_CLIENT_EMAIL,
            # private_key is intentionally omitted from logs.
        )
    except Exception as exc:
        logger.error("firebase.init_failed error=%s", type(exc).__name__)
        raise FirebaseUnavailableError(
            "Failed to initialize Firebase Admin SDK."
        ) from exc

    return _firebase_app
