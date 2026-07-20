# AI Agent Instruction Manual — Vee Backend

> **Read this file first.** If you are an AI agent, a language model, or an automated tool working on this repository, this document gives you everything you need to understand the project state, architecture, and rules — without requiring conversation history.

---

## Project Summary

| Field | Value |
|-------|-------|
| **Project** | Vee — Social Audio Platform |
| **Type** | REST API backend |
| **Language** | Python 3.12 |
| **Framework** | FastAPI |
| **Database** | PostgreSQL (asyncpg driver) |
| **ORM** | SQLAlchemy 2.x (async) |
| **Migrations** | Alembic |
| **Auth** | Firebase Authentication (fully live — Phase 5 complete) |
| **Entry point** | `uvicorn app.main:app --reload` |
| **Docs** | `GET /docs` (Swagger UI) |

---

## Current Architecture

```
app/
├── api/
│   └── v1/
│       ├── __init__.py         ← combined v1 router — mounted at /api/v1
│       │                          (blocks before users router — route precedence for /users/blocked)
│       ├── auth.py             ← POST /api/v1/auth/login, GET /api/v1/auth/me
│       ├── follows.py          ← social graph endpoints (Phase 7)
│       ├── blocks.py           ← block endpoints (Phase 8)
│       └── users.py            ← GET|PATCH|DELETE /api/v1/users/me, GET /api/v1/users/{username}
├── core/
│   ├── config.py               ← All env vars via pydantic_settings.BaseSettings
│   └── exceptions.py           ← Domain exception hierarchy (AuthError, UserNotFoundError, …)
├── db/
│   ├── base.py                 ← DeclarativeBase — ALL models inherit from here
│   ├── database.py             ← Async SQLAlchemy engine (pool_size=10, max_overflow=20)
│   ├── mixins.py               ← UUIDMixin (UUID v4 PK), TimestampMixin (created_at/updated_at)
│   ├── session.py              ← AsyncSessionLocal + get_db FastAPI dependency
│   └── __init__.py             ← Exports: Base, engine, AsyncSessionLocal, get_db
├── models/
│   ├── enums.py                ← Gender enum (str-based)
│   ├── user.py                 ← User ORM model (15 fields: + deleted_at for soft-delete)
│   ├── follow.py               ← Follow ORM model (Phase 7: id, follower_id, following_id, created_at)
│   └── block.py                ← Block ORM model (Phase 8: id, blocker_id, blocked_id, created_at)
├── schemas/
│   ├── auth.py                 ← FirebaseTokenPayload (frozen), AuthenticatedUser
│   ├── user.py                 ← UserBase, UserRead, UserPublicRead, UserCreate, UserUpdate, UserDeletedRead
│   │                              + RESERVED_USERNAMES frozenset + username regex validator
│   │                              + UserPublicRead extended with social graph + block fields (Phase 7–8)
│   ├── follow.py               ← FollowRead, FollowUserRead, FollowListResponse, RelationshipRead (Phase 7)
│   └── block.py                ← BlockRead, BlockedUserRead, BlockedListResponse (Phase 8)
├── services/
│   ├── auth/
│   │   ├── __init__.py         ← exports verify_firebase_token, get_current_user
│   │   ├── firebase_init.py    ← Firebase Admin SDK singleton (env var credentials)
│   │   ├── firebase.py         ← verify_firebase_token() — full implementation
│   │   └── dependencies.py     ← get_current_user FastAPI dependency — full implementation
│   ├── identity_service.py     ← IdentityService: login_with_firebase(), get_identity()
│   ├── user_service.py         ← UserService: sync_firebase_user(), get_profile(),
│   │                              get_by_username(), update_my_profile(), soft_delete_user(),
│   │                              update_last_seen()
│   ├── follow_service.py       ← FollowService: follow/unfollow + list queries (Phase 7)
│   ├── block_service.py        ← BlockService: block/unblock + follow auto-removal (Phase 8)
│   └── privacy_guard.py        ← PrivacyGuard: can_view_profile(), can_follow(),
│                                  can_message() stub, can_join_room() stub (Phase 8)
├── repositories/
│   ├── user_repo.py            ← UserRepository — all methods implemented (+ soft_delete, search_by_username_prefix)
│   ├── follow_repo.py          ← FollowRepository — 9 methods (Phase 7)
│   └── block_repo.py           ← BlockRepository — 7 methods incl. is_mutually_blocked() (Phase 8)
├── middleware/                  ← ASGI middleware — currently empty
├── utils/
│   └── db_url.py               ← normalize_database_url()
└── main.py                     ← FastAPI app, CORS, exception handlers, mounts /api/v1

alembic/
├── versions/
│   ├── cfeccaac3dc7_phase_4_add_users_table.py              ← users table + gender_enum
│   ├── a8f3d1c90e2b_phase_6_add_deleted_at_to_users.py      ← deleted_at column + index
│   ├── b3e9f2a1c5d8_phase_7_add_follows_table.py            ← follows table (Phase 7)
│   └── c4f8e3b2d9a1_phase_8_add_blocks_table.py             ← blocks table (Phase 8)
├── env.py                      ← imports User, Follow, Block models; async migration runner
└── script.py.mako
alembic.ini
requirements.txt                ← includes firebase-admin>=6.5.0
.env.example                    ← includes Firebase credential fields
```

---

## Current Phase

**Phase 8 — Privacy & Safety Foundation** ✅ Complete

Next phase:
- ⏳ Phase 9 — Voice Rooms (LiveKit)

See `PROJECT_ROADMAP.md` for the complete phase list.

---

## Live API Endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/` | None | API status |
| GET | `/health` | None | Health check |
| GET | `/docs` | None | Swagger UI |
| POST | `/api/v1/auth/login` | Bearer Firebase token | Login / auto-register |
| GET | `/api/v1/auth/me` | Bearer Firebase token | Get current user (auth namespace) |
| GET | `/api/v1/users/me` | Bearer Firebase token | Get own full profile |
| PATCH | `/api/v1/users/me` | Bearer Firebase token | Update own profile |
| DELETE | `/api/v1/users/me` | Bearer Firebase token | Soft-delete own account |
| GET | `/api/v1/users/{username}` | None (optional) | Public profile by username (social + block status when authenticated) |
| POST | `/api/v1/users/{username}/follow` | Bearer Firebase token | Follow a user |
| DELETE | `/api/v1/users/{username}/follow` | Bearer Firebase token | Unfollow a user |
| GET | `/api/v1/users/{username}/followers` | None | List followers |
| GET | `/api/v1/users/{username}/following` | None | List following |
| GET | `/api/v1/users/{username}/relationship` | Bearer Firebase token | Mutual relationship status |
| POST | `/api/v1/users/{username}/block` | Bearer Firebase token | Block a user |
| DELETE | `/api/v1/users/{username}/block` | Bearer Firebase token | Unblock a user |
| GET | `/api/v1/users/blocked` | Bearer Firebase token | List blocked users |

---

## Authentication Flow

```
Client (mobile/web)
    │
    │  POST /api/v1/auth/login
    │  Authorization: Bearer <firebase_id_token>
    ▼
FastAPI Router (app/api/v1/auth.py)
    │
    │  HTTPBearer extracts token
    ▼
IdentityService.login_with_firebase(token)
    │
    ├─► verify_firebase_token(token)
    │       └─► firebase_admin.auth.verify_id_token()  [thread-pool executor]
    │               ├─ ExpiredIdTokenError   → AuthTokenExpiredError  → HTTP 401
    │               ├─ RevokedIdTokenError   → AuthTokenRevokedError  → HTTP 401
    │               ├─ InvalidIdTokenError   → AuthTokenInvalidError  → HTTP 401
    │               └─ FirebaseError         → FirebaseUnavailableError → HTTP 503
    │
    ├─► UserService.sync_firebase_user(payload)
    │       └─► UserRepository.get_by_firebase_uid()
    │               ├─ Found    → return existing User
    │               └─ Not found → UserRepository.create(new User)
    │                             (username auto-generated: vee_<uid[:16]>)
    │
    ├─► Guard: user.is_active == False → InactiveUserError → HTTP 403
    │
    ├─► UserService.update_last_seen(user)   [non-fatal]
    │
    └─► return User ORM instance
    │
FastAPI Router
    └─► UserRead.model_validate(user)  → JSON response
```

---

## Completed Work

### Phase 1 — Backend Foundation
- FastAPI app with CORS, Swagger, ReDoc
- `GET /` and `GET /health`
- Pydantic Settings config

### Phase 2 — Database Foundation
- SQLAlchemy 2.x async engine (asyncpg)
- `DeclarativeBase`, production pool config, `get_db` dependency
- `normalize_database_url()` utility
- Alembic configured for async migrations

### Phase 7 — Social Graph (Follow System)
- Follow ORM model with UNIQUE + CHECK constraints + 3 indexes
- FollowRepository (9 methods), FollowService (6 methods)
- 5 API endpoints: follow, unfollow, followers, following, relationship
- get_optional_current_user dependency for optional auth
- UserPublicRead extended with social graph fields
- Alembic migration: `b3e9f2a1c5d8`

### Phase 8 — Privacy & Safety Foundation
- Block ORM model with UNIQUE + CHECK constraints + 3 indexes
- BlockRepository (7 methods including is_mutually_blocked)
- BlockService: block/unblock with follow auto-removal, blocked-list query
- PrivacyGuard: can_view_profile, can_follow, can_message (stub), can_join_room (stub)
- 3 API endpoints: block, unblock, list-blocked
- UserPublicRead extended with is_blocked, has_blocked_me
- SelfBlockError (400), AlreadyBlockedError (409), NotBlockedError (409)
- blocks router included before users router (route precedence for /users/blocked)
- Alembic migration: `c4f8e3b2d9a1`

### Phase 3 — Documentation
- `ARCHITECTURE.md`, `PROJECT_ROADMAP.md`, `CONTRIBUTING.md`, `CHANGELOG.md`, `AI_AGENT.md`

### Phase 4 — Core Domain Models & Authentication Foundation
- `app/models/enums.py`, `app/db/mixins.py`, `app/models/user.py`
- `app/schemas/user.py`, `app/schemas/auth.py`
- v1 router mounted at `/api/v1`
- Alembic migration: `cfeccaac3dc7_phase_4_add_users_table.py`

### Phase 5 — Identity & Authentication Infrastructure
- Full Firebase authentication stack
- `POST /api/v1/auth/login`, `GET /api/v1/auth/me`
- Global exception handlers

### Phase 6 — Extended User Profile Management
- `deleted_at` soft-delete column on User model
- Username validation: `^[a-z0-9_]{3,30}$` regex + 80+ reserved names
- New exceptions: `UserNotFoundError`, `UsernameConflictError`, `ReservedUsernameError`
- `UserPublicRead` (public profile), `UserDeletedRead` (soft-delete confirmation)
- `UserRepository.soft_delete()` + `search_by_username_prefix()`
- `UserService.get_by_username()`, `update_my_profile()`, `soft_delete_user()`
- `GET /api/v1/users/me`, `PATCH /api/v1/users/me`, `DELETE /api/v1/users/me`
- `GET /api/v1/users/{username}` (public, no auth required)
- Exception handlers: 404, 409, 422 for user domain errors
- Alembic migration: `a8f3d1c90e2b_phase_6_add_deleted_at_to_users.py`

---

## Pending Work

| Phase | Description |
|-------|-------------|
| 9 | Voice Rooms (LiveKit integration) |
| 10 | Audio Stories (MinIO / S3 storage) |
| 11 | Chat & Direct Messaging (WebSocket + Redis) |
| 12 | Wallet & Payments |
| 13 | Notifications (FCM + Celery) |
| 14 | Security Hardening |
| 15 | Testing (pytest, 80%+ coverage) |
| 16 | Observability & Monitoring (structlog, Prometheus, Sentry) |
| 17 | Deployment & Infrastructure (Docker, CI/CD) |

---

## Coding Rules

1. **Python 3.12 only** — modern syntax; minimum version 3.12
2. **Type-annotate everything** — every parameter and return type
3. **Async for all I/O** — `async def` for routes, services, repositories
4. **Pydantic v2 schemas** — use `model_config` not inner `Config`
5. **No `print()`** — use `logging.getLogger(__name__)`
6. **No bare `except:`** — always name the exception type
7. **No hardcoded secrets** — all config through `app/core/config.py`
8. **`expire_on_commit=False`** — already configured; do not change
9. **SQLAlchemy 2.x typed mapping** — always `Mapped[T]` + `mapped_column()`
10. **No sensitive data in logs** — never log tokens, private keys, or passwords

---

## Architecture Rules

### Dependency Direction (STRICT)
```
api → services → repositories → db/models
```
- `api` imports from `services` and `schemas` only
- `services` imports from `repositories`, `schemas`, and `models`
- `repositories` imports from `models` and `db`
- `utils` and `core` may be imported by any layer
- **Never import an outer layer from an inner layer**

### Exception Flow
```
Domain exceptions (app/core/exceptions.py)
    ↑ raised by
services / repositories
    ↓ caught by
app/main.py exception handlers → structured JSON response
    OR
app/services/auth/dependencies.py → HTTPException (401/403)
```

### Mixin Usage
All new models: `class MyModel(UUIDMixin, TimestampMixin, Base):`

### Soft Delete Pattern
- `deleted_at` (DateTime nullable) + `is_active = False` set simultaneously
- Filter active records: `.where(User.is_active.is_(True), User.deleted_at.is_(None))`
- **Do not hard-delete user records** — always soft-delete

### Adding a New Model
1. Create `app/models/<name>.py` — inherit from `UUIDMixin`, `TimestampMixin`, `Base`
2. Add to `alembic/env.py` model imports block
3. `alembic revision --autogenerate -m "add <name> table"`
4. `alembic upgrade head`

### Adding a New Endpoint
1. Create `app/api/v1/<resource>.py` with `APIRouter`
2. Create schemas, service, repository
3. Register router in `app/api/v1/__init__.py` — **do NOT touch `app/main.py`**

### Protected Endpoints
```python
from app.services.auth import get_current_user
from app.models.user import User

@router.get("/protected")
async def handler(current_user: User = Depends(get_current_user)) -> SomeRead:
    ...
```

---

## Exception → HTTP Status Map

| Exception | HTTP | Code |
|-----------|------|------|
| `AuthTokenInvalidError` | 401 | `invalid_token` |
| `AuthTokenExpiredError` | 401 | `token_expired` |
| `AuthTokenRevokedError` | 401 | `token_revoked` |
| `AuthError` (catch-all) | 401 | `auth_error` |
| `SelfFollowError` | 400 | `self_follow` |
| `SelfBlockError` | 400 | `self_block` |
| `InactiveUserError` | 403 | `account_inactive` |
| `UserNotFoundError` | 404 | `user_not_found` |
| `UsernameConflictError` | 409 | `username_conflict` |
| `AlreadyFollowingError` | 409 | `already_following` |
| `NotFollowingError` | 409 | `not_following` |
| `AlreadyBlockedError` | 409 | `already_blocked` |
| `NotBlockedError` | 409 | `not_blocked` |
| `ReservedUsernameError` | 422 | `reserved_username` |
| `FirebaseUnavailableError` | 503 | `firebase_unavailable` |

---

## Forbidden Actions

| Forbidden | Reason |
|-----------|--------|
| Modify existing migration files | Breaks migration history |
| Hard-delete user records | Use `UserRepository.soft_delete()` instead |
| Add blocking I/O / `time.sleep()` | Blocks the async event loop |
| Import `requests` (sync HTTP) | Use `httpx` async instead |
| Return ORM objects from route handlers | Breaks serialisation — return schemas |
| Write SQL in service layer | Violates repository pattern |
| Write business logic in route handlers | Violates service pattern |
| Change `Base` class name in `app/db/base.py` | Alembic metadata breaks |
| Remove `expire_on_commit=False` | Causes detached instance errors |
| Install packages not in `requirements.txt` | Undocumented dependency |
| Skip importing new models in `alembic/env.py` | Migrations won't detect table |
| Use old-style `Column()` in models | Use `Mapped[T]` + `mapped_column()` |
| Register new routers in `app/main.py` | Register in `app/api/v1/__init__.py` |
| Log Firebase tokens or private keys | Security violation |
| Call `firebase_admin` directly outside `app/services/auth/` | Violates layer rules |
| Use reserved usernames in auto-generated content | Check against `RESERVED_USERNAMES` |

---

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `APP_NAME` | No | `Vee API` | Application name |
| `APP_VERSION` | No | `0.1.0` | Semantic version |
| `APP_ENV` | No | `development` | `development` / `staging` / `production` |
| `DEBUG` | No | `true` | SQLAlchemy query echo |
| `HOST` | No | `0.0.0.0` | Server bind host |
| `PORT` | No | `8000` | Server bind port |
| `ALLOWED_ORIGINS` | No | `["*"]` | CORS allowed origins |
| `DATABASE_URL` | **Yes** | — | PostgreSQL connection string |
| `FIREBASE_PROJECT_ID` | **Yes** | `""` | Firebase project ID |
| `FIREBASE_CLIENT_EMAIL` | **Yes** | `""` | Firebase service account email |
| `FIREBASE_PRIVATE_KEY` | **Yes** | `""` | Full PEM private key (`\\n` auto-normalized) |

---

## Key Design Decisions

| Decision | Reason |
|----------|--------|
| asyncpg over psycopg2 | Full async; required for SQLAlchemy 2.x async engine |
| `expire_on_commit=False` | Prevents `MissingGreenlet` errors on detached ORM instances |
| URL normalization in `utils/db_url.py` | Replit and many platforms provide `postgresql://`; asyncpg requires `+asyncpg` |
| Firebase over JWT/bcrypt | Mobile-first; Firebase handles phone/Google/Apple sign-in natively |
| Firebase SDK runs in thread-pool | `verify_id_token` is synchronous; must not block the asyncio event loop |
| Singleton Firebase app | `firebase_admin.initialize_app()` must only be called once per process |
| `\\n` normalization for private key | Hosting platforms often store PEM key with literal `\\n` sequences |
| UUID v4 primary keys | Avoids sequential ID enumeration; safe to expose in URLs |
| `UUIDMixin` + `TimestampMixin` | Prevents duplicated columns; enforces consistency across models |
| New routers in `app/api/v1/__init__.py` | `app/main.py` has one stable mount point regardless of resource count |
| `get_current_user` returns `User` ORM | Route handlers can serialize directly to any schema without extra DB call |
| `update_last_seen` is non-fatal | Presence stamping failure must never block login or authenticated requests |
| Auto-generated username `vee_<uid[:16]>` | Firebase tokens don't guarantee a username; auto-generation ensures non-null constraint |
| Soft delete via `deleted_at` + `is_active=False` | Preserves data integrity; user records never hard-deleted; admin-reversible |
| `UserPublicRead` separate from `UserRead` | Public profiles exclude private fields (email, phone, birth_date, firebase_uid) |
| `RESERVED_USERNAMES` frozenset in schemas | Schema-layer enforcement is the first gate; service layer double-checks for safety |
| Username regex `^[a-z0-9_]{3,30}$` | URL-safe, predictable, lowercase-normalized at validation time |
