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
| **Auth** | Firebase Authentication (foundation in place; full implementation Phase 5) |
| **Entry point** | `uvicorn app.main:app --reload` |
| **Docs** | `GET /docs` (Swagger UI) |

---

## Current Architecture

```
app/
├── api/
│   └── v1/
│       ├── __init__.py   ← combined v1 router — mounted at /api/v1
│       └── auth.py       ← /api/v1/auth (structure only; endpoints in Phase 5)
├── core/
│   └── config.py         ← All env vars via pydantic_settings.BaseSettings
├── db/
│   ├── base.py           ← DeclarativeBase — ALL models inherit from here
│   ├── database.py       ← Async SQLAlchemy engine (pool_size=10, max_overflow=20)
│   ├── mixins.py         ← UUIDMixin (UUID v4 PK), TimestampMixin (created_at/updated_at)
│   ├── session.py        ← AsyncSessionLocal + get_db FastAPI dependency
│   └── __init__.py       ← Exports: Base, engine, AsyncSessionLocal, get_db
├── models/
│   ├── enums.py          ← Gender enum (str-based)
│   └── user.py           ← User ORM model (14 fields, UUID PK, firebase_uid, etc.)
├── schemas/
│   ├── auth.py           ← FirebaseTokenPayload, AuthenticatedUser
│   └── user.py           ← UserBase, UserRead, UserCreate, UserUpdate
├── services/
│   ├── auth/
│   │   ├── __init__.py   ← exports verify_firebase_token, get_current_user
│   │   ├── firebase.py   ← verify_firebase_token() stub (TODO Phase 5)
│   │   └── dependencies.py ← get_current_user FastAPI dependency stub (TODO Phase 5)
│   └── user_service.py   ← UserService skeleton (TODO Phase 5)
├── repositories/
│   └── user_repo.py      ← UserRepository skeleton (TODO Phase 5)
├── middleware/            ← ASGI middleware — currently empty
├── utils/
│   └── db_url.py         ← normalize_database_url() — strips sslmode, fixes scheme
└── main.py               ← FastAPI app, CORS, /, /health, mounts /api/v1

alembic/
├── versions/
│   └── cfeccaac3dc7_phase_4_add_users_table.py  ← users table + gender_enum
├── env.py                ← Imports User model; async migration runner
└── script.py.mako
alembic.ini               ← Config (DATABASE_URL from env, not hardcoded)
requirements.txt
.env.example
```

---

## Current Phase

**Phase 4 — Core Domain Models & Authentication Foundation** ✅ Complete

Next phase:
- ⏳ Phase 5 — Firebase Auth Implementation & Extended User Profile

See `PROJECT_ROADMAP.md` for the complete phase list.

---

## Completed Work

### Phase 1 — Backend Foundation
- FastAPI app with CORS, Swagger, ReDoc
- `GET /` → JSON status response
- `GET /health` → `{"status": "healthy"}`
- Pydantic Settings config in `app/core/config.py`
- `requirements.txt`, `.env.example`, `.gitignore`, `README.md`

### Phase 2 — Database Foundation
- SQLAlchemy 2.x async engine (asyncpg)
- `DeclarativeBase` in `app/db/base.py`
- Production pool config: `pool_size=10`, `max_overflow=20`, `pool_pre_ping=True`, `pool_recycle=3600`
- `get_db` async dependency with rollback-on-error
- `normalize_database_url()` utility — converts any PostgreSQL URL scheme to `postgresql+asyncpg://`, strips psycopg2-only params (`sslmode`, `sslcert`, etc.)
- Alembic configured for async migrations; reads `DATABASE_URL` from env

### Phase 3 — Documentation
- `ARCHITECTURE.md` — full architecture reference
- `PROJECT_ROADMAP.md` — master phase roadmap
- `CONTRIBUTING.md` — branch, commit, and review standards
- `CHANGELOG.md` — version history
- `AI_AGENT.md` — this file
- `README.md` updated with links

### Phase 4 — Core Domain Models & Authentication Foundation
- `app/models/enums.py` — `Gender` string enum
- `app/db/mixins.py` — `UUIDMixin` (UUID v4 PK) and `TimestampMixin` (`created_at`/`updated_at`)
- `app/models/user.py` — `User` model with 14 columns; composite index on `(is_active, created_at)`
- `app/schemas/user.py` — `UserBase`, `UserRead`, `UserCreate`, `UserUpdate`
- `app/schemas/auth.py` — `FirebaseTokenPayload` (frozen, maps Firebase JWT claims), `AuthenticatedUser`
- `app/services/auth/` — `verify_firebase_token()` and `get_current_user` stubs with full Phase 5 TODO guidance
- `app/repositories/user_repo.py` — `UserRepository` with typed method signatures (not yet implemented)
- `app/services/user_service.py` — `UserService` with typed method signatures (not yet implemented)
- `app/api/v1/__init__.py` — combined v1 router
- `app/api/v1/auth.py` — auth router at `/api/v1/auth` (structure only)
- `app/main.py` — v1 router mounted at `/api/v1`
- `alembic/env.py` — `User` imported for Alembic detection
- Migration `cfeccaac3dc7_phase_4_add_users_table.py` — creates `gender_enum` + `users` table (generated; **not yet applied**)

---

## Pending Work

| Phase | Description |
|-------|-------------|
| 5 | Firebase Auth Implementation — implement `verify_firebase_token()`, `get_current_user`, `UserRepository`, `UserService`, login endpoint; apply migration |
| 6 | Extended User Profile & Follow System |
| 7 | Voice Rooms (LiveKit integration) |
| 8 | Audio Stories (MinIO / S3 storage) |
| 9 | Chat & Direct Messaging (WebSocket + Redis) |
| 10 | Wallet & Payments |
| 11 | Notifications (FCM + Celery) |
| 12 | Security Hardening |
| 13 | Testing (pytest, 80%+ coverage) |
| 14 | Observability & Monitoring (structlog, Prometheus, Sentry) |
| 15 | Deployment & Infrastructure (Docker, CI/CD) |

---

## Coding Rules

1. **Python 3.12 only** — use modern syntax; minimum version is 3.12
2. **Type-annotate everything** — every parameter and return type, no exceptions
3. **Async for all I/O** — `async def` for routes, services, repositories; no blocking calls
4. **Pydantic v2 schemas** — use `model_config` not inner `Config` class
5. **No `print()`** — use the application logger
6. **No bare `except:`** — always name the exception type
7. **No hardcoded secrets** — all config through `app/core/config.py` → env var
8. **`expire_on_commit=False`** on session — already configured; do not change
9. **SQLAlchemy 2.x typed mapping** — always use `Mapped[T]` + `mapped_column()`; never use the old `Column()` style

---

## Architecture Rules

### Dependency Direction (STRICT)
```
api → services → repositories → db/models
```
- `api` may import from `services` and `schemas` only
- `services` may import from `repositories`, `schemas`, and `models`
- `repositories` may import from `models` and `db`
- `utils` and `core` may be imported by any layer
- **Never import an outer layer from an inner layer**

### Layer Responsibilities
| Layer | Allowed | Forbidden |
|-------|---------|-----------|
| `api/` | Route definitions, schema validation, dependency injection | Business logic, raw SQL |
| `services/` | Business rules, orchestration | Raw SQL, HTTP status codes |
| `repositories/` | SQLAlchemy queries | Business logic, HTTP exceptions |
| `models/` | Table definitions | Business logic, Pydantic |
| `schemas/` | Request/response DTOs | ORM imports, DB sessions |
| `utils/` | Pure stateless helpers | DB access, side effects |

### Mixin Usage
All new models must use `UUIDMixin` and `TimestampMixin` from `app/db/mixins.py`.
MRO order: `class MyModel(UUIDMixin, TimestampMixin, Base):`

### Adding a New Model
1. Create `app/models/<name>.py` — inherit from `UUIDMixin`, `TimestampMixin`, `Base`
2. Add enum to `app/models/enums.py` if needed
3. Add import in `alembic/env.py` under the model imports comment block
4. Run `alembic revision --autogenerate -m "add <name> table"`
5. Apply: `alembic upgrade head`

### Adding a New Endpoint
1. Create `app/api/v1/<resource>.py` with `APIRouter`
2. Create `app/schemas/<resource>.py` for request/response schemas
3. Create `app/services/<resource>_service.py` for business logic
4. Create `app/repositories/<resource>_repo.py` for DB queries
5. Register the router in `app/api/v1/__init__.py` — **do not touch `app/main.py`**

---

## Forbidden Actions

**Never do these without explicit user instruction:**

| Forbidden | Reason |
|-----------|--------|
| Modify existing migration files in `alembic/versions/` | Breaks migration history |
| Add `time.sleep()` or blocking I/O | Blocks the async event loop |
| Import `requests` (sync HTTP) | Use `httpx` async instead |
| Return ORM objects from route handlers | Breaks serialisation — return schemas |
| Write SQL in service layer | Violates repository pattern |
| Write business logic in route handlers | Violates service pattern |
| Change `app/db/base.py` `Base` class name | Alembic metadata would break |
| Remove `expire_on_commit=False` | Causes detached instance errors |
| Install packages not in `requirements.txt` | Undocumented dependency |
| Commit to `main` directly | Protected branch |
| Skip updating `CHANGELOG.md` | Version history becomes stale |
| Skip importing new models in `alembic/env.py` | Migrations won't detect the new table |
| Use old-style `Column()` in models | Use `Mapped[T]` + `mapped_column()` only |
| Register new routers in `app/main.py` | Register in `app/api/v1/__init__.py` instead |

---

## Git Rules

| Rule | Detail |
|------|--------|
| Branch naming | `feat/`, `fix/`, `docs/`, `chore/`, `refactor/`, `test/`, `hotfix/` |
| Commit format | Conventional Commits: `type(scope): summary` |
| Commit scope | Affected layer: `auth`, `db`, `rooms`, `api`, `models`, etc. |
| Merge strategy | Squash merge into `main` |
| After completing a phase | Commit all changes, push, update `CHANGELOG.md` and `PROJECT_ROADMAP.md` |

### Commit message for a completed phase:
```
feat: Phase N — <Phase Name>

- Bullet list of deliverables
- Keep each line under 72 characters
```

---

## Development Rules

1. **Step 0 always:** scan the repo, read `README.md`, check `PROJECT_ROADMAP.md` before writing any code
2. **One phase at a time:** do not start Phase N+1 work inside a Phase N commit
3. **No orphan code:** every file created must be imported or used somewhere
4. **Validate before committing:** run import checks and Alembic check as a minimum
5. **No partial commits:** a commit must leave the app in a working state

### Validation Commands
```bash
# Check all imports resolve
python3.12 -c "from app.main import app; print('OK')"

# Check Alembic config + DB connectivity
python3.12 -m alembic check

# Generate migration (review before applying)
python3.12 -m alembic revision --autogenerate -m "description"

# Apply migrations
python3.12 -m alembic upgrade head
```

---

## Definition of Done

A phase is **Done** when:

- [ ] All deliverables listed in `PROJECT_ROADMAP.md` for the phase are present
- [ ] All success criteria for the phase are met
- [ ] No import errors (`python3.12 -c "from app.main import app"` succeeds)
- [ ] `alembic check` exits 0 (if DB changes were made)
- [ ] `README.md` updated with any new endpoints or env vars
- [ ] `PROJECT_ROADMAP.md` phase status updated from ⏳ to ✅
- [ ] `CHANGELOG.md` updated with the phase's additions
- [ ] `AI_AGENT.md` updated: Current Phase, Completed Work, architecture if changed
- [ ] Committed and pushed to GitHub with a conventional commit message

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
| `ALLOWED_ORIGINS` | No | `["*"]` | CORS allowed origins (lock down in production) |
| `DATABASE_URL` | **Yes** | — | PostgreSQL connection string |

**Planned (Phase 5):**

| Variable | Required | Description |
|----------|----------|-------------|
| `FIREBASE_SERVICE_ACCOUNT_PATH` | Yes | Path to Firebase service account JSON |

**DATABASE_URL format accepted:**
- `postgresql+asyncpg://user:pass@host:port/db` (canonical)
- `postgresql://user:pass@host:port/db` (auto-normalized)
- `postgres://user:pass@host:port/db` (auto-normalized)
- Query params like `sslmode=disable` are stripped automatically

---

## Key Design Decisions

| Decision | Reason |
|----------|--------|
| asyncpg over psycopg2 | Full async; required for SQLAlchemy 2.x async engine |
| `expire_on_commit=False` | Prevents `MissingGreenlet` errors on detached ORM instances |
| URL normalization in `utils/db_url.py` | Replit and many hosting platforms provide plain `postgresql://` URLs; asyncpg requires `+asyncpg` scheme |
| `sslmode` stripped from URL | asyncpg rejects psycopg2-style SSL params; use `connect_args={"ssl": ...}` if SSL control is needed |
| Alembic reads `DATABASE_URL` from env | Keeps credentials out of `alembic.ini` which is version-controlled |
| `pool_pre_ping=True` | Cloud PostgreSQL connections drop silently; pre-ping detects and replaces stale ones |
| Firebase over JWT/bcrypt | Vee is a mobile-first social platform; Firebase handles phone/Google/Apple sign-in natively |
| UUID v4 primary keys | Avoids sequential ID enumeration; safe to expose in URLs |
| `UUIDMixin` + `TimestampMixin` | Prevents duplicated columns across models; enforces consistency |
| New routers registered in `app/api/v1/__init__.py` | Keeps `app/main.py` stable — only one mount point regardless of how many resource routers exist |
| Migration generated but not applied in Phase 4 | Phase 5 will apply the migration as part of going live with the auth endpoints |
