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

---

## Project Structure

```
app/
├── api/            # Route handlers and API versioning
├── core/           # Configuration and application settings
├── db/             # Database connection and session management
├── models/         # ORM models
├── schemas/        # Pydantic request/response schemas
├── services/       # Business logic layer
├── repositories/   # Data access layer
├── middleware/     # Custom middleware
├── utils/          # Shared utility functions
└── main.py         # FastAPI application entry point
```

---

## Getting Started

### 1. Clone and set up environment

```bash
cp .env.example .env
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

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/` | API info and status |
| GET | `/health` | Health check |
| GET | `/docs` | Swagger UI |
| GET | `/redoc` | ReDoc UI |

---

## Roadmap

- [ ] Phase 1 — Backend Foundation ✅
- [ ] Phase 2 — Authentication & User Management
- [ ] Phase 3 — Voice Room
- [ ] Phase 4 — Social Features
- [ ] Phase 5 — Notifications & Wallet
