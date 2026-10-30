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

### 12. Provider-Agnostic AI Engine & Registry
- **Plain English**: A unified system that talks to Large Language Models (AI) without caring which company made the AI.
- **The Analogy**: A universal power adapter. Whether you plug in your phone in Egypt, China, or the US, the adapter fits the local wall outlet and provides clean electricity to your phone. The Brain's business logic is your phone; OpenAI, DeepSeek, Kimi, OpenRouter, and Ollama are different international wall outlets. The `ProviderRegistry` and `LLMService` adapt to each without requiring you to buy a new phone.
- **Why we need it**: The organization can switch from OpenAI to DeepSeek (or any other provider) with a single environment variable change, without rewriting a single line of legal reasoning or case processing code.

### 13. Source Ingestion Pipeline & Source Memory
- **Plain English**: A secure intake pipeline that accepts raw files, verifies their format and size, calculates a unique cryptographic fingerprint (SHA-256), saves the raw document safely into storage, and logs an immutable metadata record into PostgreSQL.
- **The Analogy**: Like the evidence intake desk at a court archive. When a document arrives, the registrar doesn't immediately interpret it or declare it as fact. Instead, they inspect the paper, stamp it with a tamper-proof barcode, store the physical document securely in the archives, and register the receipt into the official ledger.
- **Why we need it**: All future reasoning, parsing, and legal knowledge discovery requires an unbroken chain of custody back to the exact physical source document.

### 14. Neo4j (Graph Database)
- **Plain English**: A database specialized in storing and querying intricate networks of connections (nodes and relationships), such as legal citation graphs, cross-case entity links, and multi-hop relationships.
- **The Analogy**: Like a detective's case corkboard with photos connected by strings of yarn. While Postgres is perfect for neat tables and ledgers, Neo4j is built to immediately answer questions like "how is Concept A linked to Law B through five intermediate judicial rulings?"
- **Why we need it**: Prepared in local infrastructure for higher rings to power graph-based knowledge traversal and legal reasoning.

---

## 2. Commands You Will Use Every Day

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

---

## 3. Ring 1 General Brain Mesh: How It Works

### The Analogy: A Team of Specialists Without a Dictator Boss
Imagine a legal operations room with 6 specialists sitting at a round table:
1. **Perception Specialist**: Takes in raw letters, emails, or system pings, reads them, and translates them into organized summary folders.
2. **Observation Specialist**: Notes when events happen, files them neatly, detects if an event was already logged, and decides whether it needs follow-up work.
3. **Context Specialist**: Checks which legal case and organization an action belongs to. If someone brings a document without a case number, they stop and ask for clarification rather than guessing.
4. **Memory Specialist**: Keeps the confidential file cabinets. When someone wants to save or read a record, they verify that the person is asking for files inside the correct case cabinet.
5. **Retrieval Specialist**: Answers questions by searching through the memory cabinets, strictly making sure they never pull a file from Case A when answering a question about Case B.
6. **Planning Specialist**: Breaks down big objectives into a sequenced checklist of steps using the tools that the other specialists provide, and if a step fails, boundedly revises the checklist without looping forever.

### The Mesh Router (The Courier)
Instead of having a single monolithic "boss" that controls every micro-action, all specialists communicate through a lightweight courier called the **Mesh Router**. Every message travels in a secure envelope (`MeshRequest` / `MeshResponse`) that carries the task ID, trace ID, context boundaries, and a delegation countdown so loops are mathematically impossible.

### The Live Test Console (The Glass Control Room)
To visually watch this team of 6 specialists work together in real-time, we built a floating console on the frontend called **Ring 1 Live Test**.
- **The Analogy**: Like a glass observation window overlooking the operations room. When you press "Run Integration Test", you see the courier carry envelopes from desk to desk in real time.
- **The Live Trace**: A chronological ledger showing every envelope sent, received, and completed.
- **The Delegation Graph**: A visual map with glowing lines that light up only when specialists pass work to each other.
- **The Plan Version Inspector**: Shows how the Planning specialist creates an initial checklist (Version 1), preserves finished steps when a snag occurs (like missing context), and writes a revised checklist (Version 2) without starting over from scratch.

### The Plan Step Executor (The Checklist Runner)
Previously, checklist steps were marked "done" on paper without actually running them. Now, we have a dedicated **Plan Step Executor**:
- It takes each item on the checklist one by one.
- It finds the right specialist through the courier (Mesh Router) and hands them the task in a secure envelope.
- It waits for the specialist to complete the real work and only marks the checklist item "COMPLETED" when real results are delivered.
- If a specialist runs into an error, the executor records the exact error details and failure evidence, halts forward execution, and asks Planning to revise the remaining checklist based on what actually went wrong.
- The Planning specialist retains everything already completed, skips the failed item, and inserts tailored recovery actions (like retrieving relevant precedents or clarifying missing case details) instead of repeatedly guessing.

### The Real PDF-to-Knowledge Pipeline
Instead of feeding fake or simulated documents, the system now accepts real multi-page PDF documents:
1. **The PDF Inspector (`PDFExtractor`)**: Validates that the file is genuinely a PDF starting with `%PDF-` bytes and under the 20MB limit. It unpacks the file page-by-page, detects whether the document is scanned or text-based, and attaches 1-indexed page provenance to every chunk.
2. **The Knowledge Distiller (`StructuredKnowledgeExtractor`)**: Scans the extracted text for Egyptian legal statutes (such as Egyptian Civil Code Article 147), parties, dates, financial retainers, and contractual obligations. Every fact is saved with its exact page number and text excerpt.
3. **The 9-Step Capability Flow**:
   - **Step 1 (Perception)**: Normalizes document content into structured input envelopes.
   - **Step 2 (Observation)**: Durably records the ingestion event into PostgreSQL (`ring1_observations`) with a SHA-256 fingerprint so identical documents cannot produce duplicate rows.
   - **Step 3 (Context)**: Verifies the legal case and organization boundaries, enforcing server-side authorization.
   - **Step 4 (Planning)**: Generates a 3-step checklist with explicit dependencies: `context.resolve` → `memory.store_record` → `retrieval.query`.
   - **Step 5 (Prerequisite Checking)**: Before any step runs, `PlanStepExecutor` verifies that its required prerequisite actually succeeded. If Step 1 fails, Step 2 and Step 3 are immediately marked `BLOCKED`, preventing unauthorized or ungrounded writes.
   - **Step 6 (Bounded Replanning)**: If a step fails, the system does not silently bypass it. Instead, Planning reviews the failure evidence and issues a revised Version 2 plan with explicit recovery actions.
   - **Step 7 (Memory Persistence)**: Stores validated facts into PostgreSQL (`ring1_memory_records`), strictly isolated by `case_id`.
   - **Step 8 (Verification Retrieval)**: Issues an independent search query against PostgreSQL to prove the facts can actually be retrieved.
   - **Step 9 (Scorecard)**: Emits a final scorecard reporting pages processed, candidate facts, persisted facts, and verified retrieval count.

---

## The Durable Execution Foundation (PostgreSQL Task Ledger & Outbox)

### The Authoritative State Ledger
Instead of tracking active tasks in Python memory dictionaries (which vanish if the server restarts), every task lives in a durable PostgreSQL table called `tasks`.
- A task moves through strict, atomic state gates: `PENDING` → `QUEUED` → `RUNNING` → `SUCCEEDED` / `FAILED` / `DEAD_LETTER`.
- When an API receives a request to start a task, it writes both the `Task` and an entry in `task_outbox` in the exact same database transaction. If the database crashes mid-way, either both are saved or neither is saved. There is zero chance of a task being lost or half-created.

### The Outbox Dispatcher (The Reliable Mailroom)
Redis and background workers are treated as fast delivery messengers, not permanent records of truth.
- The mailroom (`OutboxDispatcher`) locks pending tasks safely using `FOR UPDATE SKIP LOCKED`.
- It stamps each package with an incremented `dispatch_generation` and gives itself a bounded lease window.
- It changes the task state to `QUEUED` before enqueueing to Redis.
- If a delivery messenger crashes, the abandoned lease expires and the sweeper picks it up for redelivery without ever dropping tasks.

### Generation Fencing (Preventing Zombie Workers)
In distributed systems, a worker can become slow, unresponsive, or disconnected (a "zombie"). If the system assumes the worker died and assigns the task to someone else, the zombie might wake up later and try to write outdated results.
- Every task has a `lease_generation` number.
- Whenever a worker claims a task, the generation increments.
- All database writes (recording facts, updating status, logging audit events) verify the current generation inside the write transaction.
- If a zombie worker wakes up and tries to commit work with an expired generation, PostgreSQL immediately rejects it. Outdated work can never overwrite newer truth.

### Human Validation Authority over Knowledge Candidates
AI models and automated workers can suggest new facts, but they cannot declare them to be verified truth.
- When an automated worker extracts facts, they are tagged with lifecycle state `candidate`.
- A candidate can never promote itself to validated knowledge.
- Only a verified human actor with `validation_authority = True` can promote a candidate to `validated` status, preserving complete human oversight over organizational knowledge.

### Cryptographic HMAC Pagination Cursors
When browsing through long lists of observations or records, pages must not leak confidential files or let attackers tamper with pagination tokens.
- Pagination tokens are signed using HMAC-SHA256 and encoded with Base64URL.
- The signature binds the cursor directly to the caller's organization ID, legal case ID, sort order, and filter parameters.
- If anyone changes a single character, swaps the case ID, or alters the search filter, the signature verification fails immediately and halts the query before reaching the database.

