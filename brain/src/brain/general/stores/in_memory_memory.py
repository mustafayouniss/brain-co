"""In-memory memory store implementation for tests and standalone CLI use.

Provides explicit, thread-safe in-memory memory persistence without requiring
SQLAlchemy or a live PostgreSQL database.
"""

from __future__ import annotations

import threading
import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from brain.general.contracts.storage import IMemoryStore


class InMemoryMemoryStore(IMemoryStore):
    """Thread-safe in-memory memory store."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._records: dict[str, dict[str, Any]] = {}

    async def find_by_idempotency_key(self, idempotency_key: str) -> Optional[dict[str, Any]]:
        with self._lock:
            for rec in self._records.values():
                if rec.get("idempotency_key") == idempotency_key:
                    return dict(rec)
            return None

    async def save_record(self, record: dict[str, Any]) -> str:
        with self._lock:
            rec_id = str(record.get("id") or record.get("record_id") or uuid.uuid4())
            data = dict(record)
            data["id"] = rec_id
            data["record_id"] = rec_id
            if "created_at" not in data:
                data["created_at"] = datetime.now(timezone.utc).isoformat()
            self._records[rec_id] = data
            return rec_id

    async def get_record(
        self,
        record_id: str,
        organization_id: str,
        case_id: Optional[str] = None,
    ) -> Optional[dict[str, Any]]:
        with self._lock:
            rec = self._records.get(str(record_id))
            if not rec:
                return None
            if rec.get("organization_id") != organization_id:
                return None
            if case_id and rec.get("case_id") != case_id and rec.get("scope_id") != case_id:
                return None
            return dict(rec)

    async def update_status(
        self,
        record_id: str,
        organization_id: str,
        new_status: str,
        validation_authority: bool,
        metadata: Optional[dict[str, Any]] = None,
    ) -> bool:
        with self._lock:
            rec = self._records.get(str(record_id))
            if not rec:
                return False
            if rec.get("organization_id") != organization_id:
                return False
            if not validation_authority:
                return False

            rec["status"] = new_status
            if metadata:
                rec_meta = rec.get("metadata") or {}
                rec_meta.update(metadata)
                rec["metadata"] = rec_meta
            return True

    @property
    def records(self) -> dict[str, dict[str, Any]]:
        return self._records

    def list_all(self) -> list[dict[str, Any]]:
        with self._lock:
            return [dict(r) for r in self._records.values()]
