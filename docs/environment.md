# Environment Setup Guide (Windows)

This document provides verified, step‑by‑step instructions for a newcomer to get a running backend from a fresh clone on Windows. Anything not directly observed is marked **UNVERIFIED**.

## Verified Tools and Versions
| Component | Tool / Package | Verified Version |
|---|---|---|
| OS | Microsoft Windows | Build 10.0.19045.2965 (22H2) |
| Package Manager | winget | v1.29.280 |
| VCS | Git for Windows | 2.53.0.windows.3 |
| Python Tooling | uv | 0.11.7 |
| Python Runtime | CPython 3.12 | 3.12.13 |
| Docker Engine | Docker | 29.8.2 |
| Docker Desktop | Docker Desktop | 4.94.0 |
| WSL2 | WSL 3.0.1.0 | Kernel 6.18.40.1‑1 |
| PostgreSQL image | pgvector/pgvector:pg17 | |
| PostgreSQL | 17.11 | |
| pgvector extension | 0.8.7 | |
| ORM / Migration | SQLAlchemy 2.0.54 / Alembic 1.20.0 | |
| DB driver | psycopg 3.3.6 | |
| Web framework | FastAPI 0.142.2 / Uvicorn 0.54.0 | |
| Validation | Pydantic 2.13.5 / Pydantic‑Settings 2.15.0 | |
| Testing | pytest 9.1.1 / httpx 0.28.1 | |

## Step‑by‑Step Rebuild Instructions (single path)

1. **Install `uv` and Python 3.12**
   ```powershell
   winget install --id=astral-sh.uv -e
   uv python install 3.12
   ```

2. **Create a virtual environment and install dependencies** (run from the repository root):
   ```powershell
   uv venv backend/.venv --python 3.12
   uv pip install -r backend/requirements.txt --python backend/.venv/Scripts/python.exe
   ```

3. **Verify Python version**
   ```powershell
   backend\.venv\Scripts\python.exe --version
   ```

4. **Configure environment variables**
   ```powershell
   Copy-Item .env.example .env
   ```
   Then **generate a secret key** *inside a Python script* and replace the placeholder line in `.env` (do not print the key):
   ```python
   import secrets, pathlib
   secret = secrets.token_urlsafe(32)
   env_path = pathlib.Path('.env')
   lines = env_path.read_text().splitlines()
   new_lines = [f'SECRET_KEY={secret}' if line.startswith('SECRET_KEY=') else line for line in lines]
   env_path.write_text('\n'.join(new_lines), encoding='utf-8')
   ```

5. **Start the PostgreSQL container** (container already running in the main project; reuse it)
   ```powershell
   docker compose up -d   # SKIPPED (container already running)
   ```

6. **Apply database migrations**
   ```powershell
   backend\.venv\Scripts\alembic.exe upgrade head
   ```

7. **Run the test suite**
   ```powershell
   backend\.venv\Scripts\pytest
   ```

8. **Start the application** (do not run here; just note)
   ```powershell
   backend\.venv\Scripts\uvicorn app.main:app --reload
   ```
   Then open `http://localhost:8000/docs` in a browser.

9. **Create the first admin user** (interactive, will prompt for passwords)
   ```powershell
   python -m app.scripts.create_admin
   ```

## Common Errors
- **Missing or short `SECRET_KEY`** – the app raises a `ValidationError`. Regenerate a key of at least 32 characters.
- **Database not running** – `docker compose ps` shows the container stopped; start it with `docker compose up -d`.
- **Alembic migration fails** – ensure the container is healthy and the `DATABASE_URL` in `.env` points to the running Postgres.
