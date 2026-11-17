"""Production Document Processing Service for Ring 1.

Connects document uploads to Source persistence, TaskManager durable task ledger,
and Ring 1 knowledge extraction engines (Perception, Observation, Context, Memory).
"""

from __future__ import annotations

import asyncio
import concurrent.futures
from datetime import datetime, timezone
import hashlib
import inspect
import logging
from pathlib import Path
from typing import Any, Callable, Optional
import uuid
from uuid import UUID

from fastapi import UploadFile
import sqlalchemy as sa
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ai.config.ai_config import ai_config
from app.core.audit import AuditService
from app.core.context import BrainContext
from app.core.outbox_dispatcher import OutboxDispatcher
from app.core.task_manager import StaleWorkerLeaseError, TaskManager
from app.models.case import Case
from app.models.source import Source
from app.models.task import OutboxStatus, Task, TaskOutbox, TaskState
from app.ring1.models.observation import MemoryRecord, Observation
from app.ring1.pdf.extractor import PDFExtractor
from app.ring1.pdf.structured import StructuredKnowledgeExtractor

logger = logging.getLogger("app.services.document_processing")

# Max allowed PDF upload size: 20 MB
MAX_PDF_SIZE_BYTES = 20 * 1024 * 1024

_RAW_STORAGE_DIR = Path("raw_storage/documents").resolve()


class DocumentValidationError(Exception):
    """Raised when uploaded file fails validation."""


class DocumentProcessingService:
    """Production service for validating, persisting, and processing case documents."""

    @staticmethod
    async def create_document_task(
        session: Session,
        case: Case,
        file: UploadFile,
        context: BrainContext,
    ) -> tuple[Source, Task]:
        """Validate, store raw PDF, create Source record, and register a durable Task."""
        if not file.filename:
            raise DocumentValidationError("Filename is required.")

        raw_filename = file.filename
        safe_filename = raw_filename.replace("\\", "/").split("/")[-1].strip() or "document.pdf"

        # Read bytes with bounded limit
        content = await file.read(MAX_PDF_SIZE_BYTES + 1)
        if len(content) > MAX_PDF_SIZE_BYTES:
            raise DocumentValidationError(
                f"File size exceeds maximum allowed limit of {MAX_PDF_SIZE_BYTES // (1024 * 1024)}MB"
            )

        if not content.startswith(b"%PDF-"):
            raise DocumentValidationError("Invalid file signature: File must be a valid PDF starting with %PDF-")

        # Compute sha256 of the content before writing anything to disk
        sha256_hash = hashlib.sha256(content).hexdigest()
        task_idempotency_key = f"source-doc-{case.id}-{sha256_hash}"

        # Look for an existing Source with the SAME organization_id, the SAME case_id, and the SAME checksum_sha256
        existing_source = (
            session.query(Source)
            .filter(
                Source.organization_id == context.organization_id,
                Source.case_id == str(case.id),
                Source.checksum_sha256 == sha256_hash,
            )
            .first()
        )

        if existing_source is not None:
            source = existing_source
            # Ensure physical storage file exists on disk, rewrite if removed
            if not Path(source.storage_key).exists():
                Path(source.storage_key).parent.mkdir(parents=True, exist_ok=True)
                with open(source.storage_key, "wb") as f:
                    f.write(content)

            # Find its task
            task = (
                session.query(Task)
                .filter(
                    Task.organization_id == context.organization_id,
                    Task.idempotency_key == task_idempotency_key,
                )
                .first()
            )
            if not task:
                task = (
                    session.query(Task)
                    .filter(
                        Task.organization_id == context.organization_id,
                        Task.idempotency_key == f"source-doc-{source.id}",
                    )
                    .first()
                )

            if task is not None:
                is_failed = task.state in (
                    TaskState.FAILED.value,
                    TaskState.DEAD_LETTER.value,
                    "FAILED",
                    "DEAD_LETTER",
                )
                if not is_failed:
                    # Task is completed, pending, queued, retrying, or running -> reuse existing, do not schedule
                    setattr(task, "is_duplicate", True)
                    setattr(source, "is_duplicate", True)
                    return source, task
                else:
                    # Failed or permanent failure -> retry: reset task and schedule it
                    task.state = TaskState.PENDING.value
                    task.error_details = None
                    task.result = None
                    task.worker_id = None
                    task.lease_expires_at = None
                    task.retry_count = 0
                    task.idempotency_key = task_idempotency_key
                    task.updated_at = datetime.now(timezone.utc)

                    outbox = session.query(TaskOutbox).filter(TaskOutbox.task_id == task.id).first()
                    if outbox:
                        outbox.status = OutboxStatus.PENDING.value
                        outbox.dispatch_generation += 1
                        outbox.dispatch_attempts = 0
                        outbox.updated_at = datetime.now(timezone.utc)
                    else:
                        outbox = TaskOutbox(
                            id=uuid.uuid4(),
                            task_id=task.id,
                            queue_name="ring1_tasks",
                            payload={
                                "task_id": str(task.id),
                                "organization_id": context.organization_id,
                                "case_id": str(case.id),
                            },
                            status=OutboxStatus.PENDING.value,
                            dispatch_generation=0,
                            dispatch_attempts=0,
                            created_at=datetime.now(timezone.utc),
                            updated_at=datetime.now(timezone.utc),
                        )
                        session.add(outbox)
                    session.flush()

                    AuditService.record_event(
                        session=session,
                        organization_id=context.organization_id,
                        engine_name="document_processing",
                        action="document_upload_retried",
                        task_id=task.id,
                        case_id=str(case.id),
                        actor_ref=str(context.user_id) if context.user_id else None,
                        payload={
                            "source_id": str(source.id),
                            "filename": source.original_filename,
                            "size_bytes": source.size_bytes,
                        },
                    )

                    setattr(task, "is_duplicate", False)
                    setattr(source, "is_duplicate", False)
                    return source, task
            else:
                # Existing source but missing task -> create fresh task
                task_payload = {
                    "source_id": str(source.id),
                    "filename": safe_filename,
                    "storage_key": str(source.storage_key),
                    "file_hash": sha256_hash,
                    "case_id": str(case.id),
                }
                task, _ = TaskManager.create_task_with_outbox(
                    session=session,
                    organization_id=context.organization_id,
                    task_type="document_processing",
                    payload=task_payload,
                    idempotency_key=task_idempotency_key,
                    case_id=str(case.id),
                    user_id=str(context.user_id) if context.user_id else None,
                    correlation_id=context.correlation_id,
                )
                setattr(task, "is_duplicate", False)
                setattr(source, "is_duplicate", False)
                return source, task

        # Novel document: 1. Persist raw file to local storage backend
        _RAW_STORAGE_DIR.mkdir(parents=True, exist_ok=True)
        storage_filename = f"{uuid.uuid4().hex}_{safe_filename}"
        storage_path = _RAW_STORAGE_DIR / storage_filename

        with open(storage_path, "wb") as f:
            f.write(content)

        # 2. Create Source record
        source_id = uuid.uuid4()
        user_uuid = None
        if context.user_id:
            try:
                user_uuid = UUID(context.user_id)
            except Exception:
                user_uuid = None

        source = Source(
            id=source_id,
            case_id=str(case.id),
            organization_id=context.organization_id,
            original_filename=safe_filename,
            content_type="application/pdf",
            size_bytes=len(content),
            checksum_sha256=sha256_hash,
            source_type="document",
            storage_mode="local",
            storage_key=str(storage_path),
            status="ingested",
            uploaded_by=user_uuid,
        )
        session.add(source)
        session.flush()

        # 3. Create durable Task and Outbox row via TaskManager
        task_payload = {
            "source_id": str(source.id),
            "filename": safe_filename,
            "storage_key": str(storage_path),
            "file_hash": sha256_hash,
            "case_id": str(case.id),
        }

        task, is_new = TaskManager.create_task_with_outbox(
            session=session,
            organization_id=context.organization_id,
            task_type="document_processing",
            payload=task_payload,
            idempotency_key=task_idempotency_key,
            case_id=str(case.id),
            user_id=str(context.user_id) if context.user_id else None,
            correlation_id=context.correlation_id,
        )

        AuditService.record_event(
            session=session,
            organization_id=context.organization_id,
            engine_name="document_processing",
            action="document_uploaded",
            task_id=task.id,
            case_id=str(case.id),
            actor_ref=str(context.user_id) if context.user_id else None,
            payload={
                "source_id": str(source.id),
                "filename": safe_filename,
                "size_bytes": len(content),
            },
        )

        setattr(task, "is_duplicate", False)
        setattr(source, "is_duplicate", False)
        return source, task

    @staticmethod
    def process_task_worker(
        session: Session,
        task_id: UUID,
        worker_id: str = "backend-worker-1",
    ) -> bool:
        """Background worker unit of work.
        
        Claims task, executes Ring 1 PDF parsing and structured knowledge extraction,
        persists observation and memory records, and atomically commits task status.
        """
        # 1. Claim task
        task_preview = session.get(Task, task_id)
        if task_preview and task_preview.state == TaskState.PENDING.value:
            task_preview.state = TaskState.QUEUED.value
            session.flush()

        current_gen = TaskManager.claim_task_for_worker(
            session=session,
            task_id=task_id,
            worker_id=worker_id,
            lease_duration_seconds=300,
        )
        if current_gen is None:
            logger.info("Task %s already claimed or in terminal state; skipping", task_id)
            return False

        # 2. Outbox dispatch acknowledgment
        outbox = session.query(TaskOutbox).filter(TaskOutbox.task_id == task_id).first()
        if outbox and outbox.status == OutboxStatus.PENDING.value:
            outbox.status = OutboxStatus.DISPATCHING.value
            outbox.dispatch_generation += 1
            session.flush()
            OutboxDispatcher.acknowledge_dispatch(
                session=session,
                outbox_id=outbox.id,
                claimed_dispatch_generation=outbox.dispatch_generation,
            )
        session.commit()

        # 3. Read task and payload
        task = session.get(Task, task_id)
        if not task:
            return False

        payload = task.payload or {}
        storage_key = payload.get("storage_key")
        filename = payload.get("filename", "document.pdf")
        case_id = payload.get("case_id") or str(task.case_id)
        organization_id = task.organization_id
        source_id = payload.get("source_id")

        try:
            if not storage_key or not Path(storage_key).exists():
                raise FileNotFoundError(f"Source file not found at storage key: {storage_key}")

            with open(storage_key, "rb") as f:
                pdf_bytes = f.read()

            # 4. Ring 1 PDF Extraction
            extractor = PDFExtractor()
            extraction_res = extractor.extract(pdf_bytes, filename=filename)
            if extraction_res.errors:
                raise RuntimeError(f"PDF extraction failed: {extraction_res.errors[0]}")

            # 5. Structured Legal Knowledge Extraction
            llm_service = ai_config.create_service()
            knowledge_extractor = StructuredKnowledgeExtractor(llm_service=llm_service)
            structured_doc = knowledge_extractor.extract(extraction_res)
            if inspect.iscoroutine(structured_doc):
                try:
                    loop = asyncio.get_running_loop()
                except RuntimeError:
                    loop = None

                if loop and loop.is_running():
                    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                        structured_doc = executor.submit(asyncio.run, structured_doc).result()
                else:
                    structured_doc = asyncio.run(structured_doc)

            # 6. Persist Observation with SHA-256 idempotency
            obs_id = uuid.uuid4()
            obs_idempotency_key = f"obs-doc-{extraction_res.file_hash[:16]}-{case_id[:8]}"
            obs = Observation(
                id=obs_id,
                event_id=str(obs_id),
                event_type="document.structured_knowledge",
                source="upload",
                organization_id=organization_id,
                case_id=case_id,
                payload={
                    "title": structured_doc.title,
                    "document_type": structured_doc.document_type,
                    "facts_count": len(structured_doc.facts),
                    "summary": structured_doc.summary,
                    "filename": filename,
                    "file_hash": extraction_res.file_hash,
                },
                metadata_={"content_hash": extraction_res.file_hash},
                idempotency_key=obs_idempotency_key,
                status="recorded",
            )
            try:
                with session.begin_nested():
                    session.add(obs)
                    session.flush()
            except IntegrityError:
                existing_obs = (
                    session.query(Observation)
                    .filter(
                        Observation.organization_id == organization_id,
                        Observation.idempotency_key == obs_idempotency_key,
                    )
                    .first()
                )
                if existing_obs is None:
                    raise
                obs_id = existing_obs.id

            # 7. Persist MemoryRecord (strictly in candidate status per vision & validation rules)
            mem_id = uuid.uuid4()
            mem_idempotency_key = f"mem-doc-{extraction_res.file_hash[:16]}-{case_id[:8]}"
            mem = MemoryRecord(
                id=mem_id,
                organization_id=organization_id,
                case_id=case_id,
                record_type="pdf_knowledge",
                status="candidate",  # Candidate status requires explicit human validation
                payload={
                    "filename": filename,
                    "file_hash": extraction_res.file_hash,
                    "title": structured_doc.title,
                    "document_type": structured_doc.document_type,
                    "facts_count": len(structured_doc.facts),
                    "facts": [f.model_dump() for f in structured_doc.facts],
                    "entities": [e.model_dump() for e in structured_doc.entities],
                    "obligations": [o.model_dump() for o in structured_doc.obligations],
                    "summary": structured_doc.summary,
                    "source_id": source_id,
                },
                source_observation_id=obs_id,
                idempotency_key=mem_idempotency_key,
            )
            try:
                with session.begin_nested():
                    session.add(mem)
                    session.flush()
            except IntegrityError:
                existing_mem = (
                    session.query(MemoryRecord)
                    .filter(
                        MemoryRecord.organization_id == organization_id,
                        MemoryRecord.idempotency_key == mem_idempotency_key,
                    )
                    .first()
                )
                if existing_mem is None:
                    raise
                mem_id = existing_mem.id

            # 8. Commit Task Success with Generation Fence
            TaskManager.commit_task_success(
                session=session,
                task_id=task_id,
                current_generation=current_gen,
                result={
                    "source_id": source_id,
                    "title": structured_doc.title,
                    "document_type": structured_doc.document_type,
                    "facts_count": len(structured_doc.facts),
                    "entities_count": len(structured_doc.entities),
                    "obligations_count": len(structured_doc.obligations),
                    "memory_record_id": str(mem_id),
                    "observation_id": str(obs_id),
                    "status": "completed",
                },
            )
            session.commit()
            logger.info("Task %s successfully processed and committed by worker %s", task_id, worker_id)
            return True

        except Exception as exc:
            session.rollback()
            logger.error("Processing task %s failed: %s", task_id, exc, exc_info=True)
            try:
                error_data = {
                    "code": "DOCUMENT_PROCESSING_FAILED",
                    "message": str(exc),
                }
                TaskManager.commit_task_permanent_failure(
                    session=session,
                    task_id=task_id,
                    current_generation=current_gen,
                    error_data=error_data,
                )
                session.commit()
            except StaleWorkerLeaseError:
                logger.warning("Worker %s lost lease for task %s on failure commit", worker_id, task_id)
            return False
