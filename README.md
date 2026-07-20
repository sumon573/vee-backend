# Vee Backend

Production-ready backend for **Vee** — a social audio platform.

Built with **Python 3.12** and **FastAPI**.

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
├── core/           # Configuration and application settings
│   └── config.py   # Pydantic Settings
├── db/             # Database layer
│   ├── base.py     # DeclarativeBase for all ORM models
│   ├── database.py # Async engine creation
│   ├── session.py  # Session factory and get_db dependency
│   └── __init__.py # Public exports
├── models/         # ORM models (future phases)
├── schemas/        # Pydantic request/response schemas
├── services/       # Business logic layer
├── repositories/   # Data access layer
├── middleware/     # Custom middleware
├── utils/          # Shared utility functions
└── main.py         # FastAPI application entry point

alembic/            # Database migration scripts
alembic.ini         # Alembic configuration
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

### 4. Run the server

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

> The `postgresql+asyncpg://` scheme is required for async SQLAlchemy 2.x.

### Run migrations

```bash
# Create a new migration (auto-detect model changes)
alembic revision --autogenerate -m "description"

# Apply all pending migrations
alembic upgrade head

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

- [x] Phase 1 — Backend Foundation
- [x] Phase 2 — Database Foundation
- [ ] Phase 3 — Authentication & User Management
- [ ] Phase 4 — Voice Room
- [ ] Phase 5 — Social Features
- [ ] Phase 6 — Notifications & Wallet
