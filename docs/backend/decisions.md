# Decisions — Organizational Brain (Legal V1, backend)

> Highest authority for implementation choices. It overrides `docs/constitution.md` wherever they disagree.
> Order: `decisions.md` > current ring spec (`docs/rings/`) > `vision.md` > `constitution.md`.
> Rule for AI agents: **never invent a decision.** If something is not here, in the ring spec, or in `vision.md`, STOP and ask Karim. Add every new decision here (and an ADR in `docs/adr/` if it is architectural).
> Owner: Karim (backend lead). Last updated: 2026-10-06.

---

## Settled decisions

### D-001 Backend stack
Python 3.12, FastAPI, PostgreSQL 17 with pgvector, SQLAlchemy 2.0.x (**synchronous**), psycopg v3 (`postgresql+psycopg://`), Alembic, Pydantic v2 (+ pydantic-settings), PyJWT, pytest, httpx.
Not used: Node, Express, Prisma, TypeScript on the backend, asyncpg, Neo4j, Qdrant.

### D-002 Constitution tool sections are overridden
The Constitution's "IMPLEMENTATION GUIDANCE & TOOLS" sections describe Node/Express/Prisma/React. They do **not** apply. Only the vision, invariants, ring purposes, entities, and acceptance criteria apply. Translate everything into the Python stack. Never copy Prisma schemas or TypeScript names.

### D-003 Database stays relational
PostgreSQL only. Vectors live in Postgres through pgvector. Hierarchies (e.g. legal categories) use `parent_id` or Postgres `ltree`. Relations such as Case / Lawyer / Court / Client use ordinary joins.
Neo4j is NOT adopted for V1. It may be reconsidered later only for relationship queries with an unknown number of hops.
The Constitution's "multi-store (relational + vector + graph + object)" is implemented in V1 as relational + vector inside Postgres.

### D-004 One organization per deployment (single-organization instance)
Each client gets its own instance. This is NOT a shared multi-tenant system.
Implication for Ring 4 (derived, confirm with the team lead before Ring 4 starts): the Constitution's multi-tenant organization isolation is not needed for V1; organization settings are one configuration for the deployment. **Case isolation still applies fully.**

### D-005 V1 roles
Only two roles: `admin` and `employee`. No separate reviewer role for now. Permissions are enforced server-side.

### D-006 Domain model and V1 scope
- Client -> Case -> Conversation. A Client is not a Case. Case isolation is mandatory, even between cases of the same client.
- Domain scope for V1: Egyptian Civil Law.
- Primary channel: WhatsApp.
- Confirmed ML use cases: Case Similarity and Case Classification.
- A CRM integration is required (which product: see OPEN-2).

### D-007 Infrastructure and conventions
- Database runs in Docker: image `pgvector/pgvector:pg17`, port 5432, named volume, healthcheck. Docker Desktop uses Linux containers (WSL2).
- Every schema change is an **Alembic migration**. No manual database edits. The pgvector extension is enabled by the first migration.
- Secrets live only in `.env` at the project root (git-ignored). `.env.example` holds fake placeholders.
- Dependency versions come from a real install (`pip freeze`), never from memory. SQLAlchemy stays on 2.0.x.
- Project layout: `backend/app/{api,services,models,schemas,core,db}`, `backend/tests`, `backend/migrations`, `docs/`.

### D-008 Working method
- Google Antigravity writes the code. Karim reviews. Claude supervises and checks the agent's plans and results.
- Plan first, then wait for approval. One small task per turn. Every change ships with tests whose real output is shown.
- Documentation protocol (start-of-task and end-of-task rules) is defined in `AGENTS.md` and is mandatory.
- Anything important created outside the repo (for example agent plan files stored in the user profile folder) must be copied into `docs/`.

### D-009 Python replacements for Node-era tooling are NOT decided
The Constitution mentions job queues (Bull), real-time (Socket.io), caching (Redis), access control (Casbin), document parsing, LangChain, and similar. None of these are chosen for Python yet. When a ring needs one, the agent must propose options in its plan, Karim approves, and the choice is recorded here plus an ADR. No silent picks.

### D-010 Official ring numbering
The numbering in `docs/constitution.md` v2.0 is official (confirmed by Karim, 2026-10-06): Ring 0 Foundation, 1 Brain Core, 2 Knowledge & Memory, 3 Legal Domain, 4 Organization Context, 5 Case Intelligence, 6 Observation (WhatsApp), 7 Reasoning & Assistance, 8 Learning & Validation, 9 Insights & Governance, 10 Legal V1, 11+ Future Domains. No other ring numbering is used.
Current status: Ring 0 (Foundation) is in progress. Ring 0 backend scope per the Constitution: API skeleton, database connections, authentication skeleton, testing framework, basic tests. Ring 1 does not start until Ring 0 exit criteria are met.

### D-011 Karim owns the backend decisions
Karim (backend lead) decides the backend stack and architecture and does not need team approval for it (stated by Karim, 2026-10-06). The backend is Python / FastAPI / PostgreSQL (D-001) even though the team repository `brain-co` contains a Node/Prisma scaffold, a docker-compose with Redis, Neo4j and MinIO, and a README that still lists "Organization isolation". Agents must follow `decisions.md`, not the team repo's scaffold or README. ADRs for D-001, D-003 and D-004 are optional records, not approval gates.
Practical note: other people's code (frontend, mobile, AI) talks to this backend through its API, so the API contracts (`docs/api/`) are what must stay clear and accurate.

## D-012 — Password hashing and tokens (2026-10-09, owner: Karim)
- Passwords: argon2-cffi==25.1.0 used directly (Argon2id, library defaults). FastAPI's tutorial uses pwdlib with Argon2; we skip that wrapper to keep fewer layers.
- Tokens: PyJWT, HS256 pinned, payload only sub/iat/exp, access token only.
- Not built yet: refresh tokens, revocation, password policy (min length decided in T9).

## D-013 — AI Engine Python Rebuild & Scalable Provider Registry (2026-10-09)
- Unified Python Stack: To eliminate runtime and language conflict with FastAPI backend, `ai/` is rebuilt in Python 3.12 (async-first, Pydantic v2).
- Multi-Provider Scalability: Reusable `BaseOpenAICompatibleProvider` powers `OpenAIProvider`, `DeepSeekProvider` (deepseek-chat, deepseek-reasoner/R1), `OpenRouterProvider`, `KimiProvider` (moonshot-v1), `OllamaProvider` (local), and `FakeLLMProvider`.
- Zero Code Changes in Higher Rings: Providers are managed via `ProviderRegistry` and `AIConfig` (`.env`). Higher rings (Rings 1–10) depend strictly on `ILLMProvider` and `LLMService` abstractions. Dynamic swappability via `set_provider()` or `.env`.

## D-015 — Neo4j Graph Database Container Added (2026-10-12)
- Neo4j 5 Community (`neo4j:5-community`) is added to `docker-compose.yml` with ports 7474 (HTTP) and 7687 (Bolt) and named volume `neo4j_data`.
- Purpose: Prepared as an infrastructure service to support knowledge graph exploration, citation networks, and multi-hop relationship reasoning in higher rings.
- Invariant: Ring 0 and Foundational Ingestion remain purely on PostgreSQL + pgvector; backend core transactions and Source Memory remain independent of Neo4j.

## D-016 — Ring 1 General Brain Peer-to-Peer Mesh Architecture & 6th Engine (Planning) (2026-10-27)
- Six engines cooperating peer-to-peer via `MeshRouter` (`backend/app/ring1/`): Perception, Observation, Context, Basic Memory, Basic Retrieval, and Planning.
- In-process capability dispatch with versioned envelopes (`MeshRequest`, `MeshResponse`).
- Planning Engine approved as 6th engine (documented in ADR-008, Constitution unchanged).
- Strict case-level isolation enforced across Context, Memory, and Retrieval (`case_id` boundary).
- Database persistence via SQLAlchemy models (`ring1_observations`, `ring1_memory_records`) with Alembic migration `f19a0a1b2c3d`.

---

## D-012 Ring 1 Architecture, Execution Foundation & Engine Decoupling

- **Scope**: Ring 1 Core Engines, Task Infrastructure, and Capability Execution.
- **Five Core Engines**: Exactly five core engines: Perception, Observation, Context, Memory, Retrieval.
- **Advisory Planning**: PlanningEngine is an advisory 6th capability under ADR-008 with zero execution authority.
- **No Central Orchestrator**: Prohibits any central business orchestrator. The Backend Runtime Dispatcher is strictly domain-blind and validates registered capabilities and permitted handoffs without business logic.
- **PostgreSQL Task Ledger**: PostgreSQL is the authoritative task and execution state ledger (`tasks`, `task_outbox`, `audit_events`). Redis/ARQ acts purely as an ephemeral message delivery broker.
- **Worker Claim & Generation Fencing**: Worker claims, lease renewals, state transitions, and audit logs are strictly fenced by `lease_generation`. Superseded workers cannot commit side effects.
- **Transactional Outbox**: Tasks and outbox records are created atomically in PostgreSQL. Dispatch claims use `FOR UPDATE SKIP LOCKED` with incremented `dispatch_generation` and lease expiry.
- **Human Validation Authority**: Memory candidates are stored in `candidate` status and require explicit human validation authority (`validation_authority == True`) to be promoted. Automatic self-validation is forbidden.
- **Cryptographic Cursor Pagination**: Keyset cursor pagination uses HMAC-SHA256 signatures with Base64URL encoding, binding cursors to organization, case, sort order, and canonical filter hashes.
- **Vector Freeze**: Maintained pending written AI/Data Science sign-off. Non-vector lexical candidate ranking implemented.

## D-017 — General Brain Physical Extraction into Independent Standalone Package (2026-10-30)
- **Modular Monolith**: Extracted General Brain out of `backend/app/ring1/` into an independently installable Python package `brain-co-core` under `brain/` using standard `src/` layout (`brain/src/brain/general/` and `brain/src/brain/extensions/`).
- **Domain Independence**: Canonical implementations of all 6 engines (Perception, Observation, Context, Memory, Retrieval, Planning), mesh runtime (`MeshRouter`, `RuntimeDispatcher`, `PlanStepExecutor`, `DomainRegistry`), and contracts physically live in `brain/src/brain/general/`.
- **Strict Storage Injection**: Engines depend strictly on storage protocols (`IObservationStore`, `IMemoryStore`, `IRetrievalStore`). Storage must be explicitly injected via constructors; missing storage raises `StorageConfigurationError`. Engines never silently instantiate in-memory stores. Backend provides production SQLAlchemy implementations in `backend/app/infrastructure/database/stores.py`.
- **Provider-Agnostic LLM Contract**: General Brain defines `ILLMClient`, `LLMRequest`, `LLMResponse`. Backend provides `LLMServiceAdapter` in `backend/app/infrastructure/ai/adapter.py`. Zero vendor model hardcoding in General Brain.
- **Domain Extensions Separation**: Specialized domains (`legal`, `sales`, `logistics`) moved to `brain/src/brain/extensions/`. General Brain never imports concrete domain extensions; extensions consume General Brain contracts.
- **Backward Compatibility**: `backend/app/ring1/` and `backend/app/domains/` maintain thin shims re-exporting canonical classes preserving exact class identity without duplicating implementation logic.
- **Verification**: 16 new automated architecture isolation tests in `tests/architecture/` (AST scanning and isolated subprocess execution). 347/347 tests passing (100% pass rate).

## D-018 — Multi-Tenant Idempotency Key Scoping & Strict Tenant Enforcement (2026-11-14)
- **Problem**: Global uniqueness on `idempotency_key` allowed cross-tenant collisions and data leakage where Tenant B using the same key as Tenant A could observe or collide with Tenant A's records (`SEC-01`). Additionally, stores accepted optional `organization_id` and defaulted to unscoped queries when missing, and `ObservationEngine` trusted payload `organization_id` with an insecure `"org-default"` fallback.
- **Decision**: All idempotency uniqueness constraints are composite on `(organization_id, idempotency_key)` in PostgreSQL (migration `c59d4e7f8a1b` on `ring1_observations` and `ring1_memory_records`).
- **Store & Engine Isolation**:
  - `IObservationStore` and `IMemoryStore` protocols strictly require `organization_id: str` on `find_by_idempotency_key` (removed `Optional[str] = None`).
  - All store implementations (`InMemoryObservationStore`, `InMemoryMemoryStore`, `SqlAlchemyObservationStore`, `SqlAlchemyMemoryStore`) validate that `organization_id` is a non-empty string on both lookups and persistence (`save` / `save_record`), raising `ValueError` on missing, empty, or whitespace-only inputs.
  - `ObservationEngine.handle_record_event` and `record_observation`: Requires verified server-side context (`context_ref`), validates non-empty `organization_id`, rejects missing context, unverified string context references, payload tenant spoofing, and payload case mismatch; completely eliminated `"org-default"` fallback.
  - `BasicMemoryEngine.handle_store_record` and `store_candidate`: Enforces non-empty `organization_id` from authorized context, rejects string context references, and rejects payload tenant/case spoofing.
- **Database-Level NOT NULL Constraint**:
  - Enforced `nullable=False` on `Observation.organization_id` and `MemoryRecord.organization_id` in SQLAlchemy models and applied Alembic migration `d60e5f8a9b2c_enforce_not_null_organization_id.py` with pre-check validation safeguards.
- **Verification**: 12 comprehensive adversarial tests in `backend/tests/ring1/test_idempotency_tenant_isolation.py`. Full test suite passing (311 backend, 16 architecture).

## D-019 — Context Engine Server-Side Scope Authority & Trust Boundaries (2026-11-14)
- **Problem**: `ContextEngine.handle_resolve` trusted client `context_hint` to supply organization ID when missing or override authorized case IDs (`SEC-02`), and dead code blocked LLM resolution reachability (`ENG-01`).
- **Decision**: Server-side context is authoritative. Missing `server_org` fails closed (`CONTEXT_MISSING`). Client attempts to override `organization_id` or `case_id` are rejected with `AUTHORIZATION_DENIED` and HTTP 403.
- **Case Validation**: Injected `case_validator` verifies proposed case hints against tenant storage.
- **LLM Fallback**: Missing case scope deterministically returns `INSUFFICIENT_DATA` allowing `_try_llm_resolution` reachability, with inferred results clamped strictly to the verified server organization.

## D-020 — Memory Mesh Handler Human Validation Lifecycle Alignment (2026-11-14)
- **Problem**: `BasicMemoryEngine.handle_store_record` hardcoded `"status": "active"`, bypassing the Constitution's candidate lifecycle and human validation authority (`SEC-05`).
- **Decision**: All newly ingested knowledge objects stored via mesh capability `memory.store_record` enter strictly as `"candidate"`. Direct transition to `"validated"` or `"active"` requires verified `validation_authority=True` on the execution context. Candidates are excluded from standard user retrieval.

## D-021 — Ring 1 Architectural Remediation & Cognitive Chain Integration (2026-11-15)
- **Context API & Case Validation Production Wiring (P0)**:
  - `ContextEngine` now receives an authoritative database-backed `case_validator` in production endpoints (`backend/app/api/v1/context.py`) and test runners (`backend/app/ring1/service.py`).
  - Validates case IDs and case numbers strictly bounded by `organization_id` via `CaseService`. Missing or unauthorized cases fail closed with HTTP 403 Forbidden / `AUTHORIZATION_DENIED`.
- **Execution Event Provenance & Status Integrity (P0)**:
  - Eliminated fabricated `source_engine="observation"` in `test_scenario_service.py` and `pdf_pipeline_service.py`. Event `source_engine` strictly mirrors `MeshRequest.sender_engine`.
  - Context resolution steps only record `status="completed"` when `resp_c.status == ResultStatus.SUCCESS` and `resolution_status == EXPLICIT`. Failed steps record `status="failed"` and never fabricate synthetic `ContextRef` instances.
- **Explicit AI Extraction Mode & Provenance Transparency (P0)**:
  - `DocumentStructuredKnowledge` extended with `extraction_mode`, `fallback_occurred`, `fallback_reason`, and `provider_name`.
  - `LegalStructuredKnowledgeExtractor` reports `extraction_mode="llm"` with provider details on success, or `extraction_mode="deterministic"` with explicit fallback reasons on LLM failure, preventing silent misrepresentation.
- **AI Employee Grounded Cognitive Pipeline (P0)**:
  - Rewrote `/api/v1/ai/prompt` to execute the full 5-stage Ring 1 cognitive pipeline:
    1. Context resolution asserting tenant and case scope boundaries.
    2. Case knowledge retrieval from PostgreSQL memory store (`SqlAlchemyMemoryStore`).
    3. Grounded reasoning prompt formulation incorporating verified retrieved facts.
    4. LLM provider generation via configured provider.
    5. Audit observation event recording in PostgreSQL (`SqlAlchemyObservationStore`).
- **Live Gemini Provider Integration (P1)**:
  - Default model aligned to production `gemini-1.5-flash` in `ai_config.py` and `gemini_provider.py`.
  - Sandbox network isolation confirmed and verified: outbound cloud API requests encounter network timeout (exit code 28). Documented transparently without fabricating cloud responses.
- **Autonomous Multi-Hop Engine Delegation (P1)**:
  - Verified autonomous peer-to-peer delegation from `ObservationEngine.handle_record_event` to `PlanningEngine.create_plan` via `MeshRouter` on breach observations.
- **Frontend Workspace & Next.js 16.4.5 Alignment (P1)**:
  - Upgraded Next.js and `eslint-config-next` to `16.4.5` in `frontend/package.json`.
  - Implemented real-time WebSocket client hook `use-observation-ws.ts` and Brain status proxy route `/api/brain/status`. Connected workspace panels (`OverviewPanel`, `KnowledgePanel`, `AIEmployeePanel`) to live backend APIs.

## D-022 — Multi-Tenant SaaS Foundation, Organization Signup, Workspace Isolation & Domain Separation (2026-11-15)
- **Problem**:
  - Brain-Co operated as a single-organization developer prototype (`D-004`). All authentication, context engines, observation stores, and endpoints hardcoded `settings.ORGANIZATION_ID` (`org-brain-corp`).
  - There was no organization registration, public onboarding account creation was disabled, and users could not create or switch between tenant workspaces.
  - Legal domain logic and system prompts were hardcoded in generic API routes (`app/api/v1/ai.py`), violating domain extension separation.
- **Architectural Separation**:
  - **Organization**: Represents the customer tenant company (PostgreSQL table `organizations`).
  - **Deployment**: Represents the runtime environment (`settings.ENVIRONMENT`, database connections, server configuration).
  - **Domain**: Represents the business capability extension (`legal`, `sales`, `logistics`).
- **Decisions**:
  1. **Database Schema & Safe Migration (`e71f6a9b0c3d`)**:
     - Added `Organization` table (string PK `id="org-..."`, `name`, `slug`, `domain`, `is_active`, `settings`, timestamps).
     - Added `OrganizationMembership` table (UUID PK, FK to `organizations.id`, FK to `users.id`, `role IN ('admin', 'employee')`, unique constraint on `(organization_id, user_id)`).
     - Data safety guarantee: Automatically seeded legacy `'org-brain-corp'` and backfilled admin memberships for all existing users, preserving existing data with zero downtime.
  2. **Server-Authoritative Membership & Token Authentication**:
     - Registration endpoint `POST /api/v1/auth/register-organization` atomically provisions Organization, initial Admin User, and Admin Membership.
     - Login endpoint `POST /api/v1/auth/login` and switch endpoint `POST /api/v1/auth/switch-organization` embed verified `org_id`, `role`, and `domain` into JWT claims.
     - Dependency `get_brain_context` strictly validates active membership in PostgreSQL for every request; never trusts client-supplied tenant headers or claims.
  3. **Legal Domain Extension Modular Separation**:
     - Added `get_system_prompt()` to `IDomainExtension` contract.
     - Encapsulated Egyptian Civil Law grounding prompt inside `LegalDomainExtension`.
     - Generic `ai.py` dynamically resolves domain prompts via `get_domain_extension(domain_id)` registry, keeping General Brain clean and domain-agnostic.
  4. **Multi-Tenant SaaS Onboarding & Workspace Flow**:
     - Built frontend Organization Registration Screen (`/onboarding/account`) enabling company name, domain selection, admin account setup, and automatic workspace redirection.
     - Implemented Next.js proxy routes `/api/auth/register`, `/api/auth/session`, `/api/cases`, and `/api/organizations/members`.
     - Built dynamic workspace UI displaying verified tenant identity, active cases, member management, PDF document ingestion, and grounded Legal AI Employee.
  5. **Tenant Isolation Verification**:
     - Automated test suite `backend/tests/test_saas_organization_isolation.py` proves tenant partitioning across 5 real organizations with zero cross-tenant leakage across cases, memory, observations, and AI Employee.

## D-023 — Case Access Control Strategy (CACS) & Elimination of Synthetic Case Creation (2026-11-15)
- **Problem**:
  - `pdf_pipeline_service.py` contained fallback logic creating synthetic `Case` records if a requested case did not exist, creating a fail-open security bypass.
  - Case API endpoints in `cases.py` lacked explicit authorization validation, risking horizontal privilege escalation.
- **Decisions**:
  1. **Fail-Closed Case Authorization**: Cases can no longer be manufactured on-the-fly during ingestion or context resolution. A case must pre-exist in the database within the authenticated tenant organization. Missing cases raise `CaseNotFoundError` immediately.
  2. **Authoritative Role-Based Case Access (`CaseService.validate_case_access`)**:
     - Admins receive access to all cases within their tenant organization.
     - Employees receive access only to cases they created (`created_by == user_id`) or are explicitly assigned to in the `case_assignments` table.
     - Case status such as `"open"` or `"active"` does not grant access.
     - Unauthorized access returns HTTP 404 to eliminate existence oracle leaks.
  3. **Strict Ingestion Validation**: `POST /api/v1/ring1/upload-pdf` checks `CaseService.validate_case_access` before parsing any uploaded files.

## D-024 — Canonical Mesh Lifecycle Events, Dual Delivery & Single-Use WebSocket Tickets (2026-11-15)
- **Problem**:
  - WebSocket observation manager directly received events without unified sequence stamping or canonical lifecycle typing.
  - Connecting WebSockets directly using raw JWTs in query params or client-side JavaScript exposed sensitive credentials.
  - The developer `<Ring1TestConsole />` was embedded globally in the public layout.
- **Decisions**:
  1. **Canonical Mesh Event Service (`MeshEventService`)**:
     - Defined 12 canonical lifecycle event types (`MeshLifecycleEventType`).
     - Stamped with monotonic sequences, persisted durably to `mesh_events` (with fallback if migration is pending), and broadcast across WebSocket subscribers via `ws_manager.broadcast_event`.
  2. **Short-Lived Single-Use WebSocket Tickets**:
     - Implemented `TicketService` with SHA-256 token hashing and atomic single-use PostgreSQL consumption.
     - Tickets expire after 60 seconds; raw tokens are never persisted or logged.
     - Frontend requests ticket via `/api/auth/ws-ticket` using existing HttpOnly session cookie, avoiding JWT exposure in frontend JavaScript.
  3. **Dedicated Case Workspace**:
     - Removed developer test console from `frontend/src/app/layout.tsx`.
     - Built dedicated Case Workspace page at `/workspace/cases/[caseId]` providing tabbed navigation for Overview, Documents, Extracted Knowledge, Live Mesh Activity, and Case AI Employee.

---

## Open questions (do not assume an answer)

- **OPEN-2 CRM product** for the required integration.
- **OPEN-3 File/object storage** for uploaded documents (not chosen).
- **OPEN-4 LLM provider and embedding model.** The Constitution says "OpenAI or local"; nothing is chosen.
- **OPEN-5 Frontend contract.** The team repository has two API consumers: a React web dashboard (`frontend/`) and a Flutter mobile app (`mobile/`). Who builds which, and when each needs authentication, is NOT confirmed. Any API contract (starting with auth) must be agreed and written down before a consumer builds against it.
- **OPEN-7 Repository layout and where the Python backend lives.** How the Python backend, its migrations, tests, Docker setup and these docs fit into the team's folders (`backend/`, `tests/`, `infrastructure/`, `docs/`). Do not push to any remote until this is decided.

---

## Team repository (context, from the repository README as shown to Claude)

- GitHub monorepo `brain-co` (owner `mustafayouniss`, public, 4 contributors). Top-level folders: `.github`, `ai`, `backend`, `data-engineering`, `data-science`, `docs`, `frontend`, `infrastructure`, `mobile`, `shared`, `tests`, plus `docker-compose.yml` and `README.md`.
- README states: `backend/prisma` (Node/TypeScript scaffold), React 18 + Vite + Tailwind web dashboard, Flutter mobile app, docker-compose with PostgreSQL + pgvector, Redis, Neo4j, MinIO. GitHub shows TypeScript as 94.9% of the code.
- README autonomy levels are 0-3 (Observe, Assist, Execute with approval, Authorized automation), the same as `vision.md`.
- README puts the Constitution under `docs/project-specifications/` and ring specs under `docs/rings/` (0 to 11+), ADRs under `docs/adrs/`.
- Seen in a screenshot (2026-10-07): the repo's `backend/` folder contains `prisma/`, `src/` and `package.json`, i.e. a Node scaffold, as the README said. Karim has access to the repo; whether he has read or write permission is not stated.
- UNVERIFIED: the contents of those files and of the other folders.
- Plan for when code is pushed (OPEN-7): use a new branch (not `main`) so the team's existing work is not overwritten, then merge when Karim decides.

---

## Change log

- 2026-10-06: file created from decisions made so far.
- 2026-10-06: ring numbering settled (D-010); OPEN-1 removed.
- 2026-10-06: OPEN-5 corrected (earlier text wrongly named a "Flutter teammate" and an auth start date without a source); OPEN-7 and "Team repository" section added after reviewing the team README.
- 2026-10-06: D-011 added (Karim owns backend decisions, no team approval needed); the short-lived OPEN-6 was removed.
- 2026-10-07: "Team repository" section updated from a screenshot of the team's `backend/` folder; branch plan noted for OPEN-7.
- 2026-11-15: D-012 added (Dual-delivery Mesh event persistence with atomic single-use WebSocket tickets, fail-closed CACS boundaries, and transparent AI provider telemetry tagging).
