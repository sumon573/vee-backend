"""
FastAPI authentication dependency — production implementation.

Usage in route handlers:
    from app.services.auth import get_current_user
    from app.models.user import User

    @router.get("/me")
    async def get_me(
        current_user: User = Depends(get_current_user),
    ) -> UserRead:
        return UserRead.model_validate(current_user)

Flow:
    1. HTTPBearer extracts the token from "Authorization: Bearer <token>".
    2. IdentityService.login_with_firebase() verifies the token, syncs the
       user record (get-or-create), and updates last_seen_at.
    3. The resolved User ORM instance is returned to the route handler.
    4. Domain exceptions (AuthError, InactiveUserError) are caught and
       re-raised as HTTP 401 / 403 by the handlers registered in main.py.

Security:
    - auto_error=True means FastAPI returns HTTP 403 immediately if the
      Authorization header is missing (before this function is called).
    - Inactive accounts raise HTTP 403.
    - Any token verification failure raises HTTP 401.
"""

import logging
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AuthError, InactiveUserError
from app.db.session import get_db
from app.models.user import User
from app.services.identity_service import IdentityService

logger = logging.getLogger(__name__)

# HTTPBearer extracts the token from "Authorization: Bearer <token>".
# auto_error=True  → FastAPI returns HTTP 403 if the header is absent.
# auto_error=False → FastAPI passes None if the header is absent (optional auth).
_bearer_scheme = HTTPBearer(auto_error=True)
_bearer_scheme_optional = HTTPBearer(auto_error=False)


async def get_optional_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(
        _bearer_scheme_optional
    ),
    db: AsyncSession = Depends(get_db),
) -> Optional[User]:
    """
    FastAPI dependency that resolves the authenticated caller when a token is
    present, or returns None when no Authorization header is supplied.

    Use this on public endpoints that optionally enrich the response with
    user-specific data (e.g. relationship status on a public profile page).

    Args:
        credentials: Optional HTTPBearer-extracted Authorization header value.
        db: Async database session from get_db().

    Returns:
        The resolved User ORM instance, or None if no token was provided.

    Raises:
        HTTPException 401: Token was provided but is invalid, expired, or revoked.
        HTTPException 403: Token was provided but the account is inactive.
    """
    if credentials is None:
        return None
    try:
        identity_service = IdentityService(db)
        user: User = await identity_service.login_with_firebase(
            credentials.credentials
        )
        return user
    except InactiveUserError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error": exc.code, "message": exc.message},
        ) from exc
    except AuthError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": exc.code, "message": exc.message},
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    FastAPI dependency that resolves the authenticated caller.

    Verifies the Firebase ID token, loads (or creates) the user record
    from the database, and updates the presence timestamp.

    Args:
        credentials: HTTPBearer-extracted Authorization header value.
        db: Async database session from get_db().

    Returns:
        The fully resolved User ORM instance.

    Raises:
        HTTPException 401: Token is invalid, expired, or revoked.
        HTTPException 403: Account is inactive / suspended.
    """
    try:
        identity_service = IdentityService(db)
        user: User = await identity_service.login_with_firebase(
            credentials.credentials
        )
        return user
    except InactiveUserError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error": exc.code, "message": exc.message},
        ) from exc
    except AuthError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": exc.code, "message": exc.message},
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc
