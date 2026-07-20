"""
FastAPI authentication dependency.

Usage in route handlers:
    from app.services.auth import get_current_user
    from app.schemas.auth import AuthenticatedUser

    @router.get("/me")
    async def get_me(
        current_user: AuthenticatedUser = Depends(get_current_user),
    ) -> UserRead:
        ...

Architecture:
    - Extracts the Bearer token from the Authorization header.
    - Calls verify_firebase_token() to decode and validate it.
    - Returns an AuthenticatedUser — a lightweight, frozen DTO.
    - Route handlers and services receive this DTO, not raw tokens.

TODO (Phase 5):
    1. Implement the token extraction and verification call below.
    2. Add DB lookup (via UserService) to resolve the full User record.
    3. Raise HTTP 401 with a structured error body on any auth failure.
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.schemas.auth import AuthenticatedUser

# HTTPBearer extracts the token from "Authorization: Bearer <token>"
_bearer_scheme = HTTPBearer(auto_error=True)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer_scheme),
) -> AuthenticatedUser:
    """
    FastAPI dependency that validates the caller's Firebase ID token
    and returns an AuthenticatedUser DTO.

    Args:
        credentials: Injected by FastAPI from the Authorization header.

    Returns:
        AuthenticatedUser with verified identity claims.

    Raises:
        HTTPException 401: If the token is missing, expired, or invalid.

    Note:
        This is a stub. Full implementation is in Phase 5.
    """
    # TODO (Phase 5): Replace with real token verification:
    #
    #   from app.services.auth.firebase import verify_firebase_token
    #   payload = await verify_firebase_token(credentials.credentials)
    #   return AuthenticatedUser(
    #       firebase_uid=payload.uid,
    #       email=payload.email,
    #       phone=payload.phone_number,
    #       display_name=payload.name,
    #   )

    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Authentication is not yet implemented. Coming in Phase 5.",
    )
