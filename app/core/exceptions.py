"""
Vee domain exception hierarchy.

Rules:
    - Domain exceptions never import HTTPException or FastAPI.
    - HTTP mapping lives in app/main.py exception handlers.
    - Every exception carries a machine-readable `code` and a
      human-readable `message` so the handler can serialize a
      consistent JSON error body.

Exception → HTTP status mapping (enforced in app/main.py):
    AuthTokenInvalidError    → 401
    AuthTokenExpiredError    → 401
    AuthTokenRevokedError    → 401
    FirebaseUnavailableError → 503
    SelfBlockError           → 400
    InactiveUserError        → 403
    UserNotFoundError        → 404
    UsernameConflictError    → 409
    AlreadyBlockedError      → 409
    NotBlockedError          → 409
    ReservedUsernameError    → 422
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


class UserNotFoundError(VeeError):
    """Requested user record does not exist."""

    code = "user_not_found"
    message = "User not found."


class UsernameConflictError(VeeError):
    """Attempted username is already taken by another account."""

    code = "username_conflict"
    message = "This username is already taken. Please choose a different one."


class ReservedUsernameError(VeeError):
    """Attempted username is on the reserved list and cannot be claimed by users."""

    code = "reserved_username"
    message = "This username is reserved and cannot be used."


# ---------------------------------------------------------------------------
# Social graph errors  (Phase 7)
# ---------------------------------------------------------------------------


class SelfFollowError(VeeError):
    """Caller attempted to follow their own account."""

    code = "self_follow"
    message = "You cannot follow yourself."


class AlreadyFollowingError(VeeError):
    """Caller already follows the target user."""

    code = "already_following"
    message = "You are already following this user."


class NotFollowingError(VeeError):
    """Caller attempted to unfollow a user they do not follow."""

    code = "not_following"
    message = "You are not following this user."


# ---------------------------------------------------------------------------
# Privacy / blocking errors  (Phase 8)
# ---------------------------------------------------------------------------


class SelfBlockError(VeeError):
    """Caller attempted to block their own account."""

    code = "self_block"
    message = "You cannot block yourself."


class AlreadyBlockedError(VeeError):
    """Caller has already blocked the target user."""

    code = "already_blocked"
    message = "You have already blocked this user."


class NotBlockedError(VeeError):
    """Caller attempted to unblock a user they have not blocked."""

    code = "not_blocked"
    message = "You have not blocked this user."


# ---------------------------------------------------------------------------
# Direct Messaging errors  (Phase 9)
# ---------------------------------------------------------------------------


class SelfMessageError(VeeError):
    """Caller attempted to start a conversation with themselves."""

    code = "self_message"
    message = "You cannot send a message to yourself."


class ConversationNotFoundError(VeeError):
    """Conversation does not exist or the requesting user is not a participant."""

    code = "conversation_not_found"
    message = "Conversation not found."


class MessagePermissionError(VeeError):
    """Caller is blocked by or has blocked the recipient."""

    code = "message_not_allowed"
    message = "You are not allowed to message this user."
