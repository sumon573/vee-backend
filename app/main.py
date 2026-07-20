"""
Vee API — FastAPI application factory.

Startup order:
    1. FastAPI app created with metadata.
    2. CORS middleware registered.
    3. Global exception handlers registered.
    4. API routers mounted.
    5. Health endpoints defined.

Exception → HTTP status map (Phase 5 + Phase 6):
    AuthTokenExpiredError    → 401
    AuthTokenRevokedError    → 401
    AuthError (all others)   → 401
    InactiveUserError        → 403
    UserNotFoundError        → 404
    UsernameConflictError    → 409
    ReservedUsernameError    → 422
    FirebaseUnavailableError → 503
"""

import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1 import router as v1_router
from app.core.config import settings
from app.core.exceptions import (
    AuthError,
    AuthTokenExpiredError,
    AuthTokenRevokedError,
    FirebaseUnavailableError,
    InactiveUserError,
    ReservedUsernameError,
    UserNotFoundError,
    UsernameConflictError,
    VeeError,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Application
# ---------------------------------------------------------------------------

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Vee — Social Audio Platform API",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# ---------------------------------------------------------------------------
# Middleware
# ---------------------------------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Global exception handlers
#
# Domain exceptions → structured JSON error body.
# More-specific handlers must be registered before catch-all handlers.
# ---------------------------------------------------------------------------


def _error_body(exc: VeeError) -> dict:
    """Build a consistent error response payload."""
    return {"error": exc.code, "message": exc.message}


# ---- 401 — Authentication failures ----------------------------------------

@app.exception_handler(AuthTokenExpiredError)
async def token_expired_handler(
    request: Request, exc: AuthTokenExpiredError
) -> JSONResponse:
    return JSONResponse(
        status_code=401,
        content=_error_body(exc),
        headers={"WWW-Authenticate": "Bearer"},
    )


@app.exception_handler(AuthTokenRevokedError)
async def token_revoked_handler(
    request: Request, exc: AuthTokenRevokedError
) -> JSONResponse:
    return JSONResponse(
        status_code=401,
        content=_error_body(exc),
        headers={"WWW-Authenticate": "Bearer"},
    )


@app.exception_handler(AuthError)
async def auth_error_handler(request: Request, exc: AuthError) -> JSONResponse:
    """Catch-all for any AuthError subclass not handled above."""
    return JSONResponse(
        status_code=401,
        content=_error_body(exc),
        headers={"WWW-Authenticate": "Bearer"},
    )


# ---- 403 — Authorisation failures -----------------------------------------

@app.exception_handler(InactiveUserError)
async def inactive_user_handler(
    request: Request, exc: InactiveUserError
) -> JSONResponse:
    return JSONResponse(status_code=403, content=_error_body(exc))


# ---- 404 — Not found -------------------------------------------------------

@app.exception_handler(UserNotFoundError)
async def user_not_found_handler(
    request: Request, exc: UserNotFoundError
) -> JSONResponse:
    return JSONResponse(status_code=404, content=_error_body(exc))


# ---- 409 — Conflict --------------------------------------------------------

@app.exception_handler(UsernameConflictError)
async def username_conflict_handler(
    request: Request, exc: UsernameConflictError
) -> JSONResponse:
    return JSONResponse(status_code=409, content=_error_body(exc))


# ---- 422 — Validation / semantic errors ------------------------------------

@app.exception_handler(ReservedUsernameError)
async def reserved_username_handler(
    request: Request, exc: ReservedUsernameError
) -> JSONResponse:
    return JSONResponse(status_code=422, content=_error_body(exc))


# ---- 503 — External service failures ---------------------------------------

@app.exception_handler(FirebaseUnavailableError)
async def firebase_unavailable_handler(
    request: Request, exc: FirebaseUnavailableError
) -> JSONResponse:
    logger.error("firebase.unavailable path=%s", request.url.path)
    return JSONResponse(status_code=503, content=_error_body(exc))


# ---------------------------------------------------------------------------
# API routers
# ---------------------------------------------------------------------------

app.include_router(v1_router, prefix="/api/v1")

# ---------------------------------------------------------------------------
# Health endpoints
# ---------------------------------------------------------------------------


@app.get("/", tags=["Health"])
async def root() -> dict:
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "operational",
        "environment": settings.APP_ENV,
        "docs": "/docs",
    }


@app.get("/health", tags=["Health"])
async def health_check() -> dict:
    return {"status": "healthy"}
