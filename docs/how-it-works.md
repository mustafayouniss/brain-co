# How It Works: A Beginner's Guide to Our Backend

This guide explains how all the pieces of our backend setup fit together. If you are brand new to backend development, you do not need to memorize complex jargon. Think of this document as a map explaining what each piece is, why we need it, and how to work with it daily.

---

## 1. The Building Blocks (Plain Explanations & Analogies)

### 1. `venv` (Virtual Environment)
- **Plain English**: A virtual environment is an isolated, private folder on your computer that holds a specific version of Python and only the specific packages that this project needs.
- **The Analogy**: Imagine you are a painter working on two different jobs: one watercolor and one oil painting. Instead of dumping all your paints and brushes into one messy bucket where colors bleed together, you keep a dedicated toolbox for each job. The `backend/.venv` folder is our dedicated toolbox for OrgBrain.
- **Why we need it**: It prevents Python packages from conflicting with other Python projects or system tools on your machine.

### 2. `Docker`
- **Plain English**: Docker is a program that lets us package software and all its dependencies into a self-contained unit called a "container" that runs consistently on any machine.
- **The Analogy**: Think of a standard shipping container. Whether it travels on a cargo ship, a train, or a flatbed truck across different countries, the container itself has the exact same dimensions, locks, and climate inside. Docker makes sure our database runs identically on your Windows laptop, a teammate's Mac, or a cloud server in production.
- **Why we need it**: You do not have to install PostgreSQL directly onto Windows or worry about operating system differences. Docker manages it cleanly inside Linux.

### 3. `Postgres` (PostgreSQL)
- **Plain English**: PostgreSQL is our relational database engine. It is responsible for storing, organizing, protecting, and querying our structured data.
- **The Analogy**: Picture a massive, fireproof, automated bank vault filled with organized safety deposit boxes. Whenever you need to store client information or retrieve a specific legal case, Postgres handles the filing and retrieval safely without losing anything.
- **Why we need it**: It provides reliable, ACID-compliant persistence for our data tables and business records.

### 4. `pgvector`
- **Plain English**: `pgvector` is an official extension (plugin) for PostgreSQL that adds the ability to store and search mathematical representations of text called "vector embeddings".
- **The Analogy**: Standard Postgres is like a library index that searches by exact title or author name (keyword search). `pgvector` is like a wise librarian who understands the underlying *meaning* of books. If you ask for "articles about contract disputes", the librarian can find books about "breach of agreement" or "settlement arbitration" because they are conceptually close, even if they don't use the exact same words.
- **Why we need it**: OrgBrain needs semantic search and AI capabilities to understand legal documents by their contextual meaning.

### 5. `Alembic`
- **Plain English**: Alembic is a database migration management tool designed for Python and SQLAlchemy.
- **The Analogy**: Alembic is like "Git version control" for the structure of your database. If you build a house, you don't just randomly knock down walls without blueprints. Alembic is the blueprint ledger that tracks every single architectural modification made over time.
- **Why we need it**: Instead of manually editing database tables with ad-hoc SQL commands, Alembic ensures that any database changes are versioned, repeatable, testable, and can be applied or undone reliably across all environments.

### 6. `Migration`
- **Plain English**: A migration is an individual Python script containing instructions for a single change to the database structure (such as adding a table, adding a column, or enabling an extension).
- **The Analogy**: If Alembic is the blueprint binder, a migration is a single numbered page in that binder (e.g., "Step 1: Install electrical wiring in Room 101").
- **Why we need it**: Our first migration (`6dd2ff08b0bb_enable_pgvector_extension.py`) tells Postgres: "When upgrading, execute `CREATE EXTENSION IF NOT EXISTS vector`." Anyone pulling this project runs the migration and gets the exact same database structure.

### 7. `.env` (Environment File)
- **Plain English**: A local configuration file containing configuration variables, network ports, and secret credentials.
- **The Analogy**: Your house key or password notebook. You keep it in your pocket and never give it to strangers. `.env.example` is like a fake blank dummy key that shows where the notches go, while `.env` is the actual key that unlocks your local database.
- **Why we need it**: Secrets and local machine settings must never be committed to Git. `.env` stays on your computer (ignored by `.gitignore`), while code reads from it securely.

### 8. `get_db` (Database Session Dependency)
- **Plain English**: A helper function that hands an endpoint a database connection when a request arrives and automatically closes it when the request finishes.
- **The Analogy**: Like a library pass that lets you into the reading room for one visit. When you leave, the pass is turned in and the door locks behind you so connections aren't left dangling open.
- **Why we need it**: It prevents database connection leaks and makes it trivial to swap in a test database during automated testing.

### 9. Standardized Error Envelope
- **Plain English**: A single, consistent JSON structure used for every error that ever comes out of the server (`{"error": {"code": "...", "message": "..."}}`).
- **The Analogy**: A standard return receipt from a store. Regardless of whether you return shoes, groceries, or electronics, the receipt always has the exact same layout: store name, barcode, reason, and timestamp.
- **Why we need it**: Frontend apps and mobile apps don't have to guess how errors look. They can check `error.code` consistently across all endpoints.

### 10. Password Hashing (Argon2id)
- **Plain English**: A one-way mathematical transformation that scrambles a plain text password into an unreadable fingerprint, with unique random "salt" so identical passwords never look alike.
- **The Analogy**: Running fruit through a blender. You can turn fresh strawberries into a smoothie, but it is physically impossible to turn the smoothie back into intact strawberries.
- **Why we need it**: If an attacker ever stole the database, they would only get the scrambled smoothies, never the real passwords.

### 11. JWT Access Tokens (JSON Web Tokens)
- **Plain English**: A digitally signed, tamper-proof badge given to a user after they log in. The badge contains their user ID (`sub`) and expiration timestamp (`exp`).
- **The Analogy**: An amusement park wristband stamped with an expiration time. Every ride operator can inspect the stamp to confirm it hasn't expired without having to look up the customer in the main ticket office every time.
- **Why we need it**: It enables fast, secure, stateless API authentication without repeatedly querying the database on every single request.

---

## 2. How User Accounts & Security Work

Our application is a private organizational system for legal operations. Because of this, **there is no public sign-up form on the website**. Nobody can just visit the site and create an account. Instead, accounts are created through a secure, two-step chain of trust:

### Step 1: How Karim Creates the First Admin
When the system is first installed, there are no users in the database at all. To bootstrap the system:
1. Karim opens a terminal inside the backend environment and runs:
   ```powershell
   python -m app.scripts.create_admin --email karim@example.com --full-name "Karim Admin"
   ```
2. The script prompts Karim for a password twice on the command line:
   - The password characters do **not echo to the screen** while typing (using `getpass`).
   - The password is **never written inside `.env`**, never passed as a command argument, and never printed to logs.
3. The script hashes the password with Argon2id and saves the administrator account directly to PostgreSQL.

### Step 2: How Admins Create Employee Accounts
Once the initial administrator account exists, all other users are invited by admins:
1. The administrator logs into the system using `POST /api/v1/auth/login` to receive an access token.
2. The administrator calls the user creation endpoint:
   ```http
   POST /api/v1/users
   Authorization: Bearer <admin_token>
   ```
   with the employee's name, email, role (`"employee"`), and temporary password (at least 12 characters).
3. The server checks the database to verify the caller really is an administrator. If someone with an employee account tries to call this endpoint, they immediately get a `403 Forbidden` error.

### Step 3: How Users Log In and Protect Privacy
- When a user logs in (`POST /api/v1/auth/login`), the system verifies their password. If valid, they receive a JWT access token valid for 60 minutes.
- **User Enumeration Defense**: If a hacker tries guessing emails by sending random usernames, the server returns the exact same generic `401 Unauthorized` message whether the email exists with the wrong password or doesn't exist at all. This prevents attackers from figuring out who works at the organization.

---

## 3. Commands You Will Use Every Day

Here are the essential commands you will run regularly when working on this backend:

### 1. Starting the Database
```powershell
docker compose up -d
```
- **What it does**: Starts the PostgreSQL database container in the background (`-d` stands for "detached").
- **When to use**: Run this first whenever you sit down to start working.

### 2. Checking Database Status
```powershell
docker compose ps
```
- **What it does**: Lists running containers and shows if PostgreSQL is healthy (`Up` and `(healthy)`).
- **When to use**: Whenever you want to confirm the database is up and responding.

### 3. Activating the Virtual Environment
```powershell
backend\.venv\Scripts\activate
```
- **What it does**: Switches your current PowerShell terminal to use our isolated Python 3.12 environment.
- **When to use**: Run this before running Python commands, pytest, or Alembic in your terminal.

### 4. Running Database Migrations
```powershell
backend\.venv\Scripts\alembic.exe upgrade head
```
- **What it does**: Checks the database and applies any new migration scripts that haven't been run yet, bringing the database up to date.
- **When to use**: Whenever you create a new migration or pull new code from teammates.

### 5. Running Automated Tests
```powershell
backend\.venv\Scripts\pytest
```
- **What it does**: Discovers and runs all automated tests in `backend/tests/` and prints whether they passed or failed.
- **When to use**: Run this before and after writing any code to ensure everything works and nothing is broken.

### 6. Connecting to PostgreSQL Interactively
```powershell
docker compose exec postgres psql -U postgres -d orgbrain_legal
```
- **What it does**: Opens an interactive PostgreSQL terminal (`psql`) inside the running container so you can inspect tables or run SQL queries directly. Type `\q` to exit.
- **When to use**: When you need to manually inspect tables, check extensions, or troubleshoot database data.

### 7. Stopping the Database
```powershell
docker compose down
```
- **What it does**: Gracefully stops and shuts down the PostgreSQL container while preserving your data on the Docker volume.
- **When to use**: When you are done working for the day or want to free up system resources.

### 8. Running the API Server (Local Development)
```powershell
cd backend
..\backend\.venv\Scripts\uvicorn.exe app.main:app --port 8000
```
- **What it does**: Starts the local FastAPI development server on port 8000.
- **When to use**: When testing API endpoints locally. You can visit `http://127.0.0.1:8000/health` or `http://127.0.0.1:8000/api/v1/health/db` in your browser or client tool.
