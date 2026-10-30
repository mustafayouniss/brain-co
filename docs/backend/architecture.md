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
- `backend/app/models/`: SQLAlchemy 2.0 ORM declarative models (`user.py`, `source.py`, and Ring 1 models via `ring1.models.observation`).
- `backend/app/ring1/`: Ring 1 General Brain Peer-to-Peer Mesh implementation.
  - `contracts/`: Typed versioned envelopes (`envelopes.py`), capability definitions (`capabilities.py`), context boundaries (`context_ref.py`), error models (`errors.py`), and planning lifecycle models (`plan_models.py`).
  - `mesh/`: In-process peer capability router (`router.py`) enforcing delegation depth and tracing.
  - `engines/`: Six cooperating engine implementations (`base.py`, `perception.py`, `observation.py`, `context.py`, `memory.py`, `retrieval.py`, `planning.py`).
  - `execution/`: Plan step execution runtime (`executor.py`) enforcing sequential step dependencies, prerequisite validation, and runtime fault injection.
  - `pdf/`: Pure-Python PDF parsing and structured knowledge extraction (`extractor.py`, `schemas.py`, `structured.py`).
  - `models/`: Ring 1 persistence models (`Observation`, `MemoryRecord` in `observation.py`).
  - `service.py`: Real-time test orchestration service (`Ring1TestRunner`, `execute_pdf`, `execute`, `query_saved_knowledge`, in-memory `test_run_registry`).
- `backend/app/schemas/`: Pydantic v2 data models for input validation, request parsing, and response serialization.
- `backend/app/services/`: Reusable domain business logic and data processing operations decoupled from API endpoints.
- `backend/migrations/`: Alembic database schema migration environment and runners.
- `backend/migrations/versions/`: Individual revision scripts representing historical database schema transformations (`f19a0a1b2c3d_create_ring1_tables.py`).
- `backend/tests/`: Automated pytest test suites covering unit, integration, and endpoint behaviors with isolated test DB fixtures.
- `backend/tests/ring1/`: Dedicated test suite for Ring 1 mesh, contracts, all 6 engines, adversarial security, PDF extraction, and end-to-end pipeline (59 tests).

- `ai/`: Reusable, provider-agnostic AI Engine package in Python 3.12.
- `ai/core/`: Interfaces (`provider.py`), normalized Pydantic types (`request.py`, `response.py`, `error.py`), and orchestration services (`llm_service.py`).
- `ai/providers/`: Extensible provider implementations (`OpenAIProvider`, `DeepSeekProvider`, `OpenRouterProvider`, `KimiProvider`, `OllamaProvider`, `FakeLLMProvider`) and central `ProviderRegistry` factory.
- `ai/prompts/`: Template interpolation, variable extraction, and chat formatting (`prompt_template.py`).
- `ai/config/`: Centralized configuration loading multi-provider credentials from `.env` (`ai_config.py`).
- `ai/tests/`: Automated Pytest suite (54 unit tests) covering swappability, contracts, error normalization, and mock generations.
- `data-engineering/`: Data engineering workspace containing lakehouse, streaming, ingestion, and evaluation assets.
- `data-engineering/orgbrain_ingest/`: Pure Python package implementing the Foundational Source Ingestion Pipeline (`ingestion/` orchestration, validation, checksums; `storage/` abstractions and local implementation).
- `data-engineering/fixtures/ingestion/`: Deterministic evaluation fixtures (`valid_small.pdf`, `valid_small.txt`, `empty.pdf`, `unsupported_file.xyz`).
- `data-engineering/tests/`: Automated pytest unit test suite (24 unit tests) covering validation, checksum, storage backends, and pipeline orchestration.

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
- **Graph Database Image**: `neo4j:5-community` (ports 7474, 7687, volume `neo4j_data`)
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
| `e819b932c01a` | `sources` | Raw ingested source documents; UUID PK, original_filename, content_type, size_bytes > 0 check, SHA-256 checksum, storage_key, storage_mode, source_type, uploaded_by FK (users.id), status, created_at, updated_at |
| `f19a0a1b2c3d` | `ring1_observations`, `ring1_memory_records` | Ring 1 observations with idempotency keys and JSONB payload; Ring 1 memory records scoped to case_id |

### Ring 1 Live Test & Observability Endpoints
Mounted at `/api/v1/ring1` (protected by `get_test_operator_user` in `deps.py`):
- `POST /api/v1/ring1/test-run`: Executes live reproducible scenarios across the six engines (`mode`: `"e2e"`, `"force_failure"`, `"custom_prompt"`). Supports real-time Server-Sent Events (`text/event-stream`) and JSON responses.
- `GET /api/v1/ring1/test-runs/{run_id}`: Retrieves stored execution trace, plan version models, and graph edges from `Ring1TestRunRegistry`.
- `GET /api/v1/ring1/test-runs`: Lists recent test runs with execution metrics.
- `GET /api/v1/ring1/capabilities`: Lists registered capabilities from `CapabilityRegistry` and engine health.

### Ring 1 Execution & Inter-Engine Delegation Architecture
- `backend/app/ring1/execution/executor.py` (`PlanStepExecutor`):
  - Deterministic executor that runs an active `Plan` step-by-step.
  - Resolves step capabilities via `MeshRouter` and capability registry.
  - Formulates typed `MeshRequest` payloads incorporating parent execution evidence and `ContextRef`.
  - Captures real execution results and populates `step.actual_result` and `step.evidence`.
  - Sets `step.status = StepStatus.COMPLETED` only after genuine capability success.
  - Sets `step.status = StepStatus.FAILED` upon capability failure or downstream error.
  - Supports controlled execution boundary fault injection for deterministic testing (`fault_injection={capability: error_spec}`).
- **Autonomous Peer Delegation**:
  - `ObservationEngine.handle_record_event`: delegates via `self._delegate()` to `planning.create_plan` when follow-up is required.
  - `PerceptionEngine.handle_structure_input`: delegates via `self._delegate()` to `observation.record_event` when `record_observation=True`.
  - Context isolation: strictly preserves `ContextRef` across all delegated hops, decrements `max_delegations_remaining`, and prevents circular loops.
- **Evidence-Based Replanning**:
  - `PlanningEngine.handle_request_replan` evaluates failed step results, execution evidence, and failure codes.
  - Dynamically synthesizes recovery capabilities (`retrieval.query`, `context.resolve`), retains completed steps, marks superseded failures as `SKIPPED`, and enforces `max_replans` termination.
- **Plan Storage Scope**:
  - Session/runtime scoped in `PlanningEngine._plans` (in-memory dictionary per process).
  - Explicitly ephemeral across restarts; relational PostgreSQL persistence is deferred to Ring 2.
