# Documentation Accuracy Verification Log

This document records the empirical verification audit performed on `progress.md`, `environment.md`, `architecture.md`, `how-it-works.md`, and the latest journal entry (`docs/journal/2026-10-06.md`).

| Claim | Doc | Command or file used | Actual output | Status |
| :--- | :--- | :--- | :--- | :--- |
| Python 3.12 (`cpython-3.12.13-windows-x86_64-none`) installed | `progress.md` | `backend\.venv\Scripts\python.exe --version` | `Python 3.12.13` | VERIFIED |
| Python 3.12 virtual environment created at `backend/.venv` | `progress.md` | `Test-Path backend/.venv` | `True` | VERIFIED |
| Target packages installed (fastapi, uvicorn, sqlalchemy, alembic, psycopg, pgvector, pydantic, pyjwt, pytest, httpx) | `progress.md` | `uv pip list --python backend/.venv/Scripts/python.exe` | `fastapi 0.142.2`, `uvicorn 0.54.0`, `sqlalchemy 2.0.54`, `alembic 1.20.0`, `psycopg 3.3.6`, `pgvector 0.5.0`, `pydantic 2.13.5`, `pyjwt 2.15.1`, `pytest 9.1.1`, `httpx 0.28.1` | VERIFIED |
| `backend/requirements.txt` generated from actual installed packages | `progress.md` | `view_file` `backend/requirements.txt` | File exists with pinned packages (e.g. `sqlalchemy==2.0.54`, `alembic==1.20.0`, `fastapi==0.142.2`) | VERIFIED |
| `docker-compose.yml` uses image `pgvector/pgvector:pg17` | `progress.md` | `view_file` `docker-compose.yml` | `image: pgvector/pgvector:pg17` | VERIFIED |
| `.gitignore`, `docker-compose.yml`, `.env.example`, `.env` created | `progress.md` | `Test-Path` on all files | `True` for all files | VERIFIED |
| Folder hierarchy (`backend/app/{api,services,models,schemas,core,db}`, `tests/`, `docs/{rings,adr}`) scaffolded | `progress.md` | `Test-Path` on all 16 directories | `True` for all directories | VERIFIED |
| First migration `6dd2ff08b0bb_enable_pgvector_extension.py` created | `progress.md` | `view_file` `backend/migrations/versions/6dd2ff08b0bb_enable_pgvector_extension.py` | Revision `6dd2ff08b0bb`, `op.execute("CREATE EXTENSION IF NOT EXISTS vector")` | VERIFIED |
| Postgres container running & healthy | `progress.md` | `docker compose ps` | `orgbrain-postgres pgvector/pgvector:pg17 Up (healthy) 0.0.0.0:5432->5432/tcp` | VERIFIED |
| Migration applied and `vector` extension v0.8.7 active in Postgres DB | `progress.md` | `docker compose exec postgres psql -U postgres -d orgbrain_legal -c "SELECT extname, extversion FROM pg_extension WHERE extname = 'vector';"` | `extname: vector \| extversion: 0.8.7 (1 row)` | VERIFIED |
| Host OS: Windows 10 Pro / Build 10.0.19045.2965 | `environment.md` | `[System.Environment]::OSVersion.Version; (Get-CimInstance Win32_OperatingSystem).Caption; wsl --version` | Major 10, Minor 0, Build 19045, Microsoft Windows 10 Pro, Windows version: 10.0.19045.2965 | VERIFIED |
| Winget version `v1.29.280` | `environment.md` | `winget --version` | `v1.29.280` | VERIFIED |
| Git version `2.53.0.windows.3` | `environment.md` | `git --version` | `git version 2.53.0.windows.3` | VERIFIED |
| uv version `0.11.7 (9d177269e 2026-04-15 x86_64-pc-windows-msvc)` | `environment.md` | `uv --version` | `uv 0.11.7 (9d177269e 2026-04-15 x86_64-pc-windows-msvc)` | VERIFIED |
| CPython runtime `3.12.13` | `environment.md` | `backend\.venv\Scripts\python.exe --version` | `Python 3.12.13` | VERIFIED |
| Docker Engine version `29.8.2, build 7fc2dff` | `environment.md` | `docker --version` | `Docker version 29.8.2, build 7fc2dff` | VERIFIED |
| Docker Desktop version `4.94.0` | `environment.md` | `winget list --name "Docker Desktop"` | `Docker Desktop Docker.DockerDesktop 4.94.0 winget` | VERIFIED |
| WSL Subsystem `3.0.1.0`, Kernel `6.18.40.1-1` | `environment.md` | `wsl --version` | `WSL version: 3.0.1.0`, `Kernel version: 6.18.40.1-1` | VERIFIED |
| Database Image `pgvector/pgvector:pg17` | `environment.md` | `view_file` `docker-compose.yml` | `image: pgvector/pgvector:pg17` | VERIFIED |
| PostgreSQL Engine inside container version `17.11 (Debian 17.11-1.pgdg12+2)` | `environment.md` | `docker compose exec postgres psql -U postgres -d orgbrain_legal -c "SELECT version();"` | `PostgreSQL 17.11 (Debian 17.11-1.pgdg12+2) on x86_64-pc-linux-gnu...` | VERIFIED |
| Vector Extension `0.8.7` inside Postgres | `environment.md` | `docker compose exec postgres psql -U postgres -d orgbrain_legal -c "SELECT extname, extversion FROM pg_extension WHERE extname = 'vector';"` | `extname: vector \| extversion: 0.8.7 (1 row)` | VERIFIED |
| ORM / Migration versions (`sqlalchemy==2.0.54`, `alembic==1.20.0`) | `environment.md` | `uv pip list --python backend/.venv/Scripts/python.exe` | `sqlalchemy 2.0.54`, `alembic 1.20.0` | VERIFIED |
| Database Driver (`psycopg==3.3.6`, `psycopg-binary==3.3.6`) | `environment.md` | `uv pip list --python backend/.venv/Scripts/python.exe` | `psycopg 3.3.6`, `psycopg-binary 3.3.6` | VERIFIED |
| Web Framework (`fastapi==0.142.2`, `uvicorn==0.54.0`) | `environment.md` | `uv pip list --python backend/.venv/Scripts/python.exe` | `fastapi 0.142.2`, `uvicorn 0.54.0` | VERIFIED |
| Validation / Config (`pydantic==2.13.5`, `pydantic-settings==2.15.0`) | `environment.md` | `uv pip list --python backend/.venv/Scripts/python.exe` | `pydantic 2.13.5`, `pydantic-settings 2.15.0` | VERIFIED |
| Testing (`pytest==9.1.1`, `httpx==0.28.1`) | `environment.md` | `uv pip list --python backend/.venv/Scripts/python.exe` | `pytest 9.1.1`, `httpx 0.28.1` | VERIFIED |
| Default `.env` values (`POSTGRES_USER=postgres`, `POSTGRES_PASSWORD=postgres`, `POSTGRES_DB=orgbrain_legal`, `POSTGRES_HOST=localhost`, `POSTGRES_PORT=5432`, `DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/orgbrain_legal`) | `environment.md` | `view_file` `.env` | File matches all default values | VERIFIED |
| Rebuild Step 2 command `uv pip install -r backend/requirements.txt --python backend/.venv/Scripts/python.exe` | `environment.md` | `uv pip install -r backend/requirements.txt --python backend/.venv/Scripts/python.exe` | `Using Python 3.12.13 environment at: backend\.venv; Checked 39 packages in 3.53s` | FIXED |
| Folder Structure listing 17 paths | `architecture.md` | `Test-Path` on all 17 listed directories | `True` for all 17 directories | VERIFIED |
| Root-Path Resolution: `Path(__file__).resolve().parent.parent.parent.parent / ".env"` | `architecture.md` | `view_file` `backend/app/core/config.py` | `PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent`, `ENV_FILE_PATH = PROJECT_ROOT / ".env"` | VERIFIED |
| Driver format `postgresql+psycopg://<user>:<password>@<host>:<port>/<database>` | `architecture.md` | `view_file` `backend/app/core/config.py` | `postgresql+psycopg://postgres:postgres@localhost:5432/orgbrain_legal` | VERIFIED |
| Docker Image `pgvector/pgvector:pg17` | `architecture.md` | `view_file` `docker-compose.yml` | `image: pgvector/pgvector:pg17` | VERIFIED |
| Database Engine `PostgreSQL 17.11 (Debian 17.11-1.pgdg12+2)` | `architecture.md` | `docker compose exec postgres psql -U postgres -d orgbrain_legal -c "SELECT version();"` | `PostgreSQL 17.11 (Debian 17.11-1.pgdg12+2) on x86_64-pc-linux-gnu...` | VERIFIED |
| Postgres Extension `vector` version `0.8.7` | `architecture.md` | `docker compose exec postgres psql -U postgres -d orgbrain_legal -c "SELECT extname, extversion FROM pg_extension WHERE extname = 'vector';"` | `extname: vector \| extversion: 0.8.7 (1 row)` | VERIFIED |
| Package versions (`SQLAlchemy 2.0.54`, `Psycopg 3.3.6`, `Alembic 1.20.0`) | `architecture.md` | `uv pip list --python backend/.venv/Scripts/python.exe` | `sqlalchemy 2.0.54`, `psycopg 3.3.6`, `alembic 1.20.0` | VERIFIED |
| First migration `6dd2ff08b0bb_enable_pgvector_extension.py` contains `CREATE EXTENSION IF NOT EXISTS vector` | `how-it-works.md` | `view_file` `backend/migrations/versions/6dd2ff08b0bb_enable_pgvector_extension.py` | `op.execute("CREATE EXTENSION IF NOT EXISTS vector")` | VERIFIED |
| `docker compose up -d` starts container in detached mode | `how-it-works.md` | `docker compose up -d` | `orgbrain-postgres pgvector/pgvector:pg17 Up (healthy) 0.0.0.0:5432->5432/tcp` | VERIFIED |
| `docker compose ps` shows status `Up` and `(healthy)` | `how-it-works.md` | `docker compose ps` | `orgbrain-postgres pgvector/pgvector:pg17 Up (healthy)` | VERIFIED |
| `backend\.venv\Scripts\activate` script exists | `how-it-works.md` | `Test-Path backend\.venv\Scripts\activate.ps1` | `True` | VERIFIED |
| `backend\.venv\Scripts\alembic.exe upgrade head` runs migration | `how-it-works.md` | `..\backend\.venv\Scripts\alembic.exe upgrade head` (ran twice from `backend/`) | Both runs output: `INFO [alembic.runtime.migration] Context impl PostgresqlImpl.` / `INFO [alembic.runtime.migration] Will assume transactional DDL.` | VERIFIED |
| `backend\.venv\Scripts\pytest` runner script exists | `how-it-works.md` | `Test-Path backend\.venv\Scripts\pytest.exe` | `True` | VERIFIED |
| `docker compose exec postgres psql -U postgres -d orgbrain_legal` connects to psql | `how-it-works.md` | `docker compose exec postgres psql -U postgres -d orgbrain_legal -c "SELECT version();"` | `PostgreSQL 17.11 (Debian 17.11-1.pgdg12+2)...` | VERIFIED |
| Journal: Python 3.12, virtualenv at `backend/.venv` | `docs/journal/2026-10-06.md` | `backend\.venv\Scripts\python.exe --version` | `Python 3.12.13` | VERIFIED |
| Journal: Git `2.53.0.windows.3`, Winget `1.29.280`, WSL `3.0.1.0`, Kernel `6.18.40.1-1` | `docs/journal/2026-10-06.md` | `git --version`, `winget --version`, `wsl --version` | `git version 2.53.0.windows.3`, `v1.29.280`, `WSL version: 3.0.1.0`, `Kernel version: 6.18.40.1-1` | VERIFIED |
| Journal: Executed `uv pip install -r backend/requirements.txt --python backend/.venv/Scripts/python.exe` | `docs/journal/2026-10-06.md` | `uv pip install -r backend/requirements.txt --python backend/.venv/Scripts/python.exe` | `Using Python 3.12.13 environment at: backend\.venv; Checked 39 packages in 3.53s` | FIXED |
| Journal: Pinned `sqlalchemy==2.0.54` in `backend/requirements.txt` | `docs/journal/2026-10-06.md` | `view_file` `backend/requirements.txt` | `sqlalchemy==2.0.54` | VERIFIED |
| Journal: `docker-compose.yml` `postgres` service specifications | `docs/journal/2026-10-06.md` | `view_file` `docker-compose.yml` | `image: pgvector/pgvector:pg17`, `5432:5432`, `POSTGRES_DB=orgbrain_legal` | VERIFIED |
| Journal: `.env` file credentials | `docs/journal/2026-10-06.md` | `view_file` `.env` | `POSTGRES_USER=postgres`, `POSTGRES_PASSWORD=postgres`, `POSTGRES_DB=orgbrain_legal`, `DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/orgbrain_legal` | VERIFIED |
| Journal: Migration script `6dd2ff08b0bb` created with `CREATE EXTENSION IF NOT EXISTS vector` | `docs/journal/2026-10-06.md` | `view_file` `backend/migrations/versions/6dd2ff08b0bb_enable_pgvector_extension.py` | Revision `6dd2ff08b0bb`, `op.execute("CREATE EXTENSION IF NOT EXISTS vector")` | VERIFIED |
| Journal: `pgvector` v0.8.7 extension active on PostgreSQL 17.11 inside container | `docs/journal/2026-10-06.md` | `docker compose exec postgres psql ...` | `extname: vector \| extversion: 0.8.7 (1 row)` | VERIFIED |
