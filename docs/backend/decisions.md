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
