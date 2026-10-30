# Implementation Plan: GUI-Based Ring 1 Live Integration Test Console

**Target System**: `brain-co` (Backend: FastAPI / PostgreSQL; Frontend: Next.js 16)  
**Goal**: Build an interactive floating test console (`Ring 1 Live Test`) in the existing frontend to visually verify that the six Ring 1 engines (Perception, Observation, Context, Basic Memory, Basic Retrieval, Planning) actually operate together as one integrated system.

---

## 1. Architectural Discovery & Real Entry Points

### 1.1 Backend Ring 1 Architecture
- **Mesh Entry Point**: The authoritative entry point is `MeshRouter.dispatch(request: MeshRequest) -> MeshResponse` in `backend/app/ring1/mesh/router.py`.
- **Six Engines**:
  1. `PerceptionEngine`: `backend/app/ring1/engines/perception.py` (`perception.structure_input`)
  2. `ObservationEngine`: `backend/app/ring1/engines/observation.py` (`observation.record_event`) -> PostgreSQL `ring1_observations`
  3. `ContextEngine`: `backend/app/ring1/engines/context.py` (`context.resolve`)
  4. `BasicMemoryEngine`: `backend/app/ring1/engines/memory.py` (`memory.store_record`, `memory.get_record`) -> PostgreSQL `ring1_memory_records`
  5. `BasicRetrievalEngine`: `backend/app/ring1/engines/retrieval.py` (`retrieval.query`)
  6. `PlanningEngine`: `backend/app/ring1/engines/planning.py` (`planning.create_plan`, `planning.request_replan`, `planning.get_plan_status`)
- **Persistence**: Tested against real PostgreSQL container via SQLAlchemy models.
- **Current Limitation**: No public HTTP endpoint exists yet for Ring 1 mesh execution. To drive the GUI, we need a lightweight, secure API endpoint that wraps the mesh and emits real execution traces.

### 1.2 Frontend Architecture
- **Framework**: Next.js 16.4.0 (React 19, Tailwind CSS 4, Framer Motion, Lucide icons).
- **Existing Floating Component**: `frontend/src/components/floating-chat-widget.tsx` sits at `fixed bottom-4 right-4 sm:bottom-6 sm:right-6 z-50`.
- **Layout Mounting**: Components are mounted in `frontend/src/app/layout.tsx`.
- **API Proxy Pattern**: Frontend API routes in `frontend/src/app/api/...` forward requests to `${BACKEND_API_URL}/...` with `backend_token` cookie.

---

## 2. Proposed Architecture & Implementation Steps

```
+--------------------------------------------------------------------------+
|                              Next.js Frontend                            |
|                                                                          |
|  [FloatingChatWidget] (bottom-right)      [Ring1TestConsole] (bottom-left)|
|                                                        |                 |
|                                                EventSource / fetch SSE   |
|                                                        v                 |
|                                            /api/ring1/test-run           |
+--------------------------------------------------------+-----------------+
                                                         |
                                            HTTP POST (stream=true)
                                                         v
+--------------------------------------------------------------------------+
|                              FastAPI Backend                             |
|                                                                          |
|                   POST /api/v1/ring1/test-run                            |
|             (Protected by dev/admin auth guard in deps.py)               |
|                                    |                                     |
|                                    v                                     |
|                       Ring1TestRunner (service.py)                       |
|        - Instantiates MeshRouter & 6 engines with db session             |
|        - Yields real-time events via Server-Sent Events (SSE)            |
|        - Stores completed runs in TestRunRegistry                        |
|                                    |                                     |
|           +------------------------+-------------------------+           |
|           |                        |                         |           |
|           v                        v                         v           |
|      Perception               Observation                 Context        |
|           |                        | (PostgreSQL)            |           |
|           v                        v                         v           |
|     Basic Memory            Basic Retrieval               Planning       |
|      (PostgreSQL)                                                        |
+--------------------------------------------------------------------------+
```

---

## 3. Step-by-Step Execution Plan

### Step 1: Backend Ring 1 Test Execution Service
- Create `backend/app/ring1/service.py`:
  - `Ring1TestRunner`:
    - Sets up `MeshRouter`, `CapabilityRegistry`, and all 6 engines.
    - Uses `FakeLLMProvider` for deterministic, zero-cost, offline execution.
    - Emits structured event envelopes during execution:
      `{ sequence, timestamp, run_id, source_engine, destination_engine, capability, event_type, status, duration_ms, request_envelope, response_envelope, plan_version, details }`.
    - Implements:
      1. `run_e2e_scenario(stream=True/False)`: Full 6-engine legal workflow with synthetic case IDs, PostgreSQL persistence, and cross-case isolation checks.
      2. `run_force_failure_scenario(stream=True/False)`: Plan creation (v1), Step 1 completion, controlled Step 2 failure (`CONTEXT_INSUFFICIENT`), bounded replanning to v2 preserving completed Step 1, and plan comparison.
      3. `run_custom_prompt(prompt, stream=True/False)`: Custom text structured via Perception, resolved via Context, and planned via Planning.
  - `TestRunRegistry`: In-memory thread-safe cache storing recent 30 runs for deep retrieval and inspection.

### Step 2: Backend API Endpoints & Security
- Create `backend/app/api/v1/ring1.py`:
  - `POST /api/v1/ring1/test-run`:
    - Body: `{ mode: "e2e" | "force_failure" | "custom_prompt", custom_prompt?: str, stream?: bool }`.
    - If `stream: true`, returns `StreamingResponse(media_type="text/event-stream")`.
    - If `stream: false`, returns `{ run_id, status, events, initial_plan, replanned_plan, graph, summary }`.
  - `GET /api/v1/ring1/test-runs/{run_id}`: Retrieves stored run by ID.
  - `GET /api/v1/ring1/capabilities`: Returns registered capabilities and status.
- Add `get_test_operator_user` in `backend/app/api/deps.py`:
  - Allows access in development mode (`ENVIRONMENT != "production"`) or requires authenticated `admin` role.
  - Strict isolation: uses synthetic IDs only, never exposes database secrets or other tenant data.
- Mount `ring1_router` at `/api/v1/ring1` in `backend/app/api/v1/__init__.py`.

### Step 3: Frontend API Proxy Routes
- Create `frontend/src/app/api/ring1/test-run/route.ts`:
  - Proxies `POST` to backend `/api/v1/ring1/test-run`, forwarding headers, auth cookies, and supporting SSE stream passthrough.
- Create `frontend/src/app/api/ring1/test-runs/[runId]/route.ts`:
  - Proxies `GET` to backend `/api/v1/ring1/test-runs/{run_id}`.

### Step 4: Frontend Floating Ring 1 Live Test Console
- Create `frontend/src/components/ring1-test-console/ring1-test-console.tsx` and sub-components:
  - **Floating Launcher Button**:
    - Placed at `fixed bottom-4 left-4 sm:bottom-6 sm:left-6 z-50` with label `Ring 1 Live Test` and animated status beacon (avoids overlapping the floating chat widget on the right).
    - Controlled visibility (active in dev mode or admin session).
  - **Compact & Expanded Modal** (`w-[calc(100vw-2rem)] sm:w-[680px] lg:w-[760px] h-[640px] max-h-[calc(100vh-5rem)]`):
    - **Header & Controls**:
      - `Run Integration Test` (Primary Action).
      - `Force Failure & Replan` (Controlled Test Action).
      - Live status badge (`Idle`, `Running`, `Completed`, `Failed`, `Replanned v2`).
      - Chat-style input composer for testing arbitrary prompts through Perception.
    - **Tab 1: Live Trace**:
      - Chronological event timeline showing sequence #, source engine -> destination capability, event type, status badge (`COMPLETED`, `RUNNING`, `FAILED`, `DENIED`), and duration ms.
      - Clickable rows selecting an event for deep inspection.
    - **Tab 2: Delegation Graph**:
      - SVG visual graph of the 6 engines (`Perception`, `Observation`, `Context`, `Memory`, `Retrieval`, `Planning`).
      - Visual node states: `Not Invoked`, `Running` (pulsing brand glow), `Completed` (emerald), `Failed` (crimson), `Denied` (amber).
      - Directed edges drawn dynamically ONLY when real peer-to-peer delegation occurs between engines.
    - **Tab 3: Plan Versions**:
      - Side-by-side comparison of Plan v1 vs Plan v2.
      - Explicitly shows Step 1 as `Retained & Completed` (green badge), Step 2 as `Failed: Context Insufficient` (red badge), and Step 3+ as `Added in v2` (blue badge).
      - Displays failure evidence and replan rationale.
    - **Tab 4: Event Details**:
      - Deep JSON inspector showing exact `MeshRequest` and `MeshResponse` envelopes, task IDs, trace IDs, sanitized payloads, and error codes.
    - **Tab 5: Test Summary**:
      - High-level verification scorecard: invoked vs skipped engines, cross-case isolation status, database persistence counts, and plan state.
- Mount `<Ring1TestConsole />` in `frontend/src/app/layout.tsx`.

### Step 5: Testing & Acceptance Verification
1. **Backend Tests**:
   - Create `backend/tests/test_api_v1_ring1.py` covering:
     - Baseline E2E execution (`mode="e2e"`).
     - Force failure & replan execution (`mode="force_failure"`).
     - SSE event stream format validation.
     - Auth and dev-mode security validation.
2. **Frontend Validation**:
   - Run `npm --prefix frontend run typecheck`.
   - Verify UI layout, responsiveness, animations, and real-time event updates.
3. **Regression Tests**:
   - Run all 35 Ring 1 tests: `.venv/bin/pytest backend/tests/ring1 -v`.
   - Run full suite: `.venv/bin/pytest backend/tests ai/tests`.
4. **Documentation**:
   - Update `docs/progress.md` and `docs/journal/2026-10-28.md`.
