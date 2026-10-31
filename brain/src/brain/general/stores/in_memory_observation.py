"""In-memory observation store implementation for tests and standalone CLI use.

Provides explicit, thread-safe in-memory observation persistence without requiring
SQLAlchemy or a live PostgreSQL database.
"""

from __future__ import annotations

import threading
import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from brain.general.contracts.protocols import ObservationFeedResult
from brain.general.contracts.storage import IObservationStore


class InMemoryObservationStore(IObservationStore):
    """Thread-safe in-memory observation store."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._observations: list[dict[str, Any]] = []

    async def find_by_idempotency_key(self, idempotency_key: str) -> Optional[dict[str, Any]]:
        with self._lock:
            for obs in self._observations:
                if obs.get("idempotency_key") == idempotency_key:
                    return dict(obs)
            return None

    async def save(self, observation: dict[str, Any]) -> str:
        with self._lock:
            obs_id = observation.get("id") or observation.get("observation_id") or str(uuid.uuid4())
            record = dict(observation)
            record["id"] = obs_id
            record["observation_id"] = obs_id
            if not record.get("case_id") and record.get("scope_id"):
                record["case_id"] = record["scope_id"]
            if "created_at" not in record:
                record["created_at"] = datetime.now(timezone.utc).isoformat()
            self._observations.append(record)
            return obs_id

    async def list_feed(
        self,
        organization_id: str,
        case_id: Optional[str] = None,
        event_type: Optional[str] = None,
        source: Optional[str] = None,
        limit: int = 20,
        cursor_created_at: Optional[str] = None,
        cursor_id: Optional[str] = None,
    ) -> ObservationFeedResult:
        with self._lock:
            filtered = []
            for obs in self._observations:
                if obs.get("organization_id") != organization_id:
                    continue
                if case_id and obs.get("case_id") != case_id and obs.get("scope_id") != case_id:
                    continue
                if event_type and obs.get("event_type") != event_type:
                    continue
                if source and obs.get("source") != source:
                    continue
                filtered.append(dict(obs))

            # Sort descending by created_at, id
            filtered.sort(
                key=lambda x: (x.get("created_at", ""), str(x.get("id", ""))),
                reverse=True,
            )

            # Keyset pagination if cursor provided
            if cursor_created_at and cursor_id:
                filtered = [
                    x for x in filtered
                    if (x.get("created_at", ""), str(x.get("id", ""))) < (cursor_created_at, cursor_id)
                ]

            page = filtered[:limit]
            has_more = len(filtered) > limit
            next_cursor = None
            if has_more and page:
                last_item = page[-1]
                next_cursor = f"{last_item.get('created_at')}:{last_item.get('id')}"

            return ObservationFeedResult(
                items=page,
                next_cursor=next_cursor,
                has_more=has_more,
                total_count=len(filtered),
            )

    @property
    def observations(self) -> list[dict[str, Any]]:
        return self._observations
