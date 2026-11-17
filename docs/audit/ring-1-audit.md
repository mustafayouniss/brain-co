# Ring 1 — Full Backend Audit Report

**Project:** Organizational Brain — Legal V1  
**Audited by:** Senior backend auditor (read-only, evidence-based)  
**Date:** 2026-11-01  
**Ring 0 baseline commit:** `be3bc6a`  
**HEAD at audit time:** `1b5c1d2`  
**Branch:** `main`  

> **Reading guide:** Each section ends with `<!-- SECTION N DONE -->`. If this chat is interrupted, resume from the first section whose marker is missing.

---

## Table of Contents

- [S0 Executive Summary](#s0-executive-summary) *(filled last)*
- [S1 Repo State and Change Map](#s1-repo-state-and-change-map)
- [S2 Architecture As Built](#s2-architecture-as-built)
- [S3 Data Model](#s3-data-model)
- [S4 API Inventory](#s4-api-inventory)
- [S5 Services and Business Logic](#s5-services-and-business-logic)
- [S6 Security Review](#s6-security-review)
- [S7 Tests](#s7-tests)
- [S8 Ring 1 Compliance Matrix](#s8-ring-1-compliance-matrix)
- [S9 Decisions and Invariants](#s9-decisions-and-invariants)
- [S10 Docs Accuracy](#s10-docs-accuracy)
- [S11 Findings Register](#s11-findings-register)
- [S12 Fix Plan](#s12-fix-plan)
- [S13 Open Questions](#s13-open-questions)

---

## S0 Executive Summary

### Verdict
**Is Ring 1 mergeable as is? NO (Mergeable WITH CONDITIONS after executing Batch 1 & Batch 2).**  
The teammate demonstrated exceptional software engineering capability in physically extracting the General Brain into a decoupled package, implementing robust candidate validation gates, and hardening HMAC cursors. However, the pull request introduced a critical developer authentication bypass, IDOR scope spoofing in test routes, and an unapproved Neo4j container while completely omitting pgvector search. Ring 1 cannot be accepted into production without immediate access control remediation.

### Ring 1 Completeness Score
- **Specification Compliance Formula:**  
  $$\text{Completeness} = \frac{\sum \text{Item Status Scores}}{\text{Total Core Items}} = \frac{9.5}{12} = \mathbf{79.17\%}$$  
  *(where Built = 1.0, Partial = 0.5, Missing = 0.0 across the 12 core Section 1 requirements: Perception, Observation, Context, Memory, Retrieval, Observation Table, Context Table, Knowledge Table, Vector Indexes, Engine Tests, Integration Tests, Isolation Tests)*.
- **Quality-Weighted Metric:**  
  $$\text{Quality Score} = \frac{\sum \text{Quality Ratings}}{12 \times 5} = \frac{49}{60} = \mathbf{81.67\%}$$

### Quality Scorecard (/10)
- **Architecture:** `8/10` *(Clean physical extraction into `brain-co-core`, pure protocols, and domain isolation; penalized for event-loop blocking in async def and 6th engine scope addition)*
- **Data Model:** `6/10` *(Linear reversible Alembic migrations; heavily penalized for 0 vector columns/indexes and unapproved tenant columns)*
- **Security:** `6/10` *(Argon2, timing attack mitigation, and HMAC cursors are stellar; penalized for developer auth bypass in `deps.py`, IDOR in `ring1.py`, and unbounded upload in `/sources`)*
- **Scope Isolation:** `7/10` *(Case isolation in memory/retrieval is mathematically solid with sanitized 404s; compromised by test endpoint parameter trust)*
- **API Design:** `8/10` *(FastAPI routing, dependency injection, and Pydantic schemas are clean and well-structured)*
- **Error Handling:** `8/10` *(Standardized JSON envelope `{"error": {"code", "message"}}`, no stack traces leaked to clients)*
- **Tests:** `8/10` *(269 automated tests, isolated test DB fixture, AST rule check; penalized for 2 flawed test files with live network calls and missing downgrade tests)*
- **Documentation:** `8/10` *(Exhaustive architectural reports and journals; penalized for duplicate decision IDs and omitting known breaches)*
- **Run-from-Scratch:** `7/10` *(Docker compose and Alembic are straightforward; penalized for port 5433 discrepancy and missing packages in host Python)*
- **Decision Compliance:** `5/10` *(Violated D-001/D-003 by adding Neo4j, D-004 by adding `organization_id`, D-007 by altering DB port, D-008 by delivering a monolithic 541-file PR, and D-009 by adopting Redis)*

### Findings Summary
- **P0 (Critical / Decision Breach / Security Hole):** `5`
- **P1 (High / Real Bug / Missing Requirement):** `5`
- **P2 (Medium / Maintainability / Quality Gap):** `5`
- **P3 (Low / Nice to Have / Minor Hygiene):** `2`
- **Total Findings:** **17 findings**

### Top 10 Priority Findings
1. **`F-001` [P0]:** Developer Authentication Bypass in `get_test_operator_user` (`backend/app/api/deps.py:173`)
2. **`F-002` [P0]:** IDOR & Cross-Case Scope Spoofing in `upload_pdf` and `knowledge` (`backend/app/api/v1/ring1.py:144, 244`)
3. **`F-003` [P0]:** Banned Neo4j Graph Database Container Added to Docker Compose (`docker-compose.yml:21`)
4. **`F-004` [P0]:** Multi-Tenant `organization_id` Columns Added Across Schema in Violation of D-004 (`b39c4d5e6f7a.py:35`)
5. **`F-005` [P0]:** Premature Legal `cases` Table & API Router Implementation (Ring 5 Leakage) (`b39c4d5e6f7a.py:23`)
6. **`F-006` [P1]:** Missing Vector Embeddings and pgvector Vector Indexes in PostgreSQL (`f19a0a1b2c3d.py`)
7. **`F-007` [P1]:** Main Event Loop Starvation from Synchronous DB Operations in `async def` Handlers (`observations.py:50`, `stores.py:100`)
8. **`F-008` [P1]:** Denial of Service (OOM) via Unbounded Raw File Upload in `POST /api/v1/sources` (`sources.py:54`)
9. **`F-009` [P1]:** Missing Mandatory Knowledge Metadata Columns `version` and `conflict_state` (`ring1_memory_records`)
10. **`F-010` [P1]:** Deactivated Employees Can Retain Active Real-Time WebSocket Connections (`ws.py:46`)

### Ring 2 Readiness
**Safe to build Ring 2 on top? AFTER BATCH 1 AND BATCH 2.**  
Ring 2 ("Knowledge & Memory") relies directly on storing and retrieving persistent knowledge. Building on Ring 1 before closing the authentication bypass (`F-001`) and IDOR vulnerability (`F-002`) risks compounding access control vulnerabilities. Furthermore, implementing vector embeddings (`F-006` in Batch 4) is essential to enable true semantic retrieval in Ring 2.

<!-- SECTION 0 DONE -->

---

## S1 Repo State and Change Map

### 1.1 Git Status, Branch, and Remote

- **Branch:** `main` (synchronized with `origin/main`).
- **Local working directory status:** Clean. No modified or staged files prior to audit report creation.
  ```text
  On branch main
  Your branch is up to date with 'origin/main'.
  nothing to commit, working tree clean
  ```
- **Remotes:**
  ```text
  origin  https://github.com/mustafayouniss/brain-co.git (fetch)
  origin  https://github.com/mustafayouniss/brain-co.git (push)
  ```
- **Active local branches:** `main` (active HEAD), `backup-local-main`.
- **Merge state:** Clean. No merge in progress (`.git/MERGE_HEAD` absent).
- **Conflict markers:** Clean in source code. Grep for `<<<<<<<` and `>>>>>>>` found zero markers in application source files. Three occurrences exist solely as historical documentation entries in `docs/backend/journal/2026-10-12.md:39`, `docs/journal/2026-10-12.md:39`, and canvas text in `project-context-ring-architecture.canvas(1).tsx:747`.

### 1.2 Git Commit History (Last 30 Commits)

```text
1b5c1d2 Mohamed Alaa Merge pull request #2 from mustafayouniss/feat/ring1-remediation-pdf-pipeline
6e32398 Mohamed Alaa Eldin feat(architecture): extract standalone General Brain package
f466a87 Mohamed Alaa Eldin feat(ring1): implement Ring 1 General Brain architecture, API contracts, domain decoupling, short-term memory, and WebSocket streaming
1b691c1 Mohamed Alaa Eldin docs(journal): log Python 3.12 311-test suite execution
a83ef55 Mohamed Alaa Eldin test(ring1): add concurrency and failure-recovery tests and verify Python 3.12 compatibility
1a84903 Mohamed Alaa Eldin fix(ring1): targeted fixes for outbox reconciliation, cursor validation, and task state consistency
a0f4c6b Mohamed Alaa Eldin refactor(ring1): execute Ring 1 architectural restructuring and execution foundation
55ad941 Mohamed Alaa Eldin fix(backend,ai): load .env in ai_config, enable CORSMiddleware, and record live run
10d511c Mohamed Alaa Eldin feat(ring1): complete security remediation, real PDF ingestion pipeline, and live test console
3c5b3b8 Mohamed Alaa Eldin feat(ring1): implement security remediation, peer delegation, and real step execution
245e156 Mohamed Alaa Eldin docs(ring1): add comprehensive technical report for Ring 1 mesh architecture
19892ba Mohamed Alaa Eldin feat(ring1): implement Ring 1 General Brain peer-to-peer mesh architecture
173c5a7 Mohamed Alaa Eldin docs: record successful git push and update progress log
952eca5 Mohamed Alaa Eldin feat(ai): support legal workspace domain separation and update documentation
672e1c5 Mohamed Alaa Eldin feat: establish Brain general assistant with domain separation and full QA verification
278d898 Mohamed Alaa Eldin Document OpenRouter API key configuration attempt
c61a353 Mohamed Alaa Eldin Add floating AI chat widget for integration testing
2edefc6 Mohamed Alaa Eldin Remove public self-registration to align with Ring 0 specifications
d0eee15 Mohamed Alaa Eldin Fix CSRF protection for browser requests and complete runtime verification
ea217f0 Mohamed Alaa Eldin Fix authentication with HttpOnly cookies and remove security vulnerabilities
e7fe9e9 Mohamed Alaa Eldin Replace frontend with Seif's Next.js application and integrate with backend/AI
af5e902 Mohamed Alaa Eldin Add frontend LLM integration
318683e Lamiaaraby Add retrieval evaluation metrics and documentation
0865999 Mohamed Alaa Eldin fix: add .next/ to .gitignore to exclude build artifacts
f8515f6 Mustafa Younis feat(infra): add Neo4j container to docker-compose and record decision D-015
339ffb6 Mustafa Younis docs(journal): record git push execution for 2026-10-12
5e50369 Mustafa Younis feat(ingest): implement Foundational Source Ingestion Pipeline and Source Memory
05a17d1 Seif EldenKhaled Add web_app website_ring0
ccd3044 Seif EldenKhaled Add web_app website_Ring0
2434d60 Karim Mahmoud Remove outdated root docs after moving backend docs
```

### 1.3 Changes Since Ring 0 Baseline (`be3bc6a..HEAD`)

The Ring 0 exit review baseline commit `be3bc6a` ("Docs: Ring 0 exit review") was committed on 2026-10-09. Since that commit, **29 commits** were introduced by teammates (Mohamed Alaa Eldin, Mustafa Younis, Seif EldenKhaled, Lamiaaraby).

**Summary of changes by top-level directory (`git diff --stat be3bc6a HEAD`):**
- **541 files changed**, `94,691` insertions(+), `931` deletions(-).
- `ai/`: Complete AI package added (Python 3.12 provider registry, OpenAI/DeepSeek/Groq/HuggingFace/Gemini/Ollama/Fake providers, TypeScript tests, and Jest config). 53 files, ~7,400 lines.
- `backend/`: 125 files changed, `14,471` insertions(+), `8` deletions(-). Added Ring 1 peer-to-peer mesh engines, TaskManager, OutboxDispatcher, PDF ingestion pipeline, Case/Task models, Alembic migrations `e819b932c01a`, `f19a0a1b2c3d`, `a28b3c4d5e6f`, `b39c4d5e6f7a`, and 23 dedicated Ring 1 test suites.
- `brain/`: Standalone General Brain core package (`brain-co-core==0.1.0`) extracted under `brain/src/brain/` with general contracts, engines, stores, and extensions (`legal`, `sales`, `logistics`). 26 files, ~4,500 lines.
- `data-engineering/`: Source ingestion pipeline (`orgbrain_ingest`), LocalStorageBackend, 24 unit tests, dbt models, Airflow DAG stubs, and test fixtures.
- `data-science/`: Notebooks, evaluation scripts, and gold standard Q&A datasets.
- `frontend/`: Complete Next.js 16.4.0 TypeScript application replacing original stub, including Ring 1 Live Test Console with real-time SSE streaming, SVG delegation graphs, and floating AI widget.
- `mobile/`: Flutter mobile app skeleton with feature directories and `.gitkeep` files.
- `docs/`: Extensive architectural documentation, reports, manual integration reports, and journal entries.
- Root scripts: 4 test scripts committed to root (`test_openrouter.py`, `test_openrouter1.py`, `test_deepseek.py`, `test_backend_openrouter.py`).

### 1.4 Large Files (> 1 MB)

Two large binary PDF files are tracked in git under `docs/project-specifications/`:
1. `docs/project-specifications/Grad_proposal_Final-compressed_V2.pdf` — **1.68 MB**
2. `docs/project-specifications/مشروع-التخرج-سيف-الخولي.pdf` — **18.91 MB** (Arabic document specification)

> [!WARNING]
> Storing large binary PDFs (especially an 18.9 MB file) directly in the Git repository bloats the clone size for every contributor. Binary assets should ideally be stored in object storage (e.g., S3/MinIO) or tracked with Git LFS.

### 1.5 Tracked Secrets and Sensitive Files

- `git ls-files` check shows **no tracked `.env` file** in root or backend (properly ignored in `.gitignore`).
- Tracked `.env.example` in repo root contains safe dummy placeholder strings.
- Historical audit note: Commit `278d898` and `10d511c` remediated earlier commits where OpenRouter and Gemini API keys were temporarily added in documentation and committed. The active working tree contains no unredacted live secret tokens in tracked files.

### 1.6 Requirements Diff and Dependency Risk Assessment

`git diff be3bc6a HEAD -- backend/requirements.txt`:
```diff
+python-multipart==0.0.32
+pypdf==6.21.4
+reportlab==5.1.0
```

| Package | Version | Pinned? | Purpose | Needed for Ring 1? | Security & Operational Risk |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `python-multipart` | `0.0.32` | Yes (`==`) | Parses multipart form data for file uploads (`UploadFile` in FastAPI). | Yes (needed for PDF/document uploads in `/sources` and `/ring1/upload-pdf`). | Low risk. Standard FastAPI dependency for form/file processing. |
| `pypdf` | `6.21.4` | Yes (`==`) | Pure-Python PDF extraction library; reads text page-by-page. | Questionable for Ring 1 Core (PDF processing belongs to Source Ingestion/Ring 2). | Low-to-medium risk. PDF parsers historically face memory exhaustion or infinite recursion on crafted/malicious PDF files. Mitigation: file size is capped at 20MB in `ring1.py`. |
| `reportlab` | `5.1.0` | Yes (`==`) | Programmatic PDF document generation library. | **NO**. Ring 1 has no requirement to generate or export PDF files. Used only in test helpers or ad-hoc scripts. | Low risk, but adds unnecessary bloated transitive dependencies. |

**Missing Dependencies in Active Host Python Environment:**
The active system Python environment (`C:\ProgramData\miniconda3\python.exe` and `C:\Users\karim\.local\bin\python3.12.exe`) lacks the pinned dependencies:
`pytest==9.1.1`, `alembic==1.20.0`, `fastapi==0.142.2`, `sqlalchemy==2.0.54`, `psycopg==3.3.6`, `pgvector==0.5.0`, `pyjwt==2.15.1`, `argon2-cffi==25.1.0`.
Consequently, live execution of `pytest` and `alembic` commands in the current shell could not execute without environment provisioning (marked UNVERIFIED per Rule 0).

### 1.7 Infrastructure and Configuration Changes

1. **`docker-compose.yml`:**
   - **PostgreSQL port changed** from `5432:5432` to `5433:5432`.
   - **Neo4j container added:** `image: neo4j:5-community`, ports `7474:7474`, `7687:7687`, volume `neo4j_data`.
     *Violation:* AGENTS.md explicitly states: *"Stack (non-negotiable): Python 3.12, FastAPI, PostgreSQL (+ pgvector), SQLAlchemy 2.0, Alembic, Pydantic v2, PyJWT, pytest. Do NOT use Node, Express, Prisma, or Neo4j."* Decision D-001 also prohibits Neo4j. Adding Neo4j directly breaches non-negotiable stack boundaries.
2. **`.github/`:**
   - Added empty `.gitkeep` files under `.github/ISSUE_TEMPLATE/` and `.github/workflows/`. No automated CI workflows have been configured.
3. **`AGENTS.md`:**
   - No modifications made by the teammate. Preserved intact from Karim's Ring 0 baseline.
4. **`.env.example`:**
   - Expanded with comprehensive provider keys (OpenAI, DeepSeek, OpenRouter, Kimi, Ollama, Groq, HuggingFace, Gemini) and frontend configuration URLs (`NEXT_PUBLIC_BACKEND_API_URL=http://localhost:8000/api/v1`).

*In plain words:*
The teammate pulled in a huge volume of code including frontend, AI providers, and document ingestion, but kept git history clean without active merge conflicts. However, they modified database ports, introduced Neo4j against project rules, and added PDF libraries directly into the backend.

<!-- SECTION 1 DONE -->


---

## S2 Architecture As Built

### 2.1 Folder and File Structure Map

```text
OrgBrain/
├── .env.example                                      # Environment template with Postgres, AI, and Next.js variables
├── .gitignore                                        # Standard git ignore including .venv, __pycache__, .env, .next
├── AGENTS.md                                         # Master instructions and non-negotiable rules for AI agents
├── docker-compose.yml                                # Container orchestration: PostgreSQL 17 + pgvector, Neo4j 5
├── ORGANIZATIONAL_BRAIN_MASTER_PROJECT_CONSTITUTION.md # Project vision, 10 rings, and architectural invariants
├── project-context-ring-architecture.canvas(1).tsx  # Obsidian/Canvas visual representation of ring layers
├── pytest.ini                                        # Root pytest test runner configuration
├── README.md                                         # Project description and setup instructions
├── test_backend_openrouter.py                        # Ad-hoc test script for OpenRouter integration
├── test_deepseek.py                                  # Ad-hoc test script for DeepSeek API
├── test_openrouter.py                                # Ad-hoc test script for OpenRouter free models
├── test_openrouter1.py                               # Ad-hoc test script for multi-turn OpenRouter conversation
├── ai/                                               # AI Engine Package (Python 3.12 provider abstractions)
│   ├── config/ai_config.py                           # Pydantic configuration loading API keys and provider models
│   ├── core/interfaces/provider.py                   # ILLMProvider protocol contract
│   ├── core/services/llm_service.py                  # LLMService execution wrapper with logging and timing
│   ├── core/types/{error,request,response}.py        # Typed envelopes for AI messages, errors, and tokens
│   ├── providers/                                    # Concrete providers: OpenAI, DeepSeek, Groq, Gemini, etc.
│   │   ├── base_openai.py                            # Reusable base class for OpenAI-compatible HTTP endpoints
│   │   ├── registry.py                               # ProviderRegistry factory mapping IDs to classes
│   │   └── fake_provider.py                          # Deterministic in-memory fake provider for zero-cost tests
│   └── tests/                                        # Pytest test suite for AI abstraction layer (15 tests)
├── backend/                                          # FastAPI Core Application
│   ├── alembic.ini                                   # Alembic database migration tool configuration
│   ├── pytest.ini                                    # Backend pytest configuration
│   ├── requirements.txt                              # Pinned Python package dependencies
│   ├── app/
│   │   ├── main.py                                   # FastAPI entrypoint, CORS configuration, router mounting
│   │   ├── api/
│   │   │   ├── deps.py                               # Request dependencies (get_db, get_current_user, require_admin)
│   │   │   └── v1/                                   # Versioned API route endpoints
│   │   │       ├── ai.py                             # POST /prompt demonstration endpoint
│   │   │       ├── auth.py                           # POST /login, GET /me endpoints
│   │   │       ├── brain.py                          # GET /status health and engine inventory endpoint
│   │   │       ├── cases.py                          # Case management and document upload routes (Ring 5 leakage)
│   │   │       ├── context.py                        # POST /resolve context resolution endpoint
│   │   │       ├── health.py                         # GET /health, GET /health/db endpoints
│   │   │       ├── memory.py                         # GET /{id} context-isolated memory record inspection
│   │   │       ├── observations.py                   # POST /observations, GET /observations feed endpoint
│   │   │       ├── retrieval.py                      # GET /search lexical candidate retrieval endpoint
│   │   │       ├── ring1.py                          # Ring 1 Live Test runner and PDF pipeline SSE endpoints
│   │   │       ├── sources.py                        # POST /sources raw document upload endpoint
│   │   │       ├── tasks.py                          # GET /{task_id} durable task inspection endpoint
│   │   │       ├── users.py                          # Admin user creation and listing endpoints
│   │   │       └── ws.py                             # WS /observations real-time WebSocket streaming endpoint
│   │   ├── core/
│   │   │   ├── audit.py                              # AuditService logging state transitions to audit_events
│   │   │   ├── config.py                             # Settings loaded via pydantic-settings from root .env
│   │   │   ├── context.py                            # Authoritative get_brain_context dependency
│   │   │   ├── cursor.py                             # HMAC-SHA256 Base64URL signed keyset pagination engine
│   │   │   ├── dispatcher.py                         # RuntimeDispatcher executing peer delegations with limits
│   │   │   ├── errors.py                             # Standard JSON error envelopes {"error": {"code", "message"}}
│   │   │   ├── handoff.py                            # HandoffPolicy enforcing peer delegation permissions
│   │   │   ├── outbox_dispatcher.py                  # Transactional Outbox worker with generation fencing
│   │   │   ├── security.py                           # Argon2id password hashing and HS256 PyJWT tokens
│   │   │   ├── short_term_memory.py                  # Ephemeral execution state caching (Redis + memory fallback)
│   │   │   ├── task_manager.py                       # PostgreSQL TaskManager (SKIP LOCKED, lease generation)
│   │   │   └── ws_manager.py                         # ObservationWebSocketManager handling client subscriptions
│   │   ├── db/
│   │   │   ├── base.py                               # Declarative Base metadata for SQLAlchemy ORM
│   │   │   ├── session.py                            # SessionLocal factory and synchronous Engine setup
│   │   │   └── test_utils.py                         # assert_safe_test_database guard preventing dev DB corruption
│   │   ├── domains/                                  # Domain Extensions (re-export shims to brain/extensions)
│   │   │   ├── contracts.py                          # IDomainExtension and DomainRegistry interfaces
│   │   │   ├── legal/                                # Legal domain schemas and structured article extractor
│   │   │   ├── logistics/                            # Logistics fleet manifests and vehicle schemas
│   │   │   └── sales/                                # Sales pipeline and opportunity schemas
│   │   ├── infrastructure/
│   │   │   ├── ai/adapter.py                         # LLMServiceAdapter implementing brain ILLMClient
│   │   │   └── database/stores.py                    # SqlAlchemyObservationStore, MemoryStore, RetrievalStore
│   │   ├── models/                                   # SQLAlchemy ORM table definitions
│   │   │   ├── audit.py                              # AuditEvent model (audit_events table)
│   │   │   ├── case.py                               # Case model (cases table) — Ring 5 scope leakage
│   │   │   ├── source.py                             # Source model (sources table)
│   │   │   ├── task.py                               # Task, TaskOutbox models (tasks, task_outbox tables)
│   │   │   └── user.py                               # User model (users table)
│   │   ├── ring1/                                    # Ring 1 General Brain Engine Compatibility Shims
│   │   │   ├── contracts/                            # Envelopes, context refs, plan models, error codes
│   │   │   ├── engines/                              # Re-exports: Perception, Observation, Context, Memory, etc.
│   │   │   ├── execution/executor.py                 # PlanStepExecutor running steps through MeshRouter
│   │   │   ├── mesh/router.py                        # MeshRouter in-process capability dispatcher
│   │   │   ├── models/observation.py                 # Observation, MemoryRecord models
│   │   │   ├── pdf/                                  # PDFExtractor and StructuredKnowledgeExtractor
│   │   │   └── services/                             # Ring1TestRunner façade, TestScenarioService, PdfPipeline
│   │   ├── schemas/                                  # Pydantic v2 API request and response DTO schemas
│   │   ├── scripts/create_admin.py                   # CLI utility script to bootstrap initial administrator
│   │   └── services/                                 # Business services: user_service, case_service, source_service
│   ├── migrations/                                   # Alembic schema migration environment
│   │   ├── env.py                                    # Migration execution script with offline/online branches
│   │   └── versions/                                 # 6 linear migration revisions (6dd2ff08b0bb to b39c4d5e6f7a)
│   └── tests/                                        # Pytest test suite (17 root files, 23 ring1 files)
├── brain/                                            # Standalone General Brain Core Package (brain-co-core)
│   └── src/brain/
│       ├── extensions/{legal,logistics,sales}/       # Industry-specific domain extension packages
│       └── general/                                  # Canonical domain-agnostic General Brain core
│           ├── contracts/                            # Pure Python protocols (storage, LLM, capabilities, context)
│           ├── engines/                              # Pure implementations of 6 cognitive engines
│           ├── policies/handoff.py                   # Handoff and delegation constraints
│           ├── runtime/                              # MeshRouter, RuntimeDispatcher, PlanStepExecutor
│           └── stores/                               # In-memory test store implementations
├── data-engineering/                                 # Data ingestion pipelines, dbt models, Airflow DAG stubs
├── data-science/                                     # Evaluation datasets and model exploration notebooks
├── docs/                                             # Project documentation, specifications, architectural records
│   ├── audit/ring-1-audit.md                         # This audit report
│   ├── backend/                                      # Moved backend documentation (decisions.md, progress.md)
│   └── rings/                                        # Ring specifications and technical milestone reports
├── frontend/                                         # Next.js 16.4.0 TypeScript Web Application
├── infrastructure/                                   # Setup SQL scripts (pgvector-setup.sql)
└── mobile/                                           # Flutter mobile application package stubs
```

### 2.2 Module Dependency and Import Map

```mermaid
graph TD
    subgraph "External Layers"
        FE["Frontend (Next.js 16)"]
        CLI["CLI Scripts (create_admin.py)"]
    end

    subgraph "FastAPI Application (backend/app/)"
        API["API Routers (api/v1/)"]
        DEPS["Dependencies (api/deps.py, core/context.py)"]
        SERVICES["Backend Services (case_service, task_manager)"]
        ADAPTERS["Storage & AI Adapters (infrastructure/)"]
        MODELS["SQLAlchemy Models (models/, ring1/models/)"]
    end

    subgraph "General Brain Core (brain/src/brain/)"
        GB_ENGINES["Canonical Engines (perception, observation, context, memory, retrieval, planning)"]
        GB_RUNTIME["Mesh Runtime (MeshRouter, PlanStepExecutor)"]
        GB_CONTRACTS["Protocols & Envelopes (contracts/)"]
    end

    subgraph "AI Engine (ai/)"
        LLM_SVC["LLMService"]
        PROVIDERS["ProviderRegistry (OpenAI, DeepSeek, Fake)"]
    end

    subgraph "Database (PostgreSQL 17)"
        PG[("PostgreSQL + pgvector")]
    end

    FE -->|HTTP / SSE / WS| API
    CLI --> SERVICES
    API --> DEPS
    API --> SERVICES
    API --> GB_ENGINES
    DEPS --> MODELS
    SERVICES --> MODELS
    SERVICES --> ADAPTERS
    ADAPTERS --> MODELS
    MODELS --> PG
    SERVICES --> PG

    ADAPTERS -->|Implements| GB_CONTRACTS
    GB_ENGINES --> GB_CONTRACTS
    GB_RUNTIME --> GB_CONTRACTS
    ADAPTERS --> LLM_SVC
    LLM_SVC --> PROVIDERS
```

**Circular Dependency Analysis:**
- No circular dependencies exist at runtime.
- The potential cycle between `backend/app/ring1/pdf/structured.py` and `backend/app/domains/legal/extractor.py` was explicitly decoupled by deferring the import locally inside methods (`import LegalStructuredKnowledgeExtractor` inside `__init__` and `extract()`).
- General Brain (`brain/`) has zero inbound imports from `backend/` or `app/`, ensuring it can be packaged and distributed independently.

### 2.3 Request Flow of Key Features

#### A. Record Observation Event (`POST /api/v1/observations`)
```text
Client (HTTP POST JSON)
  → FastAPI Router (`app/api/v1/observations.py:create_observation`)
    → Dependency: `get_db` opens SQLAlchemy Session
    → Dependency: `get_brain_context` parses Bearer JWT, validates org_id and active user in DB
    → Idempotency Check: `db.query(Observation).filter(idempotency_key)`
    → DB Insert: Create `Observation` ORM object in `ring1_observations` table
    → Audit Log: `AuditService.record_event` writes row to `audit_events` table
    → Database Commit: `db.commit()` commits transaction
    → Real-time Broadcast: `ws_manager.broadcast_observation()` broadcasts JSON to active WebSockets
    → Client Response: HTTP 201 Created with `ObservationResponse`
```

#### B. Keyset-Paginated Observation Feed (`GET /api/v1/observations`)
```text
Client (HTTP GET with ?limit=50&cursor=...)
  → FastAPI Router (`app/api/v1/observations.py:list_observations`)
    → Dependency: `get_brain_context` validates JWT and extracts tenant scope
    → Cursor Verification: `decode_and_verify_cursor()` verifies HMAC-SHA256 signature, validates org_id, case_id, filter hash, sort order, and RFC 4122 UUID syntax
    → SQL Query: Query `ring1_observations` with `WHERE (created_at, id) < (cursor_time, cursor_id)` ordered by `created_at DESC, id DESC LIMIT 51`
    → Cursor Encoding: If rows > 50, encode last record into signed HMAC Base64URL cursor token
    → Client Response: HTTP 200 OK with `ObservationListResponse`
```

#### C. Context-First Lexical Retrieval (`GET /api/v1/retrieval/search`)
```text
Client (HTTP GET with ?q=contract&record_type=fact)
  → FastAPI Router (`app/api/v1/retrieval.py:search_records`)
    → Dependency: `get_brain_context` enforces authorized organization and case scope
    → Scope Boundary Filtering: Database query strictly filters `organization_id == context.org_id` and `case_id == context.case_id`
    → Candidate Gate: If caller lacks validation authority (`validation_authority == False`), exclude status `candidate` and `rejected`
    → Candidate Selection: Fetch matching memory records from PostgreSQL
    → Scoring & Snippet Extraction: Pure Python token matching counts keyword occurrences in `payload` JSON, computes score, extracts snippet
    → Sorting & Pagination: Sort candidates by score descending, slice by `limit`
    → Client Response: HTTP 200 OK with `RetrievalSearchResponse`
```

### 2.4 Configuration and Environment Variables

Every configuration setting is defined in `backend/app/core/config.py` using Pydantic v2 `BaseSettings` reading from root `.env`:

| Variable Name | Required? | Default Value | Where Read | Purpose |
| :--- | :--- | :--- | :--- | :--- |
| `DATABASE_URL` | No | `postgresql+psycopg://postgres:postgres@localhost:5433/orgbrain_legal` | `app/core/config.py:25` | Primary PostgreSQL synchronous connection URL |
| `POSTGRES_USER` | No | `postgres` | `app/core/config.py:28` | Database username |
| `POSTGRES_PASSWORD` | No | `postgres` | `app/core/config.py:29` | Database password |
| `POSTGRES_DB` | No | `orgbrain_legal` | `app/core/config.py:30` | Production/Development database name |
| `POSTGRES_HOST` | No | `localhost` | `app/core/config.py:31` | Database network hostname |
| `POSTGRES_PORT` | No | `5433` | `app/core/config.py:32` | Database port (changed from 5432 in docker-compose) |
| `POSTGRES_TEST_DB` | No | `orgbrain_legal_test` | `app/core/config.py:33` | Isolated test database name |
| `SECRET_KEY` | **YES** | None (validation error if absent, < 32 chars, or "change-this") | `app/core/config.py:35` | Cryptographic secret for JWT signing and HMAC cursors |
| `ACCESS_TOKEN_EXPIRE_MINUTES`| No | `60` | `app/core/config.py:36` | Lifetime in minutes of issued JWT access tokens |
| `ENVIRONMENT` | No | `development` | `app/core/config.py:38` | Runtime environment (`development`, `test`, `production`) |
| `ORGANIZATION_ID` | No | `org-brain-corp` | `app/core/config.py:39` | Instance organization identifier (breaches D-004) |
| `AI_ANONYMOUS_TESTING_ENABLED`| No | `False` | `app/core/config.py:40` | Allows unauthenticated testing; forbidden in production |

### 2.5 How to Run App and Tests From Zero

1. **Prerequisites:**
   - Docker Desktop running with PostgreSQL 17 (`docker compose up -d postgres`).
   - Python 3.12 virtual environment.
2. **Environment File:**
   ```bash
   cp .env.example .env
   # Edit .env and supply a 32+ character SECRET_KEY:
   # SECRET_KEY=0123456789abcdef0123456789abcdef
   ```
3. **Install Dependencies:**
   ```bash
   cd backend
   pip install -r requirements.txt
   ```
4. **Database Migrations:**
   ```bash
   # Run migrations to provision PostgreSQL tables
   alembic upgrade head
   ```
5. **Run FastAPI Application:**
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```
6. **Run Test Suite:**
   ```bash
   # Runs against isolated test DB (requires Docker postgres running)
   pytest -q
   ```

### 2.6 Synchronous vs Asynchronous Usage Analysis

> [!WARNING]
> **Event Loop Blocking Issue in `async def` Route Handlers:**
> The backend stack is built on SQLAlchemy 2.0 synchronous mode (`postgresql+psycopg://`), yet multiple route handlers and store adapters are defined as `async def`.
>
> In FastAPI:
> - Normal `def` route handlers run in an external threadpool (AnyIO worker thread), preventing blocking.
> - `async def` route handlers run **directly on the main asyncio event loop**. Any synchronous blocking I/O (like a database commit or query) executed inside `async def` **freezes the entire server event loop**, starving concurrent WebSocket connections and SSE streams.

**Specific Code Citations of Blocking I/O inside `async def`:**
1. `backend/app/api/v1/observations.py:38`: `async def create_observation()` executes blocking calls:
   - Line 50: `db.query(Observation)...` (synchronous SQL query)
   - Line 108: `db.commit()` (synchronous blocking network I/O)
   - Line 109: `db.refresh(obs)` (synchronous SQL query)
2. `backend/app/infrastructure/database/stores.py`:
   - Line 66: `async def save(self, observation: dict[str, Any]) -> str` calls line 100: `session.commit()` synchronously.
   - Line 40: `async def find_by_idempotency_key()` calls line 44: `session.query(Observation)...` synchronously.
   - Line 108: `async def list_feed()` calls line 149: `rows = query.limit(...).all()` synchronously.
   - Line 217: `async def save_record()` calls line 245: `session.commit()` synchronously.
   - Line 342: `async def search_records()` calls line 361: `session.execute(stmt).scalars().all()` synchronously.

*In plain words:*
The code is nicely organized into clear modules, and General Brain was cleanly extracted so it can run alone. However, the teammate wrote `async def` on database functions while using synchronous database drivers, which can freeze the entire backend when multiple users connect simultaneously.

<!-- SECTION 2 DONE -->


---

## S3 Data Model

### 3.1 Comprehensive Table Inventory

PostgreSQL 17 schema contains **8 tables** managed across 6 Alembic revisions.

```text
Database Tables:
├── users                         # Authenticated system users (Ring 0)
├── sources                       # Ingested raw source files (Source Ingestion)
├── ring1_observations            # Normalized observation event stream (Ring 1 Core)
├── ring1_memory_records          # General Brain memory & knowledge candidates (Ring 1 Core)
├── tasks                         # Durable async task execution ledger (Ring 1 Execution)
├── task_outbox                   # Transactional outbox pattern table (Ring 1 Execution)
├── audit_events                  # Monotonic execution audit ledger (Ring 1 Execution)
└── cases                         # Legal Case entity table (Ring 5 Scope Leakage)
```

#### Detailed Table Specifications

| Table Name | Column Name | Data Type | Nullable? | Default / Generator | Constraints & Foreign Keys | Indexes |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **`users`** | `id` | `UUID` | No | `gen_random_uuid()` | PRIMARY KEY | PK |
| | `email` | `VARCHAR(255)` | No | None | None | `uq_users_lower_email` (UNIQUE `lower(email)`) |
| | `hashed_password` | `VARCHAR(255)` | No | None | None | None |
| | `role` | `VARCHAR(50)` | No | `'employee'` | CHECK (`role IN ('admin', 'employee')`) | None |
| | `is_active` | `BOOLEAN` | No | `true` | None | None |
| | `created_at` | `TIMESTAMPTZ` | No | `now()` | None | None |
| | `updated_at` | `TIMESTAMPTZ` | No | `now()` | None | None |
| **`sources`** | `id` | `UUID` | No | `gen_random_uuid()` | PRIMARY KEY | PK |
| | `source_id` | `VARCHAR(128)` | No | None | UNIQUE (`uq_sources_source_id`) | Unique |
| | `original_filename`| `VARCHAR(255)`| No | None | None | None |
| | `content_type` | `VARCHAR(100)` | Yes | None | None | None |
| | `size_bytes` | `BIGINT` | Yes | None | None | None |
| | `checksum_sha256`| `VARCHAR(64)` | No | None | None | `ix_sources_checksum` |
| | `storage_key` | `VARCHAR(512)` | No | None | None | None |
| | `uploaded_by` | `UUID` | Yes | None | FK `users.id` ON DELETE SET NULL | `ix_sources_uploaded_by` |
| | `source_type` | `VARCHAR(50)` | No | `'document'` | None | None |
| | `storage_mode` | `VARCHAR(50)` | No | `'local'` | None | None |
| | `status` | `VARCHAR(50)` | No | `'ingested'` | None | `ix_sources_status` |
| | `case_id` | `VARCHAR(128)` | Yes | None | None | `ix_sources_case_id` |
| | `organization_id`| `VARCHAR(64)` | Yes | None | None | `ix_sources_organization_id` |
| | `created_at` | `TIMESTAMPTZ` | No | `now()` | None | None |
| | `updated_at` | `TIMESTAMPTZ` | No | `now()` | None | None |
| **`ring1_observations`** | `id` | `UUID` | No | `gen_random_uuid()` | PRIMARY KEY | PK |
| | `event_id` | `VARCHAR(255)` | No | None | None | None |
| | `event_type` | `VARCHAR(255)` | No | None | None | `ix_ring1_observations_event_type` |
| | `source` | `VARCHAR(255)` | No | None | None | None |
| | `actor_ref` | `VARCHAR(255)` | Yes | None | None | None |
| | `context_ref` | `VARCHAR(255)` | Yes | None | None | `ix_ring1_observations_context_ref` |
| | `case_id` | `VARCHAR(255)` | Yes | None | None | `ix_ring1_observations_case_id` |
| | `organization_id`| `VARCHAR(255)`| Yes | None | None | None |
| | `payload` | `JSONB` | Yes | None | None | None |
| | `metadata` | `JSONB` | Yes | None | None | None |
| | `trace_id` | `VARCHAR(255)` | Yes | None | None | `ix_ring1_observations_trace_id` |
| | `task_id` | `VARCHAR(255)` | Yes | None | None | None |
| | `idempotency_key`| `VARCHAR(500)`| Yes | None | None | `uq_ring1_observations_idempotency` (UNIQUE WHERE NOT NULL) |
| | `status` | `VARCHAR(50)` | No | `'recorded'` | None | None |
| | `observation_type`| `VARCHAR(100)`| Yes | None | None | None |
| | `expires_at` | `TIMESTAMPTZ` | Yes | None | None | None |
| | `event_timestamp`| `TIMESTAMPTZ` | Yes | None | None | None |
| | `created_at` | `TIMESTAMPTZ` | No | `now()` | None | `ix_ring1_observations_created_at`, `ix_ring1_observations_cursor` (`[created_at, id]`) |
| **`ring1_memory_records`** | `id` | `UUID` | No | `gen_random_uuid()` | PRIMARY KEY | PK |
| | `record_type` | `VARCHAR(100)` | No | None | None | `ix_ring1_memory_records_record_type` |
| | `context_ref` | `VARCHAR(255)` | Yes | None | None | `ix_ring1_memory_records_context_ref` |
| | `case_id` | `VARCHAR(255)` | Yes | None | None | `ix_ring1_memory_records_case_id` |
| | `organization_id`| `VARCHAR(255)`| Yes | None | None | None |
| | `payload` | `JSONB` | Yes | None | None | None |
| | `metadata` | `JSONB` | Yes | None | None | None |
| | `trace_id` | `VARCHAR(255)` | Yes | None | None | `ix_ring1_memory_records_trace_id` |
| | `task_id` | `VARCHAR(255)` | Yes | None | None | None |
| | `source_observation_id`| `UUID` | Yes | None | None | None |
| | `idempotency_key`| `VARCHAR(500)`| Yes | None | None | `uq_ring1_memory_records_idempotency` (UNIQUE WHERE NOT NULL) |
| | `status` | `VARCHAR(50)` | No | `'active'` | None | None |
| | `created_at` | `TIMESTAMPTZ` | No | `now()` | None | `ix_ring1_memory_records_created_at` |
| | `updated_at` | `TIMESTAMPTZ` | No | `now()` | None | None |
| **`tasks`** | `id` | `UUID` | No | `gen_random_uuid()` | PRIMARY KEY | PK |
| | `organization_id`| `VARCHAR(255)`| No | None | None | `ix_tasks_org_state` (`[organization_id, state]`) |
| | `case_id` | `VARCHAR(255)` | Yes | None | None | `ix_tasks_case_id` |
| | `user_id` | `VARCHAR(255)` | Yes | None | None | None |
| | `task_type` | `VARCHAR(100)` | No | `'general_ingestion'` | None | None |
| | `state` | `VARCHAR(50)` | No | `'PENDING'` | None | `ix_tasks_lease_expiry` (`[state, lease_expires_at]`) |
| | `idempotency_key`| `VARCHAR(255)`| Yes | None | None | `uq_tasks_org_idempotency` (UNIQUE `[organization_id, idempotency_key]` WHERE NOT NULL) |
| | `worker_id` | `VARCHAR(255)` | Yes | None | None | None |
| | `lease_generation`| `BIGINT` | No | `0` | None | None |
| | `lease_expires_at`| `TIMESTAMPTZ`| Yes | None | None | None |
| | `retry_count` | `INTEGER` | No | `0` | None | None |
| | `max_retries` | `INTEGER` | No | `3` | None | None |
| | `payload` | `JSONB` | Yes | None | None | None |
| | `result` | `JSONB` | Yes | None | None | None |
| | `error_details` | `JSONB` | Yes | None | None | None |
| | `correlation_id`| `VARCHAR(255)`| Yes | None | None | None |
| | `replayed_from_task_id`| `UUID` | Yes | None | None | None |
| | `replayed_to_task_id`| `UUID` | Yes | None | None | None |
| | `created_at` | `TIMESTAMPTZ` | No | `now()` | None | `ix_tasks_created_at` |
| | `updated_at` | `TIMESTAMPTZ` | No | `now()` | None | None |
| **`task_outbox`** | `id` | `UUID` | No | `gen_random_uuid()` | PRIMARY KEY | PK |
| | `task_id` | `UUID` | No | None | None | `ix_task_outbox_task_id` |
| | `queue_name` | `VARCHAR(100)` | No | `'ring1_tasks'` | None | None |
| | `payload` | `JSONB` | No | `'{}'` | None | None |
| | `status` | `VARCHAR(50)` | No | `'PENDING'` | None | `ix_task_outbox_status_lease` (`[status, dispatch_lease_expires_at]`) |
| | `dispatch_generation`| `BIGINT`| No | `0` | None | None |
| | `dispatch_attempts`| `INTEGER` | No | `0` | None | None |
| | `dispatch_lease_expires_at`| `TIMESTAMPTZ`| Yes | None | None | None |
| | `scheduled_for` | `TIMESTAMPTZ` | Yes | None | None | None |
| | `dispatched_at` | `TIMESTAMPTZ` | Yes | None | None | None |
| | `created_at` | `TIMESTAMPTZ` | No | `now()` | None | `ix_task_outbox_created_at` |
| | `updated_at` | `TIMESTAMPTZ` | No | `now()` | None | None |
| **`audit_events`** | `id` | `UUID` | No | `gen_random_uuid()` | PRIMARY KEY | PK |
| | `task_id` | `UUID` | Yes | None | None | `ix_audit_events_task_id` |
| | `organization_id`| `VARCHAR(255)`| No | None | None | `ix_audit_events_org_created` (`[organization_id, created_at]`) |
| | `case_id` | `VARCHAR(255)` | Yes | None | None | `ix_audit_events_case_id` |
| | `actor_ref` | `VARCHAR(255)` | Yes | None | None | None |
| | `engine_name` | `VARCHAR(100)` | No | None | None | `ix_audit_events_engine_action` (`[engine_name, action]`) |
| | `action` | `VARCHAR(100)` | No | None | None | None |
| | `previous_state`| `VARCHAR(50)` | Yes | None | None | None |
| | `new_state` | `VARCHAR(50)` | Yes | None | None | None |
| | `proposed_destination`| `VARCHAR(100)`| Yes | None | None | None |
| | `accepted_or_rejected`| `BOOLEAN`| No | `true` | None | None |
| | `execution_attempt`| `INTEGER` | No | `1` | None | None |
| | `lease_generation`| `BIGINT` | Yes | None | None | None |
| | `error_code` | `VARCHAR(100)` | Yes | None | None | None |
| | `payload` | `JSONB` | Yes | None | None | None |
| | `payload_checksum`| `VARCHAR(64)`| Yes | None | None | None |
| | `correlation_id`| `VARCHAR(255)`| Yes | None | None | `ix_audit_events_correlation` |
| | `created_at` | `TIMESTAMPTZ` | No | `now()` | None | None |
| **`cases`** | `id` | `UUID` | No | `gen_random_uuid()` | PRIMARY KEY | PK |
| | `case_number` | `VARCHAR(100)` | No | None | None | `ix_cases_case_number` |
| | `title` | `VARCHAR(255)` | No | None | None | None |
| | `description` | `TEXT` | Yes | None | None | None |
| | `organization_id`| `VARCHAR(64)` | No | None | UNIQUE `[organization_id, case_number]` | `ix_cases_organization_id` |
| | `status` | `VARCHAR(50)` | No | `'active'` | None | `ix_cases_status` |
| | `created_by` | `UUID` | Yes | None | FK `users.id` ON DELETE SET NULL | None |
| | `created_at` | `TIMESTAMPTZ` | No | `now()` | None | `ix_cases_created_at` |
| | `updated_at` | `TIMESTAMPTZ` | No | `now()` | None | None |

### 3.2 Text Entity Relationship Diagram (ERD)

```text
[ users ]
   │
   ├──────(1 : N, ON DELETE SET NULL)──────> [ sources ] (uploaded_by)
   │
   └──────(1 : N, ON DELETE SET NULL)──────> [ cases ] (created_by)
                                                │
                                                ├─── (Logical 1 : N by case_id string) ───> [ sources ] (case_id)
                                                ├─── (Logical 1 : N by case_id string) ───> [ ring1_observations ] (case_id)
                                                ├─── (Logical 1 : N by case_id string) ───> [ ring1_memory_records ] (case_id)
                                                ├─── (Logical 1 : N by case_id string) ───> [ tasks ] (case_id)
                                                └─── (Logical 1 : N by case_id string) ───> [ audit_events ] (case_id)

[ tasks ]
   │
   ├────── (Logical 1 : N by task_id UUID) ──────> [ task_outbox ] (task_id)
   └────── (Logical 1 : N by task_id UUID) ──────> [ audit_events ] (task_id)

[ ring1_observations ]
   │
   └────── (Logical 1 : N by source_observation_id UUID) ───> [ ring1_memory_records ]
```

> [!NOTE]
> Most inter-table linkages between Ring 1 engines (`ring1_observations`, `ring1_memory_records`, `tasks`, `task_outbox`, `audit_events`) rely on **application-level logical keys** (strings/UUIDs) rather than hard foreign key database constraints. While this decouples distributed tables, it sacrifices referential integrity (e.g. deleting a task will not cascade-delete outbox or audit rows).

### 3.3 Alembic Migration Chain Analysis

The Alembic migration chain is **linear with exactly 1 head revision**.

```text
6dd2ff08b0bb (enable_pgvector_extension)
       │
778be99882b6 (create_users_table)
       │
e819b932c01a (create_sources_table)
       │
f19a0a1b2c3d (create_ring1_tables)
       │
a28b3c4d5e6f (create_tasks_outbox_audit_tables)
       │
b39c4d5e6f7a (create_cases_table_and_source_case_id)  <-- [CURRENT HEAD]
```

- **Reversibility:** All 6 migrations provide comprehensive `downgrade()` functions that cleanly drop created tables, indexes, and columns in reverse order.
- **Destructive Operations:** None. No existing columns are dropped or truncated during upgrade. All `op.add_column` calls add nullable columns.
- **Offline SQL Validation:** In `a28b3c4d5e6f_create_tasks_outbox_audit_tables.py`, line 156 uses `with op.get_context().autocommit_block(): op.create_index(..., postgresql_concurrently=True)`. While valid for online execution, in offline mode (`--sql`), concurrent index creation cannot run within an explicit transaction block. Because `alembic` is not installed in the active host environment, offline execution output is **UNVERIFIED**.
- **DDL outside Alembic:** A scan of the entire repository found **zero `create_all()` calls** and zero raw DDL strings executed outside the `backend/migrations/` directory.

### 3.4 Vector Extension & Index Analysis

- **Extension status:** `backend/migrations/versions/6dd2ff08b0bb_enable_pgvector_extension.py` correctly executes `CREATE EXTENSION IF NOT EXISTS vector`.
- **Vector columns:** **0 columns**. Neither `ring1_observations` nor `ring1_memory_records` possesses a `Vector(...)` column type.
- **Vector indexes:** **0 indexes**. No `HNSW` or `IVFFlat` index exists in the database.
- **Vector dimension consistency:** N/A (no vector embeddings are stored).
- **Distance operators:** N/A (no `<->` L2 or `<#>` cosine distance operators are used in any SQL query).
- **Explanation:** In `docs/backend/decisions.md` (decision D-012/D-016), the teammate documented a *"Vector Freeze pending AI/Data Science written sign-off"*. Consequently, vector capability was deferred, and retrieval was built as a lexical keyword counter in Python.

### 3.5 Decision Compliance Check: `organization_id` & `cases` Tables

1. **`organization_id` Multi-Tenancy Violation (D-004):**
   - Decision D-004 states: *"One organization per deployment (single-organization instance)... NO organization_id/tenant columns"*.
   - **Violation Evidence:**
     - `cases`: column `organization_id VARCHAR(64)` (`b39c4d5e6f7a.py:35`)
     - `sources`: column `organization_id VARCHAR(64)` (`b39c4d5e6f7a.py:65`)
     - `tasks`: column `organization_id VARCHAR(255)` (`a28b3c4d5e6f.py:33`)
     - `audit_events`: column `organization_id VARCHAR(255)` (`a28b3c4d5e6f.py:122`)
     - `ring1_observations`: column `organization_id VARCHAR(255)` (`f19a0a1b2c3d.py:39`)
     - `ring1_memory_records`: column `organization_id VARCHAR(255)` (`f19a0a1b2c3d.py:111`)
     - `backend/app/core/config.py:39`: `ORGANIZATION_ID: str = "org-brain-corp"`
2. **`cases` Table Scope Violation (Ring 1 vs Ring 5):**
   - Ring 1 specification explicitly forbids Case/Client tables (reserved for Ring 5 "Case Intelligence").
   - **Violation Evidence:** Migration `b39c4d5e6f7a` creates the full `cases` table and introduces `app/api/v1/cases.py` router.

*In plain words:*
The database migration chain is clean and reversible, but the teammate skipped adding vector columns to store AI embeddings. Furthermore, they violated core decisions by adding `organization_id` columns everywhere and building a full `cases` table ahead of schedule.

<!-- SECTION 3 DONE -->


---

## S4 API Inventory

### 4.1 Complete Route Catalog

| Method | Path | Router File:Line | Authentication / Gate | Request Model / Body | Response Model / Body | Expected Status Codes | Error Handling |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `GET` | `/health` | `app/main.py:27` | None (Public) | None | `{"status": "ok"}` | `200` | None |
| `GET` | `/api/v1/health/db` | `app/api/v1/health.py:15` | None (Public) | None | `{"status": "ok", "database": "reachable"}` | `200`, `503` | 503 if `SELECT 1` fails |
| `POST`| `/api/v1/auth/login` | `app/api/v1/auth.py:40` | None (Public) | `LoginRequest` | `TokenResponse` | `200`, `401`, `422` | Identical 401 for bad email/password |
| `GET` | `/api/v1/auth/me` | `app/api/v1/auth.py:73` | `get_current_user` (Bearer) | None | `UserResponse` | `200`, `401` | Generic 401 on missing/bad token |
| `POST`| `/api/v1/users` | `app/api/v1/users.py:29` | `require_admin` (Admin DB) | `UserCreateRequest` | `UserResponse` | `201`, `400`, `401`, `403`, `409`, `422` | 409 on duplicate email, 403 non-admin |
| `GET` | `/api/v1/users` | `app/api/v1/users.py:65` | `require_admin` (Admin DB) | None | `list[UserResponse]` | `200`, `401`, `403` | 403 on non-admin |
| `POST`| `/api/v1/sources` | `app/api/v1/sources.py:34` | `get_current_user` (Bearer) | `file: UploadFile` | `SourceResponse` | `201`, `400`, `401`, `500` | 400 on validation, 500 on storage error |
| `POST`| `/api/v1/cases` | `app/api/v1/cases.py:59` | `get_brain_context` | `CaseCreate` | `CaseResponse` | `201`, `401`, `409` | 409 on duplicate case number |
| `GET` | `/api/v1/cases` | `app/api/v1/cases.py:97` | `get_brain_context` | Query: `limit, offset, status` | `list[CaseResponse]` | `200`, `401` | Filtered by token org_id |
| `GET` | `/api/v1/cases/{case_id}`| `app/api/v1/cases.py:120` | `get_brain_context` | Path: `case_id: UUID` | `CaseResponse` | `200`, `401`, `404` | 404 if case not in org |
| `POST`| `/api/v1/cases/{case_id}/documents`| `app/api/v1/cases.py:145` | `get_brain_context` | Path: `case_id`, `file: UploadFile` | `DocumentUploadResponse` | `202`, `400`, `401`, `404`, `500` | 404 if case not in org |
| `GET` | `/api/v1/cases/{case_id}/documents`| `app/api/v1/cases.py:199` | `get_brain_context` | Path: `case_id: UUID` | `list[dict]` | `200`, `401`, `404` | 404 if case not in org |
| `GET` | `/api/v1/cases/{case_id}/tasks` | `app/api/v1/cases.py:240` | `get_brain_context` | Path: `case_id: UUID` | `list[TaskResponse]` | `200`, `401`, `404` | 404 if case not in org |
| `GET` | `/api/v1/cases/{case_id}/knowledge`| `app/api/v1/cases.py:285` | `get_brain_context` | Path: `case_id`, Query: `query` | `dict` (records list) | `200`, `401`, `404` | 404 if case not in org |
| `GET` | `/api/v1/tasks/{task_id}`| `app/api/v1/tasks.py:26` | `get_brain_context` | Path: `task_id: UUID` | `TaskResponse` | `200`, `401`, `404` | 404 if task not in org |
| `POST`| `/api/v1/ai/prompt` | `app/api/v1/ai.py:88` | `get_ai_user_or_anonymous`| `PromptRequest` | `PromptResponse` | `200`, `401`, `422`, `502` | Maps LLMError to HTTP status codes |
| `GET` | `/api/v1/brain/status` | `app/api/v1/brain.py:27` | None (Public) | None | `BrainStatusResponse` | `200` | Degraded if DB unreachable |
| `POST`| `/api/v1/observations` | `app/api/v1/observations.py:38`| `get_brain_context` | `ObservationCreate` | `ObservationResponse` | `201`, `401`, `404`, `422` | Idempotent duplicate return |
| `GET` | `/api/v1/observations` | `app/api/v1/observations.py:151`| `get_brain_context` | Query: `type, source, limit, cursor` | `ObservationListResponse` | `200`, `400`, `401` | HMAC cursor verification failure (400) |
| `POST`| `/api/v1/context/resolve` | `app/api/v1/context.py:27` | `get_brain_context` | `ContextResolveRequest` | `ContextResolveResponse` | `200`, `401` | Ambiguity & constraint list |
| `GET` | `/api/v1/memory/{id}` | `app/api/v1/memory.py:27` | `get_brain_context` | Path: `id: UUID` | `MemoryRecordResponse` | `200`, `401`, `404` | Sanitized 404 eliminates oracle |
| `GET` | `/api/v1/retrieval/search` | `app/api/v1/retrieval.py:28` | `get_brain_context` | Query: `q, limit, record_type, include_candidates` | `RetrievalSearchResponse` | `200`, `400`, `401` | Excludes candidates unless authorized |
| `WS`  | `/api/v1/ws/observations`| `app/api/v1/ws.py:24` | Query: `token` (JWT) | Query: `token, case_id, scope_id` | WS stream | `1008` (Policy Violation) | Closes 1008 on missing/invalid token |
| `POST`| `/api/v1/ring1/test-run` | `app/api/v1/ring1.py:41` | `get_test_operator_user` | `TestRunRequest` | StreamingResponse / JSON | `200`, `401` | Bypassed in development |
| `GET` | `/api/v1/ring1/test-runs/{run_id}`| `app/api/v1/ring1.py:94` | `get_test_operator_user` | Path: `run_id` | `dict` | `200`, `401`, `404` | Bypassed in development |
| `GET` | `/api/v1/ring1/test-runs` | `app/api/v1/ring1.py:109` | `get_test_operator_user` | Query: `limit` | `list[dict]` | `200`, `401` | Bypassed in development |
| `GET` | `/api/v1/ring1/capabilities` | `app/api/v1/ring1.py:118` | `get_test_operator_user` | None | `dict` | `200`, `401` | Bypassed in development |
| `POST`| `/api/v1/ring1/upload-pdf` | `app/api/v1/ring1.py:141` | `get_test_operator_user` | Form: `file, organization_id, case_id, mode, stream` | StreamingResponse / JSON | `200`, `400`, `401`, `413` | Bypassed in development; IDOR risk |
| `GET` | `/api/v1/ring1/knowledge` | `app/api/v1/ring1.py:242` | `get_test_operator_user` | Query: `organization_id, case_id, query` | `dict` | `200`, `400`, `401` | Bypassed in development; IDOR risk |

---

### 4.2 Authentication & Authorization Security Matrix

```text
Authentication Scheme Distribution:
├── require_admin                  -> 2 endpoints  (POST /users, GET /users)
├── get_current_user               -> 2 endpoints  (GET /auth/me, POST /sources)
├── get_brain_context              -> 13 endpoints (Core observations, memory, cases, tasks)
├── get_ai_user_or_anonymous       -> 1 endpoint   (POST /ai/prompt)
├── get_test_operator_user (Flawed)-> 6 endpoints  (Ring 1 Test Console & PDF routes)
└── Public (No Auth)               -> 4 endpoints  (/health, /health/db, /auth/login, /brain/status)
```

#### Detailed Security Assessment

1. **Insecure Operator Dependency (`get_test_operator_user`):**
   - **File:** `backend/app/api/deps.py:150-177`
   - **Vulnerability:**
     ```python
     if settings.ENVIRONMENT.lower() != "production":
         return None
     raise _AUTH_401
     ```
     In non-production environments (`ENVIRONMENT=development` or `test`), `get_test_operator_user` **permits all unauthenticated requests**.
   - **Impact:** Any client on the local network can invoke `POST /api/v1/ring1/test-run`, `POST /api/v1/ring1/upload-pdf`, and `GET /api/v1/ring1/knowledge`.
2. **IDOR & Scope Forgery in Ring 1 Endpoints:**
   - **File:** `backend/app/api/v1/ring1.py:144-145, 244-245`
   - **Vulnerability:** `upload_pdf` and `get_case_knowledge` accept `organization_id` and `case_id` directly from user-supplied Form/Query data (`clean_org_id = organization_id.strip()`). Because `get_test_operator_user` allows unauthenticated access in development, an unauthenticated user can view or insert knowledge into **any organization or case**.
   - **Contrast with Secure Pattern:** Secure endpoints (`/memory/{id}`, `/observations`, `/retrieval/search`) use `get_brain_context`, which authoritatively forces `context.organization_id` from the validated server-side JWT claims.
3. **Missing DB User Check in WebSocket Authentication:**
   - **File:** `backend/app/api/v1/ws.py:46-63`
   - **Vulnerability:** The WebSocket endpoint validates the JWT token with `decode_access_token(token)`, but **does not query the database** to verify that `user.is_active == True`. If an employee account is deactivated or deleted in PostgreSQL, any active unexpired token can still open a WebSocket connection and listen to real-time organizational observation broadcasts.
4. **Input Size Limits & Memory Exhaustion:**
   - **`POST /api/v1/sources`:** Executes `content = await file.read()` with **no length limit**. Uploading a 5 GB file will load the entire payload into RAM, causing Denial of Service (OOM crash).
   - **`POST /api/v1/ring1/upload-pdf`:** Properly mitigates this by passing `MAX_PDF_SIZE_BYTES + 1` (20 MB limit) to `file.read()`.
5. **CORS Headers:**
   - Explicitly restricted in `main.py` to `["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:8000"]` with `allow_credentials=True`.
6. **Rate Limiting:**
   - **Completely absent** on the FastAPI backend. There is no rate limiter middleware on `/auth/login` (brute force vulnerability) or `/ai/prompt` (LLM token drain vulnerability).
7. **Security Headers:**
   - Missing standard enterprise HTTP headers: `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Strict-Transport-Security`.

*In plain words:*
Most endpoints check logins properly and prevent users from seeing data outside their organization. However, the test endpoints have a developer backdoor that lets anyone call them without a password in development, and the file upload endpoint does not limit file size.

<!-- SECTION 4 DONE -->


---

## S5 Services and Business Logic Walkthrough

### 5.1 Cognitive Engines Overview

The teammate structured the Ring 1 General Brain into **six cognitive engines** cooperating peer-to-peer via an in-process capability router (`MeshRouter`), governed by an explicit handoff policy (`HandoffPolicy`):

```text
Ring 1 Capability Mesh:
├── PerceptionEngine       (transforms raw input -> structured events)
├── ObservationEngine      (captures, normalizes, deduplicates event stream)
├── ContextEngine          (resolves tenant/case/domain execution scopes)
├── BasicMemoryEngine      (stores knowledge candidates, enforces validation gate)
├── BasicRetrievalEngine   (context-first candidate filtering and lexical search)
└── PlanningEngine         (advisory 6th capability: generates steps & replans)
```

---

### 5.2 Deep Engine Walkthroughs

#### 1. Perception Engine (`brain/src/brain/general/engines/perception.py`)
- **Purpose:** Parses raw unstructured or semi-structured data into structured envelopes without granting authorization or promoting facts to knowledge.
- **Main Functions:**
  - `process(raw_input, context, task_metadata)` (`perception.py:70`)
  - `handle_structure_input(request: MeshRequest)` (`perception.py:200`)
- **Step-by-Step Logic:**
  1. Validates `context.organization_id`.
  2. Checks for unsupported types in `_UNSUPPORTED_SOURCE_TYPES` (`{"binary_executable", "executable", "binary", "video_raw"}`).
  3. Deterministic Core: If type is in `{"json", "text", "system_event", "document"}`:
     - JSON: `_parse_json` decodes string or validates dict keys.
     - Text: `_parse_text` measures character length, word count, line count.
     - System Event: `_parse_system_event` normalizes payload.
     - Document: `_parse_document_metadata` extracts references.
  4. Intelligence Layer: Ambiguous or unknown formats trigger `_process_with_llm()` via `_call_llm_json()`. If LLM is unavailable or unconfigured, falls back to raw dictionary wrapping with partial status.
  5. Proposes destination capability: `observation.record_event`.
- **Transaction & Error Handling:** Pure computational engine; does not directly hold database transactions.
- **Real vs Stub:** Real parsing logic. LLM integration is fully wired to `ILLMClient`.

#### 2. Observation Engine (`brain/src/brain/general/engines/observation.py`)
- **Purpose:** Background event capture, idempotent deduplication, and observation feed management.
- **Main Functions:**
  - `record_observation(observation_data, context)` (`observation.py:115`)
  - `list_observations(context, cursor, limit, filters)` (`observation.py:193`)
  - `handle_record_event(request: MeshRequest)` (`observation.py:230`)
- **Step-by-Step Logic:**
  1. Validates context and ensures `event_type` is present.
  2. Computes or receives `idempotency_key`. Calls `store.find_by_idempotency_key()`. If found, immediately returns duplicate status without re-inserting.
  3. `_normalize_event()` standardizes timestamp (ISO 8601 UTC), actor reference, metadata, and payload.
  4. Calls injected store: `await self._store.save(to_save)` (persists to `ring1_observations` in PostgreSQL).
  5. Follow-up Eligibility: Checks `_RECORD_ONLY_EVENT_TYPES` (`heartbeat`, `metric`, `log_entry`, `status_check`, `audit_entry`) -> False; `_FOLLOW_UP_EVENT_TYPES` (`document.uploaded`, `case.created`, etc.) -> True.
  6. Peer Delegation: If follow-up is eligible and `auto_delegate=True`, delegates to `planning.create_plan` via `_mesh_router`.
- **Transaction Handling:** Managed inside `SqlAlchemyObservationStore` with `session.commit()` and `session.rollback()` on exception.
- **Real vs Stub:** 100% genuine persistence and deduplication logic.

#### 3. Context Engine (`brain/src/brain/general/engines/context.py`)
- **Purpose:** Resolves and validates execution boundaries, detects ambiguities, and issues immutable `ContextRef` scopes.
- **Main Functions:**
  - `resolve_context(request_scope, context)` (`context.py:65`)
  - `handle_resolve_context(request: MeshRequest)` (`context.py:175`)
- **Step-by-Step Logic:**
  1. Asserts non-empty `organization_id` (fails closed).
  2. Resolves `domain_id` (defaults to `"general"` or requested domain), `case_id`, and `user_id`.
  3. Ambiguity Evaluation: Inspects hints dictionary. If contradictory hints or unmapped scopes are detected, marks status `ResolutionStatus.AMBIGUOUS` with detected ambiguities.
  4. Returns immutable `ContextRef` with resolution status (`EXPLICIT`, `DEFAULT`, `AMBIGUOUS`, or `INSUFFICIENT_DATA`).
- **Scope Isolation:** Enforced strictly in code (`context.organization_id` must match token).

#### 4. Basic Memory Engine (`brain/src/brain/general/engines/memory.py`)
- **Purpose:** Context-isolated persistence for knowledge candidates and validation lifecycle management.
- **Main Functions:**
  - `store_candidate(fact_data, context)` (`memory.py:104`)
  - `get_record(record_id, context)` (`memory.py:182`)
  - `validate_candidate(record_id, action, context)` (`memory.py:206`)
  - `handle_store_record(request: MeshRequest)` (`memory.py:268`)
  - `handle_get_record(request: MeshRequest)` (`memory.py:383`)
- **Step-by-Step Logic:**
  1. Candidate Lifecycle Invariant: All incoming records default to `status = "candidate"`.
  2. Direct validation during store is permitted **only** if `context.validation_authority == True`.
  3. Human Validation Gate: `validate_candidate()` verifies `context.validation_authority == True`. If False, raises `VALIDATION_AUTHORITY_REQUIRED`. The engine strictly forbids self-promotion by automated agents.
  4. Context Isolation on Read (`get_record`): Queries `SqlAlchemyMemoryStore.get_record()` filtering strictly by `organization_id` and `case_id`. If record belongs to another case or organization, returns sanitized `PERMISSION_DENIED` / 404 to eliminate existence oracles.
- **Transaction Handling:** `SqlAlchemyMemoryStore` executes `session.commit()` with `session.rollback()` on error.

#### 5. Basic Retrieval Engine (`brain/src/brain/general/engines/retrieval.py`)
- **Purpose:** Context-first candidate selection and keyword ranking.
- **Main Functions:**
  - `search(query, context, limit, filters)` (`retrieval.py:94`)
  - `handle_query(request: MeshRequest)` (`retrieval.py:162`)
- **Step-by-Step Logic:**
  1. Asserts non-empty `organization_id` and non-empty `case_id` (fails closed if case_id is omitted).
  2. Query Expansion (Intelligence Layer): If `semantic_expansion=True` and LLM client exists, generates query synonyms via `_expand_query()`.
  3. Candidate Selection & Filtering: Filters memory records in PostgreSQL strictly by `organization_id == context.org_id` and `case_id == context.case_id`.
  4. Candidate Knowledge Exclusion: Records with `status IN ('candidate', 'rejected')` are strictly excluded from normal retrieval unless `include_candidates=True` **and** caller has `validation_authority=True`.
  5. Lexical Ranking: `SqlAlchemyRetrievalStore` counts lowercase token occurrences in record JSON payloads, assigns a relevance score, and returns sorted results.
- **Critical Finding on Embeddings:**
  - **No vector embeddings are generated or used.** No OpenAI `text-embedding-3`, HuggingFace sentence-transformers, or Ollama embeddings are called. Retrieval is entirely lexical keyword counting.

#### 6. Planning Engine (`brain/src/brain/general/engines/planning.py`) & PlanStepExecutor
- **Purpose:** Advisory capability sequencing, prerequisite dependency enforcement, and evidence-based replanning.
- **Main Functions:**
  - `handle_create_plan(request: MeshRequest)` (`planning.py:168`)
  - `handle_request_replan(request: MeshRequest)` (`planning.py:290`)
  - `PlanStepExecutor.execute_step(step, ...)` (`app/ring1/execution/executor.py:54`)
- **Step-by-Step Logic:**
  1. Generates goal-oriented plan steps with typed input payloads and `depends_on` prerequisite declarations.
  2. `PlanStepExecutor` validates prerequisites: If a prior step failed, the current step is automatically marked `StepStatus.BLOCKED` with reason `PREREQUISITE_FAILED`.
  3. Upon step failure, `handle_request_replan` inspects actual execution `evidence`, marks superseded failed steps as `SKIPPED`, preserves completed steps, and appends recovery steps.
- **Ephemerality:** Plans are stored purely in-memory (`self._plans: dict[str, Plan]`). They are not persisted to PostgreSQL (conforming to ADR-008).

---

### 5.3 Auxiliary Infrastructure Services

#### TaskManager (`backend/app/core/task_manager.py`)
- Authoritative PostgreSQL task ledger for async worker tasks.
- Implements atomic creation of `Task` + `TaskOutbox` using `ON CONFLICT DO NOTHING`.
- Worker claims use `SELECT ... FOR UPDATE SKIP LOCKED` and increment `lease_generation`.
- `complete_task()` and `fail_task()` enforce monotonic generation fencing; any superseded worker attempting to write results raises `StaleWorkerLeaseError`.

#### OutboxDispatcher (`backend/app/core/outbox_dispatcher.py`)
- Implements the transactional outbox pattern to relay PostgreSQL task events to background brokers.
- Polls `task_outbox` for `PENDING` records, claims them using `dispatch_generation` and lease expiry, and invokes the configured message broker (in-memory or Redis).

#### ShortTermMemoryService (`backend/app/core/short_term_memory.py`)
- Provides fast temporary execution state caching scoped as `org:{org}:task:{task}:{key}` with TTL expiration.
- Connects to Redis if available; automatically falls back to a thread-safe in-memory dictionary if Redis is down or uninstalled.

#### PDF Ingestion Pipeline (`backend/app/ring1/services/pdf_pipeline_service.py` & `pdf/`)
- Ingests PDF bytes, validates `%PDF-` signature and 20MB limit.
- `PDFExtractor` reads page-by-page text.
- `StructuredKnowledgeExtractor` uses regexes to extract Egyptian Civil Law articles, dates, entities, and obligations with exact page provenance.
- Executes all 6 engines in a pipeline and saves results to `ring1_memory_records`.
- **Scope Violation:** Contains Egyptian Civil Law regex parsing (`المادة (\d+)`) which belongs to Ring 3 (Legal Domain), violating General Brain domain-independence.

---

### 5.4 Database Query & SQL Injection Review

- **Grep for raw SQL string formatting:** `git grep -rn "text(.*format\|text(.*%\|f\".*text(" -- backend/` returned **zero hits**.
- All SQL statements in `SqlAlchemyObservationStore`, `SqlAlchemyMemoryStore`, `SqlAlchemyRetrievalStore`, `TaskManager`, and `CaseService` use SQLAlchemy 2.0 type-safe expressions (`select()`, `query()`, `filter()`, `pg_insert()`).
- Only static literal defaults like `text("gen_random_uuid()")`, `text("'recorded'")`, and `text("SELECT 1")` are passed to `text()`.
- **Conclusion:** **Zero SQL injection risk detected.**

*In plain words:*
The internal business logic is solid and genuinely works without fake code. The memory engine strictly requires human approval before turning observations into trusted knowledge, but the system relies entirely on keyword searches instead of AI vector search, and contains Egyptian legal rules that shouldn't be in Ring 1.

<!-- SECTION 5 DONE -->


---

## S6 Security Review

### 6.1 Secrets, Credentials, and Configuration Hygiene

- **Tracked Files & Repository History:**
  - Active git tree contains zero unredacted live secret tokens or private keys (`.pem`, `.key`, `.env`).
  - `.env.example` in repo root contains safe dummy placeholder strings (`your-openai-api-key-here`, `change-this-to-a-secure-random...`).
  - Historical secret remediation: Earlier unpublished commits containing raw OpenRouter (`c9ae78f7`) and Gemini API keys (`docs/rings/ring1-master-comprehensive-report.md`) were rewritten and redacted in commits `278d898a` and `10d511c`.
- **SECRET_KEY Hardening:**
  - Defined in `backend/app/core/config.py:35`.
  - Pydantic field validator (`config.py:50-57`) strictly enforces `len(SECRET_KEY) >= 32` and rejects placeholder prefixes (`"change-this"`).
  - Used for HS256 JWT access token signing (`app/core/security.py:90`) and HMAC-SHA256 pagination cursor signatures (`app/core/cursor.py:59`).
- **Timing Attack Mitigation:**
  - In `backend/app/core/security.py:14, 55-64`, a precomputed dummy Argon2 hash (`_DUMMY_HASH`) is verified when an email is not found during login (`backend/app/api/v1/auth.py:56`). This ensures identical response timing regardless of whether an email exists in the database, preventing user enumeration.

---

### 6.2 Authentication & Authorization Compliance (D-012..D-014)

| Security Requirement | Settled Rule | Implementation Status | Evidence (File:Line) |
| :--- | :--- | :--- | :--- |
| **Password Hashing** | Argon2id via `argon2-cffi==25.1.0` directly; password length 12-128 chars | **COMPLIANT** | `app/core/security.py:11, 23-33`; `app/api/v1/users.py:19` (`min_length=12, max_length=128`) |
| **Token Algorithm** | Pinned to `HS256` | **COMPLIANT** | `app/core/security.py:90, 106` (`algorithm="HS256"`, `algorithms=["HS256"]`) |
| **Required Claims** | Strictly require `exp`, `iat`, `sub` | **COMPLIANT** | `app/core/security.py:107` (`options={"require": ["exp", "iat", "sub"]}`) |
| **Role Verification** | Role must be read from the DB row at call time, NEVER from the JWT token | **COMPLIANT** | `app/api/deps.py:141-147` (`require_admin` reads `current_user.role` from `User` DB model) |
| **Uniform 401s** | Identical 401 message for bad token, expired token, unknown user, wrong password | **COMPLIANT** | `app/api/deps.py:54-58, 79, 84, 90, 94` (`detail="Could not validate credentials"`); `app/api/v1/auth.py:33-36` (`detail="Invalid email or password"`) |

---

### 6.3 Critical Vulnerabilities & Security Gaps

#### 1. [CRITICAL] Authentication Bypass in Developer Operator Dependency
- **File & Line:** `backend/app/api/deps.py:150-177`
- **Code:**
  ```python
  def get_test_operator_user(
      credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
      db: Session = Depends(get_db),
  ) -> User | None:
      ...
      if settings.ENVIRONMENT.lower() != "production":
          return None
      raise _AUTH_401
  ```
- **Vulnerability:** When `ENVIRONMENT != "production"` (the default development and staging setting), any unauthenticated HTTP request is granted access with user `None`.
- **Impact:** Any attacker or unauthenticated client on the network can access:
  - `POST /api/v1/ring1/test-run` (execute arbitrary planning scenarios)
  - `POST /api/v1/ring1/upload-pdf` (upload files and persist records into PostgreSQL)
  - `GET /api/v1/ring1/knowledge` (query persisted case memory records)
  - `GET /api/v1/ring1/test-runs` (view execution traces and logs)

#### 2. [HIGH] Insecure Direct Object Reference (IDOR) & Scope Forgery in Ring 1 Endpoints
- **File & Line:** `backend/app/api/v1/ring1.py:144-145, 244-245`
- **Code:**
  ```python
  @router.post("/upload-pdf")
  async def upload_pdf(
      file: UploadFile = File(...),
      organization_id: str = Form(...),
      case_id: str = Form(...),
      ...
  ):
      clean_org_id = organization_id.strip()
      clean_case_id = case_id.strip()
  ```
- **Vulnerability:** Target `organization_id` and `case_id` are supplied directly by the client in HTTP Form/Query data instead of being authoritatively bound to a verified JWT session. Combined with the authentication bypass above, any unauthenticated client can inject data into or query data from **any arbitrary organization or case**.

#### 3. [MEDIUM] Denial of Service via Unbounded File Upload
- **File & Line:** `backend/app/api/v1/sources.py:54`
- **Code:**
  ```python
  content = await file.read()
  ```
- **Vulnerability:** The endpoint reads the entire uploaded file into server RAM without checking content length. A malicious or oversized file upload (e.g. 5 GB) will cause severe memory pressure or out-of-memory (OOM) crash of the Uvicorn process.
- **Mitigation:** Enforce a maximum file size check prior to reading (e.g. `await file.read(MAX_FILE_BYTES + 1)` as properly implemented in `app/api/v1/ring1.py:178`).

#### 4. [MEDIUM] Inactive User WebSocket Information Leak
- **File & Line:** `backend/app/api/v1/ws.py:46-63`
- **Vulnerability:** The WebSocket connection handler decodes the JWT token via `decode_access_token()`, but fails to query the PostgreSQL database to verify `user.is_active == True`. Deactivated or terminated employees with non-expired tokens can maintain or open WebSocket connections to monitor real-time observation event streams.

#### 5. [LOW] Internal Exception Message Leakage over SSE
- **File & Line:** `backend/app/api/v1/ring1.py:66, 209`
- **Code:**
  ```python
  err_payload = {"event_type": "error", "status": "failed", "error": str(exc)}
  yield f"data: {json.dumps(err_payload)}\n\n"
  ```
- **Vulnerability:** Unhandled exceptions during live test runs or PDF ingestion stream raw `str(exc)` error strings directly to the client over Server-Sent Events, potentially revealing database table names, paths, or connection parameters.

---

### 6.4 Dangerous Functions and Code Execution Check

- **`eval()` / `exec()`:** **Zero occurrences** in application codebase.
- **`subprocess` / `shell=True`:** **Zero occurrences** in backend production runtime. Subprocess is used exclusively in `tests/architecture/test_standalone_general_brain.py` to verify independent packaging in isolated virtual environments.
- **`pickle` / `yaml.load()`:** **Zero occurrences** in backend code.
- **SSRF (Server-Side Request Forgery):** Outgoing HTTP client requests in `ai/providers/base_openai.py` connect strictly to configured provider base URLs (`OPENAI_BASE_URL`, `DEEPSEEK_BASE_URL`, etc.) loaded from environment configuration. Client-supplied parameters do not control outgoing target URLs.

*In plain words:*
Password hashing and login security follow top-tier best practices, but the developer left a development bypass on the test endpoints that allows anyone to view or upload legal documents without logging in. The raw document upload endpoint also lacks a file size limit, which could crash the server if a giant file is uploaded.

<!-- SECTION 6 DONE -->


---

## S7 Tests

### 7.1 Test Suite Inventory and Categorization

The automated test suite contains **45 test files** with **269 automated test functions** across `backend/tests/` and `tests/architecture/`.

```text
Automated Test Breakdown:
├── backend/tests/ (Ring 0 & Foundation)       -> 17 files, 137 tests
├── backend/tests/ring1/ (Ring 1 Core & Mesh)  -> 23 files, 116 tests
└── tests/architecture/ (Standalone GB)        -> 5 files, 16 tests
Total backend & architecture test functions: 269
```

| Test File Path | Test Count | What It Proves | Evaluation & Quality |
| :--- | :--- | :--- | :--- |
| `backend/tests/test_ai_integration.py` | 17 | LLM provider integration, anonymous AI testing mode, prompt length validation. | High. Validates both authenticated and anonymous branches. |
| `backend/tests/test_api_v1_health.py` | 2 | `/health` and `/api/v1/health/db` endpoint availability. | Standard health check. |
| `backend/tests/test_api_v1_ring1.py` | 7 | Ring 1 Live Test API, SSE streaming, capability inventory. | High. Tests real SSE event streaming. |
| `backend/tests/test_auth.py` | 23 | User login, JWT generation, invalid token handling, timing attack mitigation. | Excellent. Verifies constant-time dummy password hashing. |
| `backend/tests/test_auth_rbac.py` | 6 | Role-based access control, admin vs employee restrictions on endpoints. | High. Verifies role fetched from DB, not token. |
| `backend/tests/test_db_isolation.py` | 1 | Verifies test database ends with `_test` and pgvector extension is installed. | Authoritative safety verification. |
| `backend/tests/test_errors.py` | 6 | Standard JSON error response envelopes (`{"error": {"code", "message"}}`). | High. |
| `backend/tests/test_groq.py` | **0** | Non-test script making live network requests to Groq API. | **Flawed**. Not a test file; makes live network requests. |
| `backend/tests/test_health.py` | 1 | Basic application health endpoint verification. | Standard. |
| `backend/tests/test_huggingface.py` | **0** | Non-test script making live network requests to Hugging Face API. | **Flawed**. Not a test file; makes live network requests. |
| `backend/tests/test_no_raw_db_in_tests.py` | 1 | AST meta-test asserting no test imports or creates raw `DATABASE_URL`. | Exceptional meta-test. Enforces AGENTS.md rule. |
| `backend/tests/test_safety_guard.py` | 6 | Unit tests for `assert_safe_test_database()` preventing dev DB corruption. | High. |
| `backend/tests/test_security.py` | 22 | Argon2id hashing parameters, JWT secret key validation, claim enforcement. | Comprehensive security suite. |
| `backend/tests/test_sources_endpoint.py` | 5 | Ingestion of raw files via `/api/v1/sources` and PostgreSQL registration. | High integration test. |
| `backend/tests/test_source_model.py` | 6 | Constraints, SHA-256 checksums, and foreign keys on `Source` model. | High ORM test. |
| `backend/tests/test_users.py` | 25 | Admin user creation, email normalization (`lower(email)`), role constraints. | High. |
| `backend/tests/test_user_model.py` | 7 | `User` SQLAlchemy model schema constraints. | High. |
| `backend/tests/ring1/test_concurrency.py` | 4 | Worker concurrency, lease expiry, Redis outbox crash recovery. | High. Exercises multi-worker race conditions. |
| `backend/tests/ring1/test_context.py` | 3 | Context resolution, domain mapping, scope constraints. | High. |
| `backend/tests/ring1/test_context_isolation.py` | 2 | Cross-case data isolation in memory and retrieval. | Core Ring 1 invariant proof. |
| `backend/tests/ring1/test_contracts.py` | 6 | Capability registry, envelope serialization, error code mappings. | Protocol verification. |
| `backend/tests/ring1/test_cursor_security.py` | 12 | HMAC cursor tampering, filter hash binding, RFC 4122 UUID validation. | Exceptional cryptographic test coverage. |
| `backend/tests/ring1/test_domain_independence.py` | 7 | Proves non-legal domains (Sales, Logistics) run without altering engines. | Key General Brain invariant proof. |
| `backend/tests/ring1/test_e2e_mesh_integration.py` | 1 | End-to-end integration scenario across all 6 engines cooperating peer-to-peer. | Realistic legal workflow proof. |
| `backend/tests/ring1/test_engine_restructuring.py`| 7 | Storage injection and pure protocol engine implementations. | High. |
| `backend/tests/ring1/test_general_brain_api.py` | 7 | Ring 1 API endpoints (`/brain/status`, `/observations`, `/context/resolve`). | High HTTP contract testing. |
| `backend/tests/ring1/test_handoff_policy.py` | 7 | Delegation depth limits, cycle detection, handoff permissions. | High runtime policy verification. |
| `backend/tests/ring1/test_memory.py` | 10 | Candidate lifecycle, human validation authority gate, context isolation. | Verifies knowledge candidate lifecycle. |
| `backend/tests/ring1/test_mesh_integration.py` | 8 | Engine-initiated autonomous peer delegations. | Verifies peer-to-peer mesh. |
| `backend/tests/ring1/test_observation.py` | 3 | Idempotency deduplication, normalization, follow-up event filtering. | High. |
| `backend/tests/ring1/test_outbox_dispatcher.py` | 8 | Transactional outbox polling, generation claims, lease recovery. | High reliability test. |
| `backend/tests/ring1/test_pdf_e2e_pipeline.py` | 6 | Full PDF pipeline: upload -> extract -> structure -> mesh -> PostgreSQL. | High. |
| `backend/tests/ring1/test_pdf_extractor.py` | 7 | Page-by-page PDF extraction, `%PDF-` signature check, encrypted rejection. | High input validation test. |
| `backend/tests/ring1/test_perception.py` | 5 | Deterministic parsing (JSON, text, system event) and unsupported types. | High. |
| `backend/tests/ring1/test_planning.py` | 5 | Plan step generation, causal blocking, in-memory ephemerality. | High. |
| `backend/tests/ring1/test_plan_executor.py` | 5 | Step execution through MeshRouter and causal prerequisite failure blocking. | High. |
| `backend/tests/ring1/test_retrieval.py` | 3 | Lexical candidate ranking, candidate exclusion, snippet generation. | High lexical test. |
| `backend/tests/ring1/test_security_isolation_adversarial.py`| 10 | Adversarial attacks attempting cross-case data leakage and ID spoofing. | Excellent security suite. |
| `backend/tests/ring1/test_short_term_memory.py` | 6 | Execution state caching, key scoping, TTL expiration, memory fallback. | High. |
| `backend/tests/ring1/test_task_manager.py` | 12 | Atomic task+outbox creation, `SKIP LOCKED` claims, monotonic generation fencing.| High database concurrency test. |
| `tests/architecture/test_compatibility_shims.py`| 3 | Verifies legacy `app/ring1` re-exports preserve exact class identity. | High architectural test. |
| `tests/architecture/test_domain_registry_lifecycle.py`| 7 | Lifecycle of domain extensions and registry lifecycle. | High. |
| `tests/architecture/test_import_isolation.py` | 2 | AST import scanner asserting `brain/` never imports `backend/` or `FastAPI`. | Architectural boundary proof. |
| `tests/architecture/test_standalone_general_brain.py`| 1 | Subprocess test running General Brain in clean isolated environment. | Packaging proof. |
| `tests/architecture/test_storage_injection.py` | 3 | Asserts omitting explicit store raises `StorageConfigurationError`. | Contract enforcement test. |

---

### 7.2 Test Execution Evidence & Status

- **Command Attempted:**
  `python -m pytest tests/ -q --no-header --tb=no`
- **Execution Result:** **UNVERIFIED (Environment Blocked)**.
  ```text
  C:\ProgramData\miniconda3\python.exe: No module named pytest
  ```
- **Analysis:** The active host Python environments lack the required dependencies. Per Rule 0, the auditor must not install packages or modify the host environment.
- **Missing Packages Required for Test Execution:**
  - `pytest==9.1.1`
  - `pytest-asyncio`
  - All dependencies pinned in `backend/requirements.txt` (FastAPI, SQLAlchemy, psycopg, pgvector, pydantic, argon2-cffi, pyjwt, pypdf).

---

### 7.3 Weak, Risky, and Flawed Tests

1. **Live Network Call Scripts in Test Directory:**
   - **Files:** `backend/tests/test_groq.py` and `backend/tests/test_huggingface.py`
   - **Flaw:** These files contain an `async def main()` function that creates an `AsyncOpenAI` client pointing to external cloud endpoints (`api.groq.com`, `router.huggingface.co`). If executed, they depend on live internet access, external cloud API uptime, and valid API keys in `.env`. They contain 0 assertions and 0 pytest test functions.
2. **Ephemeral Memory Restart Test:**
   - **File & Line:** `backend/tests/ring1/test_planning.py:120` (`test_planning_in_memory_ephemerality_restart_behavior`)
   - **Flaw:** Merely instantiates two separate `PlanningEngine()` instances and asserts the second instance has an empty dictionary. It does not test real server process restarts or concurrency.

---

### 7.4 Database Isolation Rule Compliance Check

- **Rule:** *"Tests must only use the test_engine and db_session fixtures. Never create an engine or connection from the development DATABASE_URL inside tests."*
- **Audit Findings:** **100% COMPLIANT**.
  - All 137 backend tests requiring database access strictly use the `db_session` fixture.
  - The fixture opens an isolated connection to `orgbrain_legal_test`, wraps the test in a transaction savepoint, and executes `transaction.rollback()` upon test teardown (`conftest.py:147`).
  - `backend/tests/test_no_raw_db_in_tests.py` runs an automated AST syntax walk across all test files to guarantee no test file imports `settings.DATABASE_URL` or calls `create_engine()` directly.

---

### 7.5 Missing Test Coverage

1. **Migration Downgrade Tests:** Zero tests verify `alembic downgrade -1` or `downgrade base` against the test database to prove schema reversibility.
2. **Deactivated User WebSocket Test:** No test verifies that a deactivated user (`user.is_active = False`) is rejected by the WebSocket `/api/v1/ws/observations` endpoint.
3. **Oversized Upload DoS Test:** No test asserts that uploading an excessively large document to `/api/v1/sources` is rejected before loading into memory.
4. **Vector Similarity / Distance Operator Tests:** Completely absent because vector columns and embeddings were omitted from Ring 1 implementation.

*In plain words:*
The test suite is extensive, well-structured, and strictly protects the development database from test data contamination. However, two test files are actually live scripts that try to call internet AI servers, and there are no tests for reversing database migrations or testing oversized file uploads.

<!-- SECTION 7 DONE -->


---

## S8 Ring 1 Compliance Matrix

### 8.1 Core Ring 1 Specification Compliance

| Requirement / Item | Built? | Where in Code (File:Line) | Evidence | Quality (0-5) | Identified Gap |
| :--- | :--- | :--- | :--- | :---: | :--- |
| **Perception Service** | **YES** | `brain/src/brain/general/engines/perception.py:46` | Parses text, JSON, system events, documents; rejects binaries; delegates ambiguous inputs to LLM. | 5/5 | None. Clean, protocol-decoupled implementation. |
| **Observation Service** | **YES** | `brain/src/brain/general/engines/observation.py:60` | Normalizes events, deduplicates via idempotency key, records to store, identifies follow-up events. | 5/5 | None. Fully wired to PostgreSQL store. |
| **Context Service** | **YES** | `brain/src/brain/general/engines/context.py:38` | Resolves tenant, domain, case, and user scopes; detects conflicting hints and ambiguities. | 5/5 | None. |
| **Basic Memory Service** | **YES** | `brain/src/brain/general/engines/memory.py:42` | Stores memory records with context scoping; manages candidate lifecycle; validates human authority. | 5/5 | None. Strictly preserves human validation authority. |
| **Basic Retrieval Service** | **PARTIAL** | `brain/src/brain/general/engines/retrieval.py:34` | Context-first candidate selection and keyword frequency ranking; excludes unvalidated candidates. | 3/5 | **No vector search.** Retrieval is purely in-memory lexical keyword frequency matching in JSON strings. |
| **DB: Observation Table** | **YES** | `backend/migrations/versions/f19a0a1b2c3d_create_ring1_tables.py:26` | `ring1_observations` table with idempotency unique constraint, JSONB payload/metadata, cursor index. | 5/5 | None. |
| **DB: Context Table** | **NO** | N/A | No dedicated context table exists in PostgreSQL. `ContextRef` is computed dynamically in memory. | 2/5 | Ring 1 spec required context tables; context is ephemeral. |
| **DB: Knowledge Table** | **YES** | `backend/migrations/versions/f19a0a1b2c3d_create_ring1_tables.py:101` | `ring1_memory_records` table with record_type, case_id, status, JSONB payload and metadata. | 4/5 | Missing explicit columns for `confidence`, `version`, and `conflict_state`. |
| **DB: Vector Indexes** | **NO** | `backend/migrations/versions/6dd2ff08b0bb_enable_pgvector_extension.py:23` | `vector` extension is enabled in PostgreSQL, but **zero vector columns or HNSW/IVFFlat indexes exist**. | 0/5 | Completely missing. Vector embeddings were frozen. |
| **Engine Unit Tests** | **YES** | `backend/tests/ring1/test_perception.py`, `test_observation.py`, etc. | 23 dedicated test files verifying deterministic parsing, deduplication, error envelopes. | 5/5 | None. |
| **Integration Tests** | **YES** | `backend/tests/ring1/test_e2e_mesh_integration.py:37` | Multi-engine scenario exercising Perception -> Observation -> Context -> Memory -> Retrieval. | 5/5 | None. |
| **Context Isolation Tests**| **YES** | `backend/tests/ring1/test_context_isolation.py:37` | Proves records stored in Case A cannot be retrieved or accessed when querying Case B. | 5/5 | Thorough adversarial coverage. |

---

### 8.2 The 9 Knowledge Object Metadata Fields

The Constitution and Ring 1 specifications mandate that every stored knowledge object maintain 9 specific metadata attributes:

| Mandatory Field | Supported? | Implementation Location | Evidence & Quality Analysis |
| :--- | :---: | :--- | :--- |
| **1. Source** | **YES** | `ring1_memory_records.source` (in metadata/payload); `ring1_observations.source` column | Fully tracked in observation table and memory record dictionaries. |
| **2. Timestamp** | **YES** | `ring1_memory_records.created_at` | Timezone-aware UTC timestamp generated server-side via `func.now()`. |
| **3. Actor** | **YES** | `ring1_memory_records.metadata['actor_ref']`; `ring1_observations.actor_ref` column | Authenticated user UUID or service identifier stored on write. |
| **4. Confidence** | **PARTIAL** | Stored inside JSONB metadata (`metadata['confidence']`) | Present in Python engine dictionary (`confidence: float = 0.9`), but lacks a dedicated SQL numeric column for indexing. |
| **5. Validation Status** | **YES** | `ring1_memory_records.status` column | Dedicated `VARCHAR(50)` column (`candidate`, `validated`, `rejected`). |
| **6. Scope** | **PARTIAL** | `ring1_memory_records.case_id`, `organization_id`, `context_ref` | Dedicated columns exist for case and organization, but no general/domain scope enum column. |
| **7. Provenance** | **PARTIAL** | `ring1_memory_records.source_observation_id` UUID column | Links back to the source observation UUID, but granular page/line provenance is dumped into unstructured JSONB. |
| **8. Version** | **NO** | Absent | **No version integer/string column** exists on `ring1_memory_records`. |
| **9. Conflict State** | **NO** | Absent | **No conflict state tracking** exists in the data model or memory engine. |

---

### 8.3 Invariants Compliance Check

- **Observation ≠ Knowledge:** **COMPLIANT**. Observations are persisted in `ring1_observations` via `ObservationEngine`. Knowledge records are stored in `ring1_memory_records` via `BasicMemoryEngine`. Observations do not become knowledge without explicit structuring.
- **Candidate ≠ Trusted:** **COMPLIANT**. Memory records enter with `status = "candidate"`. The `BasicRetrievalEngine` (`retrieval.py:53`) strictly excludes `candidate` and `rejected` records by default from ordinary search.
- **The Brain Cannot Self-Validate:** **COMPLIANT**. `BasicMemoryEngine.validate_candidate()` (`memory.py:223`) requires `context.validation_authority == True`. Automated engine calls or unauthorized users cannot promote candidates to validated status.
- **Case Isolation:** **COMPLIANT**. `BasicMemoryEngine.get_record()` and `BasicRetrievalEngine.search()` strictly filter by `case_id`. Cross-case queries return sanitized 404s.
- **Permissions Enforced Server-Side:** **PARTIAL**. Enforced server-side in all production dependencies (`get_brain_context`, `require_admin`), but violated by the developer bypass in `get_test_operator_user` (`deps.py:173`).
- **No Fake AI Behavior:** **COMPLIANT**. No hardcoded or faked AI outputs exist in production routes. The `FakeLLMProvider` is utilized strictly inside unit test fixtures.
- **No Domain Logic in General Brain Code:** **PARTIAL**. `brain/src/brain/general/` is domain-independent. However, `backend/app/ring1/pdf/structured.py` directly imports Egyptian Civil Law article regexes (`المادة (\d+)`) into the Ring 1 PDF ingestion pipeline.

---

### 8.4 Out-of-Scope and Decision Violations Inventory

The following components were built by the teammate that are explicitly **OUT OF SCOPE** for Ring 1 or violate project decisions:

1. **`cases` Table & Router (Ring 5 Scope Leakage):**
   - Migration `b39c4d5e6f7a` creates the `cases` table, and `backend/app/api/v1/cases.py` provides case CRUD endpoints. Cases belong to Ring 5 (Case Intelligence).
2. **`organization_id` Columns (D-004 Violation):**
   - D-004 establishes single-organization instances without tenant columns. The teammate added `organization_id` columns across `cases`, `sources`, `tasks`, `audit_events`, `ring1_observations`, and `ring1_memory_records`.
3. **Neo4j Container in `docker-compose.yml` (D-001/D-003 Violation):**
   - Added Neo4j Community container on ports 7474/7687, violating the non-negotiable stack rule (PostgreSQL only, no Neo4j).
4. **Planning Engine & PlanStepExecutor (6th Engine):**
   - Built a complete planning and replanning engine (`PlanningEngine`, `PlanStepExecutor`). Ring 1 specifies exactly 5 cognitive engines. (Teammate documented this under ADR-008 and D-016).
5. **Next.js 16 Frontend (Full Web Application):**
   - Replaced frontend stub with a massive Next.js TypeScript application. Frontend development was not part of the Ring 1 backend task.
6. **Egyptian Legal Extraction in PDF Pipeline (Ring 3 Scope Leakage):**
   - Regular expression extraction of Egyptian Civil Law articles (`المادة (\d+)`) belongs to Ring 3 (Legal Domain).
7. **Redis Integration in `short_term_memory.py` (D-009 Violation):**
   - D-009 prohibits choosing caching tools without prior approval. `ShortTermMemoryService` connects to Redis without approval.

*In plain words:*
The teammate delivered the core five services and enforced strict human validation before data becomes trusted knowledge. However, they completely omitted AI vector search, left out version and conflict fields, and pulled in features from later rings like full legal case management and Neo4j.

<!-- SECTION 8 DONE -->


---

## S9 Decisions and Invariants

### 9.1 Decisions Audit Table (D-001 .. D-015)

| Decision ID | Description & Settled Rule | Status | Concrete Evidence (File:Line) |
| :--- | :--- | :---: | :--- |
| **D-001** | **Backend Stack:** Python 3.12, FastAPI, PostgreSQL 17 + pgvector, SQLAlchemy 2.0 sync, Alembic, Pydantic v2, PyJWT, pytest. **No Node/Express/Prisma/Neo4j/asyncpg/Qdrant**. | **VIOLATED** | `docker-compose.yml:21-38` introduces `neo4j:5-community` container. `ai/package.json` contains Node/TypeScript dependencies. |
| **D-002** | **Constitution Overridden:** Constitution Node/Prisma/Express tool sections do not apply. Translate all tools to Python. | **OK** | All backend models and endpoints are 100% Python/FastAPI/SQLAlchemy. |
| **D-003** | **Relational DB Only:** Vectors live in PostgreSQL via pgvector; hierarchies via `parent_id`/`ltree`. Neo4j is NOT adopted for V1. | **VIOLATED** | `docker-compose.yml:21-38` adds Neo4j. In addition, pgvector vector columns and vector indexes were omitted. |
| **D-004** | **Single Organization Instance:** One organization per deployment. **NO organization_id or tenant columns**. | **VIOLATED** | `organization_id` columns added to `cases` (`b39c4d5e6f7a.py:35`), `sources` (`:65`), `tasks` (`a28b3c4d5e6f.py:33`), `audit_events` (`:122`), `ring1_observations` (`f19a0a1b2c3d.py:39`), `ring1_memory_records` (`:111`), and `config.py:39`. |
| **D-005** | **V1 Roles:** Only `admin` and `employee`. Permissions enforced server-side. | **OK** | `app/models/user.py:47` enforces `CHECK (role IN ('admin', 'employee'))`. |
| **D-006** | **Domain Model:** Client -> Case -> Conversation. Domain: Egyptian Civil Law. WhatsApp primary channel. | **OK** | No WhatsApp or client tables added in Ring 1 backend (deferred to proper rings). |
| **D-007** | **Infrastructure Conventions:** `pgvector/pgvector:pg17` on port 5432; Alembic only (never `create_all`); secrets in root `.env`. | **PARTIAL** | Port changed to `5433` in `docker-compose.yml:11` and `config.py:27`. Alembic-only rule is 100% compliant (0 `create_all()` calls). |
| **D-008** | **Working Method:** Plan first; one small task per turn; test evidence shown. | **VIOLATED** | Teammate delivered a monolithic 541-file pull request combining frontend, AI, PDF processing, tasks, and data engineering in one batch. |
| **D-009** | **Python Tooling Choices Not Decided:** No Redis, Celery, Casbin, Socket.io without prior approval and ADR. | **VIOLATED** | `backend/app/core/short_term_memory.py:3, 49` silently integrates `Redis` (`redis://localhost:6379/0`). |
| **D-010** | **Ring Numbering:** Official numbering: 0 Foundation, 1 Brain Core, 2 Knowledge, etc. | **OK** | Consistently respected across docs and ring specifications. |
| **D-011** | **Backend Ownership:** Karim owns backend decisions. | **VIOLATED** | Teammate unilaterally introduced Neo4j, planning engines, and tenant columns contrary to settled backend decisions. |
| **D-012** | **Password Hashing & Tokens:** Argon2id (`argon2-cffi==25.1.0`), HS256 JWT, sub/iat/exp only, password length 12-128. | **OK** | Fully implemented in `app/core/security.py:11, 23, 90, 106` and `app/api/v1/users.py:19`. *(Note: Teammate duplicated "D-012" ID in `decisions.md:86`)*. |
| **D-013** | **AI Engine Python Rebuild:** Multi-provider registry in Python 3.12. | **OK** | Fully implemented in `ai/providers/registry.py` and `ai/core/services/llm_service.py`. |
| **D-014** | **Security Hardening:** Role read from DB row at call time, uniform 401 messages, timing attack mitigation. | **OK** | `app/api/deps.py:141-147`, `app/api/v1/auth.py:33-36, 55-58`. |
| **D-015** | **Autonomy Levels 0-3:** Observe, Assist, Execute with approval, Authorized automation. | **OK** | Enforced via human validation authority gate in `BasicMemoryEngine.validate_candidate()`. *(Note: Teammate assigned duplicate ID "D-015" to Neo4j in `decisions.md:72`)*. |

---

### 9.2 Core Invariants Evaluation

1. **Observation ≠ Knowledge:** **OK**. Implemented across distinct database tables (`ring1_observations` vs `ring1_memory_records`) and distinct cognitive engines (`ObservationEngine` vs `BasicMemoryEngine`).
2. **Candidate ≠ Trusted:** **OK**. `BasicRetrievalEngine` (`retrieval.py:53`) excludes records with status `candidate` and `rejected` from standard retrieval by default.
3. **The Brain Cannot Self-Validate:** **OK**. `BasicMemoryEngine.validate_candidate()` (`memory.py:223`) asserts `context.validation_authority == True`. Automated engine calls cannot self-promote candidate knowledge.
4. **Case Isolation:** **OK**. `BasicMemoryEngine.get_record()` and `BasicRetrievalEngine.search()` strictly filter by `case_id`.
5. **Permissions Enforced Server-Side:** **VIOLATED**. Bypassed on developer operator endpoints in development mode (`app/api/deps.py:173`).
6. **Permission-Aware Retrieval:** **OK**. Unvalidated candidates are hidden from retrieval unless caller holds validation authority.
7. **No Fake AI Behavior:** **OK**. Production routes do not simulate or hardcode fake AI outputs.
8. **No Domain Logic inside General Brain Code:** **VIOLATED**. `backend/app/ring1/pdf/structured.py` pulls Egyptian Civil Law article regex parsing into the Ring 1 PDF ingestion pipeline.

*In plain words:*
The core security rules for passwords and tokens are respected, and the brain cannot validate its own thoughts. However, the teammate violated five major decisions: they added Neo4j, added Redis, added multi-tenant organization columns, changed the database port, and bundled huge unrelated changes into a single pull request.

<!-- SECTION 9 DONE -->


---

## S10 Docs Accuracy

### 10.1 Documentation Claims vs Code Implementation Matrix

| Document | Claimed Milestone / Feature | Verified in Code? | Evidence (File:Line) | Discrepancy / Truth Assessment |
| :--- | :--- | :---: | :--- | :--- |
| `docs/progress.md` | "Standalone Package brain-co-core==0.1.0 under brain/src/brain/" | **VERIFIED** | `brain/pyproject.toml:1-30`, `brain/src/brain/general/` | Accurate. Standalone package structure was physically built. |
| `docs/progress.md` | "Automated Test Baseline: 347/347 tests passing (100% pass rate)" | **UNVERIFIED** | Missing packages in host Python (`pytest==9.1.1`). | Claim reflects teammate's Linux/WSL test run, but cannot be reproduced in active Windows host environment without installing packages. |
| `docs/progress.md` | "Vector Freeze maintained pending written AI/Data Science sign-off" | **VERIFIED** | `backend/migrations/versions/f19a0a1b2c3d_create_ring1_tables.py` | Accurate. pgvector was enabled, but vector columns were intentionally frozen/deferred. |
| `docs/progress.md` | "Five Core Engines & Protocols with advisory PlanningEngine (ADR-008)" | **VERIFIED** | `brain/src/brain/general/engines/` | Accurate in code; however, Planning is out-of-scope for Ring 1 specification. |
| `docs/progress.md` | "Moved all backend documentation into docs/backend/" | **VERIFIED** | Files reside in `docs/backend/` | Accurate. Root docs moved to `docs/backend/`. |
| `docs/backend/architecture.md` | "backend/.venv/: Isolated Python 3.12 virtual environment" | **DISCREPANCY** | `backend/.venv/` directory is absent on disk | The teammate documented their local virtualenv path (`.venv312`), but it is not committed (as per rules). Host environment lacks packages. |
| `docs/backend/decisions.md` | "D-015 — Neo4j Graph Database Container Added (2026-10-12)" | **VERIFIED** | `docker-compose.yml:21-38` | Accurate claim, but represents a direct violation of D-001/D-003. Also duplicate number "D-015". |
| `docs/backend/decisions.md` | "D-012 Ring 1 Architecture, Execution Foundation & Engine Decoupling" | **VERIFIED** | `docs/backend/decisions.md:86` | Accurate in content, but reuses existing decision number "D-012" (password hashing). |
| `docs/journal/2026-10-31.md` | "Ran complete 347-test suite... in 19.61s" | **UNVERIFIED** | Commands logged show Linux shell (`ss -tulpn`, `/tmp/brain_dist_verify`) | Teammate executed verification inside a Linux/WSL container; commands cannot be re-executed in native Windows host environment without setup. |

---

### 10.2 Progress and Journal Integrity Evaluation

1. **Does `progress.md` tell the truth?**
   - **Largely Yes, but with significant omissions:**
   - What it states happened (package extraction, AST architecture tests, HMAC cursor security, outbox dispatcher, PDF pipeline) did indeed happen and matches the codebase.
   - However, `progress.md` completely omits mention of:
     - The critical authentication bypass in `get_test_operator_user` (`deps.py:173`).
     - The addition of `organization_id` columns across all tables in violation of D-004.
     - The introduction of a full `cases` table in violation of Ring 1 scope.
     - The silent adoption of `Redis` in `short_term_memory.py` without approval.
2. **Do journals contain honest "Problems Encountered"?**
   - **No.** The daily journal entries (`docs/journal/2026-10-30.md`, `2026-10-31.md`) present clean "Summary of Actions" and tables of passing commands. They omit reporting architectural friction, decision conflicts, or security compromises introduced during implementation.

*In plain words:*
The documentation is impressively detailed and accurately describes the files and code that were created. However, it glosses over the rule violations, ignores the security bypass on the test endpoints, and re-used old decision numbers causing confusion.

<!-- SECTION 10 DONE -->


---

## S11 Findings Register

### Summary by Severity
- **P0 (Critical / Decision Breach / Security Hole):** 5 findings (`F-001` .. `F-005`)
- **P1 (High / Bug / Missing Required Feature):** 5 findings (`F-006` .. `F-010`)
- **P2 (Medium / Maintainability / Quality Gap):** 5 findings (`F-011` .. `F-015`)
- **P3 (Low / Nice to Have / Minor Hygiene):** 2 findings (`F-016` .. `F-017`)
- **Total Findings:** **17 findings**

---

### Detailed Findings (Sorted by Severity)

#### F-001 [P0] Authentication Bypass in Developer Operator Dependency
- **Area:** Security / Authentication
- **File & Line:** `backend/app/api/deps.py:150-177`
- **Evidence:**
  ```python
  if settings.ENVIRONMENT.lower() != "production":
      return None
  raise _AUTH_401
  ```
- **In plain words:** The backend lets anyone execute test runs and upload or view legal documents without logging in when running in development mode. This leaves the door completely open to unauthenticated network access.
- **Why it matters:** Critical security hole that permits unauthenticated callers to execute Ring 1 test runs, stream traces, upload files, and query case knowledge.
- **Proposed Fix:** Remove the bypass. Enforce `current_user: User = Depends(get_current_user)` or `require_admin` across all environments.
- **Effort:** Small (< 1h)
- **Risk of Fix:** Low
- **Test to Add:** `test_operator_endpoint_rejects_unauthenticated_in_development_env`
- **Assignee:** Teammate who wrote it.

---

#### F-002 [P0] Insecure Direct Object Reference (IDOR) & Scope Forgery in Ring 1 Endpoints
- **Area:** Security / Scope Isolation
- **File & Line:** `backend/app/api/v1/ring1.py:144-145, 244-245`
- **Evidence:**
  ```python
  clean_org_id = organization_id.strip()
  clean_case_id = case_id.strip()
  ```
- **In plain words:** The Ring 1 test and PDF upload endpoints trust whatever organization and case ID the client sends in the form data. Anyone can read or inject documents into other clients' cases.
- **Why it matters:** Violates the core case isolation invariant; callers can spoof `organization_id` and `case_id` to read or write data across arbitrary boundaries.
- **Proposed Fix:** Wire `upload_pdf` and `get_case_knowledge` to `context: BrainContext = Depends(get_brain_context)`, deriving `organization_id` strictly from verified server-side JWT claims.
- **Effort:** Small (< 1h)
- **Risk of Fix:** Low
- **Test to Add:** `test_ring1_upload_pdf_cross_org_spoofing_rejected`
- **Assignee:** Teammate who wrote it.

---

#### F-003 [P0] Banned Technology (Neo4j) Container Added to Docker Compose
- **Area:** Infrastructure / Technology Stack
- **File & Line:** `docker-compose.yml:21-38`, `docs/backend/decisions.md:72`
- **Evidence:**
  ```yaml
  neo4j:
    image: neo4j:5-community
    container_name: orgbrain-neo4j
  ```
- **In plain words:** The teammate added a Neo4j graph database container to the project configuration even though project rules strictly forbid Neo4j.
- **Why it matters:** Directly violates the non-negotiable stack rule in `AGENTS.md` and decisions D-001 and D-003 ("PostgreSQL only... do NOT use Neo4j").
- **Proposed Fix:** Delete the `neo4j` service and `neo4j_data` volume from `docker-compose.yml`. Remove the duplicate decision D-015 in `decisions.md`.
- **Effort:** Small (< 1h)
- **Risk of Fix:** Low
- **Test to Add:** Automated compose scanner verifying only approved images run.
- **Assignee:** Karim.

---

#### F-004 [P0] Decision Violation: Multi-Tenant `organization_id` Columns Added Everywhere
- **Area:** Data Model / Architecture Decisions
- **File & Line:** `backend/migrations/versions/b39c4d5e6f7a.py:35, 65`, `a28b3c4d5e6f.py:33, 122`, `f19a0a1b2c3d.py:39, 111`, `app/core/config.py:39`
- **Evidence:**
  ```python
  sa.Column("organization_id", sa.String(length=255), nullable=False)
  ```
- **In plain words:** The teammate added an organization ID column across all database tables, violating the rule that each deployment serves only one organization.
- **Why it matters:** Violates decision D-004 (*"One organization per deployment = NO organization_id/tenant columns"*).
- **Proposed Fix:** Reconcile with Karim: either approve single-org deployment with tenant columns for future SaaS multi-tenancy, or generate an Alembic migration to drop `organization_id` columns and clean up models.
- **Effort:** Medium (< 1/2 day)
- **Risk of Fix:** Medium (affects query filters and Pydantic schemas).
- **Test to Add:** Database column assertion test verifying schema matches architectural decision.
- **Assignee:** Karim (architectural owner).

---

#### F-005 [P0] Scope Leakage: Legal `cases` Table & API Implemented in Ring 1
- **Area:** Architecture / Ring Boundaries
- **File & Line:** `backend/migrations/versions/b39c4d5e6f7a.py:23-62`, `backend/app/models/case.py:27`, `backend/app/api/v1/cases.py:53-329`
- **Evidence:**
  ```python
  op.create_table("cases", sa.Column("id", UUID, primary_key=True)...)
  ```
- **In plain words:** A full legal case management system was built in Ring 1, even though case tables belong to Ring 5.
- **Why it matters:** Direct scope leakage; Ring 1 is General Brain Core only. Case tables belong strictly to Ring 5 ("Case Intelligence").
- **Proposed Fix:** Isolate `cases.py` router or document an explicit exception that Case tables were brought forward to support realistic case-isolated integration testing.
- **Effort:** Medium (< 1/2 day)
- **Risk of Fix:** Medium
- **Test to Add:** Architecture test verifying Ring 1 engines do not depend on `Case` model.
- **Assignee:** Karim / Teammate.

---

#### F-006 [P1] Missing Vector Embeddings and pgvector Vector Indexes
- **Area:** Data Model / Search Capabilities
- **File & Line:** `backend/migrations/versions/f19a0a1b2c3d.py`, `backend/app/infrastructure/database/stores.py:363-388`
- **Evidence:** Zero `Vector` column types in models; `SqlAlchemyRetrievalStore.search_records()` performs lowercase substring matching in JSON strings (`matches = sum(1 for t in tokens if t in text_repr)`).
- **In plain words:** The system does not actually use AI vector embeddings or pgvector search. It simply counts word matches inside JSON text in memory.
- **Why it matters:** Fails a primary Ring 1 deliverable: vector indexes in PostgreSQL. Limits retrieval to exact substring lexical matches.
- **Proposed Fix:** Add vector column `embedding = mapped_column(Vector(1536))` to `ring1_memory_records`, create HNSW index in an Alembic migration, and wire embedding generation into `BasicRetrievalEngine`.
- **Effort:** Large (> 1/2 day)
- **Risk of Fix:** Medium (requires choosing and pinning an embedding provider).
- **Test to Add:** `test_pgvector_hnsw_similarity_query`
- **Assignee:** Teammate who wrote it.

---

#### F-007 [P1] Event Loop Blocking Calls Inside `async def` Route Handlers & Stores
- **Area:** Concurrency / Performance
- **File & Line:** `backend/app/api/v1/observations.py:38, 50, 108`, `backend/app/infrastructure/database/stores.py:44, 100, 149, 245, 361`
- **Evidence:** Synchronous blocking calls `db.commit()` and `session.execute(stmt).scalars().all()` executed directly inside `async def` route handlers and store methods.
- **In plain words:** Synchronous database operations are running directly on the main asynchronous event loop. This can freeze the entire web server whenever someone saves or searches data.
- **Why it matters:** Freezes the asyncio event loop, causing severe latency degradation and dropping real-time WebSocket connections under concurrent load.
- **Proposed Fix:** Convert route handlers to standard synchronous `def` (allowing FastAPI to run them in AnyIO threadpool) or wrap synchronous store calls with `await anyio.to_thread.run_sync()`.
- **Effort:** Medium (< 1/2 day)
- **Risk of Fix:** Low
- **Test to Add:** Async concurrency test verifying WebSocket ping-pong responsiveness during concurrent database transactions.
- **Assignee:** Teammate who wrote it.

---

#### F-008 [P1] Unbounded File Upload Memory Exhaustion (DoS) in `/sources`
- **Area:** Security / Input Validation
- **File & Line:** `backend/app/api/v1/sources.py:54`
- **Evidence:**
  ```python
  content = await file.read()
  ```
- **In plain words:** The document upload endpoint reads uploaded files into memory with no size limit, which could crash the server if a giant file is uploaded.
- **Why it matters:** Severe Denial of Service (DoS) vulnerability; uploading a multi-gigabyte file will trigger an out-of-memory crash.
- **Proposed Fix:** Pass a bounded byte limit: `content = await file.read(MAX_SOURCE_SIZE_BYTES + 1)` and return HTTP 413 if exceeded.
- **Effort:** Small (< 1h)
- **Risk of Fix:** Low
- **Test to Add:** `test_ingest_source_oversized_payload_returns_413`
- **Assignee:** Teammate who wrote it.

---

#### F-009 [P1] Missing Knowledge Metadata Fields (`version`, `conflict_state`)
- **Area:** Data Model / Knowledge Integrity
- **File & Line:** `backend/app/ring1/models/observation.py:98-152`, `backend/migrations/versions/f19a0a1b2c3d.py:101-137`
- **Evidence:** `version` and `conflict_state` columns are absent from `ring1_memory_records`.
- **In plain words:** Knowledge records are missing mandatory tracking fields for version number and conflict status.
- **Why it matters:** Violates the mandatory knowledge metadata specification; knowledge evolution and conflicting facts cannot be tracked.
- **Proposed Fix:** Generate an Alembic migration adding `version INT NOT NULL DEFAULT 1` and `conflict_state VARCHAR(50) NOT NULL DEFAULT 'clean'` to `ring1_memory_records`.
- **Effort:** Small (< 1h)
- **Risk of Fix:** Low
- **Test to Add:** `test_memory_records_track_version_and_conflict_state`
- **Assignee:** Teammate who wrote it.

---

#### F-010 [P1] Inactive User WebSocket Information Leak
- **Area:** Security / WebSockets
- **File & Line:** `backend/app/api/v1/ws.py:46-63`
- **Evidence:** Token is decoded via `decode_access_token()`, but no database check is performed to verify `user.is_active == True`.
- **In plain words:** A deactivated employee can keep listening to real-time office events over WebSockets as long as their token has not expired.
- **Why it matters:** Information disclosure to terminated or deactivated employee accounts.
- **Proposed Fix:** Open database session in WebSocket dependency and verify `user = db.get(User, user_id)` and `user.is_active` before accepting connection.
- **Effort:** Small (< 1h)
- **Risk of Fix:** Low
- **Test to Add:** `test_websocket_rejects_inactive_user`
- **Assignee:** Teammate who wrote it.

---

#### F-011 [P2] Silent Tool Adoption: Redis in `short_term_memory.py`
- **Area:** Architecture / Dependencies
- **File & Line:** `backend/app/core/short_term_memory.py:3, 49`
- **Evidence:**
  ```python
  redis_client = redis.Redis.from_url(redis_url, decode_responses=True)
  ```
- **In plain words:** Redis was introduced for temporary memory caching without getting prior approval or documenting an architectural decision.
- **Why it matters:** Violates decision D-009 (*"Python replacements for Node-era tooling are NOT decided... no silent picks"*).
- **Proposed Fix:** Submit ADR to Karim for Redis approval or remove Redis client and rely on PostgreSQL / in-memory cache.
- **Effort:** Small (< 1h)
- **Risk of Fix:** Low
- **Assignee:** Karim / Teammate.

---

#### F-012 [P2] Non-Pytest Live Network Call Scripts in `backend/tests/`
- **Area:** Testing / Hygiene
- **File & Line:** `backend/tests/test_groq.py:1-53`, `backend/tests/test_huggingface.py:1-53`
- **Evidence:** Scripts containing `async def main()` with zero assertions that call external cloud APIs.
- **In plain words:** Two files inside the tests folder are not real automated tests; they are manual scripts that try to reach internet AI services.
- **Why it matters:** Pollutes test directory; breaks automated offline testing pipelines.
- **Proposed Fix:** Move them to a `scripts/` directory or rewrite them into mock-based unit tests.
- **Effort:** Small (< 1h)
- **Risk of Fix:** Low
- **Assignee:** Teammate who wrote it.

---

#### F-013 [P2] Domain-Specific Legal Extraction in Ring 1 PDF Pipeline
- **Area:** Domain Decoupling
- **File & Line:** `backend/app/ring1/pdf/structured.py:17`, `backend/app/domains/legal/extractor.py:27`
- **Evidence:** `StructuredKnowledgeExtractor` invokes `LegalStructuredKnowledgeExtractor` to parse Egyptian Civil Law articles (`المادة (\d+)`).
- **In plain words:** The Ring 1 document reader contains specific Egyptian law parsing code that belongs only in Ring 3.
- **Why it matters:** Violates the invariant that General Brain code must not contain domain-specific logic.
- **Proposed Fix:** Move legal parsing into `brain/extensions/legal/` and call it via registered extension hooks.
- **Effort:** Medium (< 1/2 day)
- **Risk of Fix:** Low
- **Assignee:** Teammate who wrote it.

---

#### F-014 [P2] Duplicate Decision Numbering in `decisions.md`
- **Area:** Documentation / Governance
- **File & Line:** `docs/backend/decisions.md:72, 86`
- **Evidence:** Duplicate `D-012` (Password hashing vs Ring 1 Architecture) and duplicate `D-015` (Autonomy levels vs Neo4j).
- **In plain words:** The documentation re-uses the same decision numbers for two completely different decisions, causing confusion.
- **Why it matters:** Breaks traceability and governance.
- **Proposed Fix:** Renumber Ring 1 architecture decision to `D-016` (or next free ID) and renumber Neo4j entry.
- **Effort:** Small (< 1h)
- **Risk of Fix:** Zero
- **Assignee:** Karim.

---

#### F-015 [P2] Missing API Rate Limiting and Standard Security Headers
- **Area:** Security / Operational Hardening
- **File & Line:** `backend/app/main.py:8-20`
- **Evidence:** No rate limiter middleware on `/auth/login` or `/ai/prompt`. No security headers middleware.
- **In plain words:** The API server does not limit how fast someone can try guessing passwords, and does not send standard browser security headers.
- **Why it matters:** Leaves authentication vulnerable to brute force and credential stuffing.
- **Proposed Fix:** Add `slowapi` rate limiting and a security headers middleware.
- **Effort:** Medium (< 1/2 day)
- **Risk of Fix:** Low
- **Assignee:** Either.

---

#### F-016 [P3] Unused Heavy Dependency `reportlab` in `requirements.txt`
- **Area:** Dependencies / Build Hygiene
- **File & Line:** `backend/requirements.txt:38`
- **Evidence:** `reportlab==5.1.0` pinned, but zero backend routes or services generate PDF documents.
- **In plain words:** A heavy PDF creation library is included in requirements.txt even though the backend never creates PDFs.
- **Why it matters:** Unnecessary package bloat.
- **Proposed Fix:** Remove `reportlab` from `backend/requirements.txt`.
- **Effort:** Small (< 1h)
- **Risk of Fix:** Zero
- **Assignee:** Either.

---

#### F-017 [P3] Large Binary PDFs Committed to Git Tree
- **Area:** Repository Hygiene
- **File & Line:** `docs/project-specifications/` (1.68 MB and 18.91 MB PDF files)
- **Evidence:** Binary files tracked in git repository.
- **In plain words:** Two large PDF documents (one is nearly 19 megabytes) are stored directly in git, making repository downloads slower.
- **Why it matters:** Bloats repository clone times for all contributors.
- **Proposed Fix:** Track binary documentation assets via Git LFS or move them to external documentation storage.
- **Effort:** Small (< 1h)
- **Risk of Fix:** Low
- **Assignee:** Karim.

*In plain words:*
We identified 17 clear findings: 5 critical issues (including a wide-open developer backdoor and forbidden Neo4j container), 5 high-priority issues (including missing AI vector search and server-freezing database calls), and 7 maintenance and cleanup items.

<!-- SECTION 11 DONE -->


---

## S12 Fix Plan

### 12.1 Remediation Batches

The 17 findings are grouped into **4 sequential, dependency-ordered batches**. Each batch is scoped for execution in a single agent session.

```text
Remediation Roadmap:
├── Batch 1: Immediate Security & Access Control Remediation   (P0/P1 Security)
├── Batch 2: Stack Boundaries & Configuration Hygiene          (P0/P2 Infrastructure & Governance)
├── Batch 3: Concurrency & Event Loop Optimization             (P1 Performance)
└── Batch 4: Data Model Alignment & Vector Search              (P0/P1 Data Model & Scope)
```

---

#### Batch 1: Immediate Security & Access Control Remediation
- **Primary Goal:** Eliminate the unauthenticated developer operator backdoor, prevent IDOR cross-case spoofing, enforce upload memory caps, and verify user status on WebSockets.
- **Findings Addressed:** `F-001`, `F-002`, `F-008`, `F-010`.
- **Files Touched:**
  - `backend/app/api/deps.py` (remove development environment bypass in `get_test_operator_user`)
  - `backend/app/api/v1/ring1.py` (bind `upload_pdf` and `knowledge` strictly to `BrainContext` token claims)
  - `backend/app/api/v1/sources.py` (enforce bounded byte read with HTTP 413 check)
  - `backend/app/api/v1/ws.py` (verify `user.is_active` in database before establishing WebSocket)
- **Tests to Add:**
  - `test_operator_endpoint_rejects_unauthenticated_in_dev`
  - `test_ring1_upload_pdf_cross_org_spoofing_rejected`
  - `test_ingest_source_oversized_payload_returns_413`
  - `test_websocket_rejects_inactive_user`
- **Estimated Effort:** ~2 to 3 hours (Small / Medium).
- **Parallelism Safety:** High. Touches only endpoint route handlers and dependencies; zero conflict with database migrations or core engine logic.
- **Acceptance Verification Check:**
  ```bash
  # 1. Unauthenticated request to /ring1/test-run must return HTTP 401:
  curl -i -X POST http://localhost:8000/api/v1/ring1/test-run \
       -H "Content-Type: application/json" -d '{"mode":"e2e"}'
  # Expected output: HTTP/1.1 401 Unauthorized

  # 2. Oversized upload must return HTTP 413:
  curl -i -X POST http://localhost:8000/api/v1/sources \
       -H "Authorization: Bearer <valid_token>" -F "file=@oversized_test_file.bin"
  # Expected output: HTTP/1.1 413 Request Entity Too Large
  ```

---

#### Batch 2: Stack Boundaries & Configuration Hygiene
- **Primary Goal:** Purge banned container dependencies, align documentation decisions, and remove ad-hoc scripts from test directories.
- **Findings Addressed:** `F-003`, `F-011`, `F-012`, `F-014`, `F-016`, `F-017`.
- **Files Touched:**
  - `docker-compose.yml` (remove `neo4j` service and `neo4j_data` volume)
  - `docs/backend/decisions.md` (remove duplicate Neo4j D-015; renumber Ring 1 architecture to D-016)
  - `backend/requirements.txt` (remove unused `reportlab==5.1.0`)
  - `backend/tests/test_groq.py` & `test_huggingface.py` (relocate to `scripts/scratch/` outside test runner)
  - Root `test_*.py` scripts (move to `scripts/dev/`)
- **Tests to Add:**
  - Static automated test asserting `docker-compose.yml` contains only approved services (Postgres).
- **Estimated Effort:** ~2 hours (Small).
- **Parallelism Safety:** High. Completely decoupled from application code.
- **Acceptance Verification Check:**
  ```bash
  docker compose config --services
  # Expected output:
  # postgres
  # (neo4j must NOT appear)

  git grep -rn "reportlab" backend/app/
  # Expected output: 0 hits
  ```

---

#### Batch 3: Concurrency & Event Loop Optimization
- **Primary Goal:** Prevent main event loop blocking by converting blocking synchronous database calls inside `async def` functions to threadpool execution.
- **Findings Addressed:** `F-007`.
- **Files Touched:**
  - `backend/app/api/v1/observations.py`
  - `backend/app/infrastructure/database/stores.py`
- **Tests to Add:**
  - Concurrency load test measuring WebSocket broadcast latency during simultaneous database commits.
- **Estimated Effort:** ~3 to 4 hours (Medium).
- **Parallelism Safety:** Medium. Coordinate with teammates touching `stores.py`.
- **Acceptance Verification Check:**
  ```bash
  pytest backend/tests/ring1/test_concurrency.py -q
  # Expected: All concurrency tests pass without thread contention
  ```

---

#### Batch 4: Data Model Alignment & Vector Search Implementation
- **Primary Goal:** Implement pgvector similarity search in PostgreSQL, reconcile `organization_id` multi-tenancy columns, add missing knowledge metadata fields (`version`, `conflict_state`), and decouple domain logic from PDF ingestion.
- **Findings Addressed:** `F-004`, `F-005`, `F-006`, `F-009`, `F-013`.
- **Files Touched:**
  - `backend/migrations/versions/` (new Alembic migration adding `embedding` Vector column, HNSW index, `version`, `conflict_state`)
  - `backend/app/ring1/models/observation.py`
  - `backend/app/infrastructure/database/stores.py` (implement cosine distance search via `<=>` operator)
  - `brain/src/brain/general/engines/retrieval.py`
  - `backend/app/ring1/pdf/structured.py`
- **Tests to Add:**
  - `test_pgvector_hnsw_similarity_query`
  - `test_memory_records_track_version_and_conflict_state`
  - `test_general_brain_pdf_pipeline_domain_decoupling`
- **Estimated Effort:** ~1 day (Large).
- **Parallelism Safety:** Requires locking migrations; must be coordinated with Karim.
- **Acceptance Verification Check:**
  ```bash
  alembic upgrade head
  pytest backend/tests/ring1/test_retrieval.py -q
  # Expected: Vector similarity search returns top-k nearest neighbors using pgvector
  ```

---

### 12.2 Top 5 Things to Fix First

1. **Close the Developer Auth Backdoor:** Remove `if settings.ENVIRONMENT.lower() != "production": return None` from `deps.py` immediately so all test and ingestion routes require valid authentication.
2. **Prevent Cross-Case Spoofing:** Stop accepting `organization_id` and `case_id` from client forms in `ring1.py`; force them from verified server-side JWT claims.
3. **Purge Neo4j Container:** Delete Neo4j from `docker-compose.yml` to restore compliance with the non-negotiable PostgreSQL-only stack rule.
4. **Fix Event-Loop Blocking I/O:** Stop calling synchronous `db.commit()` inside `async def` routes to prevent server freezes under concurrent load.
5. **Enforce Upload File Limits:** Add an explicit file size check before reading uploads into memory in `POST /api/v1/sources` to prevent server crashes.

*In plain words:*
We organized all fixes into four clear batches that can each be tackled in a single session. The top priority is locking down the developer backdoor and cross-case spoofing bugs before touching the database or performance improvements.

<!-- SECTION 12 DONE -->


---

## S13 Open Questions

### 13.1 Strategic Decisions Requiring Human Alignment

1. **Reconciliation of `organization_id` Columns (D-004 vs SaaS Multi-Tenancy):**
   - *Context:* Karim's settled decision D-004 explicitly mandates: *"One organization per deployment (single-organization instance)... NO organization_id/tenant columns"*. The teammate nevertheless introduced `organization_id` columns across `cases`, `sources`, `tasks`, `audit_events`, `ring1_observations`, and `ring1_memory_records`.
   - *Question for Karim:* Do you wish to accept `organization_id` as a permanent architectural evolution to support future multi-tenant SaaS deployments, or should an Alembic migration be generated to drop these columns to maintain strict single-tenant simplicity?
2. **Acceptance of `cases` Table in Ring 1 vs Ring 5:**
   - *Context:* The Ring 1 specification reserves Case and Client tables for Ring 5 ("Case Intelligence"). The teammate built the full `cases` table and API endpoints early to facilitate realistic integration testing.
   - *Question for Karim:* Should the `cases` table be formally grandfathered into the project baseline, or should the router be quarantined until Ring 5?
3. **Selection of Official Vector Embedding Model:**
   - *Context:* The teammate placed a freeze on vector embeddings pending written sign-off, resulting in 0 vector columns and 0 pgvector indexes in PostgreSQL.
   - *Question for Karim & Teammate:* Which embedding model and dimension should be pinned (e.g., OpenAI `text-embedding-3-small` at 1536 dimensions, or a local open-source model at 768/1024 dimensions) so that pgvector HNSW tables can be created?
4. **Approval of Redis for Short-Term Memory Caching (D-009):**
   - *Context:* Decision D-009 states Python replacements for Node caching tools are not decided. The teammate integrated Redis in `short_term_memory.py`.
   - *Question for Karim:* Is Redis formally approved for production caching, or should caching be restricted to PostgreSQL tables and thread-safe in-memory stores?
5. **Formal Approval of Planning Engine as 6th Core Engine:**
   - *Context:* The Constitution defines exactly 5 cognitive engines for Ring 1. The teammate introduced `PlanningEngine` as an advisory 6th capability under ADR-008.
   - *Question for Karim:* Do you formally endorse ADR-008 and the expansion of the General Brain mesh to 6 engines?

---

### 13.2 Items That Could Not Be Verified

| Verification Target | Status | Root Cause & Technical Justification |
| :--- | :---: | :--- |
| **Live Pytest Execution** | **UNVERIFIED** | Active host Python environment (`C:\ProgramData\miniconda3\python.exe`) lacks `pytest==9.1.1` and project dependencies (`No module named pytest`). Rule 0 strictly prohibits installing packages or altering the host system environment. |
| **Offline Alembic SQL (`upgrade head --sql`)** | **UNVERIFIED** | `alembic` command-line executable is absent from the host system PATH. Cannot generate offline SQL without installing the package. |
| **Live WebSocket Concurrency Benchmark** | **UNVERIFIED** | Rule 0 forbids launching long-running servers or background dev processes during this read-only audit. |
| **Data Science / ML Notebook Correctness** | **UNVERIFIED** | `data-science/notebooks/` contain interactive Jupyter notebooks whose runtime outputs and training weights were not executed. |

*In plain words:*
Karim needs to make five big decisions with the teammate, most importantly deciding whether to keep the organization columns for future cloud hosting and which AI embedding model to use for vector search. Test runs could not be executed because the current computer does not have the Python packages installed.

<!-- SECTION 13 DONE -->