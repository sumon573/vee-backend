# Changelog

All notable changes to this project will be documented in this file.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
This project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

---

## [0.4.0] — 2026-07-20

### Added — Phase 6: Extended User Profile Management

#### Domain Exceptions
- `app/core/exceptions.py` — added `UserNotFoundError` (404), `UsernameConflictError` (409), `ReservedUsernameError` (422)

#### User Model
- `app/models/user.py` — added `deleted_at` column (`TIMESTAMP WITH TIME ZONE`, nullable); NULL = active account, non-null = user-initiated soft-delete; reduced `username` column size from `VARCHAR(50)` to `VARCHAR(30)` to match validation rule; added `ix_users_deleted_at` index for efficient soft-delete filtering

#### Schemas
- `app/schemas/user.py` — added username regex validation (`^[a-z0-9_]{3,30}$`); added `RESERVED_USERNAMES` frozenset (80+ reserved names); added `@field_validator` for both `UserBase.username` and `UserUpdate.username`; added `UserPublicRead` (public profile — excludes firebase_uid, email, phone, birth_date); added `UserDeletedRead` (soft-delete confirmation response); updated `UserUpdate` to support `username` changes with validation

#### Repository
- `app/repositories/user_repo.py` — added `soft_delete()` (sets deleted_at + is_active=False, logs event); added `search_by_username_prefix()` (ILIKE prefix match, active-only, max 100 results, ordered by username)

#### Service
- `app/services/user_service.py` — added `get_by_username()` (active-only look-up with UserNotFoundError); added `update_my_profile()` (validates reserved names + uniqueness before delegating to repo); added `soft_delete_user()` (delegates to repo, logs event)

#### API Endpoints (Phase 6)
- `GET /api/v1/users/me` — protected; returns own full profile (`UserRead`)
- `PATCH /api/v1/users/me` — protected; partial profile update (`UserUpdate` → `UserRead`)
- `DELETE /api/v1/users/me` — protected; soft-delete own account (`UserDeletedRead`)
- `GET /api/v1/users/{username}` — public; returns public profile (`UserPublicRead`); 404 on missing/deleted

#### Application Wiring
- `app/api/v1/__init__.py` — registered `users.router` at `/api/v1/users/`
- `app/main.py` — added exception handlers: `UserNotFoundError` → 404, `UsernameConflictError` → 409, `ReservedUsernameError` → 422; reordered handlers most-specific-first

#### Migration
- `alembic/versions/a8f3d1c90e2b_phase_6_add_deleted_at_to_users.py` — adds `deleted_at` column, `ix_users_deleted_at` index, shrinks `username` to `VARCHAR(30)`

---

## [0.3.0] — 2026-07-20

### Added — Phase 5: Identity & Authentication Infrastructure

#### Exceptions
- `app/core/exceptions.py` — domain exception hierarchy: `VeeError` (root), `AuthError` (base auth), `AuthTokenInvalidError`, `AuthTokenExpiredError`, `AuthTokenRevokedError`, `FirebaseUnavailableError`, `InactiveUserError`; every exception carries a machine-readable `code` and human-readable `message`

#### Configuration
- `app/core/config.py` — added `FIREBASE_PROJECT_ID`, `FIREBASE_CLIENT_EMAIL`, `FIREBASE_PRIVATE_KEY` fields; private key `\\n` normalization documented

#### Firebase Admin SDK
- `app/services/auth/firebase_init.py` — production-safe singleton; credentials from env vars (never from disk); `\\n` → newline normalization for PEM keys; private key never logged; `get_app()` reuse guard prevents double-initialization
- `app/services/auth/firebase.py` — `verify_firebase_token()` fully implemented; runs `verify_id_token` in thread-pool executor (non-blocking); maps `ExpiredIdTokenError`, `RevokedIdTokenError`, `InvalidIdTokenError`, `FirebaseError` → domain exceptions; only safe token prefix logged

#### Authentication Dependency
- `app/services/auth/dependencies.py` — `get_current_user()` fully implemented; uses `IdentityService.login_with_firebase()`; maps `InactiveUserError` → HTTP 403, `AuthError` → HTTP 401 with `WWW-Authenticate: Bearer`

#### Identity Service (new)
- `app/services/identity_service.py` — `IdentityService`; `login_with_firebase()` (verify → sync → guard inactive → update presence → return User); `get_identity()` (lightweight token introspection); designed for future provider extension

#### Repository
- `app/repositories/user_repo.py` — all methods implemented: `get_by_id`, `get_by_firebase_uid`, `get_by_username`, `get_by_email`, `create`, `update_last_seen`, `update_profile`, `save`

#### Service
- `app/services/user_service.py` — all methods implemented: `sync_firebase_user()`, `get_profile()`, `get_by_id()`, `update_last_seen()`

#### API Endpoints
- `POST /api/v1/auth/login` — verifies Firebase ID token (Bearer), syncs user, updates presence, returns `UserRead`
- `GET /api/v1/auth/me` — protected; returns current user profile via `get_current_user` dependency

#### Application Wiring
- `app/main.py` — global exception handlers for all auth errors
- `.env.example` — Firebase credential fields with setup instructions
- `requirements.txt` — `firebase-admin>=6.5.0`

---

## [0.2.0] — 2026-07-20

### Added — Phase 4: Core Domain Models & Authentication Foundation

#### Models
- `app/models/enums.py` — `Gender` string enum (`male`, `female`, `other`, `prefer_not_to_say`)
- `app/models/user.py` — `User` ORM model with 14 fields: `id` (UUID v4), `firebase_uid`, `username`, `display_name`, `email`, `phone`, `avatar_url`, `bio`, `gender`, `birth_date`, `is_verified`, `is_active`, `created_at`, `updated_at`, `last_seen_at`; composite index on `(is_active, created_at)`

#### Database Mixins
- `app/db/mixins.py` — `UUIDMixin` (UUID v4 primary key) and `TimestampMixin` (`created_at` / `updated_at` with `server_default=func.now()`)

#### Schemas
- `app/schemas/user.py` — `UserBase`, `UserRead`, `UserCreate`, `UserUpdate`; Pydantic v2 with `ConfigDict`
- `app/schemas/auth.py` — `FirebaseTokenPayload` (frozen), `AuthenticatedUser`

#### Repository
- `app/repositories/user_repo.py` — `UserRepository` skeleton

#### Service
- `app/services/user_service.py` — `UserService` skeleton

#### API & Routing
- `app/api/v1/__init__.py` — combined v1 router
- `app/api/v1/auth.py` — auth router structure
- `app/main.py` — v1 router mounted at `/api/v1`

#### Migration
- `alembic/versions/cfeccaac3dc7_phase_4_add_users_table.py` — creates `gender_enum` PostgreSQL type and `users` table with all columns and indexes

---

## [0.1.0] — 2026-07-20

### Added — Phase 1 & 2: Backend & Database Foundation

- FastAPI application with Uvicorn, Pydantic Settings, CORS
- `GET /` and `GET /health` endpoints
- Swagger UI (`/docs`) and ReDoc (`/redoc`)
- SQLAlchemy 2.x async engine (asyncpg), `DeclarativeBase`, `get_db` dependency
- `normalize_database_url()` utility
- Alembic configured for async migrations
- `requirements.txt`, `.env.example`, `.gitignore`, `README.md`
