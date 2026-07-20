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

### ✅ Phase 7 — Social Graph (Follow System)

**Goal:** Build follow/unfollow social graph primitives.

**Deliverables:**
- `app/models/follow.py` — Follow model (id, follower_id, following_id, created_at); UNIQUE constraint; CHECK constraint (no self-follow); 3 indexes
- `app/schemas/follow.py` — `FollowRead`, `FollowUserRead`, `FollowListResponse`, `RelationshipRead`
- `app/repositories/follow_repo.py` — `follow()`, `unfollow()`, `is_following()`, `followers_count()`, `following_count()`, `list_followers()`, `list_following()`, batch count helpers
- `app/services/follow_service.py` — all business rules enforced; `follow_user()`, `unfollow_user()`, `get_followers()`, `get_following()`, `get_relationship()`, `get_social_counts()`
- `app/api/v1/follows.py` — 5 endpoints (see below)
- `app/schemas/user.py` — `UserPublicRead` extended with `followers_count`, `following_count`, `is_following`, `is_followed_by`
- `app/api/v1/users.py` — `GET /users/{username}` enriched with social graph data; optional auth for relationship context
- `app/core/exceptions.py` — `SelfFollowError` (400), `AlreadyFollowingError` (409), `NotFollowingError` (409)
- `app/main.py` — exception handlers for new social graph exceptions
- `app/services/auth/dependencies.py` — `get_optional_current_user` dependency added
- `alembic/env.py` — Follow model imported for migration detection
- `alembic/versions/b3e9f2a1c5d8_phase_7_add_follows_table.py` — Alembic migration

**API Endpoints:**

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/api/v1/users/{username}/follow` | Required | Follow a user |
| DELETE | `/api/v1/users/{username}/follow` | Required | Unfollow a user |
| GET | `/api/v1/users/{username}/followers` | Optional | List followers |
| GET | `/api/v1/users/{username}/following` | Optional | List following |
| GET | `/api/v1/users/{username}/relationship` | Required | Mutual relationship status |

**Success Criteria:**
- Follow works ✅
- Unfollow works ✅
- Self-follow blocked (DB CHECK + service layer) ✅
- Duplicate follow blocked (DB UNIQUE + service layer) ✅
- Inactive/deleted user cannot be followed ✅
- Counts correct on public profile ✅
- Relationship endpoint works ✅
- Existing Authentication unaffected ✅
- Existing User API unaffected ✅
- Import error নেই ✅
- Alembic migration generated ✅

---

### ✅ Phase 8 — Privacy & Safety Foundation

**Goal:** Reusable block infrastructure and PrivacyGuard service for all future features (Chat, Voice Room, Story, Notification, Search).

**Deliverables:**
- `app/models/block.py` — Block model (id, blocker_id, blocked_id, created_at); UNIQUE + CHECK constraints; 3 indexes
- `app/schemas/block.py` — `BlockRead`, `BlockedUserRead`, `BlockedListResponse`
- `app/repositories/block_repo.py` — `block_user()`, `unblock_user()`, `is_blocked()`, `is_mutually_blocked()`, `blocked_count()`, `blocked_users()`, `blocked_by_users()`
- `app/services/block_service.py` — business rules: no self-block, no inactive/deleted target, follow auto-removal on block, `block_user()`, `unblock_user()`, `get_blocked_users()`, `is_blocked_in_any_direction()`
- `app/services/privacy_guard.py` — `PrivacyGuard`: `can_view_profile()`, `can_follow()`, `can_message()` (stub), `can_join_room()` (stub)
- `app/api/v1/blocks.py` — 3 endpoints (see below)
- `app/schemas/user.py` — `UserPublicRead` extended with `is_blocked`, `has_blocked_me`
- `app/api/v1/users.py` — `GET /users/{username}` enriched with block status when authenticated
- `app/core/exceptions.py` — `SelfBlockError` (400), `AlreadyBlockedError` (409), `NotBlockedError` (409)
- `app/main.py` — exception handlers for 3 new block exceptions
- `app/api/v1/__init__.py` — blocks router registered before users router (route precedence)
- `alembic/env.py` — Block model imported for migration detection
- `alembic/versions/c4f8e3b2d9a1_phase_8_add_blocks_table.py` — Alembic migration

**API Endpoints:**

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/api/v1/users/{username}/block` | Required | Block a user (also removes follow in both directions) |
| DELETE | `/api/v1/users/{username}/block` | Required | Unblock a user |
| GET | `/api/v1/users/blocked` | Required | Paginated list of blocked users |

**Success Criteria:**
- Block works ✅
- Unblock works ✅
- Self-block blocked (DB CHECK + service layer) ✅
- Duplicate block blocked (DB UNIQUE + service layer) ✅
- Follow auto-removed when blocking ✅
- Inactive/deleted user cannot be blocked ✅
- is_blocked / has_blocked_me on public profile ✅
- PrivacyGuard foundation ready ✅
- Existing Follow System unaffected ✅
- Existing User APIs unaffected ✅
- Import error নেই ✅
- Alembic migration generated ✅

---

### ⏳ Phase 9 — Voice Rooms (LiveKit)

**Goal:** Real-time voice room functionality powered by LiveKit.

**Deliverables:**
- `app/models/room.py` — Room model
- `app/schemas/room.py`, `app/repositories/room_repo.py`, `app/services/room_service.py`
- `app/api/v1/rooms.py` — `POST /rooms`, `GET /rooms`, `POST /rooms/{id}/join`, `DELETE /rooms/{id}`
- LiveKit SDK integration; `LIVEKIT_API_KEY`, `LIVEKIT_API_SECRET`, `LIVEKIT_URL` env vars
- Alembic migration

---

### ⏳ Phase 10 — Audio Stories (MinIO)

**Goal:** Let users record and publish short audio stories.

**Deliverables:**
- `app/models/story.py` — Story model
- MinIO / S3 presigned URL upload flow
- 24-hour story expiry logic
- Alembic migration

---

### ⏳ Phase 11 — Chat & Direct Messaging

**Goal:** Real-time 1-to-1 and group chat via WebSocket + Redis pub/sub.

---

### ⏳ Phase 12 — Wallet & Payments

**Goal:** In-app virtual currency (coins) for tipping hosts.

---

### ⏳ Phase 13 — Notifications

**Goal:** Push and in-app notification system (FCM + Celery).

---

### ⏳ Phase 14 — Security Hardening

**Goal:** Rate limiting, CORS lock-down, security headers, OWASP Top 10 audit.

---

### ⏳ Phase 15 — Testing

**Goal:** `pytest` + `pytest-asyncio`, 80%+ coverage, CI integration.

---

### ⏳ Phase 16 — Observability & Monitoring

**Goal:** Structured logging (structlog), Prometheus metrics, Sentry.

---

### ⏳ Phase 17 — Deployment & Infrastructure

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
                                            └── Phase 9 (Voice Rooms)
                                            └── Phase 10 (Audio Stories)
                                            └── Phase 11 (Chat)
                                                    └── Phase 12 (Wallet)
                                                            └── Phase 13 (Notifications)
                                                                    └── Phase 14 (Security)
                                                                            └── Phase 15 (Testing)
                                                                                    └── Phase 16 (Monitoring)
                                                                                            └── Phase 17 (Deployment)
```
