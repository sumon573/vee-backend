# Vee Backend — Project Roadmap

> This is the **master roadmap** for the Vee backend. Every phase must be completed in order unless explicitly noted as parallelisable. Update this file at the start and end of every phase.

---

## Status Legend

| Symbol | Meaning |
|--------|---------|
| ✅ | Completed |
| 🔄 | In Progress |
| ⏳ | Pending |
| 🔒 | Blocked (depends on a prior phase) |

---

## Completed Phases

---

### ✅ Phase 1 — Backend Foundation

**Goal:** Establish a production-grade FastAPI application skeleton with zero business logic.

**Deliverables:**
- Python 3.12 runtime
- FastAPI application with Uvicorn server
- Pydantic Settings for environment-based config
- CORS middleware
- Root endpoint (`/`) returning JSON status
- Health check endpoint (`/health`)
- Swagger UI (`/docs`) and ReDoc (`/redoc`)
- `requirements.txt`, `.env.example`, `.gitignore`, `README.md`

**Success Criteria:**
- `uvicorn app.main:app` starts without errors
- `GET /` returns `{"status": "operational"}`
- `GET /docs` serves Swagger UI
- No dummy code, no unused dependencies

---

### ✅ Phase 2 — Database Foundation

**Goal:** Connect the application to PostgreSQL with a production-ready async database layer and migration tooling.

**Deliverables:**
- SQLAlchemy 2.x async engine (`asyncpg` driver)
- `app/db/base.py` — `DeclarativeBase` for all future models
- `app/db/database.py` — engine with connection pool config
- `app/db/session.py` — `AsyncSessionLocal` + `get_db` FastAPI dependency
- `app/utils/db_url.py` — URL normalizer (handles `sslmode`, scheme conversion)
- Alembic initialized and configured for async migrations
- `DATABASE_URL` env var support
- `requirements.txt` updated

---

### ✅ Phase 3 — Project Documentation & Architecture Governance

**Goal:** Make the repository self-documenting so any AI agent or developer can understand and extend it without prior context.

**Deliverables:**
- `ARCHITECTURE.md`, `PROJECT_ROADMAP.md`, `CONTRIBUTING.md`, `CHANGELOG.md`, `AI_AGENT.md`
- `README.md` updated with links to all documentation

---

### ✅ Phase 4 — Core Domain Models & Authentication Foundation

**Goal:** Establish the core User domain model and a scalable authentication foundation using Firebase Authentication.

**Deliverables:**
- `app/models/enums.py` — `Gender` string enum
- `app/db/mixins.py` — `UUIDMixin`, `TimestampMixin`
- `app/models/user.py` — `User` ORM model (14 fields + UUID PK + timestamps)
- `app/schemas/user.py`, `app/schemas/auth.py`
- Skeleton stubs for services and repositories
- Alembic migration for `users` table

---

### ✅ Phase 5 — Identity & Authentication Infrastructure

**Goal:** Production-ready Firebase Authentication infrastructure — token verification, user sync, identity orchestration, and the login endpoint.

**Deliverables:**
- `app/core/exceptions.py` — domain exception hierarchy
- Firebase Admin SDK singleton + `verify_firebase_token()`
- `get_current_user` FastAPI dependency
- `IdentityService` — login orchestration
- `UserRepository` + `UserService` — fully implemented
- `POST /api/v1/auth/login`, `GET /api/v1/auth/me`
- Global exception handlers in `app/main.py`

---

### ✅ Phase 6 — Extended User Profile Management

**Goal:** Production-ready User Domain & Profile Management — profile endpoints, username validation, reserved-name protection, and soft-delete infrastructure.

**Deliverables:**
- `app/models/user.py` — added `deleted_at` column (soft-delete); reduced `username` to `VARCHAR(30)`; added `ix_users_deleted_at` index
- `app/core/exceptions.py` — `UserNotFoundError` (404), `UsernameConflictError` (409), `ReservedUsernameError` (422)
- `app/schemas/user.py` — username regex validation (`^[a-z0-9_]{3,30}$`); `RESERVED_USERNAMES` frozenset (80+ names); `UserPublicRead`; `UserDeletedRead`; `UserUpdate` with username support
- `app/repositories/user_repo.py` — `soft_delete()`, `search_by_username_prefix()`
- `app/services/user_service.py` — `get_by_username()`, `update_my_profile()`, `soft_delete_user()`
- `app/api/v1/users.py` — `GET /api/v1/users/me`, `PATCH /api/v1/users/me`, `DELETE /api/v1/users/me`, `GET /api/v1/users/{username}`
- `app/main.py` — exception handlers for `UserNotFoundError`, `UsernameConflictError`, `ReservedUsernameError`
- `alembic/versions/a8f3d1c90e2b_phase_6_add_deleted_at_to_users.py` — Alembic migration

**Success Criteria:**
- `GET /api/v1/users/me` returns own full profile ✅
- `PATCH /api/v1/users/me` updates profile fields ✅
- `DELETE /api/v1/users/me` soft-deletes account ✅
- `GET /api/v1/users/{username}` returns public profile ✅
- Reserved usernames are rejected with 422 ✅
- Taken usernames are rejected with 409 ✅
- Missing/deleted users return 404 ✅
- Existing authentication unchanged ✅
- Existing login endpoint unchanged ✅
- Alembic migration generated ✅
- No import errors ✅

---

## Pending Phases

---

### ⏳ Phase 7 — Social Graph (Follow System)

**Goal:** Build follow/unfollow social graph primitives.

**Deliverables:**
- `app/models/follow.py` — Follow relationship model (follower_id, followee_id, created_at)
- `app/schemas/follow.py`
- `app/repositories/follow_repo.py`
- `app/services/follow_service.py`
- `app/api/v1/follows.py` — `POST /users/{username}/follow`, `DELETE /users/{username}/follow`, `GET /users/{username}/followers`, `GET /users/{username}/following`
- Follower/following counts on profile
- Alembic migration

---

### ⏳ Phase 8 — Voice Rooms (LiveKit)

**Goal:** Real-time voice room functionality powered by LiveKit.

**Deliverables:**
- `app/models/room.py` — Room model
- `app/schemas/room.py`, `app/repositories/room_repo.py`, `app/services/room_service.py`
- `app/api/v1/rooms.py` — `POST /rooms`, `GET /rooms`, `POST /rooms/{id}/join`, `DELETE /rooms/{id}`
- LiveKit SDK integration; `LIVEKIT_API_KEY`, `LIVEKIT_API_SECRET`, `LIVEKIT_URL` env vars
- Alembic migration

---

### ⏳ Phase 9 — Audio Stories (MinIO)

**Goal:** Let users record and publish short audio stories.

**Deliverables:**
- `app/models/story.py` — Story model
- MinIO / S3 presigned URL upload flow
- 24-hour story expiry logic
- Alembic migration

---

### ⏳ Phase 10 — Chat & Direct Messaging

**Goal:** Real-time 1-to-1 and group chat via WebSocket + Redis pub/sub.

---

### ⏳ Phase 11 — Wallet & Payments

**Goal:** In-app virtual currency (coins) for tipping hosts.

---

### ⏳ Phase 12 — Notifications

**Goal:** Push and in-app notification system (FCM + Celery).

---

### ⏳ Phase 13 — Security Hardening

**Goal:** Rate limiting, CORS lock-down, security headers, OWASP Top 10 audit.

---

### ⏳ Phase 14 — Testing

**Goal:** `pytest` + `pytest-asyncio`, 80%+ coverage, CI integration.

---

### ⏳ Phase 15 — Observability & Monitoring

**Goal:** Structured logging (structlog), Prometheus metrics, Sentry.

---

### ⏳ Phase 16 — Deployment & Infrastructure

**Goal:** Docker, `docker-compose.yml`, GitHub Actions CI/CD, zero-downtime deploys.

---

## Dependency Graph

```
Phase 1 (Foundation)
    └── Phase 2 (Database)
            └── Phase 3 (Documentation)
                    └── Phase 4 (Models)
                            └── Phase 5 (Auth)
                                    └── Phase 6 (User Profiles) ← current
                                            └── Phase 7 (Follow System)
                                            └── Phase 8 (Voice Rooms)
                                            └── Phase 9 (Audio Stories)
                                            └── Phase 10 (Chat)
                                                    └── Phase 11 (Wallet)
                                                            └── Phase 12 (Notifications)
                                                                    └── Phase 13 (Security)
                                                                            └── Phase 14 (Testing)
                                                                                    └── Phase 15 (Monitoring)
                                                                                            └── Phase 16 (Deployment)
```
