# Ring 1 — Reality Check Audit
## Detect Mocks, Fake Implementations, Stubs & Non-Functional Integrations

- **Audit Date:** 2026-11-15
- **Auditor:** Senior Software Architect & Independent Implementation Auditor
- **Repository Worktree:** `/home/mohamed-alaa/.gemini/antigravity/worktrees/brain-co/brain_module_technical_audit`
- **Branch:** `brain_module_technical_audit`
- **Target System:** Ring 1 General Brain (Backend, AI Mesh, Frontend, Data Engineering)

---

## A. Executive Summary

### 1. Is Ring 1 Actually Working?
**Yes, but strictly as a developer-facing cognitive engine and PDF pipeline.** 
The core backend engines (Perception, Observation, Basic Memory, Basic Retrieval, and Planning) and their underlying PostgreSQL database persistence genuinely execute, store records, enforce tenant-scoped unique constraints, and retrieve data across separate requests. Real multi-page PDFs are ingested, parsed into pages, structured into Egyptian legal obligations and facts, and durably persisted in PostgreSQL.

**However, the end-user application (the production Frontend Workspace) is almost entirely disconnected and mocked.** 
An everyday user logging into the application cannot see Brain status, cannot view the observation feed, cannot browse case knowledge, and cannot switch contexts. Almost all user-facing screens in `/workspace` are explicit empty-state mocks. Ring 1 currently functions as a headless engine wrapped in an interactive developer debug widget (`Ring1TestConsole`).

### 2. What Is Genuinely Functional?
- **Observation Engine & Persistence:** `ObservationEngine` normalizes system and user events, enforces tenant-scoped idempotency keys, and writes real rows to PostgreSQL table `ring1_observations`. HMAC-SHA256 cursor pagination works.
- **Memory Engine & Scope Isolation:** `BasicMemoryEngine` writes structured records to PostgreSQL table `ring1_memory_records`, strictly enforces tenant and case boundaries, implements human validation authority gating (`candidate` -> `validated`), and returns sanitized 404s to eliminate existence oracles.
- **Real PDF Ingestion Pipeline:** Uploading a PDF binary triggers genuine byte validation, page extraction via `pypdf`, structured legal fact extraction, observation recording, and memory persistence in PostgreSQL.
- **Mesh Router & Step Execution:** `MeshRouter` validates protocol envelopes, tracks delegation hops, and prevents loops. `PlanStepExecutor` steps through dependency DAGs, dispatches capability requests, and halts when prerequisites fail.
- **Data Engineering Pipeline:** Package `orgbrain_ingest` genuinely hashes, validates, and stores raw source files with 24 passing unit tests.

### 3. What Is Only a Demo, Mock, or Simulation?
- **Main User Workspace (`/workspace`):** Every panel ("overview", "cases", "clients", "knowledge", "insights") is an explicit mock rendering empty placeholders. It is not connected to any Ring 1 API.
- **AI Employee Panel in Workspace (`AIEmployeePanel`):** Calls `/api/ai/prompt`, a simple chat demonstration endpoint that bypasses all Ring 1 engines, memory, and context.
- **Delegation Graph in Test Console:** The animated peer-to-peer delegation graph shown in the developer console is partly simulated: sequential test runner scripts (`TestScenarioService`) dispatch requests from `sender_engine="client"`, but fake `source_engine="observation"` in event dictionaries to draw arrows on the UI.
- **AI Extraction vs. Deterministic Heuristics:** When external LLM provider credentials are unavailable, the system silently falls back to deterministic regex heuristics (e.g. for Egyptian Civil Code Article 147) while presenting the output in the UI as "Extracted Knowledge" without indicating that the LLM failed.

### 4. What Is Disconnected?
- **Real-Time WebSocket Stream:** `backend/app/api/v1/ws.py` exposes `/api/v1/ws/observations`, but the frontend repository contains **no WebSocket client or hook**; the UI only consumes SSE streams for developer test runs.
- **Onboarding Document Upload:** `frontend/src/app/onboarding/upload/page.tsx` forwards to `/api/documents/upload` -> `/sources` (Ring 0 raw sources), failing with 401/404. It is completely disconnected from the Ring 1 PDF ingestion pipeline (`/api/v1/ring1/upload-pdf`).
- **Main Workspace Brain Dashboard:** No component in `/workspace` queries `/api/v1/brain/status` or `/api/v1/ring1/capabilities`.

### 5. What Is Broken?
- **Production Context Resolution API (SEC-02-F02):** `POST /api/v1/context/resolve` fails closed with HTTP 403 for any request containing a client `case_id` because `_context_engine = ContextEngine()` is instantiated without injecting a case validator.
- **Store-Level Candidate Filtering (SEC-05-F01):** `SqlAlchemyRetrievalStore.search_records()` does not filter out `candidate` records, leaking unvalidated knowledge into ordinary store retrieval calls.
- **Next.js Version in Audit Worktree:** Audit worktree pins `next: 16.4.0` in `frontend/package.json` (triggering Next.js SecurityFatalError build blocks), while main repository worktree was upgraded to `16.4.5`.

### 6. What Remains Unverified?
- **Live Third-Party LLM Execution:** External API generation via OpenAI, DeepSeek, or Gemini was not executed against live billable API endpoints during this audit to avoid unauthorized costs and credential exposure. Real runtime fallback to deterministic extractors was verified.

---

## B. Confirmed Mock / Fake / Placeholder List

### FINDING-01: Main Workspace Panels are Pure Mocks / Empty States
- **Status:** **MOCK / SIMULATED**
- **Location:** [workspace-client.tsx](file:///home/mohamed-alaa/.gemini/antigravity/worktrees/brain-co/brain_module_technical_audit/frontend/src/components/workspace/workspace-client.tsx#L19-L22), [app.ts](file:///home/mohamed-alaa/.gemini/antigravity/worktrees/brain-co/brain_module_technical_audit/frontend/src/content/app.ts#L394-L398)
- **Evidence:**
  ```typescript
  // frontend/src/components/workspace/workspace-client.tsx:19-22
  /**
   * Legal Intelligence workspace (task H). MOCK/D8: no workspace API or data
   * source exists — every panel is an honest empty state; the prototype's
   * sample metrics (12 cases, 24 clients, …) are deliberately NOT shown.
   */
  ```
  `OverviewPanel()` renders static cards with `workspaceCopy.noData` ("—") and `workspaceCopy.notConnected` ("Backend not connected — MOCK").
  Tabs `"cases"`, `"clients"`, `"knowledge"`, and `"insights"` all render:
  `<p>{workspaceCopy.emptyNote(workspaceCopy.tabs[tabIds.indexOf(id)])}</p>`.
- **Why it is not real:** No API request is made to fetch cases, clients, observations, or memory records. The workspace displays zero real backend data.
- **Fix to make it functional:** Wire `OverviewPanel` to `/api/v1/brain/status`, build a Knowledge explorer tab consuming `GET /api/v1/ring1/knowledge`, and build an Observation feed tab consuming `GET /api/v1/observations`.
- **Owner:** Frontend

---

### FINDING-02: Workspace "AI Employee" Bypasses Ring 1 Cognitive Mesh
- **Status:** **MOCK / NON-FUNCTIONAL FOR RING 1**
- **Location:** [workspace-client.tsx](file:///home/mohamed-alaa/.gemini/antigravity/worktrees/brain-co/brain_module_technical_audit/frontend/src/components/workspace/workspace-client.tsx#L190-L196), [ai.py](file:///home/mohamed-alaa/.gemini/antigravity/worktrees/brain-co/brain_module_technical_audit/backend/app/api/v1/ai.py#L88-L123)
- **Evidence:**
  The `AIEmployeePanel` in `workspace-client.tsx` makes a POST request to `/api/ai/prompt`:
  ```typescript
  const response = await fetch("/api/ai/prompt", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ prompt: trimmedInput, context: "legal" }),
  });
  ```
  In `backend/app/api/v1/ai.py`, endpoint `/prompt` directly invokes `llm.generate()` with static system prompts (`LEGAL_SYSTEM_PROMPT` / `BRAIN_SYSTEM_PROMPT`). It does **not** call `PerceptionEngine`, does **not** resolve context via `ContextEngine`, does **not** query `BasicRetrievalEngine`, and does **not** record observations.
- **Why it is not real:** It masquerades as an "AI Employee grounded in organizational knowledge," but it is an ungrounded demo LLM wrapper with zero access to case records or persistent memory.
- **Fix to make it functional:** Route workspace inquiries through `MeshRouter` via `retrieval.query` and `perception.structure_input` to provide retrieval-augmented reasoning over case memory.
- **Owner:** Frontend / AI

---

### FINDING-03: Fabricated Source Engine in Test Console Delegation Graph
- **Status:** **MOCK / SIMULATED LOGGING**
- **Location:** [test_scenario_service.py](file:///home/mohamed-alaa/.gemini/antigravity/worktrees/brain-co/brain_module_technical_audit/backend/app/ring1/services/test_scenario_service.py#L285-L303)
- **Evidence:**
  In `TestScenarioService.execute()`:
  ```python
  # backend/app/ring1/services/test_scenario_service.py:285-303
  req_mem = MeshRequest(
      sender_engine="client",            # <--- Real request sender is "client"!
      recipient_capability=MEMORY_STORE_RECORD,
      context_ref=ctx_ref,
      payload={...},
  )
  ...
  yield record_event(
      source_engine="observation",        # <--- Falsely recorded as "observation" for UI graph!
      destination_engine="memory",
      capability=MEMORY_STORE_RECORD,
      event_type="memory_stored",
      status="completed",
  )
  ```
- **Why it is not real:** The test runner acts as an external script calling the engines sequentially. To make the frontend Delegation Graph display an animated edge from "observation" to "memory", the runner hardcodes `source_engine="observation"` in the SSE event payload, masking the fact that the client runner dispatched the call.
- **Fix to make it functional:** Enable true autonomous engine delegation (e.g. have `ObservationEngine` dispatch directly to `MemoryEngine` when `auto_delegate=True`) and log the true `request.sender_engine`.
- **Owner:** Backend / AI

---

### FINDING-04: Hardcoded "completed" Status in Context Resolution Event
- **Status:** **SIMULATED EVENT LOGGING**
- **Location:** [test_scenario_service.py](file:///home/mohamed-alaa/.gemini/antigravity/worktrees/brain-co/brain_module_technical_audit/backend/app/ring1/services/test_scenario_service.py#L206-L214)
- **Evidence:**
  ```python
  # backend/app/ring1/services/test_scenario_service.py:206-214
  resp_c = await self.router.dispatch(req_c)
  dur_c = round((time.perf_counter() - t0) * 1000, 2)
  context_ref_str = resp_c.payload.get("context_ref", "")
  ctx_ref = ContextRef(
      context_ref_id=context_ref_str,
      organization_id=org_id,
      case_id=case_id,
      domain_id="intellectual_property",
      resolution_status=ResolutionStatus.EXPLICIT,
  )
  yield record_event(
      source_engine="client",
      destination_engine="context",
      capability=CONTEXT_RESOLVE,
      event_type="context_resolved",
      status="completed",                 # <--- Hardcoded as "completed" regardless of resp_c.status!
      duration_ms=dur_c,
      response_envelope=resp_c.model_dump(mode="json"),
      details={"context_ref": context_ref_str, "status": resp_c.payload.get("status")},
  )
  ```
- **Why it is not real:** If `ContextEngine` fails closed (e.g. `resp_c.status == ResultStatus.FAILED`), `test_scenario_service.py` ignores the error, constructs a synthetic `ctx_ref` with `ResolutionStatus.EXPLICIT`, and emits `status="completed"`.
- **Fix to make it functional:** Evaluate `resp_c.status` dynamically: `status="completed" if resp_c.status == ResultStatus.SUCCESS else "failed"`, and halt execution if context resolution fails.
- **Owner:** Backend

---

### FINDING-05: Missing extraction_mode Field in Legal Schemas
- **Status:** **STUB / PLACEHOLDER**
- **Location:** [extracted-knowledge-tab.tsx](file:///home/mohamed-alaa/.gemini/antigravity/worktrees/brain-co/brain_module_technical_audit/frontend/src/components/ring1-test-console/extracted-knowledge-tab.tsx#L88)
- **Evidence:**
  In `extracted-knowledge-tab.tsx:88`:
  `<p className="text-[10px] text-[#8a94a8]">Type: {knowledge?.document_type} | Mode: {knowledge?.extraction_mode}</p>`
  In `brain/src/brain/extensions/legal/schemas.py`, `DocumentStructuredKnowledge` has **no field named `extraction_mode`**.
- **Why it is not real:** The frontend attempts to display whether extraction was performed via `"llm"` or `"deterministic"`, but the backend schema does not supply this field. In the browser, `Mode:` renders blank/undefined.
- **Fix to make it functional:** Add `extraction_mode: str = "deterministic"` (or `"llm"`) to `DocumentStructuredKnowledge` in `schemas.py` and populate it in `LegalStructuredKnowledgeExtractor`.
- **Owner:** AI / Frontend

---

### FINDING-06: Onboarding Upload Screen Disconnected from Ring 1
- **Status:** **NOT CONNECTED / FAILING STUB**
- **Location:** [upload/page.tsx](file:///home/mohamed-alaa/.gemini/antigravity/worktrees/brain-co/brain_module_technical_audit/frontend/src/app/onboarding/upload/page.tsx#L22-L52), [upload/route.ts](file:///home/mohamed-alaa/.gemini/antigravity/worktrees/brain-co/brain_module_technical_audit/frontend/src/app/api/documents/upload/route.ts#L70-L81)
- **Evidence:**
  Comment in `upload/page.tsx:22`:
  `/** Expected upload contract location (docs/FLOW_AUDIT.md, contract 4). MOCK: does not exist yet — a real request is made and its real failure is surfaced. */`
  The form posts to `/api/documents/upload`, which forwards to `/sources` (Ring 0 raw sources). It requires an authenticated session cookie that onboarding users do not possess, resulting in an unhandled 401 or 404 error. It has zero integration with the Ring 1 PDF ingestion pipeline.
- **Why it is not real:** End users attempting to upload documents during onboarding cannot ingest them into Ring 1 memory.
- **Fix to make it functional:** Connect the onboarding document upload screen to `/api/v1/ring1/upload-pdf` or persist uploaded files to the user's initial case context.
- **Owner:** Frontend / Backend

---

## C. Disconnected Components

1. **Authenticated Observation WebSocket Stream (`/api/v1/ws/observations`):**
   - **Backend Implementation:** [ws.py](file:///home/mohamed-alaa/.gemini/antigravity/worktrees/brain-co/brain_module_technical_audit/backend/app/api/v1/ws.py), [ws_manager.py](file:///home/mohamed-alaa/.gemini/antigravity/worktrees/brain-co/brain_module_technical_audit/backend/app/core/ws_manager.py).
   - **Status:** Fully functional on backend (JWT validation, active user check, tenant connection partitioning, scope filtering).
   - **Disconnection:** Zero files in `frontend/src/` open a WebSocket connection. The frontend only consumes SSE streams for developer test runs.
2. **Brain Health & Capabilities API (`/api/v1/brain/status` & `/api/v1/ring1/capabilities`):**
   - **Backend Implementation:** [brain.py](file:///home/mohamed-alaa/.gemini/antigravity/worktrees/brain-co/brain_module_technical_audit/backend/app/api/v1/brain.py).
   - **Status:** Returns active engines, registered capabilities, registered domain extensions, and database health.
   - **Disconnection:** Only queried inside `Ring1TestConsole` upon user button click; completely absent from main application dashboard or workspace header.
3. **Cursor-Paginated Observation Listing (`GET /api/v1/observations`):**
   - **Backend Implementation:** [observations.py](file:///home/mohamed-alaa/.gemini/antigravity/worktrees/brain-co/brain_module_technical_audit/backend/app/api/v1/observations.py#L144-L239).
   - **Status:** Supports HMAC-signed cursors, filters by event type/source, and returns structured metadata.
   - **Disconnection:** No user-facing feed or table in the frontend workspace queries this endpoint.

---

## D. Broken Implementations

1. **Production Context Resolution Fails Closed on Case ID (SEC-02-F02):**
   - **Location:** [context.py](file:///home/mohamed-alaa/.gemini/antigravity/worktrees/brain-co/brain_module_technical_audit/backend/app/api/v1/context.py#L18)
   - **Defect:** `_context_engine = ContextEngine()` is instantiated without a `case_validator`. In live runtime testing:
     ```bash
     POST /api/v1/context/resolve {"domain_id": "legal", "case_id": "case-123"}
     # Response: HTTP 403 Forbidden
     # {"error": {"code": "FORBIDDEN", "message": "Access denied to case 'case-123': no case validator configured to verify case scope."}}
     ```
   - **Impact:** Any external HTTP client calling context resolution with an explicit case ID is rejected.
2. **SqlAlchemyRetrievalStore Omits Candidate Status Filter (SEC-05-F01):**
   - **Location:** [stores.py](file:///home/mohamed-alaa/.gemini/antigravity/worktrees/brain-co/brain_module_technical_audit/backend/app/infrastructure/database/stores.py#L382-L391)
   - **Defect:** In `SqlAlchemyRetrievalStore.search_records()`, the SQL statement filters by `organization_id` and `case_id`, but omits `.where(MemoryRecord.status.notin_(["candidate", "rejected"]))`.
   - **Live Evidence:** During PDF pipeline execution, a query for Article 147 returned a record with `status='candidate'`. Direct store queries leak unvalidated candidate knowledge to ordinary search callers.

---

## E. Genuine Functional Components

The following components were verified through live runtime execution, database inspection, and test suites:

1. **ObservationEngine Persistence & Idempotency:**
   - **Verification:** Submitted real observation via `POST /api/v1/observations` with unique idempotency key. Row confirmed in PostgreSQL `ring1_observations`. Resubmitted duplicate key; received existing observation without duplicate insert.
2. **BasicMemoryEngine Persistence & Access Control:**
   - **Verification:** Stored knowledge record with UUID `b13982bf-9a79-4f3e-a6fb-27a31badb066`. Row confirmed in PostgreSQL `ring1_memory_records`. Retrieved independently via `GET /api/v1/memory/{id}` with 200 OK. Cross-tenant retrieval returned sanitized 404.
3. **BasicRetrievalEngine Scoped Search:**
   - **Verification:** Queried `GET /api/v1/retrieval/search?q=Article`. While status was `candidate`, query returned 0 results. Once promoted to `validated`, query returned 1 result with `score=8.0`, snippet, and payload.
4. **PDF Binary Parser & Extractor:**
   - **Verification:** Ingested multi-page PDF binary. Extracted exact character count, 2 pages, SHA-256 file hash, and text excerpts.
5. **Deterministic Legal Extractor:**
   - **Verification:** Successfully parsed Egyptian Civil Code Article 147, financial retainer clauses, and contracting parties using regex extractors when the LLM service was unconfigured.
6. **In-Process Mesh Router:**
   - **Verification:** Dispatched requests across `perception`, `observation`, `context`, `memory`, `retrieval`, and `planning` using typed `MeshRequest` and `MeshResponse` envelopes. Enforced timeout and delegation limits.
7. **Raw Ingestion Pipeline (Data Engineering):**
   - **Verification:** `data-engineering/orgbrain_ingest/` verified with 24 passing unit tests covering checksum validation and local storage.

---

## F. Unverified Components

1. **Live Production LLM Provider Calls:**
   - **Reason Unverified:** The local environment does not have a live `OPENAI_API_KEY` configured. Live execution produced:
     `{"event": "llm_request_failed", "errorType": "AUTHENTICATION_FAILED", "errorMessage": "openai client not configured — valid API key required"}`.
   - **Behavior Observed:** The system successfully caught this error and fell back to deterministic extractors. Live cloud inference with billable API credits was not executed.
2. **Live WebSocket Scalability Under Load:**
   - **Reason Unverified:** While unit tests in `test_ws_connection_pool.py` verified connection establishment, broadcast delivery, and disconnect cleanup, large-scale concurrent connection load (e.g. 1000+ simultaneous clients) was not benchmarked.

---

## G. End-to-End Reality Scenarios

### Scenario A — Observation
- **Action:** Submit real observation through `POST /api/v1/observations` → retrieve via `GET /api/v1/observations?type=...`.
- **Observed Result:**
  - `POST /api/v1/observations` returned **HTTP 201 Created**, ID: `5aab54ba-ab86-42dc-b605-f43e7bae4ed1`.
  - Row confirmed in PostgreSQL `ring1_observations`.
  - `GET /api/v1/observations` returned **HTTP 200 OK**, `items_count: 1`, matching ID verified.
- **Verdict:** **REAL & VERIFIED**

### Scenario B — Memory
- **Action:** Store a memory record → retrieve it in a separate request via `GET /api/v1/memory/{id}`.
- **Observed Result:**
  - Record ID: `b13982bf-9a79-4f3e-a6fb-27a31badb066` stored in PostgreSQL `ring1_memory_records`.
  - `GET /api/v1/memory/b13982bf-9a79-4f3e-a6fb-27a31badb066` with Bearer token returned **HTTP 200 OK**.
  - Payload keys, context reference, and `status: candidate` verified.
- **Verdict:** **REAL & VERIFIED**

### Scenario C — Retrieval
- **Action:** Search for known stored record via `GET /api/v1/retrieval/search?q=Article`.
- **Observed Result:**
  - Candidate record returned 0 matches (properly filtered out).
  - Once updated to `status: validated`, search returned **HTTP 200 OK**, `total_found: 1`, `score: 8.0`, with exact Egyptian Civil Code Article 147 snippet.
- **Verdict:** **REAL & VERIFIED**

### Scenario D — Context
- **Action:** Submit context resolution request via `POST /api/v1/context/resolve`.
- **Observed Result:**
  - Without case ID: returned **HTTP 200 OK**, status `"ambiguous"`, flagged missing case ID.
  - With client case ID (`"case-123"`): returned **HTTP 403 Forbidden** with `"no case validator configured"`.
- **Verdict:** **PARTIALLY IMPLEMENTED (Engine works; API production DI missing)**

### Scenario E — PDF Ingestion
- **Action:** Ingest valid multi-page PDF agreement via `POST /api/v1/ring1/upload-pdf`.
- **Observed Result:**
  - Extracted 2 pages, text, parties, and Article 147 facts via deterministic fallback.
  - Recorded observation event in PostgreSQL `ring1_observations`.
  - Persisted structured facts to PostgreSQL `ring1_memory_records`.
  - Retrieved stored facts independently.
- **Verdict:** **REAL & VERIFIED (Deterministic fallback path)**

### Scenario F — Mesh Execution
- **Action:** Execute multi-engine workflow through MeshRouter.
- **Observed Result:**
  - MeshRouter dispatches typed envelopes to registered capabilities.
  - PlanStepExecutor steps through DAG and handles prerequisite blocks.
  - *Caveat:* `TestScenarioService` orchestrates calls sequentially and injects simulated source engine names for UI display.
- **Verdict:** **REAL EXECUTION WITH SIMULATED EVENT LOGGING**

### Scenario G — Frontend Workspace
- **Action:** Open main user workspace at `/workspace` and inspect all tabs.
- **Observed Result:**
  - All 6 panels render empty state placeholders ("Backend not connected — MOCK").
  - Only working UI is the developer debug modal (`Ring1TestConsole`).
- **Verdict:** **MOCK / NOT CONNECTED**

---

## H. Minimal Required Fix List

### P0 — Critical Blockers (Make Core Workflows Real & Unbroken)
1. **[Backend] Wire Case Validator in Context API (SEC-02-F02):**
   - File: `backend/app/api/v1/context.py`
   - Action: Inject `db: Session = Depends(get_db)` and pass `case_validator = lambda org, c, u: CaseService.validate_case(db, org, c, u)` into `ContextEngine`.
2. **[Backend] Filter Candidate Records in SqlAlchemyRetrievalStore (SEC-05-F01):**
   - File: `backend/app/infrastructure/database/stores.py`
   - Action: Add `.where(MemoryRecord.status.notin_(["candidate", "rejected"]))` to `search_records()`.
3. **[Frontend] Align Next.js Dependency to 16.4.5:**
   - File: `frontend/package.json`
   - Action: Update `"next": "16.4.0"` to `"next": "16.4.5"` to clear the SecurityFatalError build check.

### P1 — Required Ring 1 Functionality (Connect Frontend to Real Backend)
1. **[Frontend] Implement WebSocket Client Hook:**
   - File: `frontend/src/hooks/use-observation-ws.ts`
   - Action: Connect to `/api/v1/ws/observations` with JWT cookie/token and dispatch live events.
2. **[Frontend] Connect Workspace Observation Feed:**
   - File: `frontend/src/components/workspace/workspace-client.tsx`
   - Action: Replace empty mock state with real observation table querying `GET /api/v1/observations`.
3. **[Frontend] Build Case Knowledge Browser in Workspace:**
   - File: `frontend/src/components/workspace/workspace-client.tsx`
   - Action: Connect "Knowledge" tab to `GET /api/v1/ring1/knowledge?case_id=...`.
4. **[Frontend] Build Workspace Context Switcher:**
   - File: `frontend/src/components/workspace/workspace-client.tsx`
   - Action: Add dropdown to select active case ID and attach `X-Case-ID` header to all API calls.

### P2 — Quality & Observability Improvements
1. **[AI / Frontend] Add extraction_mode to DocumentStructuredKnowledge Schema:**
   - Files: `brain/src/brain/extensions/legal/schemas.py`, `frontend/src/components/ring1-test-console/types.ts`
   - Action: Explicitly flag whether knowledge extraction was produced by LLM or deterministic regex.
2. **[Backend] Log True Request Senders in Test Scenarios:**
   - File: `backend/app/ring1/services/test_scenario_service.py`
   - Action: Record `source_engine=req.sender_engine` instead of hardcoding `"observation"`.

---

## I. Data Science & Database Team Findings

1. **Delivered by Data Engineering:**
   - Raw ingestion pipeline (`data-engineering/orgbrain_ingest/`) is 100% operational with 24 passing unit tests covering checksum validation and storage.
2. **Implemented by Backend on Behalf of Data Team (No duplicate work needed):**
   - Tables `ring1_observations` and `ring1_memory_records` created and migrated in PostgreSQL.
   - Tenant composite unique indexing `(organization_id, idempotency_key)` and `NOT NULL` constraints applied.
   - PostgreSQL pgvector extension enabled.
3. **Actionable Deliverables for Data Team:**
   - Formally review and approve the Pydantic schemas in `backend/app/schemas/ring1_api.py`.
   - Ensure that any future table schema changes are provided via Alembic migrations.
4. **Ring 2 Scope (Not Missing from Ring 1):**
   - Semantic vector embeddings, HNSW/IVFFlat vector indexes, and multi-store knowledge graphs belong exclusively to Ring 2 RAG. They are not required for Ring 1 closure.
