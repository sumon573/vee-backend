# Changelog

All notable changes to this project will be documented in this file.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
This project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

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
- `app/repositories/user_repo.py` — all methods implemented: `get_by_id` (session.get), `get_by_firebase_uid` (select+where), `get_by_username`, `get_by_email`, `create` (add+flush+refresh), `update_last_seen` (UTC stamp+flush), `update_profile` (allowlist-guarded setattr+flush), `save` (flush)

#### Service
- `app/services/user_service.py` — all methods implemented: `sync_firebase_user()` (get-or-create; auto-generates username `vee_<uid[:16]>`; uses Firebase claims for display_name/email/phone/avatar), `get_profile()`, `get_by_id()`, `update_last_seen()` (non-fatal; swallows errors with warning log)

#### API Endpoints
- `POST /api/v1/auth/login` — verifies Firebase ID token (Bearer), syncs user, updates presence, returns `UserRead`
- `GET /api/v1/auth/me` — protected; returns current user profile via `get_current_user` dependency

#### Application Wiring
- `app/main.py` — global exception handlers: `InactiveUserError` → 403, `FirebaseUnavailableError` → 503, `AuthTokenExpiredError` → 401, `AuthTokenRevokedError` → 401, `AuthError` (catch-all) → 401; all auth error responses follow `{"error": "<code>", "message": "<text>"}` shape
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

#### Schemas (Pydantic v2)
- `app/schemas/user.py` — `UserBase`, `UserRead` (with `from_attributes=True`), `UserCreate`, `UserUpdate`
- `app/schemas/auth.py` — `FirebaseTokenPayload` (frozen, maps Firebase JWT claims), `AuthenticatedUser` (lightweight DTO injected into route handlers)

#### Authentication Foundation
- `app/services/auth/__init__.py` — public surface: `verify_firebase_token`, `get_current_user`
- `app/services/auth/firebase.py` — `verify_firebase_token()` stub with full TODO for Phase 5 firebase-admin integration
- `app/services/auth/dependencies.py` — `get_current_user` FastAPI dependency stub using `HTTPBearer`; raises `HTTP 501` until Phase 5 implements real verification

#### Service & Repository Skeletons
- `app/repositories/user_repo.py` — `UserRepository` with method signatures: `get_by_id`, `get_by_firebase_uid`, `get_by_username`, `get_by_email`, `create`, `save`
- `app/services/user_service.py` — `UserService` with method signatures: `get_or_create_from_firebase`, `get_by_id`, `update_last_seen`

#### API Structure
- `app/api/v1/__init__.py` — combined v1 `APIRouter`; new resource routers registered here without touching `app/main.py`
- `app/api/v1/auth.py` — `APIRouter(prefix="/auth", tags=["auth"])` with structured TODO for Phase 5 endpoints

#### Application Wiring
- `app/main.py` — v1 router mounted at `/api/v1`
- `alembic/env.py` — `User` model imported so Alembic detects `users` table

#### Migrations
- `alembic/versions/<timestamp>_phase_4_add_users_table.py` — auto-generated migration creating `gender_enum` PostgreSQL type and `users` table with all columns and indexes

### Added — Phase 3: Documentation & Architecture Governance

- `ARCHITECTURE.md` — full architecture reference (layers, request flow, scaling, DB config)
- `PROJECT_ROADMAP.md` — master phase roadmap (14 phases, goal/deliverables/success criteria per phase)
- `CONTRIBUTING.md` — branch strategy, Conventional Commits, coding standards, PR rules, review checklist
- `CHANGELOG.md` — this file; Keep a Changelog format
- `AI_AGENT.md` — instruction manual for future AI agents
- `README.md` updated with documentation links table and roadmap status table

---

## [0.1.0] — 2026-07-20

### Added — Phase 2: Database Foundation

- `app/db/base.py` — `DeclarativeBase` shared by all future ORM models
- `app/db/database.py` — async SQLAlchemy engine with production connection pool settings (`pool_size=10`, `max_overflow=20`, `pool_pre_ping=True`, `pool_recycle=3600`)
- `app/db/session.py` — `AsyncSessionLocal` session factory and `get_db` FastAPI dependency (async generator with rollback-on-error)
- `app/db/__init__.py` — public re-exports: `Base`, `engine`, `AsyncSessionLocal`, `get_db`
- `app/utils/db_url.py` — `normalize_database_url()` utility: converts `postgres://` / `postgresql://` to `postgresql+asyncpg://` and strips `sslmode` / SSL query parameters incompatible with asyncpg
- `alembic/` — Alembic initialized with async migration support (`asyncio.run` + `async_engine_from_config`)
- `alembic/env.py` — configured to read `DATABASE_URL` from environment, normalize it, and import `Base.metadata` for autogenerate
- `alembic.ini` — `sqlalchemy.url` delegated to environment variable
- `DATABASE_URL` field added to `app/core/config.py`
- `requirements.txt` updated: `sqlalchemy>=2.0.0`, `alembic>=1.13.0`, `asyncpg>=0.29.0`
- `.env.example` updated with `DATABASE_URL` example
- `README.md` updated with Database Setup section and migration commands

### Added — Phase 1: Backend Foundation

- Python 3.12 runtime
- `app/main.py` — FastAPI application with `CORSMiddleware`, Swagger UI (`/docs`), ReDoc (`/redoc`)
- `app/core/config.py` — `pydantic_settings.BaseSettings` for environment-based configuration
- `GET /` — root endpoint returning `{"name", "version", "status", "environment", "docs"}`
- `GET /health` — health check endpoint returning `{"status": "healthy"}`
- Clean architecture folder scaffold: `api/`, `core/`, `db/`, `models/`, `schemas/`, `services/`, `repositories/`, `middleware/`, `utils/`
- `requirements.txt` — minimal dependencies: `fastapi`, `uvicorn[standard]`, `pydantic`, `pydantic-settings`, `python-dotenv`
- `.env.example` — environment variable template
- `.gitignore` — Python standard ignores
- `README.md` — project overview, tech stack, getting started guide, API endpoints

---

## Release Notes Format

When cutting a new release:

1. Move `[Unreleased]` content to a new versioned section
2. Add the release date: `## [X.Y.Z] — YYYY-MM-DD`
3. Group changes under: `Added`, `Changed`, `Deprecated`, `Removed`, `Fixed`, `Security`
4. Update `[Unreleased]` link at the bottom of this file

---

[Unreleased]: https://github.com/sumon573/vee-backend/compare/v0.3.0...HEAD
[0.3.0]: https://github.com/sumon573/vee-backend/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/sumon573/vee-backend/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/sumon573/vee-backend/releases/tag/v0.1.0
