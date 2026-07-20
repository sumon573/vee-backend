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
├── core/
│   └── config.py   # Pydantic Settings — all env vars
├── db/
│   ├── base.py     # DeclarativeBase for all ORM models
│   ├── database.py # Async engine with production pool config
│   ├── session.py  # Session factory and get_db dependency
│   └── __init__.py # Public exports
├── models/         # ORM models (future phases)
├── schemas/        # Pydantic request/response schemas
├── services/       # Business logic layer
├── repositories/   # Data access layer
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
# Edit .env and set your DATABASE_URL
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

1. Create your model in `app/models/` inheriting from `Base`
2. Import it in `alembic/env.py` under the model imports section
3. Run `alembic revision --autogenerate -m "add <model>"`
4. Apply with `alembic upgrade head`

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/` | API info and status |
| GET | `/health` | Health check |
| GET | `/docs` | Swagger UI |
| GET | `/redoc` | ReDoc UI |

---

## Roadmap

See [PROJECT_ROADMAP.md](PROJECT_ROADMAP.md) for the full phase-by-phase plan.

| Phase | Status | Description |
|-------|--------|-------------|
| 1 | ✅ | Backend Foundation |
| 2 | ✅ | Database Foundation |
| 3 | ✅ | Documentation & Architecture Governance |
| 4 | ⏳ | Authentication & User Management |
| 5 | ⏳ | Extended User Profile & Follow System |
| 6 | ⏳ | Voice Rooms (LiveKit) |
| 7 | ⏳ | Audio Stories (MinIO) |
| 8 | ⏳ | Chat & Messaging |
| 9 | ⏳ | Wallet & Payments |
| 10 | ⏳ | Notifications |
| 11 | ⏳ | Security Hardening |
| 12 | ⏳ | Testing |
| 13 | ⏳ | Observability & Monitoring |
| 14 | ⏳ | Deployment & Infrastructure |
