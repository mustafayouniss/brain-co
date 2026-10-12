# Foundational Source Ingestion Pipeline — Technical Documentation

## 1. Purpose & Source Memory Foundation

The purpose of this pipeline is to establish the first permanent foundation of the Organizational Brain data ingestion architecture:

```text
Raw File
   ↓
Validation
   ↓
Fingerprint (SHA-256)
   ↓
Raw Storage
   ↓
Source Record
   ↓
PostgreSQL (Source Memory)
```

### Why Source Memory is Foundational
In the Organizational Brain architecture, **Observation is not Knowledge**, and raw information must never enter the brain without traceability and provenance. The `Source` represents the immutable physical ground truth from which all downstream artifacts are derived in future rings:

```text
Source (Immutable physical artifact & metadata)
   ↓
Parsing (Future Ring)
   ↓
Observation (Structured observation events)
   ↓
Knowledge Candidate (Extracted facts pending human validation)
   ↓
Trusted Knowledge (Audited organizational intelligence)
   ↓
Retrieval / Reasoning (Permission-aware decision support)
```

By recording each source with a stable UUID (`source_id`), cryptographic fingerprint (SHA-256), and storage reference from moment zero, every subsequent observation, chunk, or knowledge candidate can trace its unbroken provenance back to the exact physical source document.

---

## 2. Architecture & Separation of Responsibilities

A strict boundary is maintained between **Backend** and **Data Engineering**:

```text
                    INPUT LAYER
                         │
                         │ Raw File + HTTP Request
                         ▼
                      BACKEND
                         │
                 HTTP / Authentication
                         │
                         │ file bytes + trusted user context
                         ▼
                 DATA ENGINEERING
                 INGESTION PIPELINE
                         │
               ┌─────────┼─────────┐
               ▼         ▼         ▼
            Validate   SHA-256    Store
               │         │         │
               └─────────┼─────────┘
                         ▼
                   Source Record (Metadata & Reference)
                         │
                         ▼
                    PostgreSQL
```

### Ownership Breakdown

| Concern | Component Owner | Location |
|---|---|---|
| Ingestion Pipeline Orchestration | Data Engineering | `data-engineering/orgbrain_ingest/ingestion/pipeline.py` |
| File Validation Policy | Data Engineering | `data-engineering/orgbrain_ingest/ingestion/validation.py` |
| SHA-256 Fingerprint Calculation | Data Engineering | `data-engineering/orgbrain_ingest/ingestion/checksum.py` |
| Raw Storage Abstraction | Data Engineering | `data-engineering/orgbrain_ingest/storage/base.py` |
| Local Storage Implementation | Data Engineering | `data-engineering/orgbrain_ingest/storage/local.py` |
| Pipeline Exceptions | Data Engineering | `data-engineering/orgbrain_ingest/ingestion/errors.py` |
| Data Engineering Unit Tests | Data Engineering | `data-engineering/tests/` |
| Deterministic Evaluation Fixtures | Data Engineering | `data-engineering/fixtures/ingestion/` |
| SQLAlchemy Source Model | Backend | `backend/app/models/source.py` |
| Pydantic Source Schemas | Backend | `backend/app/schemas/source.py` |
| Source DB Registration Service | Backend | `backend/app/services/source_service.py` |
| Alembic Migration | Backend | `backend/migrations/versions/e819b932c01a_create_sources_table.py` |
| Backend DB Model Integration Tests | Backend | `backend/tests/test_source_model.py` |
| HTTP Endpoint / Auth / Commit | Backend | `backend/app/api/v1/sources.py` |

---

## 3. Database Specification (`sources` Table)

Alembic Revision: `e819b932c01a_create_sources_table`  
Down Revision: `778be99882b6` (`create_users_table`)

### Schema Definition

| Column | Type | Nullable | Default / Constraint | Description |
|---|---|---|---|---|
| `id` | `UUID` | No | `gen_random_uuid()` (PK) | Immutable stable identity for the source |
| `original_filename` | `VARCHAR(500)` | No | — | Original client-provided filename |
| `content_type` | `VARCHAR(100)` | No | — | Standard MIME type (e.g. `application/pdf`) |
| `size_bytes` | `BIGINT` | No | Check `size_bytes > 0` | File size in bytes |
| `checksum_sha256` | `VARCHAR(64)` | No | Indexed | 64-char lowercase hexadecimal hash |
| `source_type` | `VARCHAR(50)` | No | `'document'` | Domain classification of source |
| `storage_mode` | `VARCHAR(50)` | No | `'local'` | Storage backend type |
| `storage_key` | `VARCHAR(1000)` | No | — | Logical storage reference |
| `status` | `VARCHAR(50)` | No | `'ingested'` | Lifecycle status (`ingested`, etc.) |
| `uploaded_by` | `UUID` | No | FK `users.id` (RESTRICT) | ID of authenticated uploader |
| `created_at` | `TIMESTAMPTZ` | No | `now()` | Ingestion timestamp |
| `updated_at` | `TIMESTAMPTZ` | No | `now()` | Last status update timestamp |

### Indexes & Constraints
1. **Primary Key**: `id` (UUIDv4)
2. **Foreign Key**: `uploaded_by` -> `users.id` with `ON DELETE RESTRICT`
3. **Check Constraint**: `ck_sources_size_bytes_positive` (`size_bytes > 0`)
4. **Index**: `ix_sources_checksum_sha256` on `checksum_sha256` (enables O(1) content deduplication lookups)
5. **Index**: `ix_sources_uploaded_by` on `uploaded_by`
6. **Index**: `ix_sources_created_at` on `created_at`

### Raw Source File vs PostgreSQL Source Record
- **PostgreSQL Source Record**: Contains only structured metadata, foreign keys, lifecycle state, cryptographic checksum, and the logical storage reference. It **never** stores large binary blobs in PostgreSQL.
- **Raw Storage File**: Contains the exact binary stream of bytes as provided by the user, stored immutably on disk/object storage.

---

## 4. Storage Architecture

```text
                    SOURCE MEMORY

             ┌──────────────┴──────────────┐
             │                             │
        PostgreSQL                    Raw Storage
             │                             │
       Source metadata                Actual bytes
       source_id                     PDF / TXT
       checksum                           ...
       storage_key ───────────────────────►
       uploaded_by
       status
```

### Abstraction (`RawStorageBackend`)
The pipeline depends strictly on the `RawStorageBackend` ABC:
- `store(content: bytes, destination_key: str) -> str`
- `retrieve(storage_key: str) -> bytes`
- `exists(storage_key: str) -> bool`
- `storage_mode -> str`

### Local Filesystem Implementation (`LocalStorageBackend`)
- **Configurable Root**: Default `raw_storage/` (can be configured via environment).
- **Directory Traversal Protection**: Rejects keys containing relative escape sequences (`../`).
- **Atomic Writes**: Writes to `.tmp` file and atomically replaces on disk.
- **Logical Keys**: Stored keys follow the convention: `sources/{source_id}/{safe_filename}`. Absolute server filesystem paths are **never** returned as storage keys.
- **Git Isolation**: `raw_storage/` is added to `.gitignore`.

### Future S3 / MinIO Swappability
To switch from local disk to S3 or MinIO, only an `S3StorageBackend(RawStorageBackend)` implementation needs to be created. The `IngestionPipeline` code in `pipeline.py` requires zero modifications.

---

## 5. API Integration Point

### Endpoint: `POST /api/v1/sources`
- **Request**: Multipart form data with file upload (`UploadFile`).
- **Authentication**: Requires valid Bearer JWT. `uploaded_by` is extracted directly from the verified `current_user` (client-provided uploader IDs are rejected).
- **Response**: `201 Created` with `SourceResponse`:
  ```json
  {
    "id": "b18b45a6-9810-449e-b81f-4efc3547ebbc",
    "original_filename": "Civil_Code.pdf",
    "content_type": "application/pdf",
    "size_bytes": 1048576,
    "checksum_sha256": "4b227777d4dd1fc61c6f884f48641d02b4d121d3fd328cb08b5531fcacdabf8a",
    "source_type": "document",
    "status": "ingested",
    "created_at": "2026-10-12T08:40:00Z"
  }
  ```
- **Information Hiding**: The response strictly omits:
  - Host filesystem paths
  - Storage keys
  - Raw bytes
  - Internal database error details

### Integration State:
- **Implemented**: `backend/app/api/v1/sources.py` is written and ready.
- **Blocked**: Mounting `sources.py` in `backend/app/api/v1/__init__.py` and importing `get_current_user` from `backend/app/api/deps.py` is **blocked** by pre-existing Git merge conflicts in those files. Per project guidelines, conflicts were left untouched.

---

## 6. Testing & Evaluation Foundation

### Data Engineering Tests (Executed & Verified)
Location: `data-engineering/tests/`  
Command: `pytest data-engineering/tests -v`  
Result: **24 passed in 0.36s**

Test coverage:
- `test_validation.py` (9 tests): Valid PDF/TXT, charset parameters, empty filename, missing extension, unsupported extension, unsupported content type, empty 0-byte file, oversized files.
- `test_checksum.py` (4 tests): Known SHA-256 test vectors, deterministic hashing, stream vs bytes equivalence, evaluation fixtures verification.
- `test_storage.py` (6 tests): Storage mode property, byte-exact store and retrieve, exists check, missing object error handling, path traversal prevention, empty key rejection.
- `test_ingestion_pipeline.py` (5 tests): Full orchestration flow, filename sanitization, empty file rejection, unsupported file rejection, registration callback coordination.

### Evaluation Foundation
Location: `data-engineering/fixtures/ingestion/`
- `valid_small.pdf`: Standard valid minimal PDF document with Egyptian Civil Code content.
- `valid_small.txt`: Standard valid Arabic legal text document (Article 147 of the Egyptian Civil Code).
- `empty.pdf`: 0-byte file for deterministic negative testing.
- `unsupported_file.xyz`: Deterministic unsupported format fixture.

---

## 7. Current Scope & Non-Goals

The following are strictly out of scope for this foundation and have **not** been implemented:
- Document Parsing / Text Extraction
- OCR (Optical Character Recognition)
- Chunking & Tokenization
- Vector Embeddings & Vector Indexes on Source
- Observation Extraction / Event Detection
- Knowledge Extraction / Candidate Promotion
- Neo4j / Graph Linking
- LLM / RAG / Prompt Processing
- Retrieval & Reasoning Engines

---

## 8. Known Limitations & Integration Blockers

The following files on branch `main` contain pre-existing Git merge conflict markers (`<<<<<<< HEAD` / `=======` / `>>>>>>> origin/main`):
1. `backend/app/core/config.py`
2. `backend/app/api/deps.py`
3. `backend/app/api/v1/__init__.py`
4. `backend/app/core/errors.py`
5. `.gitignore`

### Impact:
- **Alembic Execution**: `alembic upgrade head` imports `app.core.config`, which raises `SyntaxError: invalid syntax` due to the conflict markers in `config.py`. Therefore, running migrations against the live database is **BLOCKED** pending conflict resolution.
- **Backend Model & API Tests**: `backend/tests/conftest.py` imports `app.core.config.settings`, which also fails with `SyntaxError`. Therefore, running pytest on backend files is **BLOCKED** pending conflict resolution.
- **API Mounting**: Registering `/api/v1/sources` router is **BLOCKED** until `backend/app/api/v1/__init__.py` conflicts are resolved.

### Action Plan After Merge Conflict Resolution:
1. Run `alembic upgrade head` in `backend/` to apply migration `e819b932c01a`.
2. Mount `sources.router` in `backend/app/api/v1/__init__.py`.
3. Run `pytest backend/tests/test_source_model.py`.
