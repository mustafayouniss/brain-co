"""Production Document Processing Service for Ring 1.

Connects document uploads to Source persistence, TaskManager durable task ledger,
and Ring 1 knowledge extraction engines (Perception, Observation, Context, Memory).
"""

from __future__ import annotations

import hashlib
import logging
from pathlib import Path
from typing import Any, Callable, Optional
import uuid
from uuid import UUID

from fastapi import UploadFile
import sqlalchemy as sa
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

        # 1. Persist raw file to local storage backend
        _RAW_STORAGE_DIR.mkdir(parents=True, exist_ok=True)
        sha256_hash = hashlib.sha256(content).hexdigest()
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
            idempotency_key=f"source-doc-{source.id}",
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
            session.add(obs)
            session.flush()

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
            session.add(mem)
            session.flush()

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
