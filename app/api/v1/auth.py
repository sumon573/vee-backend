"""
Authentication routes — /api/v1/auth/

Endpoints:
    POST /api/v1/auth/login
        Accepts a Firebase ID token via Authorization: Bearer header.
        Verifies the token, gets or creates the user, updates last_seen_at,
        and returns the full user profile.

Architecture:
    - Delegates all business logic to IdentityService.
    - Returns Pydantic response schemas; never returns raw ORM objects.
    - Domain exceptions are handled by FastAPI exception handlers in main.py.

Future endpoints (Phase 6+):
    POST /api/v1/auth/logout  — token revocation / session invalidation
    GET  /api/v1/auth/me      — return currently authenticated user
"""

import logging

from fastapi import APIRouter, Depends, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.user import User
from app.schemas.user import UserRead
from app.services.auth.dependencies import get_current_user
from app.services.identity_service import IdentityService

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/auth",
    tags=["auth"],
)

_bearer_scheme = HTTPBearer(auto_error=True)


# ---------------------------------------------------------------------------
# POST /api/v1/auth/login
# ---------------------------------------------------------------------------


@router.post(
    "/login",
    response_model=UserRead,
    status_code=status.HTTP_200_OK,
    summary="Authenticate with a Firebase ID token",
    description=(
        "Accepts a Firebase ID token in the `Authorization: Bearer <token>` header. "
        "Verifies the token, creates the user profile on first login, "
        "updates last_seen_at, and returns the full user profile."
    ),
)
async def login(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> UserRead:
    """
    Login / register flow.

    The client sends their Firebase ID token (obtained from the Firebase
    client SDK after phone/Google/Apple sign-in). The server:

    1. Verifies the token cryptographically against Firebase's public keys.
    2. Looks up the user by firebase_uid.
    3. Creates a new user record if this is a first-time login.
    4. Rejects the request if the account is inactive.
    5. Stamps last_seen_at and returns the full UserRead profile.

    Errors:
        401 invalid_token   — token is malformed or signature invalid
        401 token_expired   — token has expired (client must refresh)
        401 token_revoked   — token has been revoked
        403 account_inactive — account is suspended or deactivated
        503 firebase_unavailable — Firebase service unreachable
    """
    identity_service = IdentityService(db)
    user: User = await identity_service.login_with_firebase(
        credentials.credentials
    )
    return UserRead.model_validate(user)


# ---------------------------------------------------------------------------
# GET /api/v1/auth/me
# ---------------------------------------------------------------------------


@router.get(
    "/me",
    response_model=UserRead,
    status_code=status.HTTP_200_OK,
    summary="Return the currently authenticated user",
    description=(
        "Protected endpoint. Requires `Authorization: Bearer <firebase_id_token>`. "
        "Returns the full profile of the currently authenticated user."
    ),
)
async def get_me(
    current_user: User = Depends(get_current_user),
) -> UserRead:
    """
    Return the authenticated caller's profile.

    Uses the `get_current_user` dependency which handles token verification,
    user sync, and presence update automatically.
    """
    return UserRead.model_validate(current_user)
