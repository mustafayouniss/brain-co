# Progress

## Current Status — Session 13 (2026-11-18T01:00Z)

**Technical Audit Remediation: Case Creation Concurrency & Arabic Lexical Retrieval Hardening completed and verified.**

### Key Changes
1. **Case Creation TOCTOU Race Condition Defense (Issue 1)**:
   - `create_case` (`backend/app/api/v1/cases.py`) safely catches `IntegrityError` on `uq_cases_org_number`.
   - Performs `db.rollback()` first and maps cleanly to HTTP 409 `CASE_ALREADY_EXISTS`. Unrelated integrity violations are re-raised without being masked.
   - Regression test: `test_create_case_duplicate_number_maps_to_409_regression` in `test_api_v1_cases.py`.
2. **Arabic Text Normalization & Unicode Escaping Fix (Issue 6)**:
   - Created `backend/app/core/text.py` (`normalize_arabic`) for diacritics stripping, alef, taa marbuta, and alif maqsura normalization.
   - Applied `ensure_ascii=False` and `normalize_arabic` across `SqlAlchemyRetrievalStore` and `GET /api/v1/retrieval/search` endpoint.
   - Regression test: `backend/tests/test_arabic_retrieval.py`.
3. **Ingestion Pipeline Resilience & Deduplication (Batch B - Issues 2, 3, 4)**:
   - Verified worker SAVEPOINT protection (`session.begin_nested()`), deterministic idempotency keys (`source-doc-{case_id}-{sha256}`), task retry handling, and pre-storage deduplication scoped to `(organization_id, case_id, checksum_sha256)`.
   - Regression tests: `backend/tests/test_document_ingestion_pipeline.py`.

## Previous Status — Session 12 (2026-11-17T22:45Z)

**Document Ingestion Pipeline & Tenant Isolation Hardening (Rounds 1 & 2) completed and regression tested.**

### Key Changes
1. **Tenant Isolation Hardening (Round 2)**:
   - **WebSocket Fail-Closed (Item 1)**: `_validate_session_and_case` strictly filters cases by `organization_id` and rejects non-matching or cross-tenant case IDs with 1008 without information disclosure.
   - **Scenario Runner Cross-Tenant Defense (Item 2)**: Added `Case.organization_id == org_id` filter across all three case query locations in `TestScenarioService`.
   - **Test-Run Organization Verification (Item 3)**: Eliminated client body organization fallback in `execute_ring1_test` for tokens without an org claim, enforcing strict default deployment organization.
   - **Knowledge Endpoint CACS (Item 4)**: Enforced `CaseService.validate_case_access` on `GET /ring1/knowledge` returning 404 for unassigned/unauthorized cases while retaining 403 on explicit organization mismatch.
   - **Round 2 Tests**: Added `backend/tests/test_tenant_isolation_round2.py` covering WebSocket rejection, scenario runner isolation, spoofing rejection, and knowledge endpoint 404/403 security.
2. **Worker Resilience (Round 1 - Issue 4)**:
   - In `process_task_worker`, wrapped `Observation` and `MemoryRecord` persistence in `session.begin_nested()` (SAVEPOINT).
   - Targeted `IntegrityError` catch around each block; re-queries existing record by `(organization_id, idempotency_key)` and reuses its ID.
3. **Duplicate Upload Deduplication & Retries (Round 1 - Issue 3+2)**:
   - Pre-computes SHA-256 before writing to raw storage.
   - Lookups existing Source strictly by composite key `(organization_id, case_id, checksum_sha256)`.
   - Reuses existing source and active/pending task without writing duplicate files to disk or re-scheduling worker.
   - Automatically resets and schedules failed/dead tasks when re-uploaded.
   - Updated task idempotency key format to `f"source-doc-{case.id}-{sha256}"`.
4. **Round 1 Tests**:
   - Added `backend/tests/test_document_ingestion_pipeline.py`.

## Previous Status — Session 11 (2026-11-16T13:20Z)

**Full System Remediation & Next.js 16.4.6 Runtime Security Upgrade verified on host and running Docker containers.**

### Container State
- Containers running & healthy:
  - `orgbrain-postgres` (pgvector/pgvector:pg17 on port 5433, volume `brain-co_pgdata`)
  - `orgbrain-migration` (Alembic migration service, Exited 0)
  - `orgbrain-backend` (FastAPI + Python 3.12 on port 8000, healthy)
  - `orgbrain-frontend` (Next.js 16.4.6 on port 3000, healthy)
  - `orgbrain-adminer` (Adminer 4.8 on port 8080)
- Verified Runtime Next.js Version: `16.4.6` (host and container)
- Healthchecks: configured and passing HTTP 200 on `/health` and `/`
- Database revision: `f82a1b3c4d5e (head)` applied via decoupled migration service

### Verified Core Capabilities & Security Upgrades
1. **Next.js 16.4.6 Runtime**: Host filesystem and `orgbrain-frontend` container verified executing Next.js 16.4.6 (mitigating GHSA-2464-fhr4-w9xw, GHSA-p3m5-59mp-jv5r, GHSA-673q-mjm6-r5xr).
2. **Server-Side URL Resolution**: `server-backend-url.ts` verified routing all 18 server routes to `http://backend:8000` while clients use `/api/v1`.
3. **One-Shot Migration Container**: Decoupled Alembic upgrade to prevent race conditions on multi-instance backend starts.
4. **CACS Access Control**: Case access strictly enforced server-side with tenant isolation.
5. **Session Persistence**: Page reload and route transitions retain authentication session without premature redirects.
6. **React Error #300 Remediation**: Relocated conditional early return in `FloatingChatWidget` below hook declarations; eliminated crashes (Error #300 / #310) during client-side route transitions between `/` and `/login`.

## Previous Status — Session 10 (2026-11-16T00:30Z)

**Teammate Docker setup integrated with latest BRAIN-CO codebase. Single-command deployment operational.**

### Container State
- Containers running & healthy:
  - `orgbrain-postgres` (pgvector/pgvector:pg17 on port 5433, volume `brain-co_pgdata`)
  - `orgbrain-backend` (FastAPI + Python 3.12 on port 8000, healthy)
  - `orgbrain-frontend` (Next.js 16.4.0 on port 3000, healthy)
  - `orgbrain-adminer` (Adminer 4.8 on port 8080)
- Single command startup: `docker compose up --build -d`
- Healthchecks: configured and passing HTTP 200 on `/health` and `/`
- Database revision: `f82a1b3c4d5e (head)` applied automatically on container startup

### Verified Test Results (Inside Container & Host)
| Suite | Collected | Passed | Exit | Environment |
|---|---|---|---|---|
| `backend/tests` (Ring 1 + API + CACS) | 361 | 361 | 0 | `backend` container |
| `ai/tests` | 56 | 56 | 0 | `backend` container |
| `data-engineering/tests` | 24 | 24 | 0 | `backend` container |
| `tests/architecture` | 16 | 16 | 0 | host venv |
| **Total** | **457** | **457** | **0** | **100% Pass** |

### Verified Core Capabilities
1. **Single-Command Startup**: All 4 services build and start with `docker compose up --build -d`.
2. **Containerized SaaS Auth**: Multi-tenant admin authentication and `/auth/me` profile resolution.
3. **Containerized CACS & Cases**: Case creation, assignment, and access control under Docker networking.
4. **Containerized WebSockets**: Ticket issuance (`/auth/ws-ticket`), handshake validation, connection acceptance.
5. **Containerized Mesh Execution**: 6 Ring 1 engines dispatched, 18 events captured, durable sequence storage.
6. **Containerized PDF Ingestion**: Text extraction, knowledge structuring, facts persisted and retrieved.
7. **Database GUI Access**: Adminer accessible on port 8080.

## Previous Status — Session 9 (2026-11-15T22:30Z)

**Database Migration `f82a1b3c4d5e` applied and verified on active development database `orgbrain_legal`.**

### Database State
- `orgbrain_legal` (dev, port 5433): upgraded from `e71f6a9b0c3d` to `f82a1b3c4d5e`.
- Tables present & active: `mesh_events`, `ws_tickets`, `case_assignments`.
- Pre-migration backup: `/tmp/brain_co_db_backups/orgbrain_legal_pre_f82a1b3c4d5e_20261115_202131.dump` (76,250 bytes).
- Data integrity: 17 users, 18 orgs, 14 cases 100% preserved.

### Verified Test Results (Session 9 Full Discovery)
| Suite | Collected | Passed | Exit |
|---|---|---|---|
| `backend/tests/ring1` | 189 | 189 | 0 |
| `backend/tests` (root) | 172 | 172 | 0 |
| `tests/architecture` | 16 | 16 | 0 |
| `ai/tests` | 56 | 56 | 0 |
| `data-engineering/tests` | 24 | 24 | 0 |
| **Total** | **457** | **457** | **0** |

### Verified Core Capabilities
1. **Durable Mesh Events**: Stamped sequence numbers, dual-delivery, persisted in PostgreSQL `mesh_events`, cursor replay via `since_sequence`.
2. **Atomic Single-Use WebSocket Tickets**: SHA-256 hash storage in `ws_tickets`, 60s TTL, single-use consumption across processes, replay rejection.
3. **Multi-Tenant CACS**: Admin policy across org, employee creator/assignee policy via `case_assignments`, fail-closed cross-tenant isolation.
4. **AI Telemetry Transparency**: Model confirmed as `gemini-3.5-flash-lite`, plans explicitly tagged `gemini_ai` vs `deterministic_fallback`, retrieval explicitly tagged `postgresql_lexical`.
5. **Next.js Production Build**: 36 routes compiled cleanly with 0 errors.

## Next
- **Action required:** Rotate Gemini API key in Google AI Studio console (historical redaction confirmed; key rotation required externally).
- Future Ring 2: vector embeddings, pgvector semantic search, multi-document RAG.

## Known Limitations
- Semantic/pgvector retrieval: NOT IMPLEMENTED in Ring 1 (explicitly labelled `postgresql_lexical`).
- Sequential Gemini test runs subject to external 429 quota pressure.
