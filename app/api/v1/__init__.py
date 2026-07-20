"""
API v1 — combined router.

All v1 resource routers are registered here and exposed as a single
`router` object that app/main.py mounts at `/api/v1`.

To add a new resource:
    1. Create app/api/v1/<resource>.py with an APIRouter.
    2. Import and include it below.
    3. No changes to app/main.py are required.
"""

from fastapi import APIRouter

from app.api.v1 import auth

router = APIRouter()

# Auth routes — /api/v1/auth/...
router.include_router(auth.router)
