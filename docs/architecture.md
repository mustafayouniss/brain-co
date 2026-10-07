# Architecture Documentation

This document describes the verified structural layout, configuration and database session flows, migration connectivity, and component versions for the OrgBrain backend.

---

## 1. Folder Structure

Every folder in the repository and its single-line designated purpose:

- `OrgBrain/`: Root workspace directory containing repository configurations, documentation, and container manifests.
- `docs/`: System documentation, operational runbooks, architectural decisions, and task logs.
- `docs/adr/`: Architecture Decision Records (ADRs) recording historical design choices and context.
- `docs/journal/`: Daily chronological session records capturing actions taken, commands run, and issues resolved.
- `docs/rings/`: Ring architecture boundary specifications detailing security, isolation, and ring requirements.
- `backend/`: Python application workspace containing source code, migrations, virtual environment, and dependency manifests.
- `backend/.venv/`: Isolated Python 3.12 virtual environment containing installed project dependencies.
- `backend/app/`: Primary FastAPI application package containing all backend logic and modules.
- `backend/app/api/`: HTTP API routes, endpoint handlers, and request controllers.
- `backend/app/core/`: Application settings, environment variable loaders, and core cross-cutting configurations.
- `backend/app/db/`: Database connection engine setup, base model declarations, and session factory utilities.
- `backend/app/models/`: SQLAlchemy 2.0 ORM declarative database models.
- `backend/app/schemas/`: Pydantic v2 data models for input validation, request parsing, and response serialization.
- `backend/app/services/`: Reusable domain business logic and data processing operations decoupled from API endpoints.
- `backend/migrations/`: Alembic database schema migration environment and runners.
- `backend/migrations/versions/`: Individual revision scripts representing historical database schema transformations.
- `backend/tests/`: Automated pytest test suites covering unit, integration, and endpoint behaviors.

---

## 2. Configuration and Database Session Flow

The application manages settings and database sessions through a decoupled, deterministic flow:

```
[.env (at repository root)]
          │
          ▼
[backend/app/core/config.py]
  - Resolves root path: Path(__file__).resolve().parent.parent.parent.parent / ".env"
  - Instantiates Pydantic Settings class (`settings`)
  - Exposes `settings.DATABASE_URL`
          │
          ▼
[backend/app/db/session.py]
  - Imports `settings` from `app.core.config`
  - Initializes sync engine: `create_engine(str(settings.DATABASE_URL), pool_pre_ping=True)`
  - Creates sessionmaker factory: `SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)`
          │
          ▼
[Application Services / Handlers]
  - Uses `SessionLocal()` to generate individual synchronous database transactions.
```

### Key Implementation Details
1. **Root-Path Resolution**: The `.env` file is loaded from the repository root regardless of current working directory by building an absolute path from `config.py` (`Path(__file__).resolve().parent.parent.parent.parent / ".env"`). Running commands from either `OrgBrain/` or `backend/` produces identical configuration behavior.
2. **Database Driver**: The database connection string utilizes the modern `psycopg` v3 driver format: `postgresql+psycopg://<user>:<password>@<host>:<port>/<database>`.

---

## 3. How Alembic Connects

Alembic migrations connect to PostgreSQL through the same unified application configuration:

1. **Path Resolution**: When `alembic` commands are executed (from `backend/`), `backend/migrations/env.py` adds `backend` to `sys.path`.
2. **Settings Import**: `env.py` imports the instantiated `settings` object directly from `app.core.config`.
3. **URL Overwrite**: In `run_migrations_online()` and `run_migrations_offline()`, `env.py` executes:
   ```python
   config.set_main_option("sqlalchemy.url", str(settings.DATABASE_URL))
   ```
4. **Execution**: The database connection engine is created via `engine_from_config` using the resolved application `DATABASE_URL`. Revisions are executed within an active transaction and tracked in the `alembic_version` PostgreSQL table.

---

## 4. Database Engine and Container Image Versions

The following versions were deployed, executed, and verified:

- **Docker Image**: `pgvector/pgvector:pg17`
- **Database Engine**: `PostgreSQL 17.11 (Debian 17.11-1.pgdg12+2)` on `x86_64-pc-linux-gnu`
- **Postgres Extension**: `vector` (pgvector) version `0.8.7`
- **SQLAlchemy**: `2.0.54` (pinned in `backend/requirements.txt`)
- **Psycopg**: `3.3.6` (binary driver `psycopg-binary==3.3.6`)
- **Alembic**: `1.20.0`

---

## 5. Endpoints & Test Suite

### API Routes
- `backend/app/main.py`:
  - `GET /health`: Health check endpoint returning `{"status": "ok"}`.

### Test Architecture
- `backend/tests/test_health.py`:
  - Uses `fastapi.testclient.TestClient` initialized with `app` from `app.main`.
  - Asserts HTTP status code 200 and exact JSON body `{"status": "ok"}`.

