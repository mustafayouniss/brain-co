# Ring 0 — Foundation (Backend scope)

> Source: Constitution v2.0, "RING 0 — FOUNDATION", filtered through `decisions.md` (stack D-001/D-002, no graph DB D-003, one org per deployment D-004, roles D-005).
> If this file and `decisions.md` disagree, `decisions.md` wins. Anything not written here: STOP and ask Karim.
> Status: **in progress.** Ring 1 does not start until every exit check below passes with shown evidence.

---

## 1. Purpose

Establish the development environment and core infrastructure so every later ring has solid ground: a running database, an API skeleton, an authentication skeleton, and a working test setup.

## 2. Hard boundaries for this ring (read before planning anything)

- **Rings 0, 1, 2 are General Brain only `[GB]`.** No legal-specific logic, tables, or terms. The Legal domain starts in **Ring 3**; the complete Legal V1 is **Ring 10**.
- **Do NOT create** Case, Client, Conversation, Knowledge, Observation, or Organization tables. Those belong to later rings (Case and Client are Ring 5).
- **Do NOT build** configurable roles, permissions, or validation authority. That is Ring 4. Ring 0 has only two fixed roles: `admin` and `employee` (D-005).
- **No multi-tenant fields** (no `organization_id` columns). One organization per deployment (D-004).
- **No new tools** (job queue, cache, password-hashing library, etc.) without proposing options in the plan and getting Karim's approval, then recording the choice in `decisions.md` (D-009).
- Out of scope for the backend in Ring 0: frontend skeleton, AI/LLM infrastructure, data pipelines, evaluation framework (other teams), graph database (not adopted, D-003), object storage (OPEN-3, undecided).

## 3. Already done (reported in `docs/progress.md`)

Python 3.12 venv, pinned dependencies, Docker Postgres 17 + pgvector with healthcheck, config and DB session modules, Alembic initialized, first migration enabling the `vector` extension, folder scaffold, documentation set, `AGENTS.md` rules.

## 4. Remaining tasks (one task = one new chat = plan first)

Classification labels: `[GB]` General Brain, `[SHARED]` cross-layer.

| # | Task | Label | Notes |
|---|---|---|---|
| T1 | `GET /health` returning `{"status": "ok"}` + test using FastAPI `TestClient` | `[GB]` | Mount in `app/main.py`. |
| T2 | Git: `git init`, verify `.gitignore`, first local commit | `[GB]` | **Local only.** Do not push anywhere until OPEN-7 in `decisions.md` is resolved (the team repo `brain-co` already exists). |
| T3 | Test setup: `pytest` config, `conftest.py`, tests never touch the development database | `[GB]` | **[CONFIRM]** separate test database (for example `orgbrain_legal_test`), created and migrated by the test setup. |
| T4 | API structure: versioned prefix `/api/v1`, routers under `app/api/`, one consistent JSON error format, `GET /api/v1/health/db` that runs `SELECT 1` | `[GB]` | Proves "infrastructure services are accessible". |
| T5 | `users` table + SQLAlchemy model + Alembic migration | `[SHARED]` | Fields: id (UUID), email (unique), full_name, hashed_password, role (`admin` or `employee`), is_active, created_at. No organization fields. |
| T6 | Security utilities: password hashing, JWT create/verify, with unit tests | `[SHARED]` | Hashing library not chosen: propose options in the plan (D-009). PyJWT is fixed (D-001). Secret and expiry come from `.env`. |
| T7 | Auth endpoints: `POST /api/v1/auth/login`, `GET /api/v1/auth/me` | `[SHARED]` | **[CONFIRM]** access token only for now (stateless). "Sign out" = client discards the token; refresh tokens and server-side revocation are undecided, do not build. |
| T8 | Authorization dependencies: `get_current_user`, `require_admin`, and one admin-only sample endpoint | `[SHARED]` | Enforced server-side only. |
| T9 | Create the first admin: a seed command (not a public endpoint) reading credentials from `.env` | `[SHARED]` | **[CONFIRM]** no public sign-up; the admin creates employee accounts (add `POST /api/v1/users`, admin-only, in this task or its own). |
| T10 | API contract: `docs/api/auth.md` with endpoints, request/response examples, error format, status codes | `[SHARED]` | For the frontend and mobile consumers (OPEN-5). Generated from the real, tested API, never from memory. |
| T11 | CI: GitHub Actions workflow running pytest against a Postgres service | `[GB]` | Only after OPEN-7 is decided. Check the team's existing `.github` workflows first; do not duplicate them. Constitution requires CI/CD in Ring 0. |

Order: T1, T2, T3, T4, T5, T6, T7, T8, T9, T10, T11. Do not skip ahead.

## 5. Required tests (minimum)

- Health: 200 and exact body; DB health: 200 when the database is up.
- Login: success returns a token; wrong password and unknown email both return 401 with the same message.
- `/auth/me`: 401 without a token, 401 with an invalid or expired token, 200 with a valid one.
- Authorization: an `employee` calling an admin-only endpoint gets 403; an `admin` gets 200.
- Inactive user cannot log in.
- Passwords are never stored or returned in plain text (check the database row and every response).

## 6. Exit criteria (all must be shown with real terminal output)

1. `python --version` inside the venv shows 3.12.x.
2. `docker compose up -d` and Postgres reports healthy.
3. From an empty database volume, `alembic upgrade head` runs cleanly (extension and `users` table created) and a second run does not error.
4. `/health` and `/api/v1/health/db` respond correctly.
5. Full `pytest` run passes, including every test in section 5.
6. `.env` is git-ignored and no secret appears in git history.
7. A person who did not do the setup can run the project locally using only `docs/environment.md` (Constitution: "all team members can run the project locally").
8. Code is pushed to the agreed repository (OPEN-7) and CI is green.
9. Documentation updated: `progress.md`, journal entry, `architecture.md`, `how-it-works.md`, `docs/api/auth.md`.
10. Karim and Claude review passed (checks claims against evidence).

## 7. Risks

- Infrastructure complexity and unfamiliarity with the stack (mitigated by `environment.md` and small tasks).
- Agent builds beyond scope (Case/Client tables, configurable permissions, multi-tenant fields). Section 2 is the guard.
- Auth done insecurely (plain-text passwords, secrets in git, tokens that never expire). Section 5 tests are the guard.

## 8. What Ring 1 unlocks

Ring 1 (Brain Core): Perception, Observation, Context, basic Memory and basic Retrieval engines, all `[GB]`.
