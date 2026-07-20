# Contributing to Vee Backend

> Read `ARCHITECTURE.md` and `AI_AGENT.md` before making any changes.

---

## Branch Strategy

We follow **GitHub Flow** — simple, linear, and suitable for continuous delivery.

```
main                    ← production-ready, protected
  └── feat/phase-4-auth
  └── fix/token-expiry
  └── docs/update-roadmap
  └── chore/bump-deps
```

| Branch Prefix | When to Use |
|--------------|-------------|
| `feat/`      | New feature or phase work |
| `fix/`       | Bug fix |
| `docs/`      | Documentation only |
| `chore/`     | Dependency bumps, config changes, tooling |
| `refactor/`  | Code restructuring with no behaviour change |
| `test/`      | Adding or fixing tests |
| `hotfix/`    | Emergency production fix (branches from `main`) |

**Rules:**
- Never commit directly to `main`
- Branch names use kebab-case: `feat/phase-6-voice-rooms`
- Delete branches after merging
- Keep branches short-lived (ideally < 3 days)

---

## Commit Message Convention

Follow **Conventional Commits** (`https://www.conventionalcommits.org`).

### Format

```
<type>(<scope>): <short summary>

[optional body — wrap at 72 characters]

[optional footer: BREAKING CHANGE: ..., Closes #123]
```

### Types

| Type | When to Use |
|------|------------|
| `feat` | New feature or endpoint |
| `fix` | Bug fix |
| `docs` | Documentation only |
| `chore` | Dependency, config, tooling |
| `refactor` | Restructuring with no behaviour change |
| `test` | Adding or updating tests |
| `perf` | Performance improvement |
| `ci` | CI/CD configuration |

### Scope (optional but encouraged)

Use the affected layer or module: `auth`, `db`, `rooms`, `wallet`, `models`, `api`, `middleware`.

### Examples

```
feat(auth): add JWT access token generation

fix(db): normalize sslmode parameter for asyncpg compatibility

docs: add ARCHITECTURE.md and PROJECT_ROADMAP.md

chore(deps): bump sqlalchemy to 2.0.36

feat(rooms): implement LiveKit token generation endpoint

Closes #42
```

**Rules:**
- Summary line ≤ 72 characters
- Use imperative mood: "add", "fix", "update" — not "added", "fixed"
- No period at end of summary
- Reference issue numbers in footer: `Closes #123`

---

## Coding Standards

### General

- **Python 3.12** — use modern syntax (`match`, `type X = ...`, etc.)
- **Type hints everywhere** — every function parameter and return type must be annotated
- **No `Any`** — use proper types; if `Any` is unavoidable, add a comment explaining why
- **No bare `except:`** — always catch specific exception types
- **No `print()`** — use the application logger
- **No hardcoded secrets** — all secrets via environment variables through `app/core/config.py`

### Async

- All I/O must be `async` — no blocking calls (`requests`, `time.sleep`, `open()` for large files)
- Use `asyncio.gather()` for concurrent independent async operations
- Never call `asyncio.run()` inside a running event loop

### FastAPI Specifics

- All route handlers must be `async def`
- Use `Depends()` for dependency injection — never instantiate sessions or services manually inside routes
- Route functions return Pydantic schemas — never raw ORM objects
- Use `response_model=` on every route

### Database

- All DB access through the repository layer — never raw SQL in services or routes
- Use `AsyncSession` — never the sync `Session`
- Every repository method receives `session: AsyncSession` as a parameter
- Wrap multi-step writes in explicit transactions

---

## Naming Conventions

| Item | Convention | Example |
|------|-----------|---------|
| Files | `snake_case.py` | `user_service.py` |
| Classes | `PascalCase` | `UserRepository` |
| Functions / methods | `snake_case` | `get_user_by_email` |
| Variables | `snake_case` | `current_user` |
| Constants | `UPPER_SNAKE_CASE` | `MAX_RETRIES` |
| Pydantic schemas | `PascalCase` + suffix | `UserCreate`, `UserRead` |
| Router prefixes | `/resource` (plural) | `/users`, `/rooms` |
| Alembic migrations | Auto-generated slug | `a1b2c3d4_add_users_table` |

---

## Folder Rules

| Rule | Reason |
|------|--------|
| One model per file in `app/models/` | Easy to locate, avoids circular imports |
| One schema file per domain in `app/schemas/` | Mirrors models |
| One service class per domain in `app/services/` | Single Responsibility |
| One repository class per aggregate in `app/repositories/` | Clean DDD boundary |
| Pure helpers only in `app/utils/` | No side effects, no DB access |
| No cross-layer imports against the dependency rule | Outer → inner only |

When adding a new model:
1. Create `app/models/<name>.py`
2. Import it in `alembic/env.py` under the model imports section
3. Run `alembic revision --autogenerate -m "add <name> table"`
4. Apply with `alembic upgrade head`

---

## Pull Request Rules

1. **Every PR targets `main`** (GitHub Flow)
2. **One concern per PR** — do not mix feature work with refactoring
3. **PR title follows commit convention:** `feat(auth): add login endpoint`
4. **PR description must include:**
   - What changed and why
   - How to test it
   - Screenshots or curl examples for API changes
   - Migration steps if DB schema changed
5. **All CI checks must pass** before merging
6. **No self-merge** — at least one reviewer approval required (when team > 1)
7. **Squash merge preferred** to keep `main` history linear

---

## Review Checklist

Before approving a PR, verify:

### Architecture
- [ ] No layer boundaries violated (outer → inner only)
- [ ] No business logic in route handlers
- [ ] No raw SQL in services
- [ ] No ORM imports in schemas

### Code Quality
- [ ] All functions have type annotations
- [ ] No `Any`, no bare `except`, no `print()`
- [ ] No hardcoded secrets or localhost URLs
- [ ] New utilities are in `app/utils/`, not scattered

### Database
- [ ] New model inherits from `Base`
- [ ] New model imported in `alembic/env.py`
- [ ] Migration file included in the PR
- [ ] Migration is reversible (`downgrade` implemented)

### Documentation
- [ ] `README.md` updated if new endpoints or env vars added
- [ ] `PROJECT_ROADMAP.md` updated if a phase was completed
- [ ] `CHANGELOG.md` updated
- [ ] `AI_AGENT.md` updated if architecture changed
- [ ] Docstrings on public functions

### Tests (Phase 12+)
- [ ] New code has corresponding tests
- [ ] No regressions in existing tests
- [ ] Coverage did not decrease
