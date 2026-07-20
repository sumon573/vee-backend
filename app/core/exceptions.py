"""
Vee domain exception hierarchy.

Rules:
    - Domain exceptions never import HTTPException or FastAPI.
    - HTTP mapping lives in app/main.py exception handlers.
    - Every exception carries a machine-readable `code` and a
      human-readable `message` so the handler can serialize a
      consistent JSON error body.

Exception → HTTP status mapping (enforced in app/main.py):
    AuthTokenInvalidError  → 401
    AuthTokenExpiredError  → 401
    AuthTokenRevokedError  → 401
    FirebaseUnavailableError → 503
    InactiveUserError      → 403
"""


# ---------------------------------------------------------------------------
# Base
# ---------------------------------------------------------------------------


class VeeError(Exception):
    """Root exception for all Vee domain errors."""

    code: str = "vee_error"
    message: str = "An unexpected error occurred."

    def __init__(self, message: str | None = None) -> None:
        self.message = message or self.__class__.message
        super().__init__(self.message)

    def __str__(self) -> str:
        return self.message


# ---------------------------------------------------------------------------
# Authentication errors
# ---------------------------------------------------------------------------


class AuthError(VeeError):
    """Base class for all authentication failures."""

    code = "auth_error"
    message = "Authentication failed."


class AuthTokenInvalidError(AuthError):
    """Token is structurally invalid or signed with the wrong key."""

    code = "invalid_token"
    message = "The authentication token is invalid or malformed."


class AuthTokenExpiredError(AuthError):
    """Token has passed its expiry time."""

    code = "token_expired"
    message = "The authentication token has expired. Please sign in again."


class AuthTokenRevokedError(AuthError):
    """Token has been explicitly revoked (e.g. user signed out on another device)."""

    code = "token_revoked"
    message = "The authentication token has been revoked. Please sign in again."


class FirebaseUnavailableError(AuthError):
    """Firebase Authentication service could not be reached or is misconfigured."""

    code = "firebase_unavailable"
    message = "Authentication service is temporarily unavailable. Please try again."


# ---------------------------------------------------------------------------
# User / authorisation errors
# ---------------------------------------------------------------------------


class InactiveUserError(VeeError):
    """Account exists but is suspended or soft-deleted."""

    code = "account_inactive"
    message = "This account has been suspended or deactivated."
