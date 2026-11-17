# Ring 1 Context & Isolation Security Audit

**Auditor Role**: Senior Backend Security Auditor  
**Scope**: Read-only context and tenant/case isolation audit across FastAPI, PostgreSQL, Ring 1 engines, and General Brain architecture.  
**Target Commit**: `9eef8386a066404350ebf032136897b605ea1189` (Branch: `main`)  
**Timestamp**: 2026-11-15T18:35:00+02:00  

---

## S1 Repo State

### 1.1 Git Working Tree & Branch Details
- **Active Branch**: `main`
- **HEAD Commit**: `9eef8386a066404350ebf032136897b605ea1189` (`Merge pull request #3 from mustafayouniss/brain_module_technical_audit`)
- **Working Tree Cleanliness**:
  - Application source code (`backend/`, `brain/`): **CLEAN** (zero modified, untracked, or staged code files).
  - Uncommitted changes:
    - Modified: `docs/journal/2026-11-15.md` (active working session journal)
    - Untracked: `docs/audit/` (audit report artifact directory)
  - Result: Working tree is verified clean of uncommitted application code changes.

### 1.2 Last 15 Commits
| Hash | Subject |
|---|---|
| `9eef838` | Merge pull request #3 from mustafayouniss/brain_module_technical_audit |
| `63160ae` | feat: integrate SaaS foundation and scoped live mesh workspace |
| `8db328c` | fix(ws): prevent connection pool exhaustion |
| `21f694a` | Merge branch 'fix/f-007a' |
| `bd54a22` | Merge branch 'fix/f-010' |
| `87e0bcf` | Merge branch 'fix/f-002a' |
| `3bcdf18` | fix(ws): F-010 reject inactive users and recheck active/expiry on open sockets |
| `48e7bad` | fix(ring1): F-002a org id comes from server settings, reject mismatch |
| `3a730d2` | fix(observations): run blocking DB calls off the event loop (F-007a) |
| `a64a3c3` | fix(sources): enforce MAX_UPLOAD_BYTES chunked limit on file ingestion (F-008) |
| `c877aa2` | fix(security): F-001 fail-closed test operator bypass |
| `1b5c1d2` | Merge pull request #2 from mustafayouniss/feat/ring1-remediation-pdf-pipeline |
| `6e32398` | feat(architecture): extract standalone General Brain package |
| `f466a87` | feat(ring1): implement Ring 1 General Brain architecture, API contracts, domain decoupling, short-term memory, and WebSocket streaming |
| `1b691c1` | docs(journal): log Python 3.12 311-test suite execution |

<!-- SECTION 1 DONE -->


## S2 Context Resolution

### 2.1 BrainContext Architecture & Construction End-to-End

`BrainContext` is defined in `brain/src/brain/general/contracts/context.py` (L14-86) and re-exported by `backend/app/core/context.py` (L27).
It is an immutable, frozen dataclass (`@dataclass(frozen=True)`):
```python
# brain/src/brain/general/contracts/context.py:14-32
@dataclass(frozen=True)
class BrainContext:
    organization_id: str
    user_id: Optional[str] = None
    case_id: Optional[str] = None
    scope_id: Optional[str] = None
    domain_id: str = "general"
    task_id: Optional[str] = None
    correlation_id: Optional[str] = None
    role: str = "employee"
    validation_authority: bool = False
    permissions: tuple[str, ...] = field(default_factory=tuple)
```
Its `__post_init__` (L33-37) synchronizes `case_id` and `scope_id` if only one is supplied:
```python
# brain/src/brain/general/contracts/context.py:33-37
    def __post_init__(self) -> None:
        if self.scope_id and not self.case_id:
            object.__setattr__(self, "case_id", self.scope_id)
        elif self.case_id and not self.scope_id:
            object.__setattr__(self, "scope_id", self.case_id)
```

### 2.2 JWT Lifecycle: Creation, Claims, and Decoding

#### 2.2.1 Token Minting (`create_access_token`)
Defined in `backend/app/core/security.py` (L75-101):
- **Algorithm**: Hardcoded `HS256` (L101).
- **Key**: `settings.SECRET_KEY` (L101).
- **Standard Claims**:
  - `sub`: Subject identifier string, typically `str(user.id)` (UUID) (L90).
  - `iat`: Issue timestamp in UTC (L91).
  - `exp`: Expiration timestamp in UTC (`now + duration`, defaulting to `settings.ACCESS_TOKEN_EXPIRE_MINUTES = 60`) (L84-92).
- **Optional Context Claims**:
  - `org_id` and `organization_id`: Both claims are written with the exact same value (L94-96):
    ```python
    # backend/app/core/security.py:94-96
    if org_id:
        payload["org_id"] = str(org_id)
        payload["organization_id"] = str(org_id)
    ```
  - `role`: User role string (`"admin"` or `"employee"`) (L97-98).
  - `domain`: Organization domain string (e.g. `"legal"`) (L99-100).

#### 2.2.2 Token Validation & Decoding (`decode_access_token`)
Defined in `backend/app/core/security.py` (L104-125):
- **Algorithm Constraint**: Explicitly restricted to `["HS256"]` (L117).
- **Required Claims**: Explicitly enforced `options={"require": ["exp", "iat", "sub"]}` (L118).
- **Subject Check**: Enforces `isinstance(sub, str)` and non-empty (L120-122).
- **Error Handling**: Catches all `jwt.PyJWTError` and raises uniform `TokenSecurityError` (L124-125).
- **Role & Org Claim Behavior**: The decoding function parses payload dictionary; it does **not** trust `role` for privilege escalation, nor does it enforce `org_id` presence at the token decode level.

### 2.3 Dependency Flow: `get_brain_context`

Defined in `backend/app/core/context.py` (L33-135):
1. **Credentials Inspection** (L54-69):
   - If `credentials is None`:
     - Checks `settings.AI_ANONYMOUS_TESTING_ENABLED` and `settings.ENVIRONMENT.lower() != "production"`.
     - If both true: returns dev context (`user_id="anonymous-dev-user"`, `role="employee"`, `validation_authority=False`) (L56-64).
     - If false: raises HTTP 401 `{"code": "AUTHENTICATION_REQUIRED", "message": "Missing bearer token credentials"}` (L65-69).
2. **Token Verification** (L71-78):
   - Invokes `decode_access_token(credentials.credentials)`. On `TokenSecurityError`, raises HTTP 401 `INVALID_TOKEN`.
3. **User Record Verification** (L80-92):
   - Parses `payload["sub"]` as `uuid.UUID`.
   - Executes `db.get(User, user_uuid)`.
   - If user is `None` or `not user.is_active`, raises HTTP 401 `USER_INACTIVE_OR_NOT_FOUND`.
4. **Organization Resolution & Membership Gate** (L94-114):
   - Reads `token_org_id = payload.get("org_id") or payload.get("organization_id")`.
   - If `token_org_id` is present:
     - Queries DB via `OrganizationService.get_user_membership(db, user.id, token_org_id)` (L99).
     - If membership does not exist: raises HTTP 403 `ORGANIZATION_MEMBERSHIP_DENIED` (L101-105).
     - Sets `active_org_id = token_org_id`.
   - If `token_org_id` is absent from token:
     - Fallback queries `OrganizationService.list_user_organizations(db, user.id)` (L108).
     - Selects first membership, or defaults to `settings.ORGANIZATION_ID` (`"org-brain-corp"`) (L109-113).
5. **Role & Authority Derivation** (L117-119):
   - Role is taken from `membership.role` (if present) or `user.role` from DB (never client payload).
   - `validation_authority` is derived solely as `(role == "admin")`.
6. **Case & Scope Resolution (CRITICAL DEFECT)** (L121-125):
   ```python
   # backend/app/core/context.py:121-125
   # If case_id or scope_id is specified in headers or query
   case_id = x_case_id or scope_id
   if not case_id:
       case_id = request.query_params.get("case_id")
   ```
   **Finding**: The client can supply any arbitrary `X-Case-ID`, `X-Scope-ID`, or `?case_id=` string. `get_brain_context` injects this client value directly into `BrainContext.case_id` without verifying that the case exists, belongs to `active_org_id`, or is accessible to `user.id`. The docstring at L47 claims `"Client-requested case_id/scope_id is validated against tenant access rules before exposure"`, but the implementation contains zero validation logic.

### 2.4 Test Operator & Anonymous Testing Analysis

#### 2.4.1 `get_test_operator_user` Flow
Defined in `backend/app/api/deps.py` (L150-177):
```python
# backend/app/api/deps.py:161-176
    if credentials is not None:
        try:
            payload = decode_access_token(credentials.credentials)
            sub = payload.get("sub", "")
            user_id = uuid.UUID(sub)
            user: User | None = db.get(User, user_id)
            if user is not None and user.is_active:
                if user.role == "admin" or settings.ENVIRONMENT.lower() != "production":
                    return user
        except Exception:
            pass

    if settings.ENVIRONMENT.lower() in ("development", "test") and getattr(settings, "ALLOW_TEST_OPERATOR", False):
        return None

    raise _AUTH_401
```
- In `production`:
  - If credentials are valid and user is active: passes **only** if `user.role == "admin"`. If not admin, falls through to L173.
  - At L173, `settings.ENVIRONMENT.lower() in ("development", "test")` evaluates to `False`.
  - Always raises HTTP 401 `_AUTH_401`.
  - **Verdict**: Cannot return `None` or non-admin in production.
- In `development`/`test`:
  - If `ALLOW_TEST_OPERATOR=True` and no credentials provided: returns `None`.
  - **Weakness in Exception Handling**: At L170-171, `except Exception: pass` swallows DB disconnections or syntax errors, causing a token holder to silently drop down into the `ALLOW_TEST_OPERATOR` bypass.

#### 2.4.2 `get_ai_user_or_anonymous` Flow
Defined in `backend/app/api/deps.py` (L99-128):
```python
# backend/app/api/deps.py:124-127
    if settings.AI_ANONYMOUS_TESTING_ENABLED and settings.ENVIRONMENT.lower() != "production":
        return None

    raise _AUTH_401
```
- Protected by `validate_production_anonymous` model validator in `backend/app/core/config.py` (L45-51):
  ```python
  # backend/app/core/config.py:46-51
  @model_validator(mode="after")
  def validate_production_anonymous(self) -> "Settings":
      if self.AI_ANONYMOUS_TESTING_ENABLED and self.ENVIRONMENT.lower() == "production":
          raise ValueError(
              "AI_ANONYMOUS_TESTING_ENABLED cannot be enabled in production environment"
          )
      return self
  ```
  If `AI_ANONYMOUS_TESTING_ENABLED=True` in production, application startup aborts with a `ValueError`.

### 2.5 Code Paths Producing Context WITHOUT a Verified JWT

| Path ID | Entry Point | File:Line | Preconditions | Resulting Context | Reachable in Production? |
|---|---|---|---|---|---|
| **CP-1** | `get_brain_context` | `backend/app/core/context.py:54-64` | `credentials is None` AND `AI_ANONYMOUS_TESTING_ENABLED=True` AND `ENVIRONMENT != "production"` | `BrainContext(user_id="anonymous-dev-user", role="employee", validation_authority=False)` with unvalidated client `case_id` | **NO** (Blocked by config validator L47 and runtime check L55) |
| **CP-2** | `get_ai_user_or_anonymous` | `backend/app/api/deps.py:124-125` | `credentials is None` AND `AI_ANONYMOUS_TESTING_ENABLED=True` AND `ENVIRONMENT != "production"` | Returns `None` (caller runs unauthenticated) | **NO** (Blocked by config validator L47 and runtime check L124) |
| **CP-3** | `get_test_operator_user` | `backend/app/api/deps.py:173-174` | `credentials is None` AND `ALLOW_TEST_OPERATOR=True` AND `ENVIRONMENT in ("development", "test")` | Returns `None` (caller runs test harness unauthenticated) | **NO** (Explicitly checks environment not in `("development", "test")` L173) |
| **CP-4** | Public Endpoints | Multiple (see S3) | Routes mounted without `Depends(get_current_user)` or `Depends(get_brain_context)` | No context or global settings used (`GET /api/v1/brain/status` exposes `settings.ORGANIZATION_ID`) | **YES** (Designed as unauthenticated routes) |

<!-- SECTION 2 DONE -->


## S3 Endpoint Isolation Matrix

### 3.1 Exhaustive Route Audit Matrix
Total endpoints audited: **28 routes** (25 HTTP route handlers across 14 versioned routers + root app, and 2 WebSocket streams).

| Method | Path | Auth Dependency | Organization ID Source | Case ID / Scope Source | Case Ownership Checked? (Where) | DB Queries Filtered by Org? (File:Line) | Cross-Context Behavior (Other Org / Other Case) | Risk |
|---|---|---|---|---|---|---|---|---|
| `GET` | `/health` | **None** | N/A | N/A | N/A | N/A | `200 OK` (Public health check) | P3 |
| `GET` | `/api/v1/health/db` | **None** | N/A | N/A | N/A | N/A | `200 OK` (Public DB ping) | P3 |
| `POST` | `/api/v1/auth/register-organization` | **None** | Generated server-side | N/A | N/A | N/A | `201 Created` (Public signup) | P2 |
| `POST` | `/api/v1/auth/login` | **None** | Optional `body.organization_id` validated against memberships in DB | N/A | N/A | **Yes**: `auth.py:117-118`, `145-156` | `401 Unauthorized` (Uniform error) | P3 |
| `POST` | `/api/v1/auth/switch-organization` | `get_current_user` | `body.organization_id` (membership verified in DB) | N/A | N/A | **Yes**: `auth.py:200-210` | `403 Forbidden` (`ORGANIZATION_MEMBERSHIP_DENIED`) | P2 |
| `GET` | `/api/v1/auth/me` | `get_current_user` | JWT payload `org_id`/`organization_id` | N/A | N/A | **Yes**: `auth.py:250-256` | `401 Unauthorized` | P3 |
| `POST` | `/api/v1/auth/ws-ticket` | `get_brain_context` | `context.organization_id` (Server-derived) | `body.case_id` | **YES**: `CaseService.validate_case_access` (`auth.py:339-345`) | **Yes**: `case_service.py:178` | `404 Not Found` (Sanitized failure) | P3 |
| `POST` | `/api/v1/users` | `require_admin` | **NONE** (Unscoped user model) | N/A | N/A | **NO**: `users.py:51-57` (Users table lacks `organization_id`) | `403 Forbidden` (non-admin) / `201 Created` (admin creates global user) | **P1** |
| `GET` | `/api/v1/organizations/me` | `get_brain_context` | `context.organization_id` | N/A | N/A | **Yes**: `organizations.py:31` | `401 Unauthorized` | P3 |
| `GET` | `/api/v1/organizations/members` | `get_brain_context` | `context.organization_id` | N/A | N/A | **Yes**: `organizations.py:50` | `401 Unauthorized` | P3 |
| `POST` | `/api/v1/organizations/members` | `get_brain_context` + `get_current_user` | `context.organization_id` | N/A | N/A | **Yes**: `organizations.py:87` | `403 Forbidden` (non-admin) | P3 |
| `POST` | `/api/v1/cases` | `get_brain_context` | `context.organization_id` | N/A (Generated) | N/A | **Yes**: `cases.py:73-75` | `401 Unauthorized` | P3 |
| `GET` | `/api/v1/cases` | `get_brain_context` | `context.organization_id` | N/A | N/A | **Yes**: `cases.py:105-107` | `401 Unauthorized` | P3 |
| `GET` | `/api/v1/cases/{case_id}` | `get_brain_context` | `context.organization_id` | Path parameter `{case_id}` | **Partial**: Checks org ownership via `CaseService.get_case` (`cases.py:126-129`), but does **NOT** check employee case assignment under CACS | **Yes**: `cases.py:126-129` (`Case.organization_id == org_id`) | Other org: `404 Not Found`; Other case same org: `200 OK` (Intra-tenant leak) | **P2** |
| `POST` | `/api/v1/cases/{case_id}/documents` | `get_brain_context` | `context.organization_id` | Path parameter `{case_id}` | **Partial**: Checks org ownership (`cases.py:154-159`), but does **NOT** check employee case assignment | **Yes**: `cases.py:154` | Other org: `404 Not Found`; Other case same org: `201 Created` (Intra-tenant write) | **P2** |
| `GET` | `/api/v1/cases/{case_id}/documents` | `get_brain_context` | `context.organization_id` | Path parameter `{case_id}` | **Partial**: Checks org ownership (`cases.py:205`), but does **NOT** check employee case assignment | **Yes**: `cases.py:205, 214-217` | Other org: `404 Not Found`; Other case same org: `200 OK` (Intra-tenant leak) | **P2** |
| `GET` | `/api/v1/cases/{case_id}/tasks` | `get_brain_context` | `context.organization_id` | Path parameter `{case_id}` | **Partial**: Checks org ownership (`cases.py:246`), but does **NOT** check employee case assignment | **Yes**: `cases.py:246, 255-258` | Other org: `404 Not Found`; Other case same org: `200 OK` (Intra-tenant leak) | **P2** |
| `GET` | `/api/v1/cases/{case_id}/knowledge` | `get_brain_context` | `context.organization_id` | Path parameter `{case_id}` | **Partial**: Checks org ownership (`cases.py:292`), but does **NOT** check employee case assignment | **Yes**: `cases.py:292, 300-306` | Other org: `404 Not Found`; Other case same org: `200 OK` (Intra-tenant leak) | **P2** |
| `GET` | `/api/v1/tasks/{task_id}` | `get_brain_context` | `context.organization_id` | N/A | N/A | **Yes**: Post-query check `task.organization_id != context.organization_id` (`tasks.py:32-37`) | `404 Not Found` (Sanitized) | P2 |
| `POST` | `/api/v1/sources` | `get_current_user` | **NONE** (Omitted from call) | **NONE** (Omitted from call) | **NO** (`sources.py:81-92`) | **NO**: `sources.py:81-92` creates `Source` with `organization_id=None` and `case_id=None` | `200 OK` leak / unscoped global file ingestion | **P0** |
| `POST` | `/api/v1/ai/prompt` | `get_brain_context` | `brain_ctx.organization_id` | Request body `request.case_id` | **YES**: `ContextEngine.resolve_context` (`ai.py:129-137`) verifies case in org; rejects unverified cases (`ai.py:146-150`) | **Yes**: `ai.py:169-170` | `403 Forbidden` (Oracle: reveals case status rather than 404) | **P2** |
| `POST` | `/api/v1/ring1/test-run` | `get_test_operator_user` | N/A | N/A | N/A | N/A | `401 Unauthorized` | P2 |
| `GET` | `/api/v1/ring1/test-runs/{run_id}` | `get_test_operator_user` | N/A | N/A | N/A | N/A | `401/404` | P2 |
| `GET` | `/api/v1/ring1/test-runs` | `get_test_operator_user` | N/A | N/A | N/A | N/A | `401 Unauthorized` | P2 |
| `GET` | `/api/v1/ring1/capabilities` | `get_test_operator_user` | N/A | N/A | N/A | N/A | `401 Unauthorized` | P2 |
| `POST` | `/api/v1/ring1/upload-pdf` | `get_brain_context` | `context.organization_id` (Form `organization_id` validated against context `ring1.py:167-171`) | Form body `case_id` | **NO**: `case_id` accepted verbatim (`ring1.py:174-179`); never verified against DB cases table or user permissions | **Partial**: Org mismatch rejected (`ring1.py:168`), but case is unvalidated | Other org: `403 Forbidden`; Arbitrary case injection within org | **P1** |
| `GET` | `/api/v1/ring1/knowledge` | `get_brain_context` | `context.organization_id` (Query `organization_id` validated `ring1.py:262-266`) | Query parameter `case_id` | **NO**: `case_id` accepted verbatim (`ring1.py:269-275`); never checked against DB cases or user permissions | **Yes**: Filtered by org in `pdf_pipeline_service.py:807`, but `case_id` is unvalidated | Other org: `403 Forbidden`; Other case same org: `200 OK` (Unrestricted case knowledge leak) | **P1** |
| `GET` | `/api/v1/brain/status` | **None** (`get_db` only) | `settings.ORGANIZATION_ID` (`brain.py:54`) | N/A | N/A | N/A | `200 OK` (Publicly leaks `organization_id` and `environment`) | **P2** |
| `POST` | `/api/v1/observations` | `get_brain_context` | `context.organization_id` (`observations.py:84`) | Body `payload.case_id` (`observations.py:45`) | **NO**: `payload.case_id` stored directly without verifying case exists or belongs to caller | **Yes**: Scoped by `organization_id` (`observations.py:53, 84`), but case is unverified | Writes observation to arbitrary case within caller's org | **P1** |
| `GET` | `/api/v1/observations` | `get_brain_context` | `context.organization_id` (`observations.py:174`) | `context.effective_scope_id` (`observations.py:176-177`) | **NO**: Uses unvalidated context scope | **Yes**: `Observation.organization_id == context.organization_id` (`observations.py:174`) | `200 OK` (Can read observations for any case in org via `X-Case-ID` header) | **P2** |
| `POST` | `/api/v1/context/resolve` | `get_brain_context` | `context.organization_id` (`context.py:91`) | Body `payload.case_id` (`context.py:70-71`) | **YES**: `production_case_validator` checks `Case.organization_id == org_id` (`context.py:34-51`) | **Yes**: `context.py:41` | `403 Forbidden` (Reveals case existence/permission failure) | **P2** |
| `GET` | `/api/v1/memory/{id}` | `get_brain_context` | `context.organization_id` (`memory.py:43`) | `context.effective_scope_id` (`memory.py:50`) | **YES**: Post-fetch check enforces `record.organization_id == context.organization_id` (`memory.py:43-47`) and `record.case_id == context.effective_scope_id` (`memory.py:50-55`) | **Yes**: `memory.py:43, 50` | `404 Not Found` (Sanitized anti-oracle response) | P3 |
| `GET` | `/api/v1/retrieval/search` | `get_brain_context` | `context.organization_id` (`retrieval.py:41`) | `context.effective_scope_id` (`retrieval.py:46`) | **NO**: Scope from context unverified | **Yes**: Filtered by org (`retrieval.py:41`) and case (`retrieval.py:46`) | `200 OK` (Can search any case in org via `X-Case-ID` header) | **P2** |
| `WS` | `/api/v1/ws/observations` | Single-use Ticket or JWT token | Consumed ticket (`ws.py:163`) or JWT claim (`ws.py:196-198`) | Ticket `case_id` (`ws.py:164`) or Query `case_id`/`scope_id` (`ws.py:200`) | **Partial / Flawed**: `_validate_session_and_case` (`ws.py:110-124`) enforces CACS if case exists in DB; **BUT if case does NOT exist in DB, L126-127 permits access**: `return True`! | **Yes**: `Case.organization_id == organization_id` (`ws.py:95, 104`) | Non-existent case: `WS Connection Accepted` (Bypasses CACS); Wrong org: `WS 1008 Policy Violation` | **P1** |
| `WS` | `/api/v1/ws/events` | Single-use Ticket or JWT token | Consumed ticket or JWT claim | Ticket `case_id` or Query `case_id` | **Partial / Flawed**: Same permissive fallback as `/ws/observations` (`ws.py:126-127`) | **Yes**: `ws.py:95, 104` | Non-existent case: `WS Connection Accepted`; Wrong org: `WS 1008 Policy Violation` | **P1** |

---

### 3.2 Routes Accepting `organization_id` or `case_id` from Client Input

The design mandate specifies:
> "organization_id is an internal constant (settings.ORGANIZATION_ID) set ONLY by the server, never trusted from the client. The client sends only the ids it wants to work on (e.g. case_id); the backend must verify the user may access them."

Here is every route accepting `organization_id` or `case_id` from the request body, form, query, or path:

#### A. Routes accepting `organization_id` from client input:
1. `POST /api/v1/auth/login` (Body `body.organization_id`): Validated against user's DB memberships (`auth.py:145-156`).
2. `POST /api/v1/auth/switch-organization` (Body `body.organization_id`): Validated against DB memberships (`auth.py:200-210`).
3. `POST /api/v1/ring1/upload-pdf` (Form `organization_id`): Validated against `context.organization_id` (`ring1.py:167-171`), returns 403 on mismatch.
4. `GET /api/v1/ring1/knowledge` (Query `organization_id`): Validated against `context.organization_id` (`ring1.py:262-266`), returns 403 on mismatch.

#### B. Routes accepting `case_id` from client input:
1. `POST /api/v1/auth/ws-ticket` (Body `body.case_id`): **VALIDATED** via `CaseService.validate_case_access` (`auth.py:339-345`).
2. `GET /api/v1/cases/{case_id}` (Path `{case_id}`): **PARTIALLY VALIDATED** via `CaseService.get_case` (`cases.py:126-129`) — verifies organization ownership, but fails to enforce employee case assignment under CACS.
3. `POST /api/v1/cases/{case_id}/documents` (Path `{case_id}`): **PARTIALLY VALIDATED** — org checked, assignment skipped (`cases.py:154`).
4. `GET /api/v1/cases/{case_id}/documents` (Path `{case_id}`): **PARTIALLY VALIDATED** — org checked, assignment skipped (`cases.py:205`).
5. `GET /api/v1/cases/{case_id}/tasks` (Path `{case_id}`): **PARTIALLY VALIDATED** — org checked, assignment skipped (`cases.py:246`).
6. `GET /api/v1/cases/{case_id}/knowledge` (Path `{case_id}`): **PARTIALLY VALIDATED** — org checked, assignment skipped (`cases.py:292`).
7. `POST /api/v1/ring1/upload-pdf` (Form `case_id`): **NOT VALIDATED** (`ring1.py:147, 174-179`). Ingested without checking case existence or user assignment.
8. `GET /api/v1/ring1/knowledge` (Query `case_id`): **NOT VALIDATED** (`ring1.py:253, 269-275`). Queried without checking case existence or user assignment.
9. `POST /api/v1/observations` (Body `payload.case_id`): **NOT VALIDATED** (`observations.py:45`). Stored directly without checking case existence or user assignment.
10. `POST /api/v1/context/resolve` (Body `payload.case_id`): **VALIDATED** via `ContextEngine.resolve_context` (`context.py:34-51`).
11. `POST /api/v1/ai/prompt` (Body `request.case_id`): **VALIDATED** via `ContextEngine.resolve_context` (`ai.py:129-137`).
12. `WS /api/v1/ws/observations` (Query `case_id`): **FLAWED VALIDATION** (`ws.py:83-128`). Validated if in DB; bypassed if not in DB.
13. `WS /api/v1/ws/events` (Query `case_id`): **FLAWED VALIDATION** (`ws.py:83-128`). Validated if in DB; bypassed if not in DB.

<!-- SECTION 3 DONE -->


## S4 Data Layer Isolation

### 4.1 Schema & Model Isolation Audit
Audit of all 10 persistent models across `backend/app/models/` and `backend/app/ring1/models/`.

| Model | Table Name | `organization_id` Column | `case_id` Column | Foreign Keys Enforcing Isolation | Isolation Indexes Defined | Risk Analysis |
|---|---|---|---|---|---|---|
| `Case` | `cases` | `String(64), nullable=False` (`case.py:60`) | N/A (`id: UUID PK`) | **None** on `organization_id` (No FK to `organizations.id`) | `ix_cases_organization_id`, `uq_cases_org_number` (composite unique `(organization_id, case_number)`) | High data integrity; missing DB FK to `organizations` table |
| `CaseAssignment` | `case_assignments` | **None** (Inherits tenant through case) | `UUID, nullable=False` (`case_assignment.py:44`) | `ForeignKey("cases.id", ondelete="CASCADE")`, `ForeignKey("users.id", ondelete="CASCADE")` | `uq_case_assignment_case_user`, `ix_case_assignments_case_id`, `ix_case_assignments_user_id` | Solid cascade and unique pair enforcement |
| `Organization` | `organizations` | N/A (`id: String(64) PK`) | N/A | None | `ix_organizations_slug`, `ix_organizations_domain` | Root tenant entity |
| `OrganizationMembership` | `organization_memberships` | `String(64), nullable=False` | N/A | `ForeignKey("organizations.id", ondelete="CASCADE")`, `ForeignKey("users.id", ondelete="CASCADE")` | `uq_org_membership_user_org`, `ix_org_memberships_org_id`, `ix_org_memberships_user_id` | Strictly models user-to-organization mapping |
| `Source` | `sources` | `String(64), nullable=True` (`source.py:46`) | `String(128), nullable=True` (`source.py:42`) | **None** (No FK to `organizations` or `cases`) | `ix_sources_organization_id`, `ix_sources_case_id`, `ix_sources_uploaded_by` | **CRITICAL DEFECT**: Both columns are nullable; un-scoped global file ingestion is possible |
| `User` | `users` | **None** (`user.py:38-72`) | N/A | None | `uq_users_email_lower` | Users are global entities; tenancy is established purely via `organization_memberships` |
| `Task` | `tasks` | `String(255), nullable=False` (`task.py:74`) | `String(255), nullable=True` (`task.py:75`) | **None** on org or case | `ix_tasks_org_state`, `ix_tasks_case_id`, `uq_tasks_org_idempotency` | Enforces tenant scoping and tenant-level idempotency |
| `TaskOutbox` | `task_outbox` | **None** (`task.py:140-168`) | **None** | None | `ix_task_outbox_status_lease`, `ix_task_outbox_task_id` | Tenancy context is serialized purely inside JSONB `payload` column |
| `AuditEvent` | `audit_events` | `String(255), nullable=False` (`audit.py:47`) | `String(255), nullable=True` (`audit.py:48`) | **None** on org or case | `ix_audit_events_org_created`, `ix_audit_events_case_id`, `ix_audit_events_task_id` | Append-only ledger; always requires non-empty `organization_id` |
| `WebSocketTicket` | `ws_tickets` | `String(100), nullable=False` (`ws_ticket.py:48`) | `String(100), nullable=True` (`ws_ticket.py:53`) | `ForeignKey("organizations.id", ondelete="CASCADE")`, `ForeignKey("users.id", ondelete="CASCADE")` | `ix_ws_tickets_consumed_expires`, `ix_ws_tickets_org_user` | Strongly typed and bounded to organization FK |
| `MeshEventRecord` | `mesh_events` | `String(100), nullable=False` (`mesh_event.py:55`) | `String(100), nullable=True` (`mesh_event.py:60`) | `ForeignKey("organizations.id", ondelete="CASCADE")` | `ix_mesh_events_org_case_seq`, `ix_mesh_events_run_seq` | Strongly bounded to organization FK |
| `Observation` | `ring1_observations` | `String(255), nullable=False` (`observation.py:64`) | `String(255), nullable=True` (`observation.py:63`) | **None** on org or case | `uq_ring1_observations_idempotency` (`organization_id`, `idempotency_key`), `ix_ring1_observations_case_id` | Tenant-level idempotency; unconstrained string org/case |
| `MemoryRecord` | `ring1_memory_records` | `String(255), nullable=False` (`observation.py:126`) | `String(255), nullable=True` (`observation.py:125`) | **None** on org or case | `uq_ring1_memory_records_idempotency` (`organization_id`, `idempotency_key`), `ix_ring1_memory_records_case_id` | Tenant-level idempotency; unconstrained string org/case |

---

### 4.2 Query-Level Isolation & Helper Evaluation

#### 4.2.1 Violation of the Single Shared Query Filter Mandate
The project design rules require:
> "Every DB query must be filtered by context through ONE shared helper, not hand-written filters per endpoint."

**Audit Finding**: There is **NO shared query helper** anywhere in `backend/app/`.
Every single repository, service, and API route implements hand-crafted filter clauses. This has directly led to inconsistent isolation boundaries:
- In `SqlAlchemyObservationStore.list_feed` (`stores.py:134`): Hand-written `filter(Observation.organization_id == organization_id)`
- In `SqlAlchemyMemoryStore.get_record` (`stores.py:295`): Hand-written `where(MemoryRecord.organization_id == organization_id)`
- In `SqlAlchemyRetrievalStore.search_records` (`stores.py:382`): Hand-written `where(MemoryRecord.organization_id == organization_id)`
- In `CaseService.list_cases` (`case_service.py:99`): Hand-written `filter(Case.organization_id == organization_id)`
- In `CaseService.get_case` (`case_service.py:118`): Hand-written `filter(Case.id == case_id, Case.organization_id == organization_id)`
- In `CaseService.validate_case_access` (`case_service.py:178`): Hand-written `filter(Case.organization_id == organization_id)`
- In `tasks.py:32`: `db.get(Task, task_id)` — **Unscoped query**, post-filtered in Python.
- In `memory.py:37`: `db.get(MemoryRecord, id)` — **Unscoped query**, post-filtered in Python.
- In `cases.py:214`: Hand-written `filter(Source.organization_id == context.organization_id, Source.case_id == str(case_id))`
- In `cases.py:256`: Hand-written `filter(Task.organization_id == context.organization_id, Task.case_id == str(case_id))`
- In `cases.py:301`: Hand-written `where(MemoryRecord.organization_id == context.organization_id, MemoryRecord.case_id == str(case_id))`
- In `pdf_pipeline_service.py:804`: Hand-written `where(MemoryRecord.organization_id == organization_id, MemoryRecord.case_id == case_id)`
- In `observations.py:173`: Hand-written `filter(Observation.organization_id == context.organization_id)`
- In `retrieval.py:41`: Hand-written `filter(MemoryRecord.organization_id == context.organization_id)`

---

### 4.3 Database Queries Capable of Returning Data Outside Caller's Context

| Query Location | Method / Operation | Flaw Description | Impact |
|---|---|---|---|
| `backend/app/api/v1/sources.py:81-92` | `create_source()` | Source created with `organization_id=None` and `case_id=None` (`source_service.py:48-61`). | Any authenticated user can create un-scoped files; global file ingestion without tenant bounds. |
| `backend/app/api/v1/tasks.py:32` | `db.get(Task, task_id)` | Query executes directly against PK without WHERE `organization_id = :org_id`. | While checked at L33, the SQL engine returns the row into memory across tenant boundaries. |
| `backend/app/api/v1/memory.py:37` | `db.get(MemoryRecord, id)` | Query executes directly against PK without WHERE `organization_id = :org_id`. | Data row loaded across tenant boundary; evaluated post-query in Python. |
| `backend/app/api/v1/ring1.py:277` → `pdf_pipeline_service.py:804-812` | `query_saved_knowledge()` | Query filters by `case_id = clean_case_id`, but `clean_case_id` comes from unvalidated user query param (`ring1.py:253`). | **Data Leak**: Any user in an organization can read all knowledge records of any case in the organization. |
| `backend/app/api/v1/cases.py:126` | `CaseService.get_case()` | Filters by `Case.organization_id`, but skips employee assignment validation under CACS. | **Data Leak**: Any employee can view any case details in the organization without being assigned. |
| `backend/app/api/v1/cases.py:205, 214-217` | `GET /{case_id}/documents` | Checks case exists in org, but never verifies requesting employee is assigned to the case. | **Data Leak**: Any employee can view source documents belonging to cases they are not assigned to. |
| `backend/app/api/v1/cases.py:246, 255-258` | `GET /{case_id}/tasks` | Checks case exists in org, but never verifies requesting employee is assigned to the case. | **Data Leak**: Any employee can view tasks and task results for cases they are not assigned to. |
| `backend/app/api/v1/cases.py:292, 300-306` | `GET /{case_id}/knowledge` | Checks case exists in org, but never verifies requesting employee is assigned to the case. | **Data Leak**: Any employee can view knowledge records for cases they are not assigned to. |
| `backend/app/api/v1/observations.py:173-178` | `list_observations()` | Uses `context.effective_scope_id` from client-provided `X-Case-ID` without verifying case access. | **Data Leak**: Any employee can retrieve observations for arbitrary cases within the organization. |
| `backend/app/api/v1/retrieval.py:41-47` | `search_records()` | Uses `context.effective_scope_id` from client-provided `X-Case-ID` without verifying case access. | **Data Leak**: Any employee can run semantic searches over arbitrary cases within the organization. |

<!-- SECTION 4 DONE -->


## S5 Brain Engines and Package Boundary

### 5.1 Context Passing Across Engine Boundaries
In the General Brain architecture (`brain/src/brain/general/`), execution context is modeled through two primary contracts:
1. `BrainContext`: High-level frozen dataclass used by endpoints and synchronous engine calls (`contracts/context.py`).
2. `ContextRef`: Pydantic model (`contracts/context_ref.py`) attached to peer-to-peer `MeshRequest` / `MeshResponse` envelopes.

#### Flow Across Engines:
- **Observation Engine** (`engines/observation.py`):
  - When invoked via `MeshRequest.context_ref` (`handle_record_event`, L240-300): Requires `require_context_ref(request)`. Validates `context_ref.organization_id` is non-empty. Rejects payload if `payload.organization_id != context_ref.organization_id` (L279).
  - **Spoofing Weakness**: At L287-298, if `context_ref.case_id` is not set or empty, the handler falls back to accepting `payload["case_id"]` from the untrusted request payload:
    ```python
    # brain/src/brain/general/engines/observation.py:297
    case_id = authorized_case or (str(payload_case).strip() if payload_case else None)
    ```
- **Memory Engine** (`engines/memory.py`):
  - In `store_record(fact_data, context)` (L108-190): Validates `context.organization_id` is present.
  - Forces initial status of newly created knowledge objects to `"candidate"` (L152):
    ```python
    # brain/src/brain/general/engines/memory.py:152-155
    initial_status = "candidate"
    if fact_data.get("status") == "validated" and context.validation_authority:
        initial_status = "validated"
    ```
  - When called without `validation_authority=True`, payload attempting to set `status="validated"` is forced back to `"candidate"`.
- **Retrieval Engine** (`engines/retrieval.py`):
  - In `query(query, context)` (L100-156): Asserts `context.organization_id` and non-empty `context.case_id`.
  - In `handle_query(request)` (L162-180): Asserts `request.context_ref` carries a non-empty `case_id`.
- **Perception Engine** (`engines/perception.py`):
  - Operates purely as a stateless structured parsing engine; accepts and carries `context_ref` without mutating boundaries.
- **Context Engine** (`engines/context.py`):
  - Implements `production_case_validator` (`context.py:34-51`). Queries DB for `Case.organization_id == org_id`. If case is not found or not in org, returns `ResolutionStatus.FAILED` or `ResolutionStatus.AMBIGUOUS`.

---

### 5.2 Context Validation & Missing/Mismatched Context Handling
Can an engine be called with missing, empty, or mismatched context?
1. **Missing or Empty Context**:
   - `BaseEngine.require_context_ref` (`base.py:92-100`) rejects requests with `MeshError(code=EngineErrorCode.CONTEXT_MISSING)` and status `NEEDS_CLARIFICATION`.
   - String-only context references (`isinstance(ctx, str)`) are explicitly rejected by engines (`observation.py:259`, `memory.py:270`) to prevent unverified context ID strings from establishing identity.
2. **Payload Organization Spoofing**:
   - Protected: `ObservationEngine` explicitly checks `payload_org != authorized_org` (`observation.py:128, 279`) and raises `EngineErrorCode.AUTHORIZATION_DENIED`.
3. **Payload Case Spoofing**:
   - **VULNERABILITY**: In `ObservationEngine.handle_record_event` (`observation.py:297`), if the calling message passes an unscoped `context_ref` (where `context_ref.case_id` is `None`), it blindly accepts `payload["case_id"]` from the request body. An unscoped sender can thus inject observations stamped with arbitrary `case_id` values.
4. **Automatic Case Generation in PDF Pipeline**:
   - In `backend/app/ring1/services/pdf_pipeline_service.py` (L150-163), when `execute_pdf` is called with an arbitrary `case_id`, if the case does not exist in the database, the service **automatically inserts a new Case into the database**:
     ```python
     # backend/app/ring1/services/pdf_pipeline_service.py:150-153
     case_rec = Case(
         id=uuid.uuid4(),
         case_number=f"AUTO-{case_id[:8]}",
         title=f"Auto Case for {case_id}",
         organization_id=organization_id,
         status="open",
     )
     self.runner.db_session.add(case_rec)
     self.runner.db_session.commit()
     ```
     It then mints a `ContextRef` with `ResolutionStatus.EXPLICIT` (L161). This completely bypasses case creation RBAC and CACS assignment checks.

---

### 5.3 Knowledge Candidate Retrieval Isolation Defect
The design rules mandate:
> "Observations are not knowledge. Candidate knowledge must not appear in normal retrieval unless validated."

**Critical Violation**:
In `backend/app/infrastructure/database/stores.py` (`SqlAlchemyRetrievalStore.search_records`, L382-392):
```python
# backend/app/infrastructure/database/stores.py:382-392
stmt = select(MemoryRecord).where(
    MemoryRecord.organization_id == organization_id
)
if case_id:
    stmt = stmt.where(MemoryRecord.case_id == case_id)
if record_type:
    stmt = stmt.where(MemoryRecord.record_type == record_type)

stmt = stmt.order_by(MemoryRecord.created_at.desc()).limit(limit * 3)
records = session.execute(stmt).scalars().all()
```
`SqlAlchemyRetrievalStore` **omits any filter on `MemoryRecord.status`**.
Unvalidated knowledge candidates (`status == "candidate"`) are retrieved and returned in regular search results alongside validated facts (`L411: "status": rec.status`). Downstream callers or LLM prompts consuming `search_records` receive unvalidated candidate observations as trusted retrieved knowledge.

---

### 5.4 Handoff Validation Between Engines
Handoff validation is governed by `HandoffPolicy` (`brain/src/brain/general/policies/handoff.py:42-150`):
- **Checks Enforced**:
  1. Capability registration check in `ALL_CAPABILITIES` (L96-101).
  2. Rule enforcement: Observation Engine cannot autonomously initiate planning (`AUTONOMOUS_PLANNING_FORBIDDEN`, L104-112).
  3. Cycle & loop detection: Self-loop rejection (L115-120), repeated cycles in history (L131-137).
  4. Delegation recursion depth limit: Max depth defaults to 10 (L123-128).
  5. Strict transition allowlist: Enforces `PERMITTED_TRANSITIONS` frozenset (L48-80).
- **Security Gap**:
  - `HandoffPolicy.validate_handoff` validates **only** capability strings and execution topology `(source_capability, target_capability, traversal_history)`.
  - It does **NOT** validate context consistency. It does not verify that the delegated `MeshRequest` retains the same `organization_id`, `case_id`, or security credentials as the parent request. Context propagation safety relies entirely on individual engine implementations.

<!-- SECTION 5 DONE -->


## S6 Real-Time and Background Paths

### 6.1 WebSocket Streaming & Real-Time Isolation

#### 6.1.1 Authentication & Ticket Lifecycle
- **Single-Use Ticket Flow** (`POST /api/v1/auth/ws-ticket` → `ws.py:152-177`):
  - Tickets are generated via `TicketService.create_ticket` using 256-bit cryptographically secure random tokens (`secrets.token_urlsafe(32)`).
  - Raw tokens are hashed with SHA-256 (`TicketService.hash_ticket`, `ticket_service.py:46-49`); plaintext tokens are never persisted or logged.
  - Tickets carry an explicit 60-second TTL (`TICKET_TTL_SECONDS = 60`) and are bound to `(user_id, organization_id, case_id)`.
  - Consumption is atomic in PostgreSQL via `UPDATE ws_tickets SET consumed = TRUE ... RETURNING` (`ticket_service.py:105-115`), preventing replay attacks and race conditions across multi-worker deployments.
- **Legacy JWT Path** (`ws.py:178-202`):
  - Supported via query parameter `?token=...`.
  - **Risk**: Passing JWTs in query parameters exposes bearer credentials to proxy access logs, browser history, and server logs.
- **Handshake Origin Validation** (`ws.py:46-63`):
  - Inspects `websocket.headers.get("origin")` and rejects disallowed origins with `WS_1008_POLICY_VIOLATION`.

#### 6.1.2 Scope Filtering & Broadcast Dual-Boundary (`ws_manager.py`)
Active connections are partitioned in memory by `organization_id` (`ws_manager.py:35`):
- **Boundary A (Tenant Isolation)**:
  - Broadcast messages are dispatched only to sockets registered under `self._connections[organization_id]` (`ws_manager.py:102-105`). Sockets belonging to another organization never receive payloads.
- **Boundary B (Intra-Tenant Case Isolation)** (`ws_manager.py:115-123`):
  - If an event is case-private (`target_case is not None`), it is delivered **only** to connections where `meta.scope_id == target_case`. Unscoped subscribers (`meta.scope_id is None`) are explicitly skipped (`L117-118`).
  - If an event is organization-wide (`target_case is None`), it is delivered **only** to unscoped subscribers (`meta.scope_id is None`), preventing organization broadcasts from polluting case-filtered subscribers (`L121-122`).

#### 6.1.3 Flawed Case Validation for Non-Existent Cases (`ws.py`)
In `_validate_session_and_case` (`backend/app/api/v1/ws.py:110-128`):
```python
# backend/app/api/v1/ws.py:125-127
if case_match:
    # Case exists in DB: enforce strict CACS
    ...
else:
    # If case does not exist in DB, allow as generic observation scope filter
    return True
```
**Finding**: If a client requests a WebSocket stream with a `case_id` that does **not** exist in the `cases` table, CACS validation is completely bypassed and the connection is allowed. Any subscriber can register for arbitrary observation scope strings, creating an unmonitored event channel.

#### 6.1.4 Periodic Re-Check, Revocation, and DB Session Lifetime
- **Periodic Active-User Re-Check** (`ws.py:245-262`):
  - Every `settings.WS_RECHECK_SECONDS = 30`, the socket loop invokes `_validate_session_and_case` via `run_in_threadpool`.
  - Re-evaluates: `user.is_active`, organization membership, and active case assignment in PostgreSQL.
  - Checks token expiration: `is_expired = bool(token_exp and float(token_exp) <= time.time())`.
  - On revocation or expiration, immediately terminates the socket with `WS_1008_POLICY_VIOLATION`.
- **Database Session Lifetime**:
  - The connection pool exhaustion bug (commit `8db328c`) is verified fixed: `_validate_session_and_case` uses short-lived context managers (`with SessionLocal() as db:`). Open WebSockets do not hold database connections open while idle.
- **Connection Limits**:
  - **Weakness**: `ws_manager.py` has no maximum connection ceiling per user or organization. Vulnerable to memory or descriptor exhaustion if a client opens thousands of concurrent sockets.

---

### 6.2 Short-Term Memory / Redis Scoping (`short_term_memory.py`)
- **Key Naming Convention**:
  Standardized format: `org:{organization_id}:task:{task_id}:{key}` (`short_term_memory.py:40-46`).
- **Isolation Assessment**:
  Every key is explicitly prefixed with `org` and `task_id`. Cross-tenant and cross-task access is structurally prevented by key namespacing.
- **TTL & Expiration**:
  Default expiration is 3600 seconds (1 hour). In Redis mode, uses native `SET ... EX` (`L83`). In-memory fallback enforces expiration on read and cleans expired keys (`L115-124`).
- **Cleanup**:
  `delete(organization_id, task_id)` cleans all keys matching prefix `org:{org_id}:task:{task_id}:*` (`L150-165`).

---

### 6.3 Transactional Outbox & Background Task Context Propagation
- **Transactional Atomicity** (`task_manager.py:35-135`):
  `TaskManager.create_task_with_outbox` inserts the `Task` ledger entry and the `TaskOutbox` row within the same database transaction.
- **Context Serialization**:
  The outbox row explicitly captures security and routing context in its JSONB `payload` (`task_manager.py:126-133`):
  ```python
  payload={
      "task_id": str(task.id),
      "organization_id": organization_id,
      "case_id": case_id,
      "user_id": user_id,
      "correlation_id": correlation_id,
      "task_type": task_type,
      "payload": payload,
  }
  ```
- **Outbox Claiming & Multi-Tenant Fencing** (`outbox_dispatcher.py:24-81`):
  - `OutboxDispatcher.claim_pending_records` claims rows globally using `SELECT ... FOR UPDATE SKIP LOCKED`.
  - Monotonic `dispatch_generation` and lease timers (`dispatch_lease_expires_at`) prevent duplicate dispatch and fence against stale dispatchers.
- **Dead-Letter Handling**:
  - Dispatch failures exhaust at 5 attempts, transitioning task to `FAILED` with code `DISPATCH_EXHAUSTED` (`outbox_dispatcher.py:149`).
  - Execution retries exhaust at 3 attempts, transitioning task to `DEAD_LETTER` (`task_manager.py:373`).
- **Re-Application of Context**:
  Workers consuming outbox messages must reconstruct `BrainContext` from the serialized `organization_id`, `case_id`, and `user_id`. The outbox ledger accurately preserves the necessary boundary fields.

<!-- SECTION 6 DONE -->


## S7 Information Leaks

### 7.1 Status Code & Error Message Oracles (403 vs 404)
The architectural decision mandates:
> "Cross-context access must return 404, not 403, so existence is not revealed."

#### Audit Findings on Existence Oracles:
1. **AI Prompt Endpoint (`POST /api/v1/ai/prompt`)**:
   - At `ai.py:146-150`, when a case is unauthorized or context cannot be explicitly resolved, the route returns:
     ```python
     raise HTTPException(
         status_code=status.HTTP_403_FORBIDDEN,
         detail="Explicit case authorization required to execute AI prompts.",
     )
     ```
   - **Leak**: Returns `403 Forbidden` instead of `404 Not Found`. An attacker probing case IDs learns whether a case exists and requires authorization vs does not exist.
2. **Context Resolution (`POST /api/v1/context/resolve`)**:
   - At `context.py:84-86`, returns `403 Forbidden` when case access is denied.
3. **Ring 1 Upload and Knowledge (`POST /upload-pdf` & `GET /knowledge`)**:
   - At `ring1.py:168-171` and `ring1.py:263-266`, returns `403 Forbidden` with `"organization_id does not match this deployment."` This reveals to an external caller that the server recognized the target organization but rejected the mismatch.
4. **Proper Anti-Oracle Implementations (Compliant)**:
   - `GET /api/v1/memory/{id}` (`memory.py:38-47`): Returns the identical `404 Not Found` detail `"Memory record '{id}' not found"` regardless of whether the record does not exist or belongs to another organization/case.
   - `GET /api/v1/tasks/{task_id}` (`tasks.py:34-37`): Returns the identical `404 Not Found` detail `"Task '{task_id}' not found"` for not-found and cross-organization queries.
   - `CaseService.validate_case_access` (`case_service.py:190, 213`): Fails closed with `CaseNotFoundError`, translated by `auth.py:348-351` into `404 Not Found`.

---

### 7.2 Public Deployment Metadata Disclosure
In `backend/app/api/v1/brain.py` (L54-55):
```python
# backend/app/api/v1/brain.py:53-56
return {
    "status": "ready",
    "engines": active_engines,
    "capabilities": capabilities,
    "organization_id": settings.ORGANIZATION_ID,
    "environment": settings.ENVIRONMENT,
}
```
**Finding**: `GET /api/v1/brain/status` is mounted with zero authentication dependencies. It leaks the server's internal `settings.ORGANIZATION_ID` (`"org-brain-corp"`) and `settings.ENVIRONMENT` (`"production"`) to any unauthenticated caller on the public internet.

---

### 7.3 Logging and Sensitive Data Handling
- **Passwords**: `user_service.py` hashes passwords with Argon2id prior to storage; plaintext passwords are never logged. `settings.hide_input_in_errors = True` (`config.py:22`) prevents Pydantic validation errors from echoing raw passwords in stack traces.
- **Tokens**: Plaintext WebSocket tickets are hashed with SHA-256 before persistence; neither raw JWTs nor ticket tokens are printed in standard info logs.
- **Debug Payload Logging**: `ws.py:240` logs `websocket.receive_text()[:100]` at `DEBUG` level, which in debug environments could record client message snippets.

---

### 7.4 Cryptographic Pagination Cursors (`cursor.py`)
- **HMAC Signing**: All pagination cursors in `list_observations` are signed with HMAC-SHA256 using `settings.SECRET_KEY` (`cursor.py:58-64`).
- **Context Binding**: Cursors bind 7 fields: `{"v", "org_id", "case_id", "filter_hash", "sort", "created_at", "id"}` (`cursor.py:23, 45-53`).
- **Replay & Tampering Prevention**:
  - `decode_and_verify_cursor` strictly asserts `payload["org_id"] == expected_org_id` (`cursor.py:135`) and `payload["case_id"] == expected_case_id` (`cursor.py:141-147`).
  - Attempting to replay a cursor generated for Organization A inside Organization B fails with HTTP 400 `INVALID_CURSOR_SCOPE`.
  - Modifying the cursor payload breaks the HMAC signature and fails with HTTP 400 `TAMPERED_CURSOR`.
- **Verdict**: Cryptographically solid and strictly prevents cross-context cursor replays.

---

### 7.5 Audit Ledger Integrity (`audit.py`)
- **Mandatory Tenancy**: `AuditEvent.organization_id` is a non-nullable column (`audit.py:47`). `AuditService.record_event` requires `organization_id` as a non-optional argument (`audit.py:34`).
- **Tamper Detection**: Computes a canonical SHA-256 checksum over the event payload (`calculate_checksum`, `audit.py:24-28`), persisted in `payload_checksum`.
- **Audit Completeness**: Context fields (`organization_id`, `case_id`, `actor_ref`, `correlation_id`) are persistently recorded for all state transitions and engine operations.

<!-- SECTION 7 DONE -->


## S8 Isolation Test Coverage

### 8.1 Existing Isolation & Auth Test Suite
Audit of test modules validating security and boundary constraints:

| Test File | Test Function | Verified Property | Cross-Context Denial Verified? |
|---|---|---|---|
| `tests/test_saas_organization_isolation.py` | `test_five_real_organizations_signup_and_isolation` | Verifies 5 separate organizations can register, log in, create cases, and cannot view or list other organizations' cases. | **YES** (Verifies 404/empty across organizations) |
| `tests/test_organization_saas.py` | `test_switch_organization_security` | Verifies switching organizations requires verified membership in target org. | **YES** (Rejects cross-org switch with 403) |
| `tests/test_organization_saas.py` | `test_organization_member_management` | Verifies only admin can add employees to the organization. | **YES** (Rejects non-admin with 403) |
| `tests/test_case_access_control.py` | `test_employee_cannot_access_unassigned_case` | Service-level verification of `CaseService.validate_case_access` under CACS. | **YES** (Raises `CaseNotFoundError` for unassigned employee) |
| `tests/test_case_access_control.py` | `test_revoked_assignment_blocks_access` | Service-level check that deleting `CaseAssignment` cuts access. | **YES** (Raises `CaseNotFoundError` immediately) |
| `tests/test_ws_authorization_and_isolation.py` | `test_dual_boundary_event_isolation` | Verifies WebSocket Boundary A (cross-tenant rejection) and Boundary B (unscoped subscribers do not receive case-private events). | **YES** (Tenants and unscoped subscribers receive 0 case events) |
| `tests/test_ws_authorization_and_isolation.py` | `test_ws_ticket_endpoint_authorizations` | Verifies ticket creation requires valid user and case access. | **YES** (Fails ticket minting for unassigned case) |
| `tests/test_ws_authorization_and_isolation.py` | `test_ws_connection_and_replay_rejection` | Verifies ticket single-use consumption and replay denial. | **YES** (Replay closes socket with 1008) |
| `tests/test_ws_connection_pool.py` | `test_user_deactivation_closes_websocket` | Verifies periodic re-check detects deactivated user and terminates socket. | **YES** (Socket terminated on user deactivation) |
| `tests/test_ws_connection_pool.py` | `test_jwt_expiration_closes_websocket` | Verifies periodic re-check detects expired token and closes socket. | **YES** (Socket terminated on token expiry) |
| `tests/ring1/test_cursor_security.py` | `test_cross_organization_cursor_rejected` | Verifies HMAC-signed cursor cannot be replayed in a different organization. | **YES** (Raises HTTP 400 `INVALID_CURSOR_SCOPE`) |
| `tests/ring1/test_cursor_security.py` | `test_cross_case_cursor_rejected` | Verifies cursor cannot be replayed in a different case scope. | **YES** (Raises HTTP 400 `INVALID_CURSOR_SCOPE`) |
| `tests/ring1/test_cursor_security.py` | `test_tampered_cursor_signature_rejected` | Verifies HMAC signature tampering fails validation. | **YES** (Raises HTTP 400 `TAMPERED_CURSOR`) |
| `tests/ring1/test_idempotency_tenant_isolation.py` | `test_idempotency_scoped_by_organization` | Verifies two organizations submitting identical idempotency keys do not collide. | **YES** (Idempotency isolated by `organization_id`) |
| `tests/ring1/test_security_isolation_adversarial.py` | `test_adversarial_context_spoofing` | Verifies engine handles mismatched payload vs context. | **YES** (Rejects payload org mismatch) |

---

### 8.2 Untested Cross-Context Scenarios (Test Gaps by S3 Route)

| Route | Untested Cross-Context Vulnerability Scenario | Risk |
|---|---|---|
| `POST /api/v1/sources` | **NO TEST** checking organization or case isolation on raw file ingestion. (Sources are uploaded globally with `NULL` org/case). | **P0** |
| `POST /api/v1/ring1/upload-pdf` | **NO TEST** verifying that a user cannot ingest a PDF to an unassigned case or arbitrary foreign `case_id`. | **P1** |
| `GET /api/v1/ring1/knowledge` | **NO TEST** verifying that an employee in Org A cannot query knowledge records for an unassigned case in Org A via `?case_id=target_case`. | **P1** |
| `POST /api/v1/observations` | **NO TEST** verifying that an employee cannot submit observations claiming a case ID they are not assigned to. | **P1** |
| `GET /api/v1/observations` | **NO TEST** verifying that an employee cannot read another case's observation feed within the organization by passing `X-Case-ID`. | **P2** |
| `GET /api/v1/cases/{case_id}` | **NO HTTP ROUTE TEST** asserting that an employee receives `404` when requesting a case they are not assigned to. (`cases.py:126` only checks org, not assignment). | **P2** |
| `GET /api/v1/cases/{case_id}/documents` | **NO TEST** asserting that an unassigned employee is blocked from listing documents of another case. | **P2** |
| `GET /api/v1/cases/{case_id}/tasks` | **NO TEST** asserting that an unassigned employee is blocked from listing tasks of another case. | **P2** |
| `GET /api/v1/cases/{case_id}/knowledge` | **NO TEST** asserting that an unassigned employee is blocked from listing knowledge records of another case. | **P2** |
| `WS /api/v1/ws/observations` | **NO TEST** asserting that subscribing to a non-existent `case_id` string is blocked. (Currently permitted by `ws.py:126-127`). | **P1** |
| `GET /api/v1/brain/status` | **NO TEST** asserting that public status endpoints do not leak `settings.ORGANIZATION_ID` and `settings.ENVIRONMENT`. | **P2** |
| `SqlAlchemyRetrievalStore` | **NO TEST** asserting that unvalidated candidate memory records (`status == "candidate"`) are excluded from search results. | **P1** |

---

### 8.3 Test Suite Execution Evidence
Per Rule 7, the test suite was executed using the project virtual environment without installing dependencies:
- **Command**:
  ```powershell
  Set-Location d:\Study\projects\OrgBrain\backend; .venv\Scripts\python.exe -m pytest -q --ignore=tests/test_groq.py --ignore=tests/test_huggingface.py
  ```
- **Execution Output**:
  ```text
  172 passed, 177 errors in 351.75s (0:05:51)
  ```
- **Analysis**:
  - **172 unit and contract tests PASSED** (including `test_cursor_security.py`, `test_short_term_memory.py`, `test_contracts.py`, `test_handoff_policy.py`, `test_general_brain_api.py`, etc.).
  - **177 tests failed at database fixture setup** (`sqlalchemy.exc.OperationalError: connection to server at "localhost" (127.0.0.1), port 5433 failed: Connection refused`). The local PostgreSQL development daemon on port 5433 was offline during the audit. Tests relying on a live database connection could not complete fixture setup and are recorded as `NOT VERIFIED` for live runtime execution.

<!-- SECTION 8 DONE -->


## S9 Recently Changed Code

Detailed security review of the 6 recent remediations and changes:

### 9.1 `get_test_operator_user` Fail-Closed Logic (`deps.py:150-177`)
- **Target Commit**: `c877aa2 fix(security): F-001 fail-closed test operator bypass`
- **Assessment**: **CORRECT** in production; **RISKY** in development/test.
- **Evidence**:
  ```python
  # backend/app/api/deps.py:168-176
  if user.role == "admin" or settings.ENVIRONMENT.lower() != "production":
      return user
  ...
  if settings.ENVIRONMENT.lower() in ("development", "test") and getattr(settings, "ALLOW_TEST_OPERATOR", False):
      return None

  raise _AUTH_401
  ```
  - In `production`: Non-admin authenticated tokens fall through to L173. Line 173 evaluates to `False`. The function strictly raises `_AUTH_401`. Unauthenticated requests raise `_AUTH_401`. Production fail-closed behavior is verified.
  - **Identified Weakness**: Lines 170-171 contain `except Exception: pass`. Any unexpected runtime error during token decoding or database retrieval in non-production environments silently falls through to line 173, granting test operator bypass (`return None`) rather than failing with an error.

---

### 9.2 `organization_id` Handling in `ring1.py` (`upload_pdf`, `knowledge`)
- **Target Commit**: `48e7bad fix(ring1): F-002a org id comes from server settings, reject mismatch`
- **Assessment**: **RISKY** / **PARTIAL**.
- **Evidence**:
  ```python
  # backend/app/api/v1/ring1.py:167-172
  if organization_id and organization_id.strip() and organization_id.strip() != context.organization_id:
      raise HTTPException(
          status_code=status.HTTP_403_FORBIDDEN,
          detail="organization_id does not match this deployment.",
      )
  clean_org_id = context.organization_id
  clean_case_id = case_id.strip()
  ```
  - **What is Correct**: Rejecting mismatched `organization_id` prevents cross-tenant organization spoofing, and `clean_org_id` always defaults to `context.organization_id`.
  - **What is Risky / Defective**:
    1. Returns `403 Forbidden` instead of `404 Not Found`, leaking existence of organization mismatch to external callers.
    2. Completely skips `case_id` validation. `clean_case_id` is passed directly to the PDF execution pipeline and memory querying without verifying whether the case exists, belongs to the organization, or is accessible to the caller.

---

### 9.3 `MAX_UPLOAD_BYTES` Chunked Read in `sources.py`
- **Target Commit**: `a64a3c3 fix(sources): enforce MAX_UPLOAD_BYTES chunked limit on file ingestion (F-008)`
- **Assessment**: **CORRECT** for size enforcement; **BROKEN** for data isolation.
- **Evidence**:
  ```python
  # backend/app/api/v1/sources.py:59-68
  while chunk := await file.read(chunk_size):
      total_bytes += len(chunk)
      if total_bytes > settings.MAX_UPLOAD_BYTES:
          raise HTTPException(
              status_code=status.HTTP_413_CONTENT_TOO_LARGE,
              detail=f"File size exceeds maximum allowed size of {settings.MAX_UPLOAD_BYTES} bytes",
          )
      chunks.append(chunk)
  ```
  - Bounded chunk streaming stops reading immediately upon exceeding `MAX_UPLOAD_BYTES` (20MB), successfully preventing memory exhaustion from arbitrarily large payloads.
  - However, the endpoint still links files purely to `uploaded_by=current_user.id` and leaves `organization_id` and `case_id` as `None` (see Finding C-001).

---

### 9.4 `run_in_threadpool` in `observations.py`
- **Target Commit**: `3a730d2 fix(observations): run blocking DB calls off the event loop (F-007a)`
- **Assessment**: **CORRECT**.
- **Evidence**:
  ```python
  # backend/app/api/v1/observations.py:50, 106, 107
  existing = await run_in_threadpool(lambda: db.query(Observation)...first())
  ...
  await run_in_threadpool(db.commit)
  await run_in_threadpool(db.refresh, obs)
  ```
  - Offloads blocking synchronous SQLAlchemy calls (`query`, `commit`, `refresh`) from the async event loop to Starlette's threadpool worker.
  - Calls are strictly awaited sequentially, preventing concurrent access to the same `Session` instance.

---

### 9.5 `ws.py` Active-User Re-Check & `SessionLocal` Pool Safety
- **Target Commits**:
  - `8db328c fix(ws): prevent connection pool exhaustion`
  - `3bcdf18 fix(ws): F-010 reject inactive users and recheck active/expiry on open sockets`
- **Assessment**: **CORRECT** for pool safety & revocation; **BROKEN** for non-existent cases.
- **Evidence**:
  ```python
  # backend/app/api/v1/ws.py:41-43, 71-73
  def _user_is_active(user_id: uuid.UUID) -> bool:
      with SessionLocal() as db:
          user = db.get(User, user_id)
          return bool(user is not None and user.is_active)
  ```
  - Short-lived `SessionLocal()` context managers eliminate connection pool leakage. Idle WebSockets consume zero database pool connections.
  - The 30-second loop re-checks user active state, organization membership, case assignment, and JWT expiration timestamp (`ws.py:245-262`), terminating revoked sessions immediately.
  - **Defect**: Lines 126-127 (`ws.py`) explicitly return `True` if `case_match` is `None`, permitting subscriptions to non-existent case strings without CACS validation.

---

### 9.6 `conftest.py` Fixture Hardening & Test Isolation
- **Target Code**: `backend/tests/conftest.py:41-47, 163-168`
- **Assessment**: **CORRECT**.
- **Evidence**:
  ```python
  # backend/tests/conftest.py:163-167
  test_session_factory = sessionmaker(
      bind=db_session.connection(),
      join_transaction_mode="create_savepoint",
  )
  monkeypatch.setattr("app.api.v1.ws.SessionLocal", test_session_factory)
  ```
  - Automatically overrides `SessionLocal` in `ws.py` to route through the transactional `db_session` savepoint during testing, preventing WebSocket tests from attempting to open out-of-band connections to non-test databases.
  - Protects test suite database safety via `assert_safe_test_database`.

<!-- SECTION 9 DONE -->


## S10 Findings Register

Comprehensive register of all 14 security findings identified across S1–S9, sorted strictly by Severity (P0 → P3).

| ID | Severity | Status | Title | File:Line | Exploit Scenario / Impact | Quick Verification Procedure | Proposed Plain-Words Fix | Effort | Dependencies |
|---|---|---|---|---|---|---|---|---|---|
| **C-001** | **P0** | CONFIRMED | Unscoped Global Source Document Ingestion | `backend/app/api/v1/sources.py:81-92`, `models/source.py:46` | An authenticated user uploads documents that are stored with `organization_id=NULL` and `case_id=NULL`, placing files into a global unscoped pool and violating tenant isolation. | Call `POST /api/v1/sources` with a valid token; query PostgreSQL `SELECT id, organization_id, case_id FROM sources` and observe `NULL` values. | Change auth dependency to `get_brain_context`, pass `organization_id` and `case_id` into `create_source()`, and alter DB schema to make `organization_id` `NOT NULL`. | S | None |
| **C-002** | **P1** | CONFIRMED | Normal Knowledge Retrieval Returns Unvalidated Candidates | `backend/app/infrastructure/database/stores.py:382-392` | Unvalidated candidate observations (`status="candidate"`) are returned in normal semantic retrieval alongside validated knowledge, polluting LLM prompts with untrusted facts. | Ingest raw document creating candidate facts; execute `GET /api/v1/retrieval/search` and observe candidate facts returned with `status="candidate"`. | In `SqlAlchemyRetrievalStore.search_records`, add default `.where(MemoryRecord.status == "validated")`, requiring an explicit parameter to query candidates. | S | None |
| **C-003** | **P1** | CONFIRMED | Unvalidated `case_id` in Ring 1 Ingestion & Knowledge Endpoints | `backend/app/api/v1/ring1.py:174-179, 269-275`, `pdf_pipeline_service.py:804` | Any employee in an organization can view all knowledge records or ingest documents into ANY case in that organization simply by supplying `?case_id=target_case`, completely bypassing CACS. | Call `GET /api/v1/ring1/knowledge?case_id=<unassigned_case_uuid>` as a restricted employee; observe HTTP 200 and all case memory records returned. | Call `CaseService.validate_case_access` in both `upload_pdf` and `get_case_knowledge` prior to execution, failing closed with 404 if unauthorized. | M | C-005 |
| **C-004** | **P1** | CONFIRMED | Unvalidated `case_id` in Observation Creation | `backend/app/api/v1/observations.py:45, 83` | A user can record observations under any arbitrary case ID string within their organization because `payload.case_id` is written directly without permission checks. | Submit `POST /api/v1/observations` with `payload.case_id` set to an unassigned case; verify observation row is inserted with that case ID. | Validate `payload.case_id` using `CaseService.validate_case_access` before creating `Observation`, returning 404 if denied. | S | C-005 |
| **C-005** | **P1** | CONFIRMED | Architecture-Wide Absence of Shared Context Query Filtering Helper | Architecture-wide (`stores.py`, `cases.py`, `pdf_pipeline_service.py`, `observations.py`) | Every endpoint and store writes SQL WHERE clauses by hand, resulting in inconsistent scoping, omitted CACS checks, and leaky queries across the system. | Grep for queries across `backend/app/` to observe hand-crafted WHERE clauses and lack of uniform helper. | Create a centralized `apply_context_filter(query, model, context)` helper and mandate its usage across all repositories and routes. | L | None |
| **C-006** | **P1** | CONFIRMED | WebSocket CACS Authorization Bypass on Non-Existent Cases | `backend/app/api/v1/ws.py:126-127` | A client subscribing to a `case_id` that does not exist in the database is automatically granted access, creating an unmonitored event channel. | Connect to `/api/v1/ws/observations?case_id=nonexistent-case-uuid`; observe WebSocket handshake succeeds instead of failing closed with 1008. | Fail closed: if `case_match` is None, return `False` so `_handle_websocket_stream` terminates with `WS_1008_POLICY_VIOLATION`. | S | None |
| **C-007** | **P2** | CONFIRMED | Unassigned Employees Can Access All Cases in `cases.py` Endpoints | `backend/app/api/v1/cases.py:126, 154, 205, 246, 292` | Endpoints in `cases.py` call `CaseService.get_case()` which only verifies organization ownership, allowing any employee to view documents, tasks, and knowledge of cases they are not assigned to. | As an employee unassigned to Case X, call `GET /api/v1/cases/{case_x_id}`; observe 200 OK instead of 404. | Replace `CaseService.get_case()` with `CaseService.validate_case_access()` across all case sub-resource routes in `cases.py`. | M | C-005 |
| **C-008** | **P2** | CONFIRMED | Public Information Disclosure of Internal Deployment Identifiers | `backend/app/api/v1/brain.py:54-55` | Unauthenticated public callers can discover the server's internal deployment `ORGANIZATION_ID` (`org-brain-corp`) and `ENVIRONMENT` (`production`). | Send `curl -X GET http://localhost:8000/api/v1/brain/status` with no auth headers; observe internal org and env in response. | Remove `organization_id` and `environment` from public response, or protect endpoint behind `get_current_user`. | S | None |
| **C-009** | **P2** | CONFIRMED | Status Code Oracle Leaking Case Existence (403 vs 404) | `backend/app/api/v1/ai.py:146-150`, `backend/app/api/v1/context.py:84-86` | Probing case IDs via AI prompt or context resolution returns 403 Forbidden instead of 404 Not Found, revealing whether target cases exist. | Call `POST /api/v1/ai/prompt` with an unassigned case; observe 403 status code instead of 404. | Standardize on 404 Not Found (`CaseNotFoundError`) across all case authorization failures. | S | None |
| **C-010** | **P2** | CONFIRMED | Unscoped In-Memory Database Lookups via `db.get()` | `backend/app/api/v1/tasks.py:32`, `backend/app/api/v1/memory.py:37` | `db.get(Task, task_id)` and `db.get(MemoryRecord, id)` fetch rows into memory before evaluating organization ownership in Python. | Inspect SQL statements generated during `GET /tasks/{task_id}`; observe lack of `WHERE organization_id = :org_id` in SQL query. | Use `session.query(Model).filter(Model.id == id, Model.organization_id == context.organization_id).first()` in SQL. | S | C-005 |
| **C-011** | **P2** | CONFIRMED | Automatic Case Insertion Bypasses Workflow in PDF Ingestion | `backend/app/ring1/services/pdf_pipeline_service.py:150-153` | If a PDF upload specifies a non-existent case_id, the service creates a new `Case` row with `status="open"` without user validation or auditing. | Upload a PDF with a random UUID for `case_id`; check `cases` table to verify auto-created `AUTO-...` row. | Require case to exist and be accessible; reject with 404 if case does not exist. | S | C-003 |
| **C-012** | **P2** | CONFIRMED | Global User Creation Unbound to Admin Organization | `backend/app/api/v1/users.py:38-64` | Admin creating a user does not associate the user with the admin's organization, creating dangling unscoped accounts. | As admin, call `POST /api/v1/users`; observe created user has no row in `organization_memberships`. | Automatically create `OrganizationMembership` binding the new user to the creator's `organization_id`. | M | None |
| **C-013** | **P3** | CONFIRMED | Broad Exception Swallowing in `get_test_operator_user` | `backend/app/api/deps.py:170-171` | `except Exception: pass` swallows unexpected database or token decoding errors, falling through to dev test operator bypass. | Inject a DB error during token check; observe silent fallthrough to line 173. | Catch specific exceptions (`TokenSecurityError`, `ValueError`) and re-raise or fail closed on DB errors. | S | None |
| **C-014** | **P3** | CONFIRMED | Missing WebSocket Connection Limit Ceiling | `backend/app/core/ws_manager.py:30-61` | `ObservationWebSocketManager` does not limit the number of simultaneous connections per user/org, risking socket exhaustion. | Open hundreds of WebSocket connections from one client; observe unlimited memory allocation. | Add `MAX_CONNECTIONS_PER_ORG` / `MAX_CONNECTIONS_PER_USER` limit in `ws_manager.connect()`. | S | None |

<!-- SECTION 10 DONE -->


## S11 Fix Plan

The 14 identified findings are organized into 4 focused, safe remediation batches designed for independent implementation and verification.

---

### Batch 1: Immediate Ingestion Containment & Public Privacy (Session 1)
- **Findings Covered**:
  - `C-001` (P0: Unscoped Source Ingestion)
  - `C-006` (P1: WebSocket Bypass on Non-Existent Cases)
  - `C-008` (P2: Public Deployment Metadata Disclosure)
- **Files Touched**:
  - `backend/app/api/v1/sources.py`
  - `backend/app/models/source.py`
  - `backend/app/services/source_service.py`
  - `backend/app/api/v1/ws.py`
  - `backend/app/api/v1/brain.py`
- **Tests to Add**:
  - `tests/test_sources_isolation.py`: Verify `POST /api/v1/sources` stamps `organization_id` from `BrainContext` and rejects unauthenticated callers.
  - `tests/test_brain_status_privacy.py`: Verify `GET /api/v1/brain/status` does not leak `settings.ORGANIZATION_ID` or `settings.ENVIRONMENT`.
  - `tests/test_ws_nonexistent_case.py`: Verify WebSocket connection specifying a non-existent `case_id` fails closed with code `1008`.
- **Potential Regressions / What Could Break**:
  - External API clients relying on `GET /api/v1/brain/status` to read deployment metadata.
  - Legacy tests calling `POST /api/v1/sources` without providing `BrainContext` headers.

---

### Batch 2: CACS Authorization Enforcement on Case Resources (Session 2)
- **Findings Covered**:
  - `C-003` (P1: Unvalidated `case_id` in Ring 1 Ingestion & Knowledge)
  - `C-004` (P1: Unvalidated `case_id` in Observation Creation)
  - `C-007` (P2: Unassigned Employee Case Access in `cases.py`)
  - `C-011` (P2: Automatic Case Insertion in PDF Ingestion)
- **Files Touched**:
  - `backend/app/api/v1/ring1.py`
  - `backend/app/api/v1/cases.py`
  - `backend/app/api/v1/observations.py`
  - `backend/app/ring1/services/pdf_pipeline_service.py`
- **Tests to Add**:
  - `tests/test_ring1_case_cacs.py`: Assert employee unassigned to Case X receives `404 Not Found` when calling `POST /ring1/upload-pdf` or `GET /ring1/knowledge?case_id=X`.
  - `tests/test_cases_cacs_http.py`: Assert employee unassigned to Case X receives `404 Not Found` when accessing `GET /cases/{case_x_id}` and its sub-resources (`documents`, `tasks`, `knowledge`).
  - `tests/test_observations_cacs.py`: Assert `POST /api/v1/observations` with unassigned `payload.case_id` raises `404 Not Found`.
- **Potential Regressions / What Could Break**:
  - PDF ingestion automated tests that relied on `pdf_pipeline_service.py` synthesizing auto-cases on the fly. Tests must explicitly create and assign the target case first.

---

### Batch 3: Retrieval Knowledge Filtration & Anti-Oracle Standardization (Session 3)
- **Findings Covered**:
  - `C-002` (P1: Normal Retrieval Returns Unvalidated Candidates)
  - `C-009` (P2: Status Code Oracle Leaking Case Existence via 403)
- **Files Touched**:
  - `backend/app/infrastructure/database/stores.py`
  - `backend/app/api/v1/ai.py`
  - `backend/app/api/v1/context.py`
- **Tests to Add**:
  - `tests/test_retrieval_candidate_exclusion.py`: Verify `SqlAlchemyRetrievalStore.search_records` filters by `status == "validated"` by default and excludes candidate observations.
  - `tests/test_anti_oracle_status_codes.py`: Verify that accessing an unauthorized case via `POST /ai/prompt` or `POST /context/resolve` returns `404 Not Found` rather than `403 Forbidden`.
- **Potential Regressions / What Could Break**:
  - Existing tests in `test_ai_integration.py` or `test_api_v1_ring1.py` that specifically assert `response.status_code == 403` will need assertion updates to `404`.

---

### Batch 4: Centralized Query Scoping Helper & Architecture Hygiene (Session 4)
- **Findings Covered**:
  - `C-005` (P1: Architecture-Wide Lack of Shared Context Query Helper)
  - `C-010` (P2: Unscoped Database Lookups via `db.get`)
  - `C-012` (P2: Global User Creation Unbound to Admin Organization)
  - `C-013` (P3: Broad Exception Swallowing in `get_test_operator_user`)
  - `C-014` (P3: WebSocket Connection Limit Ceiling)
- **Files Touched**:
  - `backend/app/core/query_filters.py` (New centralized query helper module)
  - `backend/app/api/v1/tasks.py`
  - `backend/app/api/v1/memory.py`
  - `backend/app/api/v1/users.py`
  - `backend/app/api/deps.py`
  - `backend/app/core/ws_manager.py`
- **Tests to Add**:
  - `tests/test_shared_query_filters.py`: Test unit queries using `query_filters.py` with mock models, verifying tenant and CACS injection in SQL.
  - `tests/test_users_admin_binding.py`: Verify `POST /api/v1/users` automatically binds the created user to the creator admin's organization.
  - `tests/test_ws_connection_limits.py`: Verify exceeding `MAX_CONNECTIONS_PER_ORG` closes additional sockets with `1008`.
- **Potential Regressions / What Could Break**:
  - Refactoring endpoint queries to use the shared helper requires careful testing across all query combinations to ensure no unexpected column collisions.

<!-- SECTION 11 DONE -->


## S12 Not Verified and Open Questions

### 12.1 Unverified Items & Limitations

1. **Live Database Integration Test Suite Execution (`NOT VERIFIED`)**:
   - Running the pytest suite (`.venv\Scripts\python.exe -m pytest -q --ignore=tests/test_groq.py --ignore=tests/test_huggingface.py`) yielded:
     ```text
     172 passed, 177 errors in 351.75s
     ```
   - All 177 failures were caused by `sqlalchemy.exc.OperationalError: connection to server at "localhost" (127.0.0.1), port 5433 failed: Connection refused`.
   - The local PostgreSQL daemon on port 5433 was offline during the audit. While 172 in-memory/contract tests passed, runtime verification of PostgreSQL transactional rollback, savepoint behavior, and live query execution remains **UNVERIFIED**.
2. **Pgvector / Embedding Partition Isolation (`NOT VERIFIED`)**:
   - The schema includes pgvector structures for semantic search. Verification of cosine distance filtering across tenant partitions in PostgreSQL with real embeddings could not be verified without a running database and embedding service.
3. **Multi-Node Redis Cluster State (`NOT VERIFIED`)**:
   - `ShortTermMemoryService` was verified in local in-memory fallback mode. Clustered Redis distributed TTL eviction, cross-node replication latency, and memory cleanup under high concurrency remain unverified on live cluster hardware.
4. **Physical Disk Volume Ingestion Isolation (`NOT VERIFIED`)**:
   - `POST /api/v1/sources` writes raw files to `raw_storage/` via `LocalStorageBackend`. While the database record creation was audited, host operating system directory permissions and shared-volume file isolation were not inspected.

---

### 12.2 Open Decisions Requiring Human Alignment

1. **Tenant Binding on User Identities**:
   - *Current Design*: The `users` table carries no `organization_id`. Users exist in a global namespace and link to organizations via `organization_memberships`.
   - *Decision Needed*: If each deployment represents exactly one organization (`settings.ORGANIZATION_ID`), should user creation automatically bind accounts to `settings.ORGANIZATION_ID` with a non-nullable column, preventing cross-organization account sprawl?
2. **Review & Approval Endpoint for Candidate Knowledge**:
   - *Current Design*: Unvalidated candidate facts are created with `status="candidate"`.
   - *Decision Needed*: Once `SqlAlchemyRetrievalStore` excludes candidate facts from normal retrieval (to satisfy the design rule that observations are not knowledge), what workflow and dedicated UI endpoint will operators with `validation_authority` use to review, approve, or reject candidate knowledge?
3. **Public Monitoring vs Metadata Privacy**:
   - *Current Design*: `GET /api/v1/brain/status` exposes `organization_id` and `environment` without authentication.
   - *Decision Needed*: Is this endpoint intended as an unauthenticated orchestrator probe (e.g. Kubernetes readiness)? If yes, internal tenant identifiers must be stripped. If it is an administrative diagnostics endpoint, it must be protected by `Depends(get_current_user)`.
4. **Permissibility of Unscoped Observations**:
   - *Current Design*: `POST /api/v1/observations` permits creating observations without a `case_id` (organization-wide scope).
   - *Decision Needed*: Should all observations in legal domain workflows strictly mandate a valid `case_id`, failing closed if no case scope is provided?

<!-- SECTION 12 DONE -->
