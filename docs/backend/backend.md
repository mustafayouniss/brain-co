# Backend Documentation

## Overview
This document provides a comprehensive overview of the backend implementation for the OrgBrain project. It is intended for teammates working on the frontend, AI, or data science components, so they can understand backend design decisions, APIs, data models, and operational considerations without needing to ask the backend developers directly.

---

## Tech Stack (Non‑negotiable)
- **Language**: Python 3.12
- **Web Framework**: FastAPI
- **Database**: PostgreSQL with `pgvector` extension for vector search
- **ORM**: SQLAlchemy 2.0
- **Migrations**: Alembic
- **Data Validation & Settings**: Pydantic v2
- **Authentication**: PyJWT
- **Testing**: pytest (using `test_engine` and `db_session` fixtures only)
- **Containerisation**: Docker (standardised in `docker-compose.yml`)

---

## Project Structure
```
OrgBrain/
├─ app/                # FastAPI application package
│   ├─ api/            # Routers (endpoints)
│   ├─ core/           # Settings, security utilities
│   ├─ db/             # SQLAlchemy models, session handling
│   ├─ schemas/        # Pydantic request/response models
│   └─ services/       # Business‑logic layer
├─ migrations/         # Alembic migration scripts
├─ tests/              # pytest test suite
├─ docs/               # Documentation (this file lives here)
├─ alembic.ini
├─ requirements.txt
└─ pyproject.toml
```

---

## API Design Principles
1. **RESTful** endpoints defined in `app/api/` using FastAPI routers.
2. **Versioning** – all public endpoints are prefixed with `/api/v1/`.
3. **Authentication** – JWT token passed in `Authorization: Bearer <token>` header; enforced via a FastAPI dependency.
4. **Error handling** – use `HTTPException` with appropriate status codes; custom error responses defined in `app/core/exceptions.py`.
5. **Pagination** – standard limit/offset query parameters; results are ordered deterministically.
6. **Filtering & Permissions** – every request is filtered by `case_id` (or analogous tenant identifier) server‑side; callers must never receive data outside their scope.

---

## Database Overview
- **Schema** resides in `app/db/models.py`.
- Every table includes a primary key `id` (UUID) and a `case_id` column for tenant isolation.
- Vector columns use `pgvector` (e.g., `embedding vector(1536)`).
- **Migrations** – any schema change must be accompanied by an Alembic migration (`alembic revision --autogenerate`). Direct DB edits are prohibited.

---

## Authentication & Authorization
- JWTs are signed with a secret defined in `app/core/config.py`.
- Token payload includes `user_id`, `role`, and `case_id`.
- Role‑based access control is enforced in endpoint dependencies (`get_current_user`, `require_role`).
- All data access layers automatically filter by `case_id` extracted from the token.

---

## Testing Strategy
- Tests live under `tests/` and must use the provided fixtures `test_engine` and `db_session`.
- No test should instantiate a real engine from the development `DATABASE_URL`.
- Use `client` fixture (FastAPI `TestClient`) for endpoint testing.
- Run the test suite with:
  ```powershell
  pytest
  ```
- Coverage threshold is 90 %; CI will fail otherwise.

---

## Deployment & Ops
- Docker image built from `Dockerfile` targeting `python:3.12-slim`.
- Environment variables (`DATABASE_URL`, `SECRET_KEY`, etc.) are injected via Docker Compose or the hosting platform.
- Migrations run on container start (`alembic upgrade head`).
- Health check endpoint: `GET /health` returns `200 OK` when the DB connection is healthy.

---

## How Frontend / AI / Data‑Science Teams Should Interact
1. **Consume APIs** – refer to the OpenAPI schema generated at `/docs` (Swagger UI) for request/response models.
2. **Understand Permissions** – every request must include a valid JWT; the backend will automatically scope data by `case_id`.
3. **Vector Search** – for semantic similarity, use the `/api/v1/search` endpoint; payload requires a 1536‑dimensional embedding vector (e.g., from OpenAI or Cohere).
4. **Error Codes** – common codes:
   - `401` – authentication failed.
   - `403` – insufficient role.
   - `404` – resource not found (or not visible to the requesting case).
   - `422` – validation error (Pydantic).
5. **Version Compatibility** – the backend adheres to the versions listed in `requirements.txt`. Any change to a library version must be recorded in `docs/decisions.md`.

---

## Decision Log (Reference)
All architectural or technology decisions are recorded in `docs/decisions.md`. When something is unclear, consult that file before making assumptions.

---

*This document is maintained by the backend team. Keep it up‑to‑date as the system evolves.*
