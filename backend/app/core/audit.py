"""Durable Audit Service for Ring 1.

Writes append-only audit events to PostgreSQL with SHA-256 payload checksums
for tamper and corruption detection. Fenced to worker lease generations.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any, Optional
import uuid
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.audit import AuditEvent


class AuditService:
    """Synchronous transactional audit writer for Ring 1."""

    @staticmethod
    def calculate_checksum(payload: Optional[dict[str, Any]]) -> Optional[str]:
        if not payload:
            return None
        canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    @classmethod
    def record_event(
        cls,
        session: Session,
        organization_id: str,
        engine_name: str,
        action: str,
        *,
        task_id: Optional[UUID] = None,
        case_id: Optional[str] = None,
        actor_ref: Optional[str] = None,
        previous_state: Optional[str] = None,
        new_state: Optional[str] = None,
        proposed_destination: Optional[str] = None,
        accepted_or_rejected: bool = True,
        execution_attempt: int = 1,
        lease_generation: Optional[int] = None,
        error_code: Optional[str] = None,
        payload: Optional[dict[str, Any]] = None,
        correlation_id: Optional[str] = None,
    ) -> AuditEvent:
        """Create and flush a durable audit event row within the caller's transaction."""
        checksum = cls.calculate_checksum(payload)

        event = AuditEvent(
            id=uuid.uuid4(),
            task_id=task_id,
            organization_id=organization_id,
            case_id=case_id,
            actor_ref=actor_ref,
            engine_name=engine_name,
            action=action,
            previous_state=previous_state,
            new_state=new_state,
            proposed_destination=proposed_destination,
            accepted_or_rejected=accepted_or_rejected,
            execution_attempt=execution_attempt,
            lease_generation=lease_generation,
            error_code=error_code,
            payload=payload,
            payload_checksum=checksum,
            correlation_id=correlation_id,
        )
        session.add(event)
        session.flush()
        return event
