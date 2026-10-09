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
- `backend/app/api/`: HTTP API routes, endpoint handlers, dependency providers (`deps.py`), and versioned routers (`v1/`).
- `backend/app/core/`: Application settings, environment variable loaders, unified error handling (`errors.py`), and cryptographic/security utilities (`security.py`).
- `backend/app/db/`: Database connection engine (hide_parameters=True), declarative Base (`base.py`), session factory, and test safety guards (`test_utils.py`).
- `backend/app/models/`: SQLAlchemy 2.0 ORM declarative models. Currently: `user.py` (User entity with case-insensitive email uniqueness and role check constraint).
- `backend/app/schemas/`: Pydantic v2 data models for input validation, request parsing, and response serialization.
- `backend/app/services/`: Reusable domain business logic and data processing operations decoupled from API endpoints.
- `backend/migrations/`: Alembic database schema migration environment and runners.
- `backend/migrations/versions/`: Individual revision scripts representing historical database schema transformations.
- `backend/tests/`: Automated pytest test suites covering unit, integration, and endpoint behaviors with isolated test DB fixtures.
- `ai/`: Reusable, provider-agnostic AI Engine package in Python 3.12.
- `ai/core/`: Interfaces (`provider.py`), normalized Pydantic types (`request.py`, `response.py`, `error.py`), and orchestration services (`llm_service.py`).
- `ai/providers/`: Extensible provider implementations (`OpenAIProvider`, `DeepSeekProvider`, `OpenRouterProvider`, `KimiProvider`, `OllamaProvider`, `FakeLLMProvider`) and central `ProviderRegistry` factory.
- `ai/prompts/`: Template interpolation, variable extraction, and chat formatting (`prompt_template.py`).
- `ai/config/`: Centralized configuration loading multi-provider credentials from `.env` (`ai_config.py`).
- `ai/tests/`: Automated Pytest suite (54 unit tests) covering swappability, contracts, error normalization, and mock generations.

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
  - Validates SECRET_KEY (min length 32, no placeholder)
  - Exposes `settings.DATABASE_URL` and `settings.TEST_DATABASE_URL`
          │
          ▼
[backend/app/db/session.py]
  - Imports `settings` from `app.core.config`
  - Initializes sync engine: `create_engine(str(settings.DATABASE_URL), pool_pre_ping=True, hide_parameters=True)`
  - Creates sessionmaker factory: `SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)`
          │
          ▼
[backend/app/api/deps.py (`get_db`)]
  - Yields `SessionLocal()` transaction and guarantees closing in `finally` block
          │
          ▼
[Application Services / Handlers]
  - Receives `Session` via `Depends(get_db)`
```

### Key Implementation Details
1. **Root-Path Resolution**: The `.env` file is loaded from the repository root regardless of current working directory by building an absolute path from `config.py` (`Path(__file__).resolve().parent.parent.parent.parent / ".env"`). Running commands from either `OrgBrain/` or `backend/` produces identical configuration behavior.
2. **Database Driver**: The database connection string utilizes the modern `psycopg` v3 driver format: `postgresql+psycopg://<user>:<password>@<host>:<port>/<database>`.

---

## 3. How Alembic Connects

Alembic migrations connect to PostgreSQL through the same unified application configuration:

1. **Path Resolution**: When `alembic` commands are executed (from `backend/`), `backend/migrations/env.py` adds `backend` to `sys.path`.
2. **Settings Import**: `env.py` imports the instantiated `settings` object directly from `app.core.config`.
3. **URL Selection**: `env.py` checks `config.attributes.get("database_url")` (set by tests to point to the isolated test database); if absent, it falls back to `settings.DATABASE_URL` so regular CLI runs always target the development database.
4. **Execution**: The database connection engine is created via `engine_from_config`. Revisions are executed within an active transaction and tracked in the `alembic_version` PostgreSQL table.

---

## 4. Database Engine, Security and Dependency Versions

The following versions were deployed, executed, and verified:

- **Docker Image**: `pgvector/pgvector:pg17`
- **Database Engine**: `PostgreSQL 17.11 (Debian 17.11-1.pgdg12+2)` on `x86_64-pc-linux-gnu`
- **Postgres Extension**: `vector` (pgvector) version `0.8.7`
- **SQLAlchemy**: `2.0.54` (pinned in `backend/requirements.txt`)
- **Psycopg**: `3.3.6` (binary driver `psycopg-binary==3.3.6`)
- **Alembic**: `1.20.0`
- **Password Hashing**: `argon2-cffi==25.1.0` (Argon2id)
- **JWT Provider**: `pyjwt==2.15.1` (HS256)
- **HTTPX2**: `2.13.1` (pinned test dependency)

---

## 5. Endpoints & Test Suite

### API Routes
- `backend/app/main.py`:
  - `GET /health`: Root health check endpoint returning `{"status": "ok"}`.
  - Mounts `api_router` from `app.api.v1` under `/api/v1`.
- `backend/app/api/v1/health.py`:
  - `GET /api/v1/health/db`: Database health check running `SELECT 1` via `get_db`. Returns `{"status": "ok", "database": "up"}` on success, or 503 `SERVICE_UNAVAILABLE` on failure.

### Security Architecture
- `backend/app/core/security.py`:
  - `hash_password(plain)`: Argon2id password hashing with length validation (1-128 chars).
  - `verify_password(plain, hashed)`: Safe verification returning `bool` without raising on malformed hashes.
  - `verify_dummy_password(plain)`: Precomputed dummy hash verification for unknown users to defeat timing attacks.
  - `password_needs_rehash(hashed)`: Detection of outdated hashing parameters.
  - `create_access_token(subject)`: Generates HS256 JWT containing strictly `sub`, `iat`, and `exp`.
  - `decode_access_token(token)`: Validates signature and required claims (`sub`, `iat`, `exp`), raising uniform `TokenSecurityError`.

### Error Handling Architecture
- `backend/app/core/errors.py`:
  - Single registration entrypoint: `register_exception_handlers(app)`.
  - Enforces unified JSON error format: `{"error": {"code": "...", "message": "...", "details": ...}}`.
  - Handlers:
    - `StarletteHTTPException`: Maps status codes to machine-readable string codes; preserves response headers.
    - `RequestValidationError`: Returns 422 with sanitized list of field errors (dotted path, message, type) without exposing submitted values or context.
    - `Exception`: Catches all unhandled exceptions; logs traceback server-side and returns generic 500 error.

### Test Architecture
- `backend/tests/conftest.py`:
  - `test_engine`: Session-scoped, provisions and runs Alembic migrations on `orgbrain_legal_test`.
  - `db_session`: Function-scoped, runs tests inside transactions rolled back at teardown.
  - `client`: TestClient with `get_db` overridden to use `db_session`.
- Suites:
  - `test_health.py`: Root health check test.
  - `test_api_v1_health.py`: Tests `/api/v1/health/db` reachability and simulated failure with leak prevention.
  - `test_errors.py`: Tests 404, 405, 422 validation error formatting, 500 unhandled errors, and custom HTTPException handling.
  - `test_db_isolation.py`: Smoke test asserting current database ends with `_test` and contains `vector` extension.
  - `test_safety_guard.py`: Unit tests for `assert_safe_test_database`.
  - `test_no_raw_db_in_tests.py`: Static guardrail scanner ensuring test files never access development DATABASE_URL.
  - `test_user_model.py`: Tests for `User` model — UUID generation, `is_active` default, ORM email normalisation, duplicate email (both ORM and raw SQL bypass), invalid role, null hashed_password, and `engine.hide_parameters`.
  - `test_security.py`: Unit tests for password hashing, safe verification, dummy hash timing mitigation, rehash checking, JWT round-trip/expiry/tampering/alg-none rejection, and SECRET_KEY validation.

### Database Tables (via Alembic)
| Revision | Table | Description |
|---|---|---|
| `6dd2ff08b0bb` | — | Enables `pgvector` extension |
| `778be99882b6` | `users` | User accounts; UUID PK, case-insensitive unique email, VARCHAR+CHECK role, timezone-aware `created_at` |


