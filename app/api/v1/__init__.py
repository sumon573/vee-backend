"""
API v1 — combined router.

All v1 resource routers are registered here and exposed as a single
`router` object that app/main.py mounts at `/api/v1`.

To add a new resource:
    1. Create app/api/v1/<resource>.py with an APIRouter.
    2. Import and include it below.
    3. No changes to app/main.py are required.

IMPORTANT — Router include order:
    Routers with static paths under /users/ (e.g. /users/blocked, /users/me)
    must be included BEFORE the users router to prevent FastAPI from capturing
    static segments as {username} wildcard values.
"""

from fastapi import APIRouter

from app.api.v1 import auth, blocks, follows, messages, users

router = APIRouter()

# Auth routes — /api/v1/auth/...
router.include_router(auth.router)

# Privacy / block routes — /api/v1/users/blocked, /api/v1/users/{username}/block  (Phase 8)
# MUST be included before users.router — /users/blocked must match before /users/{username}
router.include_router(blocks.router)

# User profile routes — /api/v1/users/...  (Phase 6)
router.include_router(users.router)

# Social graph routes — /api/v1/users/{username}/follow|followers|following|relationship  (Phase 7)
router.include_router(follows.router)

# Direct Messaging routes — /api/v1/messages/...  (Phase 9)
# Static sub-paths (/conversations) are defined before dynamic (/{conversation_id})
# inside the messages router itself, so include order here is safe.
router.include_router(messages.router)
