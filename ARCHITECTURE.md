# Vee Backend — Architecture

> This document is the authoritative reference for the architectural decisions, layer responsibilities, and design principles of the Vee backend. Every AI agent, developer, or contributor must read this before making structural changes.

---

## Project Vision

**Vee** is a production-grade social audio platform. Users can join live voice rooms, share audio stories, send messages, manage wallets, and receive notifications in real time.

The backend is designed for:
- **Horizontal scalability** — stateless API servers behind a load balancer
- **Async-first** — every I/O operation is non-blocking (asyncio + asyncpg)
- **Clean separation of concerns** — each layer has a single, well-defined responsibility
- **Future-proof extensibility** — new features plug into existing layers without restructuring

---

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Clients                              │
│              (Mobile App / Web / Admin)                     │
└────────────────────────┬────────────────────────────────────┘
                         │ HTTP / WebSocket
┌────────────────────────▼────────────────────────────────────┐
│                    API Gateway / Reverse Proxy               │
│                  (Nginx / Caddy — future)                    │
└────────────────────────┬────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────┐
│                    FastAPI Application                       │
│  ┌──────────┐  ┌──────────┐  ┌───────────┐  ┌──────────┐  │
│  │  Router  │  │  Schema  │  │Middleware │  │  Config  │  │
│  │ (api/)   │  │(schemas/)│  │(middlewr/)│  │ (core/)  │  │
│  └────┬─────┘  └──────────┘  └───────────┘  └──────────┘  │
│       │                                                      │
│  ┌────▼─────────────────────────────────────────────────┐  │
│  │                   Service Layer (services/)           │  │
│  │           Business Logic — orchestration only        │  │
│  └────┬─────────────────────────────────────────────────┘  │
│       │                                                      │
│  ┌────▼─────────────────────────────────────────────────┐  │
│  │                Repository Layer (repositories/)       │  │
│  │             Data Access — SQL queries only           │  │
│  └────┬─────────────────────────────────────────────────┘  │
│       │                                                      │
│  ┌────▼─────────────────────────────────────────────────┐  │
│  │                  Database Layer (db/)                 │  │
│  │       SQLAlchemy 2.x Async Engine + Session          │  │
│  └────┬─────────────────────────────────────────────────┘  │
└────────┼────────────────────────────────────────────────────┘
         │
┌────────▼─────────────┐   ┌──────────────┐   ┌────────────┐
│    PostgreSQL         │   │    Redis      │   │   MinIO    │
│  (Primary Store)      │   │  (Cache/PubS) │   │  (Media)   │
└──────────────────────┘   └──────────────┘   └────────────┘
```

---

## Clean Architecture

The codebase follows **Clean Architecture** principles:

```
                    ┌─────────────────────┐
                    │    API Layer        │  ← Outermost: HTTP handlers
                    │  (api/, schemas/)   │
                    └────────┬────────────┘
                             │ calls
                    ┌────────▼────────────┐
                    │   Service Layer     │  ← Business rules
                    │   (services/)       │
                    └────────┬────────────┘
                             │ calls
                    ┌────────▼────────────┐
                    │ Repository Layer    │  ← Data access abstraction
                    │  (repositories/)    │
                    └────────┬────────────┘
                             │ uses
                    ┌────────▼────────────┐
                    │   Database Layer    │  ← Innermost: persistence
                    │  (db/, models/)     │
                    └─────────────────────┘
```

**The Dependency Rule:** Dependencies always point inward. Outer layers know about inner layers; inner layers know nothing about outer layers.

---

## Folder Structure

```
vee-backend/
│
├── app/
│   ├── api/                # Route definitions, versioned routers
│   │   └── v1/             # (future) API version 1 routers
│   │       ├── auth.py
│   │       ├── users.py
│   │       └── ...
│   │
│   ├── core/               # Cross-cutting concerns
│   │   └── config.py       # Pydantic Settings (env-based configuration)
│   │
│   ├── db/                 # Database infrastructure
│   │   ├── base.py         # DeclarativeBase — all models inherit from here
│   │   ├── database.py     # Async engine creation and pool config
│   │   ├── session.py      # Session factory + get_db FastAPI dependency
│   │   └── __init__.py     # Public exports: Base, engine, get_db
│   │
│   ├── models/             # SQLAlchemy ORM models (table definitions)
│   │   └── user.py         # (future) User model
│   │
│   ├── schemas/            # Pydantic schemas (request/response DTOs)
│   │   └── user.py         # (future) UserCreate, UserRead, etc.
│   │
│   ├── services/           # Business logic (orchestrates repositories)
│   │   └── user_service.py # (future)
│   │
│   ├── repositories/       # Data access layer (raw DB queries)
│   │   └── user_repo.py    # (future)
│   │
│   ├── middleware/         # Custom ASGI middleware
│   │   └── logging.py      # (future) Request logging
│   │
│   ├── utils/              # Stateless helper functions
│   │   └── db_url.py       # PostgreSQL URL normalizer for asyncpg
│   │
│   └── main.py             # FastAPI app factory, middleware registration
│
├── alembic/                # Database migration scripts
│   ├── versions/           # Auto-generated migration files
│   ├── env.py              # Async migration runner
│   └── script.py.mako      # Migration file template
│
├── alembic.ini             # Alembic config (URL delegated to env var)
├── requirements.txt        # Python dependencies
├── .env.example            # Environment variable template
├── .gitignore
├── README.md
├── ARCHITECTURE.md         # ← You are here
├── PROJECT_ROADMAP.md
├── CONTRIBUTING.md
├── CHANGELOG.md
└── AI_AGENT.md
```

---

## Layer Responsibilities

### API Layer (`app/api/`)

- Defines HTTP routes using `APIRouter`
- Validates input via Pydantic schemas
- Calls service layer — never repositories directly
- Returns response schemas — never raw ORM objects
- Handles HTTP-level concerns: status codes, headers, auth dependencies

**What it must NOT do:** contain business logic, write SQL, or call the database directly.

---

### Schema Layer (`app/schemas/`)

- Pure Pydantic v2 models for request bodies and response payloads
- Separates wire format from database format
- Naming convention: `UserCreate`, `UserRead`, `UserUpdate`, `UserList`

**What it must NOT do:** import SQLAlchemy models or database sessions.

---

### Service Layer (`app/services/`)

- Contains all business rules and orchestration logic
- Calls one or more repositories to fulfil a use case
- Raises domain exceptions (not HTTP exceptions)
- Stateless — receives `AsyncSession` from the API layer via dependency injection

**What it must NOT do:** write SQL directly, import `APIRouter`, or know about HTTP status codes.

---

### Repository Layer (`app/repositories/`)

- The only layer that writes SQL (via SQLAlchemy ORM or `select()`)
- One repository per aggregate root (e.g., `UserRepository`)
- Receives `AsyncSession` as a constructor argument
- Returns ORM model instances or `None`

**What it must NOT do:** contain business logic, raise HTTP exceptions, or call other repositories.

---

### Model Layer (`app/models/`)

- SQLAlchemy 2.x declarative ORM models
- All models inherit from `app.db.base.Base`
- Defines table schema, columns, relationships, and constraints
- After adding any model, import it in `alembic/env.py` for auto-migration detection

**What it must NOT do:** contain business logic or Pydantic validation.

---

### Database Layer (`app/db/`)

| File | Responsibility |
|------|---------------|
| `base.py` | `DeclarativeBase` shared by all models |
| `database.py` | Async engine with production pool settings |
| `session.py` | `AsyncSessionLocal` factory + `get_db` dependency |
| `__init__.py` | Public re-exports |

---

### Core Layer (`app/core/`)

- Application-wide configuration via `pydantic_settings.BaseSettings`
- All environment variables defined here as typed fields
- Singleton `settings` object imported across the app

---

### Middleware Layer (`app/middleware/`)

- Custom ASGI middleware (request ID injection, structured logging, rate limiting)
- Registered in `app/main.py` via `app.add_middleware()`

---

### Utils Layer (`app/utils/`)

- Pure, stateless helper functions with no side effects
- Must not import from `api/`, `services/`, or `repositories/`
- Currently: `db_url.py` — URL normalization for asyncpg compatibility

---

## Dependency Direction

```
api  →  services  →  repositories  →  db / models
         ↑                ↑
       schemas          models
         ↑
        core (config)   utils (helpers)
```

- `core` and `utils` are imported by any layer
- `models` are imported by `repositories` and `db`
- `schemas` are imported by `api` and sometimes `services`
- Never import from an outer layer into an inner layer

---

## Request Flow

```
1. Client sends HTTP request
        ↓
2. Middleware pipeline
   (logging, auth header extraction, request ID)
        ↓
3. FastAPI Router (app/api/)
   - Validates request body via Pydantic schema
   - Resolves FastAPI dependencies (get_db, get_current_user)
        ↓
4. Service function (app/services/)
   - Applies business rules
   - Calls repository methods
        ↓
5. Repository method (app/repositories/)
   - Executes SQLAlchemy query via AsyncSession
        ↓
6. PostgreSQL (via asyncpg)
        ↓
7. Result propagates back up through the same chain
        ↓
8. Router serialises ORM model → Pydantic response schema
        ↓
9. FastAPI returns JSON response to client
```

---

## Database Layer

**Engine:** Created once at application startup in `app/db/database.py`.

| Setting | Value | Reason |
|---------|-------|--------|
| `pool_size` | 10 | Sustained connection pool |
| `max_overflow` | 20 | Burst capacity |
| `pool_pre_ping` | True | Detect stale connections |
| `pool_recycle` | 3600s | Prevent long-lived connection issues |
| `echo` | `DEBUG` env | SQL logging in dev only |

**Session:** `async_sessionmaker` with `expire_on_commit=False` (avoids lazy-load errors on detached instances).

**Migrations:** Alembic with async engine. Run `alembic upgrade head` before starting the server in any environment.

---

## Future Infrastructure

| Component | Purpose | Phase |
|-----------|---------|-------|
| Redis | Session cache, pub/sub for real-time events | Phase 6 |
| LiveKit | WebRTC voice room infrastructure | Phase 5 |
| MinIO / S3 | Audio story and avatar file storage | Phase 7 |
| Celery + Redis | Async background tasks (notifications, wallet) | Phase 8 |
| Prometheus + Grafana | Metrics and alerting | Phase 11 |
| Sentry | Error tracking | Phase 11 |

---

## Deployment Strategy

**Target:** Containerised deployment on a cloud provider (AWS / GCP / DigitalOcean).

```
Client → CDN → Load Balancer → N × FastAPI containers → PostgreSQL (RDS)
                                                        → Redis (ElastiCache)
                                                        → MinIO / S3
```

- Each container is stateless — no local file storage
- Database migrations run as a one-off job before deploying new containers
- Environment variables injected via secrets manager (AWS Secrets Manager / Vault)

---

## Scaling Strategy

| Concern | Approach |
|---------|---------|
| API throughput | Horizontal pod autoscaling (HPA) on CPU/request rate |
| DB read load | Read replicas + SQLAlchemy read/write router (future) |
| Real-time connections | LiveKit media server cluster |
| Media storage | Object storage (MinIO / S3) — not local disk |
| Background jobs | Celery workers scaled independently of API servers |
| Cache | Redis cluster for session tokens, rate limiting, pub/sub |
