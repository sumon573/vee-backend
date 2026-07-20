"""
Firebase ID token verification.

Architecture:
    This module is the single point of contact with Firebase Authentication.
    It decodes and validates a raw Firebase ID token string and returns a
    structured `FirebaseTokenPayload` containing the verified claims.

    Route handlers and other services must never call Firebase directly —
    they receive an already-verified `AuthenticatedUser` via the
    `get_current_user` FastAPI dependency (see dependencies.py).

TODO (Phase 5 — Firebase Integration):
    1. Add `firebase-admin>=6.0` to requirements.txt
    2. Initialize the SDK once at app startup:

        import firebase_admin
        from firebase_admin import credentials, auth as firebase_auth

        _cred = credentials.Certificate(settings.FIREBASE_SERVICE_ACCOUNT_PATH)
        firebase_admin.initialize_app(_cred)

    3. Replace the stub below with the real implementation:

        decoded = firebase_auth.verify_id_token(token)
        return FirebaseTokenPayload(
            uid=decoded["uid"],
            email=decoded.get("email"),
            ...
        )

    4. Map Firebase error types to domain exceptions:
        firebase_admin.exceptions.InvalidArgumentError → 401
        firebase_admin.auth.ExpiredIdTokenError        → 401
        firebase_admin.auth.RevokedIdTokenError        → 401
"""

from app.schemas.auth import FirebaseTokenPayload


async def verify_firebase_token(token: str) -> FirebaseTokenPayload:
    """
    Verify a raw Firebase ID token and return its decoded claims.

    Args:
        token: The raw Bearer token string from the Authorization header.

    Returns:
        FirebaseTokenPayload with verified claims.

    Raises:
        TODO (Phase 5): Domain-specific auth exceptions mapped from
        firebase-admin error types.

    Note:
        This is a stub. Real verification is implemented in Phase 5.
    """
    # TODO (Phase 5): Replace with firebase_admin.auth.verify_id_token(token)
    raise NotImplementedError(
        "Firebase token verification is not yet implemented. "
        "This stub will be replaced in Phase 5."
    )
