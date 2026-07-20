"""
Authentication routes — /api/v1/auth/

Architecture:
    - Defines the HTTP surface for auth-related operations.
    - Delegates all business logic to services; never calls repositories directly.
    - Returns Pydantic response schemas; never returns raw ORM objects.

Current state (Phase 4 — Foundation):
    Only the router and its prefix/tags are defined.
    Actual endpoints (login, token refresh, logout) are implemented in Phase 5
    once Firebase token verification is live.

TODO (Phase 5):
    POST /api/v1/auth/login   — accept Firebase ID token, return AuthenticatedUser
    POST /api/v1/auth/refresh — refresh session (if applicable)
    POST /api/v1/auth/logout  — revoke token / blacklist (if applicable)
"""

from fastapi import APIRouter

router = APIRouter(
    prefix="/auth",
    tags=["auth"],
)

# ---------------------------------------------------------------------------
# TODO (Phase 5): Add authentication endpoints below.
#
# Example structure:
#
#   from fastapi import Depends, HTTPException, status
#   from app.db.session import get_db
#   from app.schemas.auth import FirebaseTokenPayload
#   from app.schemas.user import UserRead
#   from app.services.auth import verify_firebase_token
#   from app.services.user_service import UserService
#   from sqlalchemy.ext.asyncio import AsyncSession
#
#   @router.post("/login", response_model=UserRead, status_code=status.HTTP_200_OK)
#   async def login(
#       token: str,
#       db: AsyncSession = Depends(get_db),
#   ) -> UserRead:
#       payload: FirebaseTokenPayload = await verify_firebase_token(token)
#       service = UserService(db)
#       user = await service.get_or_create_from_firebase(payload)
#       return UserRead.model_validate(user)
#
# ---------------------------------------------------------------------------
