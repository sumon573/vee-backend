# Vee Backend

Production-ready backend for **Vee** — a social audio platform.

Built with **Python 3.12** and **FastAPI**.

---

## Documentation

| Document | Description |
|----------|-------------|
| [ARCHITECTURE.md](ARCHITECTURE.md) | Full architecture reference — layers, request flow, scaling |
| [PROJECT_ROADMAP.md](PROJECT_ROADMAP.md) | Master phase roadmap — completed, current, and pending phases |
| [CONTRIBUTING.md](CONTRIBUTING.md) | Branch strategy, commit convention, coding standards, PR rules |
| [CHANGELOG.md](CHANGELOG.md) | Version history in Keep a Changelog format |
| [AI_AGENT.md](AI_AGENT.md) | Instruction manual for AI agents — read this first |

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Runtime | Python 3.12 |
| Framework | FastAPI |
| Server | Uvicorn |
| Config | Pydantic Settings |
| Database | PostgreSQL + SQLAlchemy 2.x (async) |
| Migrations | Alembic |
| Driver | asyncpg |

---

## Project Structure

```
app/
├── api/            # Route handlers and API versioning
│   └── v1/
│       ├── auth.py     # POST /api/v1/auth/login, GET /api/v1/auth/me
│       ├── blocks.py   # POST|DELETE /users/{username}/block, GET /users/blocked
│       ├── follows.py  # POST|DELETE /users/{username}/follow, GET followers/following/relationship
│       └── users.py    # GET/PATCH/DELETE /api/v1/users/me, GET /api/v1/users/{username}
├── core/
│   ├── config.py   # Pydantic Settings — all env vars
│   └── exceptions.py # Domain exception hierarchy
├── db/
│   ├── base.py     # DeclarativeBase for all ORM models
│   ├── database.py # Async engine with production pool config
│   ├── session.py  # Session factory and get_db dependency
│   └── __init__.py # Public exports
├── models/         # ORM models
│   ├── enums.py    # Gender enum
│   ├── user.py     # User model (with soft-delete support)
│   ├── follow.py   # Follow relationship model (Phase 7)
│   └── block.py    # Block relationship model (Phase 8)
├── schemas/        # Pydantic request/response schemas
│   ├── auth.py     # FirebaseTokenPayload, AuthenticatedUser
│   ├── user.py     # UserRead, UserPublicRead, UserUpdate, UserDeletedRead
│   ├── follow.py   # FollowRead, FollowUserRead, FollowListResponse, RelationshipRead
│   └── block.py    # BlockRead, BlockedUserRead, BlockedListResponse
├── services/       # Business logic layer
│   ├── auth/       # Firebase token verification + get_current_user dependency
│   ├── identity_service.py # Login orchestration
│   ├── user_service.py     # Profile management, soft-delete
│   ├── follow_service.py   # Follow/unfollow business rules (Phase 7)
│   ├── block_service.py    # Block/unblock business rules (Phase 8)
│   └── privacy_guard.py    # Reusable privacy permission checks (Phase 8)
├── repositories/   # Data access layer
│   ├── user_repo.py     # All User DB queries
│   ├── follow_repo.py   # All Follow DB queries (Phase 7)
│   └── block_repo.py    # All Block DB queries (Phase 8)
├── middleware/     # Custom ASGI middleware
├── utils/
│   └── db_url.py   # PostgreSQL URL normalizer for asyncpg
└── main.py         # FastAPI application entry point

alembic/            # Database migration scripts
alembic.ini         # Alembic config (DATABASE_URL from env)
```

---

## Getting Started

### 1. Clone and set up environment

```bash
cp .env.example .env
# Edit .env and set your DATABASE_URL and Firebase credentials
```

### 2. Create virtual environment

```bash
python3.12 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Apply database migrations

```bash
alembic upgrade head
```

### 5. Run the server

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

---

## Database Setup

### Environment variable

Set the following in your `.env` file:

```env
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/vee
```

> Plain `postgresql://` and `postgres://` schemes are also accepted — the application normalises them automatically.

### Migration commands

```bash
# Apply all pending migrations
alembic upgrade head

# Create a new migration (auto-detect model changes)
alembic revision --autogenerate -m "description"

# Roll back one migration
alembic downgrade -1

# Check current migration state
alembic current

# View migration history
alembic history
```

### Adding new models

1. Create your model in `app/models/` inheriting from `UUIDMixin`, `TimestampMixin`, `Base`
2. Import it in `alembic/env.py` under the model imports section
3. Run `alembic revision --autogenerate -m "add <model>"`
4. Apply with `alembic upgrade head`

---

## API Endpoints

### Public

| Method | Path | Description |
|--------|------|-------------|
| GET | `/` | API info and status |
| GET | `/health` | Health check |
| GET | `/docs` | Swagger UI |
| GET | `/redoc` | ReDoc UI |
| GET | `/api/v1/users/{username}` | Public user profile (with follower/following counts; block status when authenticated) |
| GET | `/api/v1/users/{username}/followers` | List a user's followers |
| GET | `/api/v1/users/{username}/following` | List users a user follows |

### Protected (Firebase Bearer token required)

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/auth/login` | Login / auto-register |
| GET | `/api/v1/auth/me` | Get own profile (auth namespace) |
| GET | `/api/v1/users/me` | Get own full profile (users namespace) |
| PATCH | `/api/v1/users/me` | Update own profile |
| DELETE | `/api/v1/users/me` | Soft-delete own account |
| POST | `/api/v1/users/{username}/follow` | Follow a user |
| DELETE | `/api/v1/users/{username}/follow` | Unfollow a user |
| GET | `/api/v1/users/{username}/relationship` | Mutual relationship status |
| POST | `/api/v1/users/{username}/block` | Block a user (auto-removes follow in both directions) |
| DELETE | `/api/v1/users/{username}/block` | Unblock a user |
| GET | `/api/v1/users/blocked` | Paginated list of blocked users |

---

## Error Response Format

All domain errors return a structured JSON body:

```json
{
  "error": "machine_readable_code",
  "message": "Human readable description."
}
```

| HTTP Status | Error Code | Cause |
|-------------|-----------|-------|
| 401 | `invalid_token` | Malformed Firebase token |
| 401 | `token_expired` | Firebase token expired |
| 401 | `token_revoked` | Firebase token revoked |
| 400 | `self_follow` | Attempted to follow yourself |
| 403 | `account_inactive` | Account suspended or deleted |
| 404 | `user_not_found` | Username not found or deleted |
| 409 | `username_conflict` | Username already taken |
| 409 | `already_following` | Already following this user |
| 409 | `not_following` | Not currently following this user |
| 400 | `self_block` | Attempted to block yourself |
| 409 | `already_blocked` | Already blocked this user |
| 409 | `not_blocked` | Not currently blocking this user |
| 422 | `reserved_username` | Username is reserved |
| 503 | `firebase_unavailable` | Firebase service unreachable |

---

## Roadmap

See [PROJECT_ROADMAP.md](PROJECT_ROADMAP.md) for the full phase-by-phase plan.

| Phase | Status | Description |
|-------|--------|-------------|
| 1 | ✅ | Backend Foundation |
| 2 | ✅ | Database Foundation |
| 3 | ✅ | Documentation & Architecture Governance |
| 4 | ✅ | Core Domain Models & Authentication Foundation |
| 5 | ✅ | Identity & Authentication Infrastructure |
| 6 | ✅ | Extended User Profile Management |
| 7 | ✅ | Social Graph (Follow System) |
| 8 | ✅ | Privacy & Safety Foundation (Block System) |
| 9 | ⏳ | Voice Rooms (LiveKit) |
| 8 | ⏳ | Audio Stories (MinIO) |
| 9 | ⏳ | Chat & Messaging |
| 10 | ⏳ | Wallet & Payments |
| 11 | ⏳ | Notifications |
| 12 | ⏳ | Security Hardening |
| 13 | ⏳ | Testing |
| 14 | ⏳ | Observability & Monitoring |
| 15 | ⏳ | Deployment & Infrastructure |
