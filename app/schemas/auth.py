"""
Pydantic v2 schemas for authentication data transfer objects.

These schemas represent the parsed and validated data from a
Firebase ID token, not HTTP request/response bodies directly.

Rules:
    - No SQLAlchemy imports.
    - No db session imports.
    - Use `model_config = ConfigDict(...)` — not inner Config class.
"""

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class FirebaseTokenPayload(BaseModel):
    """
    Validated claims extracted from a decoded Firebase ID token.

    Field names match the standard JWT / Firebase token claim keys.

    TODO (Phase 5): Populate this from firebase-admin.auth.verify_id_token()
    """

    model_config = ConfigDict(frozen=True)

    uid: str = Field(..., description="Firebase UID — stable unique identifier.")
    email: Optional[str] = Field(default=None, description="Email if provided and verified.")
    phone_number: Optional[str] = Field(default=None, description="E.164 phone number if linked.")
    name: Optional[str] = Field(default=None, description="Display name from the Firebase profile.")
    picture: Optional[str] = Field(default=None, description="Avatar URL from the Firebase profile.")
    email_verified: bool = Field(default=False)


class AuthenticatedUser(BaseModel):
    """
    Lightweight representation of the authenticated caller injected
    into route handlers via the `get_current_user` dependency.

    Carries only what route handlers and services need — not the
    full ORM model (use UserService for that).

    TODO (Phase 5): Extend once full user record is resolved from DB.
    """

    model_config = ConfigDict(frozen=True)

    firebase_uid: str
    email: Optional[str] = None
    phone: Optional[str] = None
    display_name: Optional[str] = None
