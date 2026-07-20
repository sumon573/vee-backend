# Changelog

All notable changes to this project will be documented in this file.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
This project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### In Progress
- Phase 3 — Project Documentation & Architecture Governance

---

## [0.1.0] — 2025-07-20

### Added — Phase 2: Database Foundation

- `app/db/base.py` — `DeclarativeBase` shared by all future ORM models
- `app/db/database.py` — async SQLAlchemy engine with production connection pool settings (`pool_size=10`, `max_overflow=20`, `pool_pre_ping=True`, `pool_recycle=3600`)
- `app/db/session.py` — `AsyncSessionLocal` session factory and `get_db` FastAPI dependency (async generator with rollback-on-error)
- `app/db/__init__.py` — public re-exports: `Base`, `engine`, `AsyncSessionLocal`, `get_db`
- `app/utils/db_url.py` — `normalize_database_url()` utility: converts `postgres://` / `postgresql://` to `postgresql+asyncpg://` and strips `sslmode` / SSL query parameters incompatible with asyncpg
- `alembic/` — Alembic initialized with async migration support (`asyncio.run` + `async_engine_from_config`)
- `alembic/env.py` — configured to read `DATABASE_URL` from environment, normalize it, and import `Base.metadata` for autogenerate
- `alembic.ini` — `sqlalchemy.url` delegated to environment variable
- `DATABASE_URL` field added to `app/core/config.py`
- `requirements.txt` updated: `sqlalchemy>=2.0.0`, `alembic>=1.13.0`, `asyncpg>=0.29.0`
- `.env.example` updated with `DATABASE_URL` example
- `README.md` updated with Database Setup section and migration commands

### Added — Phase 1: Backend Foundation

- Python 3.12 runtime
- `app/main.py` — FastAPI application with `CORSMiddleware`, Swagger UI (`/docs`), ReDoc (`/redoc`)
- `app/core/config.py` — `pydantic_settings.BaseSettings` for environment-based configuration
- `GET /` — root endpoint returning `{"name", "version", "status", "environment", "docs"}`
- `GET /health` — health check endpoint returning `{"status": "healthy"}`
- Clean architecture folder scaffold: `api/`, `core/`, `db/`, `models/`, `schemas/`, `services/`, `repositories/`, `middleware/`, `utils/`
- `requirements.txt` — minimal dependencies: `fastapi`, `uvicorn[standard]`, `pydantic`, `pydantic-settings`, `python-dotenv`
- `.env.example` — environment variable template
- `.gitignore` — Python standard ignores
- `README.md` — project overview, tech stack, getting started guide, API endpoints

---

## Release Notes Format

When cutting a new release:

1. Move `[Unreleased]` content to a new versioned section
2. Add the release date: `## [X.Y.Z] — YYYY-MM-DD`
3. Group changes under: `Added`, `Changed`, `Deprecated`, `Removed`, `Fixed`, `Security`
4. Update `[Unreleased]` link at the bottom of this file

---

[Unreleased]: https://github.com/sumon573/vee-backend/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/sumon573/vee-backend/releases/tag/v0.1.0
