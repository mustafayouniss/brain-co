# Progress

## Done
- Moved all backend documentation into `docs/backend/`.
- Deleted outdated copies from root `docs/`.
- Implemented Foundational Source Ingestion Pipeline in `data-engineering/orgbrain_ingest/` (validation, SHA-256 fingerprinting, raw storage abstraction, LocalStorageBackend, orchestration pipeline).
- Authored 24 unit tests in `data-engineering/tests/` (100% passing).
- Created deterministic evaluation fixtures in `data-engineering/fixtures/ingestion/`.
- Created `Source` SQLAlchemy model in `backend/app/models/source.py` and exported in `backend/app/models/__init__.py`.
- Created Pydantic `SourceResponse` schema in `backend/app/schemas/source.py`.
- Created `source_service.py` with caller-owned commit / flush pattern.
- Created Alembic migration `e819b932c01a_create_sources_table.py`.
- Created `backend/tests/test_source_model.py`.
- Created `backend/app/api/v1/sources.py` endpoint handler.
- Created technical documentation in `docs/source-ingestion.md`.
- **Replaced frontend with Seif's Next.js application and integrated with backend/AI**:
  - Backed up original skeletal frontend to `frontend_backup_2026-10-15/`
  - Moved Seif's complete Next.js 16.4.0 frontend to `frontend/` (canonical path)
  - Replaced simulated auth with real FastAPI JWT authentication
  - Integrated AI into workspace via backend `/api/v1/ai/prompt` endpoint
  - Removed floating AI chat widget (per task constraints)
  - Frontend builds successfully, typecheck passes
  - Backend tests pass (108/108)
  - Auth and AI integration verified via curl
- **Fixed authentication and session integration**:
  - Implemented Next.js server-side login with HttpOnly cookies
  - Created `/api/auth/login`, `/api/auth/logout`, `/api/auth/session` routes
  - Removed localStorage JWT storage (deprecated functions kept for compatibility)
  - Fixed proxy-storage token mismatch
  - Removed development authentication bypass in proxy
  - Added CSRF protection for state-changing API routes
  - Cookie expiry aligned with backend JWT lifetime (60 minutes)
  - Verified login, session, logout, and AI proxy via curl

## Next
- Resolve pre-existing merge conflicts in `config.py`, `deps.py`, `v1/__init__.py`, `errors.py`.
- Apply Alembic migration `e819b932c01a` to create `sources` table in database.
- Mount `/api/v1/sources` router and run backend integration tests.
- Address frontend dependency vulnerabilities (npm audit fix --force)
- Test end-to-end frontend-backend-AI flow via browser UI

## Blockers
- Pre-existing Git merge conflicts in `backend/app/core/config.py`, `backend/app/api/deps.py`, `backend/app/api/v1/__init__.py`, and `backend/app/core/errors.py` block Alembic execution, API route mounting, and backend test runner.
