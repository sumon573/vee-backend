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
│       ├── auth.py             ← POST /api/v1/auth/login, GET /api/v1/auth/me
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
│   ├── follow.py               ← Follow ORM model (Phase 7: id, follower_id, following_id, created_at)
│   └── user.py                 ← User ORM model (15 fields: + deleted_at for soft-delete)
├── schemas/
│   ├── auth.py                 ← FirebaseTokenPayload (frozen), AuthenticatedUser
│   ├── follow.py               ← FollowRead, FollowUserRead, FollowListResponse, RelationshipRead (Phase 7)
│   └── user.py                 ← UserBase, UserRead, UserPublicRead, UserCreate, UserUpdate, UserDeletedRead
│                                  + RESERVED_USERNAMES frozenset + username regex validator
│                                  + UserPublicRead extended with social graph fields (Phase 7)
├── services/
│   ├── auth/
│   │   ├── __init__.py         ← exports verify_firebase_token, get_current_user
│   │   ├── firebase_init.py    ← Firebase Admin SDK singleton (env var credentials)
│   │   ├── firebase.py         ← verify_firebase_token() — full implementation
│   │   └── dependencies.py     ← get_current_user FastAPI dependency — full implementation
│   ├── identity_service.py     ← IdentityService: login_with_firebase(), get_identity()
│   └── user_service.py         ← UserService: sync_firebase_user(), get_profile(),
│                                  get_by_username(), update_my_profile(), soft_delete_user(),
│                                  update_last_seen()
├── repositories/
│   └── user_repo.py            ← UserRepository — all methods implemented (+ soft_delete, search_by_username_prefix)
├── middleware/                  ← ASGI middleware — currently empty
├── utils/
│   └── db_url.py               ← normalize_database_url()
└── main.py                     ← FastAPI app, CORS, exception handlers, mounts /api/v1

alembic/
├── versions/
│   ├── cfeccaac3dc7_phase_4_add_users_table.py         ← users table + gender_enum
│   └── a8f3d1c90e2b_phase_6_add_deleted_at_to_users.py ← deleted_at column + index
├── env.py                      ← imports User model; async migration runner
└── script.py.mako
alembic.ini
requirements.txt                ← includes firebase-admin>=6.5.0
.env.example                    ← includes Firebase credential fields
```

---

## Current Phase

**Phase 6 — Extended User Profile Management** ✅ Complete

Next phase:
- ⏳ Phase 7 — Social Graph (Follow System)

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
| GET | `/api/v1/users/{username}` | None | Public profile by username |

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
| 7 | Social Graph — Follow/Unfollow system |
| 8 | Voice Rooms (LiveKit integration) |
| 9 | Audio Stories (MinIO / S3 storage) |
| 10 | Chat & Direct Messaging (WebSocket + Redis) |
| 11 | Wallet & Payments |
| 12 | Notifications (FCM + Celery) |
| 13 | Security Hardening |
| 14 | Testing (pytest, 80%+ coverage) |
| 15 | Observability & Monitoring (structlog, Prometheus, Sentry) |
| 16 | Deployment & Infrastructure (Docker, CI/CD) |

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
| `InactiveUserError` | 403 | `account_inactive` |
| `UserNotFoundError` | 404 | `user_not_found` |
| `UsernameConflictError` | 409 | `username_conflict` |
| `AlreadyFollowingError` | 409 | `already_following` |
| `NotFollowingError` | 409 | `not_following` |
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
