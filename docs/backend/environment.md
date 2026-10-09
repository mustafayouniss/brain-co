# Environment Setup Guide (Windows)

This document provides verified, step-by-step instructions to rebuild this exact development environment from scratch on a clean Windows machine. Every tool, version, configuration setting, and resolution step listed here is based on what was verified in this setup. Anything not directly observed is marked UNVERIFIED.

---

## 1. Verified Tools and Exact Versions

| Component | Tool / Package | Verified Version | Installation / Verification Command |
| :--- | :--- | :--- | :--- |
| **Operating System** | Microsoft Windows | Windows 10 Home/Pro/Enterprise (Build `10.0.19045.2965`, 22H2 64-bit) | `[System.Environment]::OSVersion.Version` / `wsl --status` |
| **Package Manager** | Windows Package Manager (winget) | `v1.29.280` | `winget --version` |
| **VCS** | Git for Windows | `2.53.0.windows.3` | `git --version` |
| **Python Tooling** | uv (Astral) | `0.11.7 (9d177269e 2026-04-15 x86_64-pc-windows-msvc)` | `uv --version` |
| **Python Runtime** | CPython (managed via uv) | `3.12.13` (`cpython-3.12.13-windows-x86_64-none`) | `backend\.venv\Scripts\python.exe --version` |
| **Container Engine** | Docker Engine | `29.8.2`, build `7fc2dff` | `docker --version` |
| **Container Desktop**| Docker Desktop for Windows | `4.94.0` (winget ID: `Docker.DockerDesktop`) | `winget list --name "Docker Desktop"` |
| **WSL Subsystem** | Windows Subsystem for Linux (WSL2) | WSL `3.0.1.0`, Kernel `6.18.40.1-1`, Default Version `2` | `wsl --version` |
| **Database Container**| Docker Image | `pgvector/pgvector:pg17` | `docker compose images` |
| **Database Engine** | PostgreSQL (inside container) | `17.11 (Debian 17.11-1.pgdg12+2) on x86_64-pc-linux-gnu` | `SELECT version();` |
| **Vector Extension** | pgvector (inside Postgres) | `0.8.7` | `SELECT extname, extversion FROM pg_extension WHERE extname = 'vector';` |
| **ORM / Migration** | SQLAlchemy / Alembic | `sqlalchemy==2.0.54`, `alembic==1.20.0` | `backend\.venv\Scripts\pip.exe list` |
| **Database Driver** | psycopg (binary v3) | `psycopg==3.3.6`, `psycopg-binary==3.3.6` | `backend\.venv\Scripts\pip.exe list` |
| **Web Framework** | FastAPI / Uvicorn | `fastapi==0.142.2`, `uvicorn==0.54.0` | `backend\.venv\Scripts\pip.exe list` |
| **Validation / Conf** | Pydantic / Pydantic Settings | `pydantic==2.13.5`, `pydantic-settings==2.15.0` | `backend\.venv\Scripts\pip.exe list` |
| **Testing** | pytest / HTTPX | `pytest==9.1.1`, `httpx==0.28.1` | `backend\.venv\Scripts\pip.exe list` |

---

## 2. Docker Desktop Settings

Docker Desktop must be configured with the following parameters:
- **Engine**: WSL 2 based engine.
  - Setting: `Settings > General > Use the WSL 2 based engine` must be checked (`true`).
- **Container Architecture**: Linux containers (default).
  - Must **not** be switched to Windows containers.
- **WSL Integration**:
  - Setting: `Settings > Resources > WSL integration > Enable integration with my default WSL distro` enabled.
  - Verified default WSL distribution: `docker-desktop`.

---

## 3. Issues Encountered & Verified Fixes

During the initial environment bootstrap, Docker Desktop and WSL2 encountered three specific blockers. Here is how each was diagnosed and resolved:

### Issue 1: Hardware Virtualization Disabled in Firmware (BIOS/UEFI)
- **Symptom**: Docker Desktop fails to initialize or WSL reports that hardware assisted virtualization is disabled.
- **Cause**: CPU Virtualization Extensions (Intel VT-x or AMD SVM) were disabled at motherboard firmware level.
- **Resolution**:
  1. Restart PC and enter BIOS/UEFI setup (typically by pressing `F2`, `F12`, or `Del` during boot).
  2. Navigate to CPU Configuration / Advanced Processor Settings.
  3. Locate **Intel Virtualization Technology (VT-x)** or **AMD SVM (Secure Virtual Machine)**.
  4. Change status from `Disabled` to `Enabled`.
  5. Save configuration and exit (usually `F10`), then boot back into Windows.

### Issue 2: Windows Feature "VirtualMachinePlatform" Not Enabled
- **Symptom**: WSL2 fails to start background virtual machine instances with an error indicating missing virtualization platform prerequisites.
- **Cause**: Windows optional component `VirtualMachinePlatform` is turned off by default on fresh installations.
- **Resolution**:
  1. Open PowerShell as Administrator.
  2. Run the following DISM command:
     ```powershell
     dism.exe /online /enable-feature /featurename:VirtualMachinePlatform /all /norestart
     ```
  3. Reboot the computer if prompted to finalize installation.

### Issue 3: WSL2 Kernel Outdated / WSL Version Mismatch
- **Symptom**: Docker Desktop reports an obsolete WSL kernel or requires a kernel update package.
- **Cause**: Factory Windows installation contains WSL stub without current kernel binaries.
- **Resolution**:
  1. Open PowerShell or Command Prompt.
  2. Update the WSL subsystem and kernel to latest version:
     ```powershell
     wsl --update
     ```
  3. Set WSL default version to 2:
     ```powershell
     wsl --set-default-version 2
     ```
  4. Verify installed versions:
     ```powershell
     wsl --version
     ```
     Verified output: WSL version `3.0.1.0`, Kernel version `6.18.40.1-1`.

---

## 4. Step-by-Step Rebuild Instructions

### Step 1: Install uv and Python 3.12
1. Install `uv` via winget (or official installer):
   ```powershell
   winget install --id=astral-sh.uv -e
   ```
2. Install Python 3.12 using uv:
   ```powershell
   uv python install 3.12
   ```

### Step 2: Create Virtual Environment and Install Dependencies
From the repository root (`OrgBrain/`):
```powershell
uv venv backend/.venv --python 3.12
uv pip install -r backend/requirements.txt --python backend/.venv/Scripts/python.exe
```
> **Note**: This venv was created by `uv` and has no `pip`; use `uv pip`, never `python -m pip`.

Verify the active Python version:
```powershell
backend\.venv\Scripts\python.exe --version
# Expected: Python 3.12.13
```

### Step 3: Configure Environment Variables
Copy `.env.example` to `.env`:
```powershell
Copy-Item .env.example .env
```
Default verified `.env` values for local development:
```env
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=orgbrain_legal
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_TEST_DB=orgbrain_legal_test
DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/orgbrain_legal
SECRET_KEY=<your_generated_secret_key>
ACCESS_TOKEN_EXPIRE_MINUTES=60
```

#### Generate a Secure SECRET_KEY
The application **strictly refuses to start without a valid `SECRET_KEY`** (raises a `ValidationError` if the variable is missing, shorter than 32 characters, or uses the `"change-this*"` placeholder).

Each developer must generate their own private random key and set it in the root `.env`:
```powershell
backend\.venv\Scripts\python.exe -c "import secrets; print(secrets.token_urlsafe(32))"
```
Copy the generated string and set `SECRET_KEY=<output>` in your root `.env`.

> [!WARNING]
> **Never** paste your `SECRET_KEY` into chats, terminal logs, or journal entries, and **never** commit `.env` to Git.

### Step 4: Start Postgres Container via Docker Compose
Start the service in detached mode:
```powershell
docker compose up -d
```

### Step 5: Verify Postgres Container and Extension
1. Verify container state and healthcheck:
   ```powershell
   docker compose ps
   ```
   Verified output: Container `orgbrain-postgres` status is `Up` and `(healthy)`.

2. Apply the Alembic migration to enable `pgvector`:
   ```powershell
   backend\.venv\Scripts\alembic.exe upgrade head
   ```

3. Query PostgreSQL directly to confirm `vector` extension exists:
   ```powershell
   docker compose exec postgres psql -U postgres -d orgbrain_legal -c "SELECT extname, extversion FROM pg_extension WHERE extname = 'vector';"
   ```
   Verified output:
   ```text
    extname | extversion 
   ---------+------------
    vector  | 0.8.7
   (1 row)
   ```
