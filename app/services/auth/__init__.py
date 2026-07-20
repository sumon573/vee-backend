"""
Authentication service package.

Public surface:
    verify_firebase_token   — verifies a raw Firebase ID token string
    get_current_user        — FastAPI dependency that resolves the caller
"""

from app.services.auth.dependencies import get_current_user
from app.services.auth.firebase import verify_firebase_token

__all__ = [
    "verify_firebase_token",
    "get_current_user",
]
