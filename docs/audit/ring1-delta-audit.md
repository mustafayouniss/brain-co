# Ring 1 Delta Security & Context Isolation Audit

**Auditor Role**: Senior Backend Security Auditor  
**Scope**: Read-only delta audit comparing base commit `9eef838` with `HEAD` across `backend/` and `brain/`.  
**Base Commit**: `9eef8386a066404350ebf032136897b605ea1189`  
**HEAD Commit**: `ffd75e3` (Branch: `main`)  
**Timestamp**: 2026-11-17T08:15:00+02:00  

---

## D1 What Changed

1. `backend/Dockerfile`: Production Docker container configuration with uvicorn entrypoint, offline wheel cache fallback, and runtime Python paths.
2. `backend/app/api/v1/cases.py`: Added CACS access control (`validate_case_access`) on single case and sub-resource routes, role-based case listing, and added the new `GET /{case_id}/events` route for mesh lifecycle telemetry.
3. `backend/app/api/v1/ring1.py`: Added CACS validation on `POST /upload-pdf` (fail-closed 404), and added context/role resolution with case access checks on `POST /test-run`.
4. `backend/app/api/v1/ws.py`: Added cross-tenant check against `Case` table in `_validate_session_and_case` for non-existent cases, but retained permissive fallback for non-UUID strings.
5. `backend/app/infrastructure/ai/adapter.py`: Configured default backend model to `gemini-3.5-flash-lite` and simplified model routing hints.
6. `backend/app/ring1/service.py`: Forwarded `organization_id` and `case_id` parameters through `Ring1TestRunner.execute`.
7. `backend/app/ring1/services/pdf_pipeline_service.py`: Removed auto-synthesis of missing cases in `execute_pdf` (fail-closed with `CaseNotFoundError`), dual delivery to WebSocket, and updated `query_saved_knowledge` to resolve case by UUID/case_number.
8. `backend/app/ring1/services/test_scenario_service.py`: Added case scoping, plan step execution telemetry, dual WebSocket broadcast, and persistence of lifecycle events.
9. `backend/app/services/__init__.py`: Exported `MeshEventService` and `MeshLifecycleEventType`.
10. `backend/app/services/case_service.py`: Added employee role scoping to `list_cases`, database error fallback handling in `assign_user_to_case` and `validate_case_access`.
11. `backend/app/services/mesh_event_service.py`: New service providing canonical lifecycle event telemetry, dual delivery (SSE/WebSocket), and historical replay queries.
12. `backend/app/services/ticket_service.py`: Added thread-safe in-memory fallback store when `ws_tickets` table is not yet migrated.
13. `backend/tests/ring1/test_pdf_e2e_pipeline.py`: Added tests for case validation, dual delivery, and unknown case 404 handling; added `admin_headers` to some upload tests.
14. `backend/tests/test_api_v1_cases.py`: Added test coverage for CACS enforcement, employee isolation, and `GET /{case_id}/events`.
15. `backend/tests/test_api_v1_ring1.py`: Added test coverage for CACS scoped test runs and capabilities.
16. `backend/tests/test_case_access_control.py`: Added CACS unit tests for role-based listing and assignment fallback.
17. `backend/tests/test_mesh_lifecycle_events.py`: Added tests for canonical lifecycle event types and `MeshEventService`.
18. brain/src/brain/general/engines/base.py: Added LLM client status/error tracking telemetry fields (`_last_llm_error`, `_last_llm_status`, `_last_llm_model`).
19. brain/src/brain/general/engines/planning.py: Added telemetry for plan origin (`gemini_ai` vs `deterministic_fallback`) and provider error details.
20. brain/src/brain/general/engines/retrieval.py: Added `retrieval_method` telemetry field to retrieval query responses.
21. brain/src/brain/general/stores/in_memory_retrieval.py: Added `strategy_name = "postgresql_lexical"` attribute to `LexicalRetrievalStrategy`.

<!-- SECTION D1 DONE -->


## D2 New or Changed Routes

| Method | Path | Auth Dependency | Where Org / Case Come From | Case Access Checked (Yes/No) | Cross-Context Result |
|---|---|---|---|---|---|
| `GET` | `/api/v1/cases` | `context: BrainContext = Depends(get_brain_context)` | Org: `context.organization_id` (server/JWT); Case: N/A | **Yes**: Filtered by creator or assignment for employees (`case_service.py:108-118`) | `200 OK` (Only assigned/created cases returned) |
| `GET` | `/api/v1/cases/{case_id}` | `context: BrainContext = Depends(get_brain_context)` | Org: `context.organization_id` (server/JWT); Case: Path `{case_id}` | **Yes**: `CaseService.validate_case_access` (`cases.py:146-155`) | `404 Not Found` (Sanitized for wrong org or unassigned employee) |
| `POST` | `/api/v1/cases/{case_id}/documents` | `context: BrainContext = Depends(get_brain_context)` | Org: `context.organization_id` (server/JWT); Case: Path `{case_id}` | **Yes**: `CaseService.validate_case_access` (`cases.py:183-195`) | `404 Not Found` (Sanitized for wrong org or unassigned employee) |
| `GET` | `/api/v1/cases/{case_id}/documents` | `context: BrainContext = Depends(get_brain_context)` | Org: `context.organization_id` (server/JWT); Case: Path `{case_id}` | **Yes**: `CaseService.validate_case_access` (`cases.py:249-260`) | `404 Not Found` (Sanitized for wrong org or unassigned employee) |
| `GET` | `/api/v1/cases/{case_id}/tasks` | `context: BrainContext = Depends(get_brain_context)` | Org: `context.organization_id` (server/JWT); Case: Path `{case_id}` | **Yes**: `CaseService.validate_case_access` (`cases.py:304-315`) | `404 Not Found` (Sanitized for wrong org or unassigned employee) |
| `GET` | `/api/v1/cases/{case_id}/knowledge` | `context: BrainContext = Depends(get_brain_context)` | Org: `context.organization_id` (server/JWT); Case: Path `{case_id}` | **Yes**: `CaseService.validate_case_access` (`cases.py:363-374`) | `404 Not Found` (Sanitized for wrong org or unassigned employee) |
| `GET` | `/api/v1/cases/{case_id}/events` *(NEW)* | `context: BrainContext = Depends(get_brain_context)` | Org: `context.organization_id` (server/JWT); Case: Path `{case_id}` | **Yes**: `CaseService.validate_case_access` (`cases.py:433-444`) | `404 Not Found` (Sanitized for wrong org or unassigned employee) |
| `POST` | `/api/v1/ring1/test-run` | `get_test_operator_user`, `credentials = Depends(_bearer_scheme)` | Org: JWT token if present, else body `request.organization_id` (checked against token); Case: body `request.case_id` | **Yes**: Checked via `CaseService.validate_case_access` if `request.case_id` provided (`ring1.py:94-106`) | Org mismatch: `403 Forbidden`; Unauthorized case: `404 Not Found` |
| `POST` | `/api/v1/ring1/upload-pdf` | `context: BrainContext = Depends(get_brain_context)` | Org: `context.organization_id` (form `organization_id` checked against context); Case: Form `case_id` | **Yes**: Checked via `CaseService.validate_case_access` (`ring1.py:268-278`) | Org mismatch: `403 Forbidden` (Oracle); Unauthorized case: `404 Not Found` |
| `WS` | `/api/v1/ws/observations` & `/api/v1/ws/events` | Single-use Ticket or JWT query token | Org: Ticket or JWT; Case: Ticket `case_id` or query `case_id` | **Partial / Flawed**: Checked if case exists in DB; if non-existent or non-UUID, allows connection (`ws.py:129-138`) | Cross-tenant UUID: `WS 1008 Policy Violation`; Non-existent case: `Accepted (True)` |

<!-- SECTION D2 DONE -->


## D3 New or Changed DB Queries and Models

1. `backend/app/api/v1/cases.py:108-118`: `CaseService.list_cases(session, organization_id, user_id, user_role)`:
   - Filtered by Org: **YES** (`Case.organization_id == organization_id`).
   - Filtered by Case/User: **YES** (for non-admin, filtered by `(Case.created_by == user_id) | Case.id.in_(assigned_ids)`).
2. `backend/app/api/v1/cases.py:146, 183, 249, 304, 363, 433`: `CaseService.validate_case_access(...)`:
   - Filtered by Org: **YES** (`Case.organization_id == organization_id`).
   - Filtered by Case: **YES** (`Case.id == parsed_uuid` or `Case.case_number == case_id_or_number`).
   - Filtered by User: **YES** (admin allowed, non-admin requires creator match or active `CaseAssignment`).
3. `backend/app/api/v1/cases.py:263-270`: `db.query(Source)` in `list_case_documents`:
   - Filtered by Org: **YES** (`Source.organization_id == context.organization_id`).
   - Filtered by Case: **YES** (`sa.or_(Source.case_id == str(c.id), Source.case_id == c.case_number)`).
4. `backend/app/api/v1/cases.py:318-325`: `db.query(Task)` in `list_case_tasks`:
   - Filtered by Org: **YES** (`Task.organization_id == context.organization_id`).
   - Filtered by Case: **YES** (`sa.or_(Task.case_id == str(c.id), Task.case_id == c.case_number)`).
5. `backend/app/api/v1/cases.py:373-380`: `sa.select(MemoryRecord)` in `get_case_knowledge`:
   - Filtered by Org: **YES** (`MemoryRecord.organization_id == context.organization_id`).
   - Filtered by Case: **YES** (`sa.or_(MemoryRecord.case_id == str(c.id), MemoryRecord.case_id == c.case_number)`).
   - Knowledge Candidate Status Filtered: **NO** (omits `MemoryRecord.status == "validated"`).
6. `backend/app/api/v1/cases.py:447-464`: `MeshEventService.get_events` in `get_case_events`:
   - Filtered by Org: **YES** (`MeshEventRecord.organization_id == organization_id`).
   - Filtered by Case: **YES** (`MeshEventRecord.case_id == case_id`).
7. `backend/app/api/v1/ring1.py:94-106`: `CaseService.validate_case_access` in `execute_ring1_test`:
   - Filtered by Org: **YES** (`active_org_id`).
   - Filtered by Case: **YES** (`request.case_id`).
8. `backend/app/api/v1/ring1.py:268-278`: `CaseService.validate_case_access` in `upload_pdf`:
   - Filtered by Org: **YES** (`clean_org_id`).
   - Filtered by Case: **YES** (`clean_case_id`).
9. `backend/app/api/v1/ws.py:129-136`: `cross_case = db.query(Case).filter(Case.id == parsed_uuid).first()`:
   - Filtered by Org: **NO** (Unscoped cross-tenant query across all organizations).
   - Filtered by Case: **YES** (`Case.id == parsed_uuid`).
10. `backend/app/ring1/services/pdf_pipeline_service.py:145-155`: `Case` query in `execute_pdf`:
    - Filtered by Org: **YES** (`Case.organization_id == organization_id`).
    - Filtered by Case: **YES** (`(Case.id == parsed_uuid) | (Case.case_number == case_id)`). If not found, raises `CaseNotFoundError` (fail-closed).
11. `backend/app/ring1/services/pdf_pipeline_service.py:823-841`: `MemoryRecord` query in `query_saved_knowledge`:
    - Filtered by Org: **YES** (`MemoryRecord.organization_id == organization_id`).
    - Filtered by Case: **YES** (`MemoryRecord.case_id.in_(case_matches)`).
    - Status Filtered: **NO** (Returns all records, including candidates).
12. `backend/app/ring1/services/test_scenario_service.py:149, 770`: `existing_case = query(Case).filter(Case.id == c_uuid).first()`:
    - Filtered by Org: **NO** (Unscoped query omitting `organization_id`).
    - Filtered by Case: **YES** (`Case.id == c_uuid`).
13. `backend/app/services/case_service.py:111-115`: `query(CaseAssignment.case_id).filter(CaseAssignment.user_id == user_id)`:
    - Filtered by Org: Inherited through `Case.organization_id == organization_id`.
    - Filtered by User: **YES** (`CaseAssignment.user_id == user_id`).
14. `backend/app/services/mesh_event_service.py:110-128`: `MeshEventRecord` insert:
    - Scoped by Org: **YES** (`organization_id`).
    - Scoped by Case: **YES** (`clean_case_id`).
15. `backend/app/services/mesh_event_service.py:167-185`: `MeshEventRecord` select:
    - Filtered by Org: **YES** (`MeshEventRecord.organization_id == organization_id.strip()`).
    - Filtered by Case: **YES** (if `case_id` provided).

<!-- SECTION D3 DONE -->


## D4 Status of Findings C-001 through C-014

| ID | Previous Severity | Current Status | Evidence & Explanation |
|---|---|---|---|
| **C-001** | P0 | **UNCHANGED** | `backend/app/api/v1/sources.py:81-92` was not modified; files are still created with `organization_id=None` and `case_id=None`. |
| **C-002** | P1 | **UNCHANGED** | `backend/app/infrastructure/database/stores.py:382-392` was not modified; `SqlAlchemyRetrievalStore` still returns unvalidated candidate records. |
| **C-003** | P1 | **PARTIALLY FIXED** | Fixed on `POST /ring1/upload-pdf` via `CaseService.validate_case_access` (`ring1.py:268-278`), but **UNCHANGED** on `GET /ring1/knowledge` (`ring1.py:352-364`) where arbitrary `case_id` is queried without CACS checks. |
| **C-004** | P1 | **UNCHANGED** | `backend/app/api/v1/observations.py:45, 83` was not modified; `payload.case_id` is still written without CACS authorization checks. |
| **C-005** | P1 | **UNCHANGED** | Architecture-wide absence of a single shared context query helper remains; routes in `cases.py` and `mesh_event_service.py` continue to hand-craft SQL filter clauses. |
| **C-006** | P1 | **WORSE** | `backend/app/api/v1/ws.py:132` introduces an unscoped cross-tenant query (`db.query(Case).filter(Case.id == parsed_uuid)`), while non-existent cases and non-UUID case identifiers still fall through to `return True` (`ws.py:137`). |
| **C-007** | P2 | **FIXED** | `backend/app/api/v1/cases.py` now enforces `CaseService.validate_case_access` and CACS role-based filtering across `list_cases`, `get_case`, `documents`, `tasks`, and `knowledge` (lines 115, 146, 183, 249, 304, 363). |
| **C-008** | P2 | **UNCHANGED** | `backend/app/api/v1/brain.py:54-55` was not modified; internal identifiers `ORGANIZATION_ID` and `ENVIRONMENT` remain publicly exposed. |
| **C-009** | P2 | **UNCHANGED** | `backend/app/api/v1/ai.py:148` and `backend/app/api/v1/context.py:84-86` still raise `403 Forbidden` on case access failures instead of standardizing on `404 Not Found`. |
| **C-010** | P2 | **UNCHANGED** | Neither `tasks.py` nor `memory.py` was touched; queries still fetch records by PK using `db.get()` across tenant boundaries before Python-level filtering. |
| **C-011** | P2 | **FIXED** | `backend/app/ring1/services/pdf_pipeline_service.py:144-156` completely removed automatic `Case` synthesis, now querying `Case` with tenant scoping and raising `CaseNotFoundError` (fail-closed) when the case is missing. |
| **C-012** | P2 | **UNCHANGED** | `backend/app/api/v1/users.py:38-64` was not modified; user creation remains unbound to the creator admin's organization. |
| **C-013** | P3 | **UNCHANGED** | `backend/app/api/deps.py:170-171` still catches `Exception: pass` during token decoding in `get_test_operator_user`. |
| **C-014** | P3 | **UNCHANGED** | `backend/app/core/ws_manager.py:30-61` was not modified; WebSocket connection ceiling limits remain absent. |

<!-- SECTION D4 DONE -->


## D5 New Findings Register

### N-001: Unscoped Cross-Tenant Database Query in WebSocket Case Access Validation
- **Severity**: **P1**
- **Status**: **CONFIRMED**
- **File:Line**: [backend/app/api/v1/ws.py:132](file:///d:/Study/projects/OrgBrain/backend/app/api/v1/ws.py#L132)
- **Impact**: In attempting to check whether a requested `case_id` belongs to another organization, `_validate_session_and_case` executes `cross_case = db.query(Case).filter(Case.id == parsed_uuid).first()`. This query omits `Case.organization_id == organization_id`, querying rows across all tenants into session memory and directly violating the rule that every DB query must be filtered by context.
- **Plain Fix**: Remove cross-tenant probing entirely. Query only `filter(Case.id == parsed_uuid, Case.organization_id == organization_id)`; if no row matches, immediately return `False` to fail closed with `WS_1008_POLICY_VIOLATION`.

### N-002: Unscoped Cross-Tenant Case Lookup in Ring 1 Test Scenario Runner
- **Severity**: **P1**
- **Status**: **CONFIRMED**
- **File:Line**: [backend/app/ring1/services/test_scenario_service.py:149, 770](file:///d:/Study/projects/OrgBrain/backend/app/ring1/services/test_scenario_service.py#L149)
- **Impact**: In both `e2e` mode and `custom_prompt` mode, the scenario runner executes `existing_case = self.runner.db_session.query(Case).filter(Case.id == c_uuid).first()`. This query lacks `organization_id` scoping. If a UUID of another tenant's case is provided, it matches the foreign case, binding execution to a cross-tenant entity.
- **Plain Fix**: Add `Case.organization_id == org_id` to the query: `query(Case).filter(Case.id == c_uuid, Case.organization_id == org_id).first()`.

### N-003: Unvalidated Candidate Knowledge Records Returned in Case Knowledge Endpoint
- **Severity**: **P1**
- **Status**: **CONFIRMED**
- **File:Line**: [backend/app/api/v1/cases.py:373-380](file:///d:/Study/projects/OrgBrain/backend/app/api/v1/cases.py#L373-L380)
- **Impact**: In `GET /api/v1/cases/{case_id}/knowledge`, the query selects `MemoryRecord` by `organization_id` and `case_id`, but omits any filter on `MemoryRecord.status == "validated"`. This violates the rule "candidate knowledge is not returned in normal retrieval", exposing unvalidated observations as verified facts to clients.
- **Plain Fix**: Add `.where(MemoryRecord.status == "validated")` (or `"active"`) by default to the query statement.

### N-004: Status Code Oracle on Organization Mismatch in Test Run Endpoint
- **Severity**: **P2**
- **Status**: **CONFIRMED**
- **File:Line**: [backend/app/api/v1/ring1.py:77-81](file:///d:/Study/projects/OrgBrain/backend/app/api/v1/ring1.py#L77-L81)
- **Impact**: In `POST /api/v1/ring1/test-run`, passing an `organization_id` that differs from the caller's token raises `HTTPException(status_code=status.HTTP_403_FORBIDDEN)`. This leaks the presence of an organization boundary mismatch rather than failing closed with 404 or ignoring client-supplied org identifiers.
- **Plain Fix**: Never trust `request.organization_id` from the client; overwrite it authoritatively with `token_org` or return `404 Not Found`.

### N-005: Fallback to Client Request Body for Organization ID when Token Claim is Missing
- **Severity**: **P2**
- **Status**: **CONFIRMED**
- **File:Line**: [backend/app/api/v1/ring1.py:87-88](file:///d:/Study/projects/OrgBrain/backend/app/api/v1/ring1.py#L87-L88)
- **Impact**: If a valid JWT lacks `org_id` / `organization_id` claims, `execute_ring1_test` falls back to `request.organization_id or getattr(settings, "ORGANIZATION_ID", ...)`. A caller with an unscoped token can pass any arbitrary `organization_id` in the request body, violating the rule "organization comes from the server/JWT never from the client".
- **Plain Fix**: If the token lacks an organization claim, resolve the user's active organization strictly via database membership (`OrganizationService.list_user_organizations`), never from the client request payload.

<!-- SECTION D5 DONE -->


## D6 Test Suite Changes & Missing Isolation Coverage

### 6.1 Tests Added or Modified
1. `backend/tests/ring1/test_pdf_e2e_pipeline.py`:
   - Updated `test_pdf_e2e_normal_pipeline` and `test_pdf_e2e_failure_and_recovery_pipeline` to insert prerequisite `Organization` and `Case` database fixtures.
   - Updated `test_pdf_upload_api_endpoint_non_streaming`, `test_pdf_upload_api_endpoint_streaming`, and `test_saved_knowledge_persistence_and_isolation` to pass `headers=admin_headers` and create target `Case` rows.
   - Added `test_pdf_upload_unknown_case_fails_closed_404_no_synthesis`: verifies uploading to an unknown case returns 404 and does not auto-synthesize rows in PostgreSQL.
   - Added `test_pdf_execute_unknown_case_raises_case_not_found`: verifies `Ring1TestRunner.execute_pdf` raises `CaseNotFoundError`.
2. `backend/tests/test_api_v1_cases.py`:
   - Added comprehensive tests for CACS access control:
     - `test_list_cases_admin_sees_all_vs_employee_sees_assigned_only`
     - `test_get_case_unassigned_employee_receives_404`
     - `test_upload_document_unassigned_employee_receives_404`
     - `test_list_documents_unassigned_employee_receives_404`
     - `test_list_tasks_unassigned_employee_receives_404`
     - `test_get_knowledge_unassigned_employee_receives_404`
     - `test_get_events_endpoint_and_isolation`
3. `backend/tests/test_api_v1_ring1.py`:
   - Added `test_ring1_production_environment_requires_admin`
   - Added `test_ring1_test_run_with_scoped_case_success`
   - Added `test_ring1_test_run_with_unauthorized_case_fails_404`
   - Added `test_ring1_test_run_with_org_mismatch_fails_403`
4. `backend/tests/test_case_access_control.py`:
   - Added unit tests for `CaseService.list_cases`, `assign_user_to_case`, and `validate_case_access` with role-based CACS and fallback when `CaseAssignment` table is missing.
5. `backend/tests/test_mesh_lifecycle_events.py`:
   - Added `test_canonical_lifecycle_event_types`
   - Added `test_mesh_event_service_record_and_dual_delivery`

### 6.2 Isolation Scenarios Still Missing Tests
1. **Candidate Knowledge Exclusion on Case Knowledge Route**: Zero tests assert that unvalidated candidate records (`status == "candidate"`) are excluded from `GET /api/v1/cases/{case_id}/knowledge` or `GET /api/v1/ring1/knowledge`.
2. **Employee CACS Isolation on `GET /api/v1/ring1/knowledge`**: Zero tests verify that an employee unassigned to a case receives `404 Not Found` when requesting `GET /api/v1/ring1/knowledge?case_id=X` (the endpoint currently does not check case assignment).
3. **Non-UUID Case String WebSocket Rejection**: Zero tests assert that a WebSocket client requesting a non-existent alphanumeric case identifier (e.g. `?case_id=CASE-9999`) is rejected with code 1008 rather than accepted via the ephemeral fallback.
4. **Source Ingestion Tenant Boundary**: Zero tests assert that `POST /api/v1/sources` stamps `organization_id` or verifies case assignment.
5. **Token Organization Spoofing on Test Run**: Zero tests verify that an authenticated user cannot override their organization by providing a different `request.organization_id` when the token is missing org claims.

<!-- SECTION D6 DONE -->


## D7 Analysis of the 4 Failing Tests on Main

### 1. `tests/ring1/test_pdf_e2e_pipeline.py::test_pdf_upload_api_validation_errors`
- **Classification**: **STALE TEST**
- **Exercised Code**: `backend/app/api/v1/ring1.py:150-196` (`upload_pdf`)
- **Evidence**:
  1. In `backend/app/api/v1/ring1.py:158`, `upload_pdf` requires authentication via `context: BrainContext = Depends(get_brain_context)`.
  2. In `backend/app/core/context.py:65-69`, when `credentials is None` (and `AI_ANONYMOUS_TESTING_ENABLED` is False, the default in `app/core/config.py:41`), `get_brain_context` raises `HTTPException(status_code=401, detail={"code": "AUTHENTICATION_REQUIRED", ...})`.
  3. In `backend/tests/ring1/test_pdf_e2e_pipeline.py:305-333`, `test_pdf_upload_api_validation_errors(client)` invokes `client.post("/api/v1/ring1/upload-pdf", ...)` without passing `headers=admin_headers` (unlike lines 253, 284, 352 where `admin_headers` was added).
  4. The request is rejected at the dependency gate with `401 Unauthorized` before reaching the endpoint logic, causing `assert resp.status_code == 400` to fail with `401 != 400`.
  5. The endpoint validation logic itself (checking PDF magic bytes `%PDF-` at line 192 and non-empty `case_id` at line 183) is correct, but the test is stale because it omitted the required authentication header fixture.

### 2. `tests/ring1/test_pdf_e2e_pipeline.py::test_pdf_upload_unknown_case_fails_closed_404_no_synthesis`
- **Classification**: **STALE TEST**
- **Exercised Code**: `backend/app/api/v1/ring1.py:150-280` (`upload_pdf`)
- **Evidence**:
  1. In `backend/app/api/v1/ring1.py:158`, `upload_pdf` requires `context: BrainContext = Depends(get_brain_context)`.
  2. In `backend/tests/ring1/test_pdf_e2e_pipeline.py:385-400`, `test_pdf_upload_unknown_case_fails_closed_404_no_synthesis(client, db_session)` calls `client.post("/api/v1/ring1/upload-pdf", ...)` with `files` and `data`, but omits `headers=admin_headers`.
  3. FastAPI executes `get_brain_context` with `credentials=None`, which immediately raises `HTTP 401 Unauthorized`.
  4. Consequently, `resp.status_code` is 401 instead of 404, causing `assert resp.status_code == 404` to fail with `401 != 404`.
  5. The code under test in `backend/app/api/v1/ring1.py:268-278` correctly calls `CaseService.validate_case_access` and raises `HTTPException(status_code=404, detail="Case ... not found or access denied")` when authenticated. The test fails solely because the test author omitted `admin_headers`.

### 3. `tests/test_api_v1_ring1.py::test_ring1_knowledge_rejects_mismatched_organization_id`
- **Classification**: **STALE TEST**
- **Exercised Code**: `backend/app/api/v1/ring1.py:333-350` (`get_case_knowledge`)
- **Evidence**:
  1. In `backend/app/api/v1/ring1.py:339`, `get_case_knowledge` requires `context: BrainContext = Depends(get_brain_context)`.
  2. In `backend/tests/test_api_v1_ring1.py:142-152`, `test_ring1_knowledge_rejects_mismatched_organization_id(client)` calls `client.get("/api/v1/ring1/knowledge", params={"organization_id": "evil-org", ...})` without providing an `Authorization` header.
  3. With no bearer credentials, `get_brain_context` (`backend/app/core/context.py:65-69`) raises `HTTP 401 Unauthorized`.
  4. The route handler's organization check at `backend/app/api/v1/ring1.py:345` (`if organization_id ... != context.organization_id: raise HTTPException(403)`) is never reached.
  5. The test asserts `response.status_code == 403`, which fails because the response is `401`. The test was written prior to mandatory authentication on this route and needs `admin_headers` to supply a valid token for `context.organization_id` to evaluate against the mismatched query parameter.

### 4. `tests/test_saas_organization_isolation.py::test_five_real_organizations_signup_and_isolation`
- **Classification**: **STALE TEST**
- **Exercised Code**: `backend/app/api/v1/ai.py:93-243` (`generate_ai_response`) & `backend/app/api/deps.py:183-192` (`get_llm_service`)
- **Evidence**:
  1. In `backend/tests/test_saas_organization_isolation.py:202-212`, Step 7 executes:
     ```python
     ai_own_case = client.post(
         "/api/v1/ai/prompt",
         json={"prompt": "Summarize case status", "context": "legal", "case_id": org1["case_id"]},
         headers=org1["headers"],
     )
     assert ai_own_case.status_code == 200
     ```
  2. In `backend/app/api/v1/ai.py:99`, `generate_ai_response` depends on `llm: LLMService = Depends(get_llm_service)`.
  3. `get_llm_service()` in `backend/app/api/deps.py:183-192` calls `ai_config.create_service()`, which instantiates an LLM provider based on `.env` (`AI_PROVIDER=openai`, with placeholder `OPENAI_API_KEY=your-openai-api-key-here`).
  4. Unlike `test_ai_integration.py:196` which explicitly stubs `app.dependency_overrides[get_llm_service] = lambda: fake_service`, `test_five_real_organizations_signup_and_isolation` does not override `get_llm_service`.
  5. In `backend/app/api/v1/ai.py:212`, `response = await llm.generate(llm_request)` makes a live call to the OpenAI API with the placeholder key. The call fails with `LLMError` / `AuthenticationError`, caught by the global error handler (`backend/app/core/errors.py:92-111`) which returns `502 Bad Gateway` (or unhandled `500 Internal Server Error`).
  6. Consequently, `ai_own_case.status_code` is 502/500, causing `assert ai_own_case.status_code == 200` to fail. The isolation logic (steps 1–6 and step 7 cross-case 403) works as intended, but the test author failed to mock the AI provider in this test.

<!-- SECTION D7 DONE -->
