# Development Environment Setup Progress

## What's Done
- [x] Inspected system versions (Python, pip, Git, Docker, winget).
- [x] Installed Python 3.12 (`cpython-3.12.13-windows-x86_64-none`) via `uv python install 3.12`.
- [x] Created Python 3.12 virtual environment at `backend/.venv` via `uv venv backend/.venv --python 3.12`.
- [x] Installed target packages (`fastapi`, `uvicorn[standard]`, `sqlalchemy==2.0.54`, `alembic`, `psycopg[binary]`, `pgvector`, `pydantic`, `pydantic-settings`, `pyjwt`, `pytest`, `httpx`).
- [x] Generated `backend/requirements.txt` via freeze from actual installed packages (UTF-8, no BOM).
- [x] Created `.gitignore`, `docker-compose.yml` (`pgvector/pgvector:pg17`), `.env.example`, and `.env`.
- [x] Scaffolded folder hierarchy (`backend/app/{api,services,models,schemas,core,db}`, `tests/`, `docs/{rings,adr}`).
- [x] Created `backend/app/core/config.py` (resolving `.env` from project root) and `backend/app/db/session.py` (sync SQLAlchemy + psycopg v3).
- [x] Started Postgres via Docker Compose and verified healthcheck passes (`healthy`).
- [x] Initialized Alembic in `backend/migrations`, configured `env.py` to use application settings.
- [x] Created first migration `6dd2ff08b0bb_enable_pgvector_extension.py` with `CREATE EXTENSION IF NOT EXISTS vector`.
- [x] Ran migration `alembic upgrade head`, proved idempotency with a second run, and verified `vector` extension (`v0.8.7`) exists in `pg_extension`.
- [x] Authored core documentation suite based exclusively on verified facts: `docs/environment.md`, `docs/architecture.md`, `docs/journal/2026-10-06.md`, `docs/how-it-works.md`, and `docs/00-START-HERE.md`.
- [x] Verified and locked `AGENTS.md` start/end-of-task rules and behavioral guidelines.
- [x] Updated environment setup docs (`docs/environment.md`), journal (`docs/journal/2026-10-06.md`), and verification log (`docs/verification-log.md`) to use `uv pip install` command syntax for uv-managed venv.
- [x] **T1** — `GET /health` returning `{"status": "ok"}` + test using FastAPI `TestClient`. Mounted in `app/main.py`.
- [x] **T2** — `git init`, verified `.gitignore` excludes `.env`/`.venv`/`__pycache__`/`.pytest_cache`, first local commit. Added safety and logging rules to `AGENTS.md`.

## What's Done (continued)
- [x] **T3** — Test setup: `pytest.ini`, `conftest.py` (safety guard + `alembic upgrade head` provisioning + per-test rollback session), smoke test, safety guard unit tests. Both databases verified in Postgres; dev DB has only `alembic_version`.
- [x] **T3b** — Test setup hardening: extended `assert_safe_test_database` to require `dev_db_name` and refuse equality with dev database; added AGENTS.md rule that tests must only use fixtures; added scanner test (`test_no_raw_db_in_tests.py`) forbidding `settings.DATABASE_URL` and `create_engine(` in test files; installed and pinned `httpx2==2.13.1` (test dependency), eliminating `StarletteDeprecationWarning`.

## What's Next (Ring 0 — remaining tasks, in order)
- [ ] **T4** — API structure: versioned prefix `/api/v1`, routers under `app/api/`, one consistent JSON error format, `GET /api/v1/health/db` that runs `SELECT 1`.
- [ ] **T5** — `users` table + SQLAlchemy model + Alembic migration.
- [ ] **T6** — Security utilities: password hashing, JWT create/verify, with unit tests.
- [ ] **T7** — Auth endpoints: `POST /api/v1/auth/login`, `GET /api/v1/auth/me`.
- [ ] **T8** — Authorization dependencies: `get_current_user`, `require_admin`, admin-only sample endpoint.
- [ ] **T9** — First admin: seed command (not a public endpoint).
- [ ] **T10** — Frontend contract: `docs/api/auth.md`.
- [ ] **T11** — CI: GitHub Actions. *(Only after OPEN-7 is decided.)*

## Known Issues
- None. (Starlette prefers httpx2; httpx still worked but emitted StarletteDeprecationWarning; resolved by installing httpx2==2.13.1 (https://pypi.org/project/httpx2/, maintained by Pydantic, source github.com/pydantic/httpx2). Earlier mention of issue 2826 was UNVERIFIED and removed.)

## Broken / Blockers
- None.
