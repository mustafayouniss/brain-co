# Independent Remediation Security Audit

**Target System**: `brain-co` (Graduation Project Monorepo — Ring 1 & General Brain)  
**Audit Worktree**: `/home/mohamed-alaa/.gemini/antigravity/worktrees/brain-co/brain_module_technical_audit`  
**Auditor**: Senior Application Security Engineer, Backend Architect & Independent Reviewer  
**Audit Date**: 2026-11-15  
**Audit Scope**: Uncommitted changes across `SEC-01` (Tenant-Scoped Idempotency), `SEC-02` (Context Trust Boundary), `SEC-05` (Memory Lifecycle), and related infrastructure/API modifications.

---

## 1. Executive Summary

A comprehensive, evidence-based security and architecture audit was conducted on all uncommitted remediation changes in the `brain_module_technical_audit` branch.

### Overall Verdict: **NOT READY FOR COMBINED COMMIT**

While **SEC-01 (Tenant-Scoped Idempotency)** has been thoroughly remediated with strong protocol enforcement, multi-tenant isolation, composite unique indexes, and schema NOT NULL constraints, the overall changes are **NOT READY** for a combined commit because significant authorization bypasses and lifecycle leaks remain in **SEC-02 (Context Trust Boundary)** and **SEC-05 (Memory Lifecycle)**:

1. **SEC-02 Fail-Open Case Authorization Gap**: In `brain/src/brain/general/engines/context.py`, client-supplied case hints are accepted and stamped with `ResolutionStatus.EXPLICIT` whenever `self._case_validator` is `None`. In production (`backend/app/api/v1/context.py:18` and `backend/app/ring1/service.py:69`), `ContextEngine` is instantiated with **no case validator**. Any authenticated user can submit arbitrary, non-existent, or foreign case IDs and receive an authoritative `EXPLICIT` resolution.
2. **SEC-02 Unchecked Header Trust in API Context**: In `backend/app/core/context.py:112-125`, `get_brain_context` blindly trusts the client-provided `X-Case-ID` header and `?case_id=` query parameter without querying the PostgreSQL `cases` table.
3. **SEC-02 Observation Endpoint Case Scope Override**: In `backend/app/api/v1/observations.py:45`, `payload.case_id` overrides `context.effective_scope_id` without validation against the server context or the `cases` table.
4. **SEC-05 Retrieval Ingestion Leakage**: `SqlAlchemyRetrievalStore.search_records` (and `InMemoryRetrievalStore`) fails to filter out unvalidated `candidate` memory records. The mesh capability `retrieval.query` exposes unverified candidate facts to downstream retrieval consumers.
5. **SEC-05 Direct Store Write Active Default**: `SqlAlchemyMemoryStore.save_record` defaults unvalidated records to `status="active"`, bypassing engine-level human validation gates if called directly.

All 405 tests currently pass across the repository (311 backend, 16 architecture, 52 AI, 26 data engineering). However, passing tests in this instance masked structural fail-open boundaries because existing tests only exercised `case_validator` with mocked test fixtures rather than production wiring.

---

## 2. Repository and Git Baseline

### 2.1 Git Metadata
- **Repository Root**: `/home/mohamed-alaa/.gemini/antigravity/worktrees/brain-co/brain_module_technical_audit`
- **Active Branch**: `brain_module_technical_audit`
- **Current HEAD Commit**: `8db328c2e9bc331337b9864d71ad268b6b82e338`
- **Working Tree Status**: Dirty (21 tracked modified files, 6 untracked files)

### 2.2 Migration Graph & Alembic Status
- **Current Database Head**: `d60e5f8a9b2c (head)`
- **Migration Linear Chain**:
  `6dd2ff08b0bb` (pgvector)  
  $\rightarrow$ `778be99882b6` (users)  
  $\rightarrow$ `e819b932c01a` (sources)  
  $\rightarrow$ `f19a0a1b2c3d` (ring1_tables)  
  $\rightarrow$ `a28b3c4d5e6f` (tasks_outbox_audit)  
  $\rightarrow$ `b39c4d5e6f7a` (cases table & sources foreign keys)  
  $\rightarrow$ `c59d4e7f8a1b` (composite unique index on `(organization_id, idempotency_key)`)  
  $\rightarrow$ `d60e5f8a9b2c` (enforce `NOT NULL` on `organization_id`)

### 2.3 Scope and File-to-Issue Mapping

| File Path | Status | Primary Issue | Description |
|---|---|---|---|
| `brain/src/brain/general/contracts/storage.py` | Modified | SEC-01 | Requires `organization_id: str` without default on `find_by_idempotency_key` |
| `brain/src/brain/general/stores/in_memory_observation.py` | Modified | SEC-01 | Enforces non-empty `organization_id` on lookups and saves |
| `brain/src/brain/general/stores/in_memory_memory.py` | Modified | SEC-01 | Enforces non-empty `organization_id` on lookups and saves |
| `backend/app/infrastructure/database/stores.py` | Modified | SEC-01, SEC-05 | Enforces tenant-scoped lookups; `save` validations; status updates |
| `backend/app/ring1/models/observation.py` | Modified | SEC-01 | Adds `nullable=False` and composite index to `Observation` and `MemoryRecord` |
| `backend/app/api/v1/observations.py` | Modified | SEC-01, SEC-02 | Scopes duplicate lookup to `context.organization_id`; payload case handling |
| `brain/src/brain/general/engines/observation.py` | Modified | SEC-01 | Enforces context validation, removes `"org-default"`, rejects spoofing |
| `backend/migrations/versions/c59d4e7f8a1b_*.py` | Untracked | SEC-01 | Creates composite partial unique index `(organization_id, idempotency_key)` |
| `backend/migrations/versions/d60e5f8a9b2c_*.py` | Untracked | SEC-01 | Pre-checks legacy rows and alters `organization_id` to `NOT NULL` |
| `backend/tests/ring1/test_idempotency_tenant_isolation.py` | Untracked | SEC-01 | 12 adversarial tests for multi-tenant idempotency isolation |
| `brain/src/brain/general/contracts/context_ref.py` | Modified | SEC-02, SEC-05 | Adds `validation_authority: bool = False` field |
| `brain/src/brain/general/engines/context.py` | Modified | SEC-02 | Context boundary enforcement, case validator hook, LLM fallback clamp |
| `backend/app/api/v1/context.py` | Modified | SEC-02 | REST endpoint handling 403 on case/org override; instantiates `ContextEngine` |
| `backend/tests/ring1/test_context_security_adversarial.py` | Untracked | SEC-02 | 8 adversarial tests for context boundary enforcement |
| `brain/src/brain/general/engines/memory.py` | Modified | SEC-01, SEC-05 | Requires `organization_id`; enforces `candidate` lifecycle status |
| `backend/tests/ring1/test_memory_lifecycle_security.py` | Untracked | SEC-05 | 5 tests for memory validation authority and candidate status |
| `backend/app/ring1/services/pdf_pipeline_service.py` | Modified | SEC-01, SEC-02 | Injects `context_ref` into mesh context resolution call |
| `backend/app/ring1/services/test_scenario_service.py` | Modified | SEC-01, SEC-02 | Injects `context_ref` into mesh context resolution calls |
| `backend/tests/ring1/test_context.py` | Modified | SEC-02 | Updates unit test requests with explicit `ContextRef` |
| `backend/tests/ring1/test_e2e_mesh_integration.py` | Modified | SEC-02 | Updates unit test requests with explicit `ContextRef` |
| `backend/tests/ring1/test_mesh_integration.py` | Modified | SEC-01 | Adds `ContextRef` to mesh observation calls |
| `backend/tests/ring1/test_observation.py` | Modified | SEC-01 | Adds `ContextRef` to observation engine unit tests |
| `docs/backend/architecture.md` | Modified | Documentation | Documents migrations `c59d4e7f8a1b` and `d60e5f8a9b2c` |
| `docs/backend/decisions.md` | Modified | Documentation | Updates `D-018`, `D-019`, and `D-020` records |
| `docs/backend/how-it-works.md` | Modified | Documentation | Explains tenant-scoped idempotency in plain terms |
| `docs/progress.md` | Modified | Documentation | Records progress on SEC-01, SEC-02, and SEC-05 |
| `docs/journal/2026-11-14.md` | Untracked | Documentation | Daily command and verification log |

---

## 3. Security Issue SEC-01 — Tenant-Scoped Idempotency

### 3.1 Original Issue
Idempotency key lookups in `InMemoryObservationStore`, `InMemoryMemoryStore`, `SqlAlchemyObservationStore`, and `SqlAlchemyMemoryStore` previously accepted an optional `organization_id: Optional[str] = None`. When omitted or `None`, SQL queries omitted the `organization_id` filter, allowing cross-tenant duplicate collisions and data leakage where Tenant B could inspect or collide with Tenant A's existing records. Furthermore, `ObservationEngine.handle_record_event` accepted payload organization values and fell back to an insecure `"org-default"`.

### 3.2 Code Review & Architecture Audit
1. **Protocol Signature Integrity**: `IObservationStore` and `IMemoryStore` in `brain/src/brain/general/contracts/storage.py` were updated to strictly require `organization_id: str` without default values:
   ```python
   async def find_by_idempotency_key(
       self,
       idempotency_key: str,
       organization_id: str,
   ) -> Optional[dict[str, Any]]: ...
   ```
2. **Store Input Validation**: All 4 implementations (`InMemoryObservationStore`, `InMemoryMemoryStore`, `SqlAlchemyObservationStore`, `SqlAlchemyMemoryStore`) explicitly validate `organization_id`:
   ```python
   clean_org = str(organization_id).strip() if organization_id is not None else ""
   if not clean_org:
       raise ValueError("organization_id must be a non-empty string for idempotency lookup")
   ```
   Both lookups and saves (`save` / `save_record`) reject missing, empty, or whitespace strings with `ValueError`.
3. **Database Unconditional Filtering**: In `SqlAlchemyObservationStore` and `SqlAlchemyMemoryStore`, the SQLAlchemy `select` statement includes `where(Model.organization_id == clean_org)` unconditionally.
4. **Engine Tenant Provenance**: In `ObservationEngine.handle_record_event`, the engine:
   - Calls `require_context_ref(request)`.
   - Fails closed if `request.context_ref` is `None` (`NEEDS_CLARIFICATION` / `CONTEXT_MISSING`).
   - Fails closed if `request.context_ref` is a string (`FAILED` / `CONTEXT_MISSING`).
   - Rejects payload organization spoofing (`payload.organization_id != context.organization_id`) with `AUTHORIZATION_DENIED`.
   - Rejects payload case mismatch with `AUTHORIZATION_DENIED`.
   - Completely removes `"org-default"`.
   - Passes validated `org_id` to `find_by_idempotency_key`.

### 3.3 Database Constraints & Migration Review
- **Composite Unique Index (`c59d4e7f8a1b`)**:
  Both `ring1_observations` and `ring1_memory_records` dropped their single-column unique indexes and created composite partial unique indexes on `["organization_id", "idempotency_key"]` where `idempotency_key IS NOT NULL`.
- **NOT NULL Column Enforcement (`d60e5f8a9b2c`)**:
  Before altering columns to `nullable=False`, the migration executes explicit pre-check queries on both tables to ensure no legacy rows contain NULL or whitespace-only `organization_id`. If found, it raises `RuntimeError` and aborts.
  Bidirectional reversibility was tested and verified with `alembic downgrade -1` followed by `alembic upgrade head`.

### 3.4 Adversarial Evaluation (SEC-01)
- **Same Key Across Different Tenants**: Tenant A and Tenant B both write with `idempotency_key="shared-123"`. Both succeed independently, create distinct records, and retrieve only their own data.
- **Cross-Tenant Duplicate Probe**: Tenant B calls `find_by_idempotency_key("shared-123", organization_id="Tenant-B")` before Tenant B writes. Returns `None`. No existence leak.
- **Intra-Tenant Duplicate Rejection**: Tenant A submits the same key twice. In PostgreSQL, duplicate insertion raises `IntegrityError`. The engine returns `duplicate=True` with Tenant A's existing ID.
- **Empty / None Tenant ID**: Calling any store method with `None`, `""`, or `"   "` raises `ValueError`.

### 3.5 Verdict: **SAFE & FULLY RESOLVED**

---

## 4. Security Issue SEC-02 — Context Trust Boundary and Client Hint Overrides

### 4.1 Original Issue
`ContextEngine` previously trusted client-supplied `context_hint` payloads over authenticated server-side context, permitting clients to override `organization_id` or `case_id`.

### 4.2 Audit of Remediation Changes

#### A. Organization Isolation (Verified Secure)
- In `ContextEngine.handle_resolve` (`brain/src/brain/general/engines/context.py:174-188`), `server_org` is strictly required from `request.context_ref.organization_id`. If missing, it fails closed with `CONTEXT_MISSING`. If `context_hint.organization_id` mismatches `server_org`, it returns `ResultStatus.FAILED` with `EngineErrorCode.AUTHORIZATION_DENIED`.
- In `ContextEngine.resolve_context` (transport-independent API), `context.organization_id` is authoritative. Any mismatch with `request_scope["organization_id"]` returns `FORBIDDEN_ORG_OVERRIDE`.
- In `_try_llm_resolution` (`context.py:408`), LLM-inferred context clamps `organization_id` strictly to `server_org`, preventing prompt injection from establishing foreign tenant contexts.

#### B. Case Authorization & The `case_validator` Fail-Open Flaw (CRITICAL GAP)
`ContextEngine` introduces an optional `case_validator` callback in `__init__`:
```python
self._case_validator: Optional[Callable[[str, str, Optional[str]], bool]] = case_validator
```
In `handle_resolve` (`context.py:206-234`):
```python
if server_case:
    if hint_case and hint_case != server_case:
        return self._error(request, ResultStatus.FAILED, EngineErrorCode.AUTHORIZATION_DENIED, ...)
    case_id = server_case
    resolution_status = ResolutionStatus.EXPLICIT
elif hint_case:
    user_id = ...
    if self._case_validator:
        if not self._case_validator(server_org, hint_case, user_id):
            return self._error(request, ResultStatus.FAILED, EngineErrorCode.AUTHORIZATION_DENIED, ...)
    case_id = hint_case
    resolution_status = ResolutionStatus.EXPLICIT
else:
    case_id = None
    resolution_status = ResolutionStatus.INSUFFICIENT_DATA
```
And identically in `resolve_context` (`context.py:107-117`).

**Vulnerability Analysis**:
1. When `server_case` is `None` (standard for tenant-level JWT tokens where users access multiple cases), the code evaluates `elif hint_case:`.
2. If `self._case_validator` is `None`, the validator block `if self._case_validator:` evaluates to `False` and is **silently skipped**.
3. The engine immediately assigns `case_id = hint_case` and marks `resolution_status = ResolutionStatus.EXPLICIT`!
4. **Production Tracing**:
   - In `backend/app/api/v1/context.py:18`:
     `_context_engine = ContextEngine()` is instantiated with **default `case_validator=None`**.
   - In `backend/app/ring1/service.py:69`:
     `self.context = ContextEngine(llm_service=self.llm_service, mesh_router=self.router)` is instantiated with **`case_validator=None`**.
   - **Nowhere in the entire application is a real `case_validator` wired up.** The only occurrences passing a validator are two mock unit tests in `test_context_security_adversarial.py:121, 147`.
5. **Impact**: An attacker with a valid tenant token can pass `{"case_id": "case-unauthorized-victim"}` to `POST /api/v1/context/resolve` and receive an authoritative `ResolutionStatus.EXPLICIT` response. Furthermore, if LLM resolution is triggered, lines 257-262 skip validation if `_case_validator` is `None`, blindly accepting LLM-hallucinated case IDs as authoritative.

#### C. Unchecked Header Trust in `get_brain_context`
In `backend/app/core/context.py:111-125`:
```python
case_id = x_case_id or scope_id
if not case_id:
    case_id = request.query_params.get("case_id")

return BrainContext(
    organization_id=token_org_id,
    user_id=str(user.id),
    case_id=case_id,
    ...
)
```
While docstring line 47 claims `"Client-requested case_id/scope_id is validated against tenant access rules before exposure"`, **no database query or case service validation is performed**. Whatever string the client passes in `X-Case-ID` or `?case_id=` is assigned directly to `BrainContext.case_id`.

#### D. Payload Case Override in `POST /api/v1/observations`
In `backend/app/api/v1/observations.py:45`:
```python
case_id = payload.case_id or payload.scope_id or context.effective_scope_id
```
If a client has `context.effective_scope_id="Case-A"`, but submits `{"case_id": "Case-B"}` in the JSON body, `payload.case_id` overrides the context case scope without any validation or authorization check.

### 4.3 Verdict: **POTENTIAL BYPASS / INCOMPLETE REMEDIATION (HIGH RISK)**

---

## 5. Security Issue SEC-05 — Memory Lifecycle Validation Bypass

### 5.1 Original Issue
`BasicMemoryEngine.handle_store_record` previously hardcoded `status="active"` on new memory records, allowing unverified facts ingested by perception or untrusted clients to enter active memory without satisfying the human validation gate.

### 5.2 Code Review & Architecture Audit

#### A. Ingestion Lifecycle Enforcement (Remediated at Engine Boundary)
In `brain/src/brain/general/engines/memory.py:348-360`:
```python
val_auth = bool(getattr(context_ref, "validation_authority", False))
requested_status = request.payload.get("status")
initial_status = "candidate"
if requested_status in ("validated", "active") and val_auth:
    initial_status = requested_status
```
And in `store_candidate`:
```python
initial_status = "candidate"
if fact_data.get("status") == "validated" and context.validation_authority:
    initial_status = "validated"
```
Unauthenticated mesh requests and regular user operations default strictly to `status="candidate"`. Only contexts with verified `validation_authority=True` can directly ingest records as `validated` or `active`.

#### B. Direct Store Call Bypass Gap
In `backend/app/infrastructure/database/stores.py:268` (`SqlAlchemyMemoryStore.save_record`):
```python
mem = MemoryRecord(
    ...
    status=record.get("status", "active"),
)
```
While `BasicMemoryEngine` enforces `initial_status = "candidate"`, the underlying storage adapter `SqlAlchemyMemoryStore.save_record` defaults missing status to `"active"`! Any internal background job, script, or service calling `store.save_record` directly bypasses the candidate lifecycle.

#### C. Candidate Leakage in Retrieval Search
In `backend/app/api/v1/retrieval.py:53-54` (`GET /api/v1/retrieval/search`):
```python
if not (include_candidates and context.validation_authority):
    query = query.filter(MemoryRecord.status.notin_(["candidate", "rejected"]))
```
The REST endpoint correctly excludes candidates from standard searches.
**HOWEVER**, in the mesh retrieval path (`BasicRetrievalEngine.handle_query` $\rightarrow$ `IRetrievalStore.search_records`):
- `SqlAlchemyRetrievalStore.search_records` (`backend/app/infrastructure/database/stores.py:382-391`) executes:
  ```python
  stmt = select(MemoryRecord).where(MemoryRecord.organization_id == organization_id)
  if case_id: stmt = stmt.where(MemoryRecord.case_id == case_id)
  if record_type: stmt = stmt.where(MemoryRecord.record_type == record_type)
  ```
  It has **no filter on `status`**.
- `InMemoryRetrievalStore.search_records` (`brain/src/brain/general/stores/in_memory_retrieval.py:77-78`) only filters `if rec.get("status") == "rejected": continue`.
Both stores return `candidate` records in general search results. Any mesh agent, plan step executor, or background engine invoking `retrieval.query` receives unvalidated candidates alongside active knowledge.

### 5.3 Verdict: **PARTIALLY REMEDIATED / RETRIEVAL LEAK CONFIRMED**

---

## 6. Additional Changed Code and Regression Review

### 6.1 Database Models (`backend/app/ring1/models/observation.py`)
- Added composite unique index `uq_ring1_observations_idempotency` on `("organization_id", "idempotency_key")`.
- Changed `organization_id` on `Observation` and `MemoryRecord` from `nullable=True` to `nullable=False`.
- **Review**: Structurally sound, matches Alembic migrations `c59d4e7f8a1b` and `d60e5f8a9b2c`.

### 6.2 Service Pipelines (`pdf_pipeline_service.py` & `test_scenario_service.py`)
- In `pdf_pipeline_service.py` line 371 and `test_scenario_service.py` lines 178, 220: added `context_ref=ContextRef(organization_id=...)` to internal `MeshRequest` constructions.
- **Review**: Necessary adaptation following `ObservationEngine` and `ContextEngine` requiring verified `context_ref`.

### 6.3 Existing Unit Tests Adaptations
- `backend/tests/ring1/test_observation.py` and `test_mesh_integration.py` were updated to include `ContextRef(organization_id="org-...")`.
- **Review**: Correctly aligns legacy tests with the new fail-closed context requirement.

---

## 7. Regression and Test Results

All test runs were executed against the dedicated test database (`orgbrain_legal_test`) using `.venv312` with `ENVIRONMENT=test`.

| Test Suite / Command | Total | Passed | Failed | Skipped | Duration |
|---|---|---|---|---|---|
| `pytest backend/tests/ring1/test_idempotency_tenant_isolation.py -v` | 12 | 12 | 0 | 0 | 0.22s |
| `pytest backend/tests/ring1/test_context_security_adversarial.py backend/tests/ring1/test_context.py -v` | 11 | 11 | 0 | 0 | 0.65s |
| `pytest backend/tests/ring1/test_memory_lifecycle_security.py backend/tests/ring1/test_memory.py -v` | 15 | 15 | 0 | 0 | 0.78s |
| `pytest backend/tests/ -q` (Full Backend Suite) | 311 | 311 | 0 | 0 | 10.70s |
| `pytest tests/architecture/ -v` (AST Import Isolation) | 16 | 16 | 0 | 0 | 0.72s |
| `pytest ai/tests/ data-engineering/tests/ -q` | 78 | 78 | 0 | 0 | 0.37s |
| **Total Test Baseline** | **405** | **405** | **0** | **0** | **12.67s** |

### Critical Auditor Observation on Test Coverage
Despite 100% test pass rates:
1. `test_context_security_adversarial.py` tests `case_validator` only by passing a `mock_validator` directly into `ContextEngine(case_validator=mock_validator)`. No test checks whether the production `_context_engine` in `backend/app/api/v1/context.py` actually has a validator.
2. In `test_context_security_adversarial.py:169` (`test_context_explicit_hint_resolution`), the test asserts that `ContextEngine()` with no validator assigns `ResolutionStatus.EXPLICIT` to an arbitrary client-provided `hint_case`. The test actually passed *because* it asserted the vulnerable behavior.

---

## 8. Findings

### Finding 1: ContextEngine Fails Open on Case Boundaries When Validator is Absent
- **ID**: `SEC-02-F01`
- **Severity**: **High**
- **File & Lines**: `brain/src/brain/general/engines/context.py:107-117, 216-231, 257-262`
- **Evidence**:
  ```python
  elif hint_case:
      user_id = ...
      if self._case_validator:
          if not self._case_validator(server_org, hint_case, user_id):
              return self._error(...)
      case_id = hint_case
      resolution_status = ResolutionStatus.EXPLICIT
  ```
- **Exploit Scenario**: An authenticated user with an organization-scoped JWT (no pre-assigned `case_id`) calls `POST /api/v1/context/resolve` with `{"case_id": "case-confidential-other"}`. Since `_case_validator` is `None`, the validator check is skipped. The engine stamps `case-confidential-other` as `EXPLICIT`, returning a valid context resolution.
- **Impact**: Authorization bypass; clients can claim arbitrary case scopes without validation against tenant database records.
- **Recommended Fix**: `ContextEngine` must fail closed when `self._case_validator` is `None` and `client_case` is provided. If no validator is injected to verify case ownership, the engine must return `ResolutionStatus.INSUFFICIENT_DATA` or `AUTHORIZATION_DENIED`. Additionally, inject a real database-backed `case_validator` in production.
- **Tests Needed**: Unit test asserting that `ContextEngine(case_validator=None)` rejects or marks as `INSUFFICIENT_DATA` any unverified `client_case`.

---

### Finding 2: Production ContextEngine Missing Case Validator Dependency Injection
- **ID**: `SEC-02-F02`
- **Severity**: **High**
- **File & Lines**: `backend/app/api/v1/context.py:18`, `backend/app/ring1/service.py:69`
- **Evidence**:
  ```python
  # backend/app/api/v1/context.py:18
  _context_engine = ContextEngine()
  
  # backend/app/ring1/service.py:69
  self.context = ContextEngine(llm_service=self.llm_service, mesh_router=self.router)
  ```
- **Exploit Scenario**: In production, `_context_engine` is created at module level with zero arguments. No database session or `CaseService` is wired to validate cases against the database.
- **Impact**: Even if `ContextEngine` supported validation, production paths never invoke it.
- **Recommended Fix**: Refactor `_context_engine` in `backend/app/api/v1/context.py` to be a FastAPI dependency using `Depends(get_db)`, injecting a validator that queries `CaseService.get_case(session, org_id, case_id)`.
- **Tests Needed**: Integration test against `POST /api/v1/context/resolve` demonstrating that submitting a non-existent or foreign case ID returns HTTP 403 Forbidden.

---

### Finding 3: `POST /api/v1/observations` Allows Payload Case to Override Context Scope
- **ID**: `SEC-02-F03`
- **Severity**: **Medium**
- **File & Lines**: `backend/app/api/v1/observations.py:45`
- **Evidence**:
  ```python
  case_id = payload.case_id or payload.scope_id or context.effective_scope_id
  ```
- **Exploit Scenario**: A user authenticated with `X-Case-ID: case-A` submits an observation payload containing `{"case_id": "case-B"}`. Line 45 assigns `"case-B"`, overriding the authenticated header context without validation.
- **Impact**: Bypasses case boundaries established by server-side headers.
- **Recommended Fix**: Align with `ObservationEngine.handle_record_event`: if `context.effective_scope_id` is present and mismatches `payload.case_id`, return HTTP 403 Forbidden.
- **Tests Needed**: Test asserting that `POST /api/v1/observations` with conflicting `X-Case-ID` and body `case_id` returns HTTP 403.

---

### Finding 4: Retrieval Stores Leak Unvalidated Candidate Records in Mesh Queries
- **ID**: `SEC-05-F01`
- **Severity**: **High**
- **File & Lines**: `backend/app/infrastructure/database/stores.py:382-391`, `brain/src/brain/general/stores/in_memory_retrieval.py:76-78`
- **Evidence**:
  `SqlAlchemyRetrievalStore.search_records` queries `MemoryRecord` without filtering by `status`. `InMemoryRetrievalStore.search_records` only filters `if rec.get("status") == "rejected": continue`.
- **Exploit Scenario**: An agent or user runs a search via capability `retrieval.query`. Unvalidated AI hallucinations stored as `candidate` records are returned as search hits.
- **Impact**: Breaks knowledge lifecycle invariants; unvalidated facts are consumed as established knowledge.
- **Recommended Fix**: In both retrieval stores, add `where(MemoryRecord.status.notin_(["candidate", "rejected"]))` unless explicitly overridden by authorized options.
- **Tests Needed**: Adversarial test verifying that `retrieval.query` does not return records with `status="candidate"`.

---

### Finding 5: `SqlAlchemyMemoryStore.save_record` Defaults to `status="active"`
- **ID**: `SEC-05-F02`
- **Severity**: **Medium**
- **File & Lines**: `backend/app/infrastructure/database/stores.py:268`
- **Evidence**:
  ```python
  status=record.get("status", "active"),
  ```
- **Exploit Scenario**: If an internal ingestion pipeline or background task bypasses `BasicMemoryEngine` and writes directly via `SqlAlchemyMemoryStore.save_record`, the record enters the database directly as `"active"`.
- **Impact**: Violates safe-by-default architecture; storage layer defaults to active rather than candidate.
- **Recommended Fix**: Change default to `status=record.get("status", "candidate")`.
- **Tests Needed**: Unit test verifying `store.save_record` without status results in `status="candidate"`.

---

## 9. Combined Commit Readiness

### Decision: **NOT READY**

**Justification**:
While SEC-01 is complete and verified, the current working tree bundles changes across SEC-01, SEC-02, and SEC-05. A single combined commit would commit a severe authorization bypass in SEC-02 (`ContextEngine` failing open for case hints without a validator) and a knowledge leak in SEC-05 (retrieval stores returning unvalidated candidate facts).

The changes should **not** be committed together until Findings 1, 2, 4, and 5 are addressed.

---

## 10. Recommended Next Actions

1. **Fix SEC-02 Fail-Open Logic**: Update `brain/src/brain/general/engines/context.py` so that if `hint_case` is supplied but `self._case_validator` is `None`, the engine returns `ResolutionStatus.INSUFFICIENT_DATA` (or `AUTHORIZATION_DENIED`) rather than `EXPLICIT`.
2. **Wire Case Validator in API**: In `backend/app/api/v1/context.py`, create a dependency `get_context_engine(db: Session = Depends(get_db))` that injects a `case_validator` querying `CaseService.get_case(db, org_id, case_id)`.
3. **Fix Observation Case Override**: In `backend/app/api/v1/observations.py:45`, reject requests where `payload.case_id` conflicts with `context.effective_scope_id`.
4. **Enforce Candidate Exclusion in Retrieval Stores**: Add status filtering (`status NOT IN ('candidate', 'rejected')`) to `SqlAlchemyRetrievalStore.search_records` and `InMemoryRetrievalStore.search_records`.
5. **Change Default Store Status**: In `backend/app/infrastructure/database/stores.py:268`, change `status="active"` default to `status="candidate"`.
6. **Re-Run Audit**: Re-execute the independent audit report once these fixes are implemented before staging any commits.
