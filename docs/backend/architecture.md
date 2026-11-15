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
- `brain/`: Standalone Python package `brain-co-core` containing the domain-agnostic General Brain and Domain Extensions.
  - `pyproject.toml`: PEP 621 package build configuration using `src/` layout.
  - `src/brain/general/`: Canonical General Brain implementation.
    - `contracts/`: Capability definitions, execution envelopes, pure engine protocols, context references, storage protocols, LLM protocols, error types, and planning models.
    - `engines/`: Core decoupled cognitive engines (`perception.py`, `observation.py`, `context.py`, `memory.py`, `retrieval.py`, and advisory `planning.py`).
    - `policies/`: Peer handoff policy and delegation boundaries (`handoff.py`).
    - `runtime/`: Mesh router (`router.py`), runtime dispatcher (`dispatcher.py`), plan step executor (`executor.py`), and instantiable freeze-aware domain registry (`domain_registry.py`).
    - `stores/`: Explicit in-memory stores for unit tests and local execution (`in_memory_observation.py`, `in_memory_memory.py`, `in_memory_retrieval.py`).
  - `src/brain/extensions/`: Concrete domain extensions consuming General Brain contracts.
    - `legal/`: Egyptian Civil Law contract analyzer (`schemas.py`, `extractor.py`, `extension.py`).
    - `sales/`: B2B sales opportunity detector (`schemas.py`, `extractor.py`, `extension.py`).
    - `logistics/`: Maritime fleet tracking and customs manifest engine (`schemas.py`, `extractor.py`, `extension.py`).
- `backend/`: Python backend application workspace.
- `backend/.venv/`: Isolated Python 3.12 virtual environment containing installed project dependencies.
- `backend/app/`: Primary FastAPI application package containing all backend logic and modules.
- `backend/app/api/`: HTTP API routes, endpoint handlers, dependency providers (`deps.py`), and versioned routers (`v1/`).
- `backend/app/core/`: Application settings, environment loaders, error handling (`errors.py`), security (`security.py`), immutable server-side context (`context.py`), cryptographic HMAC keyset cursor pagination (`cursor.py`), durable audit ledger (`audit.py`), transactional task manager (`task_manager.py`), outbox dispatcher (`outbox_dispatcher.py`), handoff policy engine (`handoff.py`), and domain-blind runtime dispatcher (`dispatcher.py`).
- `backend/app/infrastructure/`: Backend adapters implementing General Brain protocols:
  - `database/stores.py`: Production SQLAlchemy implementations of `IObservationStore`, `IMemoryStore`, and `IRetrievalStore`.
  - `ai/adapter.py`: Production `LLMServiceAdapter` implementing `ILLMClient` using Backend AI services.
- `backend/app/db/`: Database connection engine (hide_parameters=True), declarative Base (`base.py`), session factory, and test safety guards (`test_utils.py`).
- `backend/app/domains/`: Backward compatibility shims for domain extensions re-exporting canonical classes from `brain.extensions.*`.
- `backend/app/models/`: SQLAlchemy 2.0 ORM declarative models (`user.py`, `source.py`, `task.py` for tasks & task_outbox, `audit.py` for audit_events, and Ring 1 models via `ring1.models.observation`).
- `backend/app/ring1/`: Backward compatibility shims for Ring 1 re-exporting canonical classes from `brain.general.*`.
- `backend/app/schemas/`: Pydantic v2 data models for input validation, request parsing, and response serialization.
- `backend/app/services/`: Reusable domain business logic and data processing operations decoupled from API endpoints.
- `backend/migrations/`: Alembic database schema migration environment and runners.
- `backend/migrations/versions/`: Individual revision scripts representing historical database schema transformations.
- `backend/tests/`: Automated pytest test suites covering unit, integration, and endpoint behaviors with isolated test DB fixtures.
- `backend/tests/ring1/`: Dedicated test suite for Ring 1 mesh, task manager, outbox dispatcher, cursor security, handoff policy, pure engine protocols, adversarial security, PDF extraction, and end-to-end pipeline.
- `tests/architecture/`: Automated architecture isolation tests:
  - `test_import_isolation.py`: AST import scanning verifying zero backend/DB imports in General Brain and zero backend imports in Domain Extensions.
  - `test_standalone_general_brain.py`: Subprocess isolation test executing General Brain with only `brain/src` on `PYTHONPATH`.
  - `test_storage_injection.py`: Storage configuration error and explicit injection verification.
  - `test_domain_registry_lifecycle.py`: Registry lifecycle, duplication rejection, and immutability freeze transition.
  - `test_compatibility_shims.py`: Exact identity preservation between legacy import paths and canonical implementations.

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
| `c59d4e7f8a1b` | `ring1_observations`, `ring1_memory_records` | Replaces single-column idempotency uniqueness with composite `(organization_id, idempotency_key)` partial unique indexes (SEC-01) |
| `d60e5f8a9b2c` | `ring1_observations`, `ring1_memory_records` | Enforces `NOT NULL` constraint on `organization_id` for both tables with migration pre-check validation (SEC-01) |

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

### Ring 1 General Brain API Contracts (Section 17)
- `GET /api/v1/brain/status`: Health check, active cognitive engines (Perception, Observation, Context, Memory, Retrieval, Planning), registered capabilities, and registered domain extensions.
- `POST /api/v1/observations`: Persists normalized observation event to `ring1_observations` with SHA-256 idempotency, records append-only `AuditEvent`, and broadcasts to authorized WebSocket subscribers.
- `GET /api/v1/observations`: Retrieves cursor-paginated observation feed with cryptographic HMAC-SHA256 Base64URL cursor integrity, strictly filtered by tenant and scope.
- `POST /api/v1/context/resolve`: Server-side context boundary resolution evaluating domain, organization, and scope references. Returns resolution status, ambiguities, and scope constraints.
- `GET /api/v1/memory/{id}`: Retrieves authorized knowledge object from `ring1_memory_records`. Enforces strict organization and scope boundaries, returning sanitized 404s on unauthorized access to prevent existence oracles.
- `GET /api/v1/retrieval/search`: Context-first lexical keyword retrieval. Enforces tenant and scope filters at the database boundary before candidate scoring and ranking. Strictly excludes unvalidated candidates.
- `WS /api/v1/ws/observations`: Real-time observation update stream. Authenticates clients via JWT token, enforces organization broadcast boundaries, and handles disconnects cleanly.

### Short-Term Memory Architecture (Section 11.1)
- `backend/app/core/short_term_memory.py` (`ShortTermMemoryService`):
  - Ephemeral task execution state caching (current plan, intermediate execution data, step state).
  - Standard key format: `org:{organization_id}:task:{task_id}:{key}`.
  - TTL expiration (default 3600 seconds).
  - Redis backend with automatic in-memory thread-safe TTL fallback.
  - PostgreSQL remains the authoritative task and execution state ledger.

### Domain Extension Architecture (Section 2.1)
- `backend/app/domains/` (`IDomainExtension`, `DomainRegistry`):
  - Decouples industry-specific intelligence from the General Brain.
  - `LegalDomainExtension`: Egyptian Civil Law extraction and contract analysis.
  - `SalesDomainExtension`: Enterprise sales deal signals and opportunity extraction.
  - `LogisticsFleetDomainExtension`: Maritime vessel manifest and cargo inspection tracking.

### AI Employee Grounded Cognitive Chain (`backend/app/api/v1/ai.py`)
- `POST /api/v1/ai/prompt`: Executes the complete Ring 1 cognitive loop:
  1. **Context Resolution**: Enforces server-side tenant isolation (`organization_id`) and validates client case scope against PostgreSQL via `CaseService`. Returns 403 Forbidden on foreign or invalid cases.
  2. **Case Knowledge Retrieval**: Queries `SqlAlchemyMemoryStore` for validated legal facts, extracted contract clauses, and knowledge objects within the case boundary.
  3. **Grounded Reasoning Formulation**: Synthesizes retrieved knowledge and conversation history into an evidence-grounded prompt with strict factual anchoring instructions.
  4. **LLM Provider Generation**: Dispatches prompt to the active AI provider (`GeminiProvider`, `DeepSeekProvider`, `OpenAIProvider`, or `FakeLLMProvider`) via `LLMService`.
  5. **Audit Observation Recording**: Emits and stores an append-only observation event in `ring1_observations` with payload details (`prompt_chars`, `response_chars`, `sources_count`, `latency_ms`) and broadcasts over the WebSocket bus.

### Multi-Tenant SaaS Architecture (Decision D-022)
- **Three-Tier Entity Separation**:
  - **Organization** (`organizations` table): Customer tenant company (`id="org-..."`, `name`, `slug`, `domain`, `is_active`, `settings`).
  - **Deployment**: Server runtime settings (`settings.ENVIRONMENT`, database connection pools, LLM provider keys).
  - **Domain**: Business capability module (`legal`, `sales`, `logistics`) providing specialized extraction and prompts.
- **Data Model & Relationships**:
  - `OrganizationMembership` (`organization_memberships` table): Maps `(organization_id, user_id)` with `role IN ('admin', 'employee')`. Unique constraint prevents duplicates.
  - Multi-tenant case and memory tables (`cases`, `sources`, `ring1_observations`, `ring1_memory_records`) store `organization_id VARCHAR(100)` and enforce tenant-scoped foreign-key isolation.
- **Authentication & Server-Side Security**:
  - `POST /api/v1/auth/register-organization`: Atomically creates `Organization`, Admin `User`, and `OrganizationMembership`.
  - `POST /api/v1/auth/login`: Issues HS256 JWT embedding `sub` (user_id), `org_id`, `role`, and `domain`.
  - `POST /api/v1/auth/switch-organization`: Verifies user's active membership in target organization before reissuing token.
  - `get_brain_context`: Authoritative dependency validating database membership on every request, rejecting spoofed tenant claims.
- **Organization Management Endpoints**:
  - `GET /api/v1/organizations/me`: Retrieves current active organization profile.
  - `GET /api/v1/organizations/members`: Lists authorized members of the organization.
  - `POST /api/v1/organizations/members`: Admin-only endpoint inviting new employees.
- **Frontend SaaS User Journey**:
  - `frontend/src/app/onboarding/account/page.tsx`: Self-service organization & administrator signup.
  - `frontend/src/app/api/auth/register/route.ts`: Sets HttpOnly session cookie on successful registration.
  - `frontend/src/components/workspace/workspace-client.tsx`: Renders authenticated company name, domain badge, role badge, tenant ID, partitioned cases list, team management, and grounded AI Employee.

### Frontend Integration & Real-Time Sync
- **Next.js 16.4.5 & React 19 Workspace**:
  - `frontend/src/components/workspace/workspace-client.tsx` connects UI panels to live backend endpoints (`/api/v1/cases`, `/api/v1/brain/status`, `/api/v1/ai/prompt`).
  - `frontend/src/hooks/use-observation-ws.ts`: Resilient WebSocket client connecting to `/api/v1/ws/observations` with automatic exponential backoff reconnection, heartbeat tracking, and tenant isolation.
  - `frontend/src/app/api/brain/status/route.ts`: Server-side proxy querying backend health and cognitive engine status.
  - All 5 core engines operate with 100% domain independence without internal code changes.

### Case Access Control Strategy (CACS) & Fail-Closed Ingestion
- **Authoritative Server-Side Validation (`CaseService.validate_case_access`)**:
  - Organization administrators have tenant-wide access to all cases belonging to their organization.
  - Organization employees are strictly restricted to cases they created (`created_by == user_id`) or are explicitly assigned to via the `case_assignments` table.
  - Case status such as `"open"` or `"active"` does not independently grant access.
  - Any unauthorized access attempt or missing case fails closed with HTTP 404 (preventing existence oracle information leakage).
- **Elimination of Auto-Synthesized Cases**:
  - Ingestion pipeline (`pdf_pipeline_service.py`) no longer manufactures missing `Case` records on the fly.
  - Ingestion requires a verified pre-existing case in the tenant database, validating either `case_number` or UUID `id`.
  - Endpoint `POST /api/v1/ring1/upload-pdf` strictly enforces CACS before invoking extractor or pipeline logic.

### Canonical Mesh Event Service & Dual Delivery (`backend/app/services/mesh_event_service.py`)
- **Canonical Lifecycle Events (`MeshLifecycleEventType`)**:
  - Defines 12 typed lifecycle events: `task_created`, `task_dispatched`, `task_received`, `context_retrieved`, `tool_invoked`, `tool_completed`, `handoff_evaluated`, `observation_persisted`, `memory_persisted`, `task_completed`, `task_failed`, `task_retry`.
- **Durable Persistence & Real-Time Broadcast**:
  - `MeshEventService.record_and_broadcast`: Generates monotonic sequence numbers, writes durable records to the `mesh_events` table (with safe fallback if migration is pending), and performs dual delivery.
  - Dual delivery broadcasts events to connected clients via `ws_manager.broadcast_event` (WebSocket) and Server-Sent Events (SSE).

### Dedicated Scoped Case Workspace & WebSocket Ticket Security
- **Single-Use WebSocket Tickets (`POST /api/v1/auth/ws-ticket`)**:
  - Frontend requests short-lived single-use tickets from `/api/auth/ws-ticket` using existing HttpOnly session cookies.
  - Backend `TicketService` stores SHA-256 hashed tickets with 60-second TTL in PostgreSQL with atomic consumption (`UPDATE ... WHERE consumed = false RETURNING ...`).
  - Frontend JavaScript never accesses or exposes the underlying backend JWT.
- **Dedicated Case Workspace (`/workspace/cases/[caseId]`)**:
  - Replaces global floating test consoles with a deep-linkable, dedicated Case Workspace page.
  - Six functional tabs:
    1. **Overview**: Reference metadata, UUID, tenant organization verification badge.
    2. **Documents**: Case-scoped PDF upload dropzone and live document repository.
    3. **Extracted Knowledge**: Grounded legal facts, obligations, and Egyptian Civil Code articles extracted from ingested case contracts.
    4. **Mesh Test Console**: Embedded operator and developer console (`MeshTestConsole`) bound strictly to the case and tenant scope. Features live custom prompt execution, 6-engine E2E execution, failure injection & bounded replan, PDF contract ingestion, real plan step execution via `PlanStepExecutor`, dynamic SVG Peer-to-Peer Delegation Graph, event details inspector, and test summary scorecard.
    5. **Live Mesh Activity**: Real-time event stream connected via authenticated, case-scoped WebSocket ticket.
    6. **Case AI Employee**: Context-grounded interactive assistant strictly anchored in the case's extracted knowledge.


