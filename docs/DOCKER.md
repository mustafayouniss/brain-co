# BRAIN-CO — Docker Architecture & Deployment Guide

This document details the containerized architecture, service dependencies, single-command developer workflow, and data persistence guarantees for **BRAIN-CO**.

---

## 1. System Architecture

BRAIN-CO runs as a coordinated multi-container system orchestrated via **Docker Compose**:

```
+--------------------------------------------------------------------------+
|                              Docker Network                              |
|                           (brain-co_default)                             |
|                                                                          |
|  +----------------------+             +-------------------------------+  |
|  |  orgbrain-frontend   |  HTTP proxy |       orgbrain-backend        |  |
|  |   (Next.js 16.4)     | ----------> |       (FastAPI / Py3.12)      |  |
|  |     Port: 3000       |             |           Port: 8000          |  |
|  +----------------------+             +-------------------------------+  |
|             ^                                         |                  |
|             |                                         | SQL (port 5432)  |
|             | Browser                                 v                  |
|             | (ws://localhost:8000)   +-------------------------------+  |
|             +------------------------ |       orgbrain-postgres       |  |
|                                       |     (PostgreSQL 17 + pgvector)|  |
|                                       |           Port: 5433          |  |
|                                       +-------------------------------+  |
|                                                       |                  |
|  +----------------------+                             |                  |
|  |   orgbrain-adminer   | ----------------------------+                  |
|  |    (DB Management)   |                                                |
|  |     Port: 8081       |                                                |
|  +----------------------+                                                |
+--------------------------------------------------------------------------+
```

### Core Services

1. **`postgres` (`orgbrain-postgres`)**:
   - Image: `pgvector/pgvector:pg17`
   - Relational store for tenants, users, cases, CACS assignments, WebSocket tickets, and durable Mesh lifecycle events.
   - Vector extension enabled for document chunk embeddings (Ring 2).
   - Container port: `5432`, Host port: `5433` (isolated from standard local 5432).
   - Persistent storage: Named Docker volume `pgdata` (`brain-co_pgdata`).

2. **`backend` (`orgbrain-backend`)**:
   - Dockerfile: `backend/Dockerfile` (Python 3.12-slim).
   - Serves FastAPI REST API and WebSocket events (`/api/v1/ws/observations`).
   - Automatically verifies database schema on startup via `alembic upgrade head`.
   - Connected to `postgres:5432` over the internal Docker network.
   - Host port: `8000`.

3. **`frontend` (`orgbrain-frontend`)**:
   - Dockerfile: `frontend/Dockerfile` (Node.js 22-alpine).
   - Next.js 16.4 production server.
   - Route Handlers proxy server-side requests directly to `http://backend:8000/api/v1`.
   - Browser client connects directly to `http://localhost:8000` (HTTP) and `ws://localhost:8000` (WebSocket) via host port mapping.
   - Host port: `3000`.

4. **`adminer` (`orgbrain-adminer`)**:
   - Lightweight web database management console.
   - Host port: `8081`.

---

## 2. Prerequisites

- Docker Engine 24.0+
- Docker Compose v2.20+
- Minimum 4 GB available RAM

---

## 3. First-Time Setup

### Step 1: Clone and Configure Environment

```bash
# Copy example configuration with safe defaults
cp .env.example .env
```

Ensure your `.env` contains:
- A strong `SECRET_KEY` (minimum 32 characters).
- Your `GEMINI_API_KEY` (or other chosen AI provider key).
- Default database parameters (`POSTGRES_DB=orgbrain_legal`, `POSTGRES_USER=postgres`, `POSTGRES_PASSWORD=postgres`).

### Step 2: One-Command Startup

Start the entire system in detached mode:

```bash
docker compose up --build -d
```

Compose automatically:
1. Re-attaches to the persistent database volume (`brain-co_pgdata`).
2. Waits for PostgreSQL to become healthy via `pg_isready`.
3. Builds and launches the backend, running `alembic upgrade head` before serving traffic.
4. Waits for the backend health check (`/health`) to report `status: ok`.
5. Builds and starts the Next.js production frontend.
6. Launches Adminer for database inspection.

---

## 4. Daily Developer Workflow

### Checking Status
```bash
docker compose ps
```

All 4 services should report `Up` or `healthy`:
```
NAME                IMAGE                    COMMAND                  SERVICE    STATUS
orgbrain-postgres   pgvector/pgvector:pg17   "docker-entrypoint.s…"   postgres   Up (healthy)
orgbrain-backend    brain-co-backend         "sh -c 'alembic upgr…"   backend    Up (healthy)
orgbrain-frontend   brain-co-frontend        "npm run start -- --…"   frontend   Up (healthy)
orgbrain-adminer    adminer:latest           "entrypoint.sh docke…"   adminer    Up
```

### Viewing Logs
```bash
# Stream all logs
docker compose logs -f

# Stream specific service logs
docker compose logs -f backend
docker compose logs -f frontend
docker compose logs -f postgres
```

### Stopping Services Safely
```bash
# Stop containers without removing them
docker compose stop

# Or remove containers and networks while preserving all data volumes
docker compose down
```

> [!CAUTION]
> **NEVER run `docker compose down -v`**. The `-v` flag permanently destroys Docker volumes, which will erase the development database and uploaded case files.

### Restarting & Rebuilding
```bash
# Restart a service
docker compose restart backend

# Rebuild and restart after code modifications
docker compose up --build -d backend
docker compose up --build -d frontend
```

---

## 5. Database Migrations & Tests

### Executing Migrations
Database migrations are automatically applied on backend container startup. To run Alembic manually inside the container:

```bash
# Check current migration revision
docker compose exec backend alembic current

# Upgrade to latest schema
docker compose exec backend alembic upgrade head
```

### Running Backend Tests
```bash
# Run pytest inside the running container environment
docker compose exec backend pytest backend/tests tests/architecture ai/tests data-engineering/tests -q
```

---

## 6. Access Endpoints

| Service | URL | Description |
|---|---|---|
| **Frontend Web App** | [http://localhost:3000](http://localhost:3000) | Next.js SaaS Workspace, Organization Dashboard, Case Workspace |
| **Backend API Docs** | [http://localhost:8000/docs](http://localhost:8000/docs) | Interactive Swagger UI for FastAPI endpoints |
| **Backend Health** | [http://localhost:8000/health](http://localhost:8000/health) | Health check endpoint returning `{"status": "ok"}` |
| **WebSocket** | `ws://localhost:8000/api/v1/ws/observations` | Live Mesh execution observation and event stream |
| **Adminer** | [http://localhost:8081](http://localhost:8081) | Web DB GUI (Server: `postgres`, User: `postgres`, DB: `orgbrain_legal`) |

---

## 7. Data Persistence & Backups

### Volume Guarantees
- `pgdata` (`brain-co_pgdata`): Contains all PostgreSQL data clusters, including relational tables and vector indexes. Data survives container destruction, system reboots, and image updates.
- `raw_storage` (`brain-co_raw_storage`): Contains uploaded PDFs, ingested document artifacts, and extracted text.

### Database Backup
```bash
docker compose exec postgres pg_dump -U postgres -d orgbrain_legal > backup_$(date +%Y%m%d).sql
```

### Database Restore
```bash
cat backup_YYYYMMDD.sql | docker compose exec -T postgres psql -U postgres -d orgbrain_legal
```
