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
- **Removed public self-registration to align with Ring 0 specifications**:
  - Replaced public registration form with admin-provisioning message
  - Updated onboarding flow to redirect to login instead of account creation
  - Aligned with Ring 0 T9: "no public sign-up; the admin creates employee accounts"
  - Frontend typecheck and production build pass
  - Backend user tests pass (25/25)
- **Added floating AI chat widget for integration testing**:
  - Created reusable floating chat widget component accessible from bottom-right corner
  - Widget uses existing `/api/ai/prompt` endpoint (Next.js) → `/api/v1/ai/prompt` (FastAPI) → LLMService
  - Reuses existing AI service abstraction and provider configuration
  - Session-based authentication via HttpOnly cookies
  - Displays loading, success, and error states (including retry capability and 401 messaging)
  - Resolved OpenRouter 402 token reservation error by injecting `max_tokens` from `ai_config.AI_MAX_TOKENS`
  - Frontend typecheck and production build pass (27 routes)
  - Backend integration tests pass (111/111)
  - Verified live end-to-end prompt response from `openai/gpt-4o-mini` via OpenRouter

- **Integrated Document Ingestion and Sources Endpoint**:
  - Mounted `sources_router` at `/api/v1/sources` in FastAPI backend
  - Applied Alembic migration `e819b932c01a` creating `sources` table in PostgreSQL
  - Created `frontend/src/app/api/documents/upload/route.ts` proxying file uploads to backend
  - Integrated `onboarding/upload/page.tsx` with real error messages and upload handling
  - Authored integration tests in `backend/tests/test_sources_endpoint.py` (4/4 passed)
  - Full test suite passes: 115 backend tests + 24 data engineering tests (139 passing tests total)
  - Verified end-to-end file upload and PostgreSQL persistence via curl

- **Implemented Development-Only Anonymous AI Testing Mode**:
  - Added `AI_ANONYMOUS_TESTING_ENABLED` and `ENVIRONMENT` configuration settings with strict production guard (`model_validator` refuses startup in production).
  - Added `get_ai_user_or_anonymous` dependency in `backend/app/api/deps.py` authoritatively controlling anonymous access on the backend.
  - Added input limits (`min_length=1`, `max_length=10000`) on `PromptRequest` in `backend/app/api/v1/ai.py`.
  - Updated `frontend/src/app/api/ai/prompt/route.ts` to forward requests without token so backend can authoritatively decide.
  - Verified unrelated endpoints (`POST /api/v1/sources`, `POST /api/v1/users`) remain 100% protected.
  - Authored comprehensive automated test suite in `backend/tests/test_ai_integration.py` (13/13 passing).
  - Full test suite passes: 122 backend tests + 24 data engineering tests (146 passing tests total).
  - Verified live in Chrome CDP: public unauthenticated user submits prompt to floating chat widget and receives genuine `openai/gpt-4o-mini` response (`ANONYMOUS_AI_TEST_SUCCESS`).

- **Completed Floating AI Widget UI/UX Transformation**:
  - Redesigned launcher with glowing neural gradient ring, contextual greeting teaser pill ("Ask Legal AI"), and unread notification badge.
  - Implemented Framer Motion animations for window entrance, message arrival, and interaction micro-animations (respecting `prefers-reduced-motion`).
  - Added interactive starter prompts for quick legal inquiries, with automatic prompt submission.
  - Added copy-to-clipboard action with visual checkmark confirmation on assistant messages.
  - Added new conversation reset action, dynamic 3-dot thinking pulse indicator, and inline retry on error.
  - Supported auto-resizing multiline composer with Enter to send and Shift+Enter for newlines.
  - Verified mobile responsive layout (390px viewport width) with 0 horizontal overflow.
  - Preserved backend contracts, OpenRouter AI integration, and development-only anonymous mode.

- **Corrected Global Chatbot to General Brain Assistant (Domain Separation)**:
  - Replaced all legal-specific starter prompts in floating-chat-widget.tsx with general Brain product questions.
  - Updated header subtitle, empty-state heading/description, placeholder, and teaser pill to reflect Brain assistant identity.
  - Added `BRAIN_SYSTEM_PROMPT` to `backend/app/api/v1/ai.py`, grounded in PROJECT_SCOPE.md, directing legal questions to the Legal workspace.
  - Acceptance tests verified via live openai/gpt-4o-mini via OpenRouter: BRAIN_GENERAL_ASSISTANT_RELEASE_SUCCESS confirmed.
  - All 5 domain-separation acceptance tests passed (Tests A–E).
  - Full test suite passes: 122 backend + 24 data-engineering + 13 AI integration (159 total).
  - Frontend typecheck and production build pass with 0 errors.

## Next
- Address frontend dependency vulnerabilities (npm audit fix --force)
- Prepare clean commit of Ring 0 verified state upon user authorization

## Blockers
- None. Brain general assistant identity, domain separation, UI/UX transformation, AI integration, and anonymous testing all verified end-to-end.
