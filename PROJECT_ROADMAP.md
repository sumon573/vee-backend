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

**Success Criteria:**
- All imports resolve without error
- `alembic check` exits with code 0
- Engine uses `postgresql+asyncpg://` scheme regardless of input URL format
- No tables created yet

---

### ✅ Phase 3 — Project Documentation & Architecture Governance

**Goal:** Make the repository self-documenting so any AI agent or developer can understand and extend it without prior context.

**Deliverables:**
- `ARCHITECTURE.md` — full architecture reference
- `PROJECT_ROADMAP.md` — this file
- `CONTRIBUTING.md` — branch, commit, and code standards
- `CHANGELOG.md` — version history in Keep a Changelog format
- `AI_AGENT.md` — instruction manual for future AI agents
- `README.md` updated with links to all documentation

**Success Criteria:**
- All documentation files are consistent with each other
- A new AI agent reading only `AI_AGENT.md` can understand the full project state
- No Python source files modified
- No new dependencies added

---

## Pending Phases

---

### ✅ Phase 4 — Core Domain Models & Authentication Foundation

**Goal:** Establish the core User domain model and a scalable authentication foundation using Firebase Authentication.

**Deliverables:**
- `app/models/enums.py` — `Gender` string enum
- `app/db/mixins.py` — `UUIDMixin` (UUID v4 primary key), `TimestampMixin` (`created_at`, `updated_at`)
- `app/models/user.py` — `User` ORM model with 14 fields (UUID PK, firebase_uid, username, display_name, email, phone, avatar_url, bio, gender, birth_date, is_verified, is_active, created_at, updated_at, last_seen_at)
- `app/schemas/user.py` — `UserBase`, `UserRead`, `UserCreate`, `UserUpdate`
- `app/schemas/auth.py` — `FirebaseTokenPayload`, `AuthenticatedUser`
- `app/services/auth/firebase.py` — `verify_firebase_token()` stub (Phase 5 TODO)
- `app/services/auth/dependencies.py` — `get_current_user` FastAPI dependency stub
- `app/repositories/user_repo.py` — `UserRepository` skeleton (method signatures, Phase 5 TODO)
- `app/services/user_service.py` — `UserService` skeleton (method signatures, Phase 5 TODO)
- `app/api/v1/__init__.py` — combined v1 router
- `app/api/v1/auth.py` — auth router structure at `/api/v1/auth` (Phase 5 TODO)
- `app/main.py` — v1 router mounted at `/api/v1`
- `alembic/env.py` — `User` model imported for migration detection
- Alembic migration — creates `gender_enum` PostgreSQL type and `users` table

**Success Criteria:**
- All imports resolve without error ✅
- Alembic detects `users` table and generates a clean migration ✅
- User model uses SQLAlchemy 2.x typed mapping (`Mapped`, `mapped_column`) ✅
- No existing code modified beyond planned wiring ✅
- Firebase business logic deferred to Phase 5 ✅

---

### ✅ Phase 5 — Identity & Authentication Infrastructure

**Goal:** Production-ready Firebase Authentication infrastructure — token verification, user sync, identity orchestration, and the login endpoint.

**Deliverables:**
- `app/core/exceptions.py` — Domain exception hierarchy (`VeeError`, `AuthError`, `AuthTokenInvalidError`, `AuthTokenExpiredError`, `AuthTokenRevokedError`, `FirebaseUnavailableError`, `InactiveUserError`)
- `app/core/config.py` — Firebase env vars: `FIREBASE_PROJECT_ID`, `FIREBASE_CLIENT_EMAIL`, `FIREBASE_PRIVATE_KEY`
- `app/services/auth/firebase_init.py` — Firebase Admin SDK singleton (production-safe, private key never logged)
- `app/services/auth/firebase.py` — `verify_firebase_token()` — full implementation; runs sync SDK call in thread-pool executor; maps all Firebase errors to domain exceptions
- `app/services/auth/dependencies.py` — `get_current_user` FastAPI dependency — full implementation; verifies token, loads/creates user, rejects inactive accounts
- `app/services/identity_service.py` — `IdentityService`; `login_with_firebase()`, `get_identity()`; designed for future provider extension
- `app/repositories/user_repo.py` — `UserRepository` — all methods implemented: `get_by_id`, `get_by_firebase_uid`, `get_by_username`, `get_by_email`, `create`, `update_last_seen`, `update_profile`, `save`
- `app/services/user_service.py` — `UserService` — all methods implemented: `sync_firebase_user()` (get-or-create), `get_profile()`, `update_last_seen()`
- `app/api/v1/auth.py` — `POST /api/v1/auth/login`, `GET /api/v1/auth/me`
- `app/main.py` — global exception handlers for all `AuthError` subclasses → structured JSON 401/403/503
- `.env.example` — Firebase credential fields documented
- `requirements.txt` — `firebase-admin>=6.5.0`

**Success Criteria:**
- All imports resolve without error ✅
- Firebase SDK initializes with env var credentials ✅
- Login endpoint returns `UserRead` on first login (auto-creates user) ✅
- Login endpoint returns `UserRead` on subsequent logins ✅
- Inactive user is rejected with HTTP 403 ✅
- All auth failures return structured JSON with `error` + `message` ✅
- Private key never appears in logs ✅
- Alembic migration unchanged ✅

---

### ⏳ Phase 6 — Extended User Profile & Follow System

**Goal:** Build social graph primitives (follow/unfollow) and enrich user profiles.

**Deliverables:**
- `app/models/follow.py` — Follow relationship model
- `app/schemas/follow.py`
- `app/repositories/follow_repo.py`
- `app/services/follow_service.py`
- `app/api/v1/follows.py` — `POST /users/{id}/follow`, `DELETE /users/{id}/follow`
- Profile endpoints: bio, avatar URL, follower/following counts
- Alembic migration

**Success Criteria:**
- User A can follow/unfollow User B
- Follower counts update correctly

---

### ⏳ Phase 6 — Voice Rooms

**Goal:** Real-time voice room functionality powered by LiveKit.

**Deliverables:**
- `app/models/room.py` — Room model (id, host_id, title, is_live, participant_count)
- `app/schemas/room.py`
- `app/repositories/room_repo.py`
- `app/services/room_service.py` — create, join, leave, end room; LiveKit token generation
- `app/api/v1/rooms.py` — `POST /rooms`, `GET /rooms`, `POST /rooms/{id}/join`, `DELETE /rooms/{id}`
- LiveKit SDK integration for access token generation
- Alembic migration
- `LIVEKIT_API_KEY`, `LIVEKIT_API_SECRET`, `LIVEKIT_URL` env vars

**Success Criteria:**
- Host creates a room and receives a LiveKit join token
- Participants join the room using the token
- Room state (live/ended) is persisted in PostgreSQL

---

### ⏳ Phase 7 — Audio Stories

**Goal:** Let users record and publish short audio stories.

**Deliverables:**
- `app/models/story.py` — Story model (id, author_id, audio_url, duration_sec, view_count, expires_at)
- `app/schemas/story.py`
- `app/repositories/story_repo.py`
- `app/services/story_service.py` — upload (MinIO presigned URL), publish, delete, view tracking
- `app/api/v1/stories.py` — CRUD + presigned upload URL endpoint
- MinIO / S3 integration for audio file storage
- 24-hour story expiry logic
- Alembic migration

**Success Criteria:**
- Client receives a presigned URL and uploads audio directly to MinIO
- Story appears in feed and expires after 24 hours

---

### ⏳ Phase 8 — Chat & Direct Messaging

**Goal:** Real-time 1-to-1 and group chat via WebSocket.

**Deliverables:**
- `app/models/conversation.py`, `app/models/message.py`
- `app/schemas/message.py`
- `app/repositories/message_repo.py`
- `app/services/chat_service.py`
- `app/api/v1/chat.py` — WebSocket endpoint + REST history endpoint
- Redis pub/sub for fanout to multiple connected clients
- Message persistence in PostgreSQL
- Alembic migrations

**Success Criteria:**
- Two users can exchange real-time messages via WebSocket
- Message history is retrievable via REST
- Disconnected clients receive missed messages on reconnect

---

### ⏳ Phase 9 — Wallet & Payments

**Goal:** In-app virtual currency (coins) for tipping hosts and purchasing features.

**Deliverables:**
- `app/models/wallet.py` — Wallet model (user_id, balance)
- `app/models/transaction.py` — Transaction ledger (from, to, amount, type, created_at)
- `app/schemas/wallet.py`
- `app/repositories/wallet_repo.py`
- `app/services/wallet_service.py` — credit, debit, transfer (atomic transactions)
- `app/api/v1/wallet.py` — balance, transaction history, tip endpoint
- Payment gateway integration (Stripe / local gateway — TBD)
- Alembic migrations

**Success Criteria:**
- Wallet balance is always consistent (no race conditions under concurrent tips)
- Every credit/debit is recorded in the ledger
- Failed payments do not modify balances

---

### ⏳ Phase 10 — Notifications

**Goal:** Push and in-app notification system.

**Deliverables:**
- `app/models/notification.py`
- `app/schemas/notification.py`
- `app/repositories/notification_repo.py`
- `app/services/notification_service.py` — create, mark-read, batch dispatch
- `app/api/v1/notifications.py`
- Firebase Cloud Messaging (FCM) integration for push notifications
- Celery + Redis for async background dispatch
- Alembic migration

**Success Criteria:**
- User receives a push notification when someone follows them or tips them
- In-app notification list shows unread count

---

### ⏳ Phase 11 — Security Hardening

**Goal:** Production-grade security across all layers.

**Deliverables:**
- Rate limiting (slowapi or custom middleware)
- JWT refresh token rotation + Redis blacklist
- Input sanitisation middleware
- CORS locked to known origins (not `*`)
- Security headers middleware (CSP, HSTS, X-Frame-Options)
- SQL injection prevention audit
- Secrets rotation documentation

**Success Criteria:**
- OWASP Top 10 risks addressed and documented
- Brute-force login attempts are rate-limited

---

### ⏳ Phase 12 — Testing

**Goal:** Comprehensive test suite covering all layers.

**Deliverables:**
- `pytest` + `pytest-asyncio` setup
- `httpx.AsyncClient` for API integration tests
- Repository unit tests with in-memory SQLite or test PostgreSQL
- Service unit tests with mocked repositories
- 80%+ code coverage
- CI configuration (GitHub Actions)

**Success Criteria:**
- `pytest` passes with 0 failures
- Coverage report shows ≥80%
- Tests run in CI on every pull request

---

### ⏳ Phase 13 — Observability & Monitoring

**Goal:** Full visibility into production application health and performance.

**Deliverables:**
- Structured JSON logging (replace print/logging with structlog)
- Request ID middleware (trace requests across logs)
- Prometheus metrics endpoint (`/metrics`)
- Grafana dashboard templates
- Sentry integration for error tracking
- Health check extended (`/health` checks DB + Redis connectivity)

**Success Criteria:**
- Every request produces a structured log line with request ID, path, status, and duration
- Sentry captures unhandled exceptions in production

---

### ⏳ Phase 14 — Deployment & Infrastructure

**Goal:** Production deployment with zero-downtime releases.

**Deliverables:**
- `Dockerfile` (multi-stage build)
- `docker-compose.yml` for local development (app + PostgreSQL + Redis + MinIO)
- GitHub Actions CI/CD pipeline
- Environment-specific config (dev / staging / prod)
- Alembic migration as deployment pre-step
- Horizontal scaling documentation

**Success Criteria:**
- `docker compose up` starts the full stack locally
- CI/CD deploys to staging on merge to `main`
- Zero-downtime rolling deploy verified

---

## Dependency Graph

```
Phase 1 (Foundation)
    └── Phase 2 (Database)
            └── Phase 3 (Documentation)
                    └── Phase 4 (Auth)
                            ├── Phase 5 (Profiles)
                            ├── Phase 6 (Voice Rooms)
                            ├── Phase 7 (Stories)
                            ├── Phase 8 (Chat)
                            └── Phase 9 (Wallet)
                                    └── Phase 10 (Notifications)
                                            └── Phase 11 (Security)
                                                    └── Phase 12 (Testing)
                                                            └── Phase 13 (Monitoring)
                                                                    └── Phase 14 (Deployment)
```
