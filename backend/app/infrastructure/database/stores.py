"""PostgreSQL / SQLAlchemy Storage Adapters for General Brain.

Implements General Brain storage protocols:
- IObservationStore
- IMemoryStore
- IRetrievalStore

Enforces strict tenant isolation (organization_id) and case isolation (case_id).
Preserves keyset pagination and database integrity without leaking ORM details to General Brain.
"""

from __future__ import annotations

from datetime import datetime, timezone
import json
import logging
from typing import Any, Callable, Optional
import uuid

from sqlalchemy import and_, or_, select
from sqlalchemy.orm import Session

from app.ring1.models.observation import MemoryRecord, Observation
from brain.general.contracts.protocols import ObservationFeedResult
from brain.general.contracts.storage import (
    IMemoryStore,
    IObservationStore,
    IRetrievalStore,
)

logger = logging.getLogger("app.infrastructure.database.stores")


class SqlAlchemyObservationStore(IObservationStore):
    """PostgreSQL storage adapter for IObservationStore."""

    def __init__(self, db_session_factory: Callable[[], Session]) -> None:
        self._session_factory = db_session_factory

    async def find_by_idempotency_key(self, idempotency_key: str) -> Optional[dict[str, Any]]:
        session: Session = self._session_factory()
        try:
            obs = (
                session.query(Observation)
                .filter(Observation.idempotency_key == idempotency_key)
                .first()
            )
            if obs is None:
                return None
            return {
                "observation_id": str(obs.id),
                "event_id": obs.event_id,
                "event_type": obs.event_type,
                "source": obs.source,
                "status": obs.status,
                "organization_id": obs.organization_id,
                "case_id": obs.case_id,
                "context_ref": obs.context_ref,
                "timestamp": obs.created_at.isoformat() if obs.created_at else None,
                "payload": obs.payload or {},
                "metadata": obs.metadata_ or {},
            }
        finally:
            session.close()

    async def save(self, observation: dict[str, Any]) -> str:
        session: Session = self._session_factory()
        try:
            obs_id = observation.get("observation_id")
            uid = uuid.UUID(str(obs_id)) if obs_id else uuid.uuid4()
            
            raw_ts = observation.get("timestamp")
            dt = None
            if raw_ts:
                try:
                    dt = datetime.fromisoformat(str(raw_ts))
                    if dt.tzinfo is None:
                        dt = dt.replace(tzinfo=timezone.utc)
                except (ValueError, TypeError):
                    dt = datetime.now(timezone.utc)

            obs = Observation(
                id=uid,
                event_id=observation.get("event_id", f"evt-{uuid.uuid4().hex[:12]}"),
                event_type=observation.get("event_type", "unknown"),
                source=observation.get("source", "unknown"),
                actor_ref=observation.get("actor_ref"),
                context_ref=observation.get("context_ref"),
                case_id=observation.get("case_id"),
                organization_id=observation.get("organization_id"),
                payload=observation.get("payload", {}),
                metadata_=observation.get("metadata", {}),
                trace_id=observation.get("trace_id"),
                task_id=observation.get("task_id"),
                idempotency_key=observation.get("idempotency_key"),
                status=observation.get("status", "recorded"),
                event_timestamp=dt or datetime.now(timezone.utc),
            )
            session.add(obs)
            session.commit()
            return str(obs.id)
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

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
        session: Session = self._session_factory()
        try:
            query = session.query(Observation).filter(
                Observation.organization_id == organization_id
            )
            if case_id:
                query = query.filter(Observation.case_id == case_id)
            if event_type:
                query = query.filter(Observation.event_type == event_type)
            if source:
                query = query.filter(Observation.source == source)

            # Keyset condition if cursor provided: (created_at, id) < (cursor_created_at, cursor_id)
            if cursor_created_at and cursor_id:
                try:
                    c_dt = datetime.fromisoformat(cursor_created_at)
                    if c_dt.tzinfo is None:
                        c_dt = c_dt.replace(tzinfo=timezone.utc)
                    c_uid = uuid.UUID(cursor_id)
                    query = query.filter(
                        or_(
                            Observation.created_at < c_dt,
                            and_(
                                Observation.created_at == c_dt,
                                Observation.id < c_uid,
                            ),
                        )
                    )
                except Exception as exc:
                    logger.warning("Invalid cursor keyset values: %s", exc)

            query = query.order_by(Observation.created_at.desc(), Observation.id.desc())
            rows = query.limit(limit + 1).all()

            has_more = len(rows) > limit
            sliced = rows[:limit]

            items = [
                {
                    "observation_id": str(r.id),
                    "event_id": r.event_id,
                    "event_type": r.event_type,
                    "source": r.source,
                    "status": r.status,
                    "timestamp": r.created_at.isoformat() if r.created_at else None,
                    "payload": r.payload or {},
                    "metadata": r.metadata_ or {},
                    "case_id": r.case_id,
                    "organization_id": r.organization_id,
                }
                for r in sliced
            ]

            next_cursor = None
            if has_more and sliced:
                last_r = sliced[-1]
                next_cursor = f"{last_r.created_at.isoformat()}:{str(last_r.id)}"

            return ObservationFeedResult(
                items=items,
                next_cursor=next_cursor,
                has_more=has_more,
                total_count=len(items),
            )
        finally:
            session.close()


class SqlAlchemyMemoryStore(IMemoryStore):
    """PostgreSQL storage adapter for IMemoryStore."""

    def __init__(self, db_session_factory: Callable[[], Session]) -> None:
        self._session_factory = db_session_factory

    async def find_by_idempotency_key(self, idempotency_key: str) -> Optional[dict[str, Any]]:
        session: Session = self._session_factory()
        try:
            stmt = select(MemoryRecord).where(
                MemoryRecord.idempotency_key == idempotency_key
            )
            rec = session.execute(stmt).scalar_one_or_none()
            if rec is None:
                return None
            return {
                "record_id": str(rec.id),
                "record_type": rec.record_type,
                "status": rec.status,
                "organization_id": rec.organization_id,
                "case_id": rec.case_id,
                "context_ref": rec.context_ref,
                "payload": rec.payload or {},
                "metadata": rec.metadata_ or {},
                "trace_id": rec.trace_id,
                "task_id": rec.task_id,
                "created_at": rec.created_at.isoformat() if rec.created_at else None,
            }
        finally:
            session.close()

    async def save_record(self, record: dict[str, Any]) -> str:
        session: Session = self._session_factory()
        try:
            rec_id = record.get("record_id")
            uid = uuid.UUID(str(rec_id)) if rec_id else uuid.uuid4()
            source_obs_id = record.get("source_observation_id")
            parsed_obs_id = None
            if source_obs_id:
                try:
                    parsed_obs_id = uuid.UUID(str(source_obs_id))
                except (ValueError, TypeError):
                    parsed_obs_id = None

            mem = MemoryRecord(
                id=uid,
                record_type=record.get("record_type", "fact_candidate"),
                context_ref=record.get("context_ref"),
                case_id=record.get("case_id"),
                organization_id=record.get("organization_id"),
                payload=record.get("payload", {}),
                metadata_=record.get("metadata", {}),
                trace_id=record.get("trace_id"),
                task_id=record.get("task_id"),
                source_observation_id=parsed_obs_id,
                idempotency_key=record.get("idempotency_key"),
                status=record.get("status", "active"),
            )
            session.add(mem)
            session.commit()
            return str(mem.id)
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    async def get_record(
        self,
        record_id: str,
        organization_id: str,
        case_id: Optional[str] = None,
    ) -> Optional[dict[str, Any]]:
        session: Session = self._session_factory()
        try:
            try:
                uid = uuid.UUID(record_id)
            except (ValueError, TypeError):
                return None

            stmt = select(MemoryRecord).where(
                MemoryRecord.id == uid,
                MemoryRecord.organization_id == organization_id,
            )
            if case_id:
                stmt = stmt.where(MemoryRecord.case_id == case_id)

            rec = session.execute(stmt).scalar_one_or_none()
            if rec is None:
                return None
            return {
                "record_id": str(rec.id),
                "record_type": rec.record_type,
                "status": rec.status,
                "organization_id": rec.organization_id,
                "case_id": rec.case_id,
                "context_ref": rec.context_ref,
                "payload": rec.payload or {},
                "metadata": rec.metadata_ or {},
                "trace_id": rec.trace_id,
                "task_id": rec.task_id,
                "created_at": rec.created_at.isoformat() if rec.created_at else None,
            }
        finally:
            session.close()

    async def update_status(
        self,
        record_id: str,
        organization_id: str,
        new_status: str,
        validation_authority: bool,
        metadata: Optional[dict[str, Any]] = None,
    ) -> bool:
        if not validation_authority:
            raise PermissionError(
                "Updating memory record status requires explicit validation authority."
            )

        session: Session = self._session_factory()
        try:
            try:
                uid = uuid.UUID(record_id)
            except (ValueError, TypeError):
                return False

            stmt = select(MemoryRecord).where(
                MemoryRecord.id == uid,
                MemoryRecord.organization_id == organization_id,
            )
            rec = session.execute(stmt).scalar_one_or_none()
            if rec is None:
                return False

            rec.status = new_status
            if metadata:
                current_meta = dict(rec.metadata_ or {})
                current_meta.update(metadata)
                rec.metadata_ = current_meta

            session.commit()
            return True
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()


class SqlAlchemyRetrievalStore(IRetrievalStore):
    """PostgreSQL storage adapter for IRetrievalStore."""

    def __init__(self, db_session_factory: Callable[[], Session]) -> None:
        self._session_factory = db_session_factory

    async def search_records(
        self,
        query: str,
        organization_id: str,
        case_id: Optional[str] = None,
        record_type: Optional[str] = None,
        limit: int = 10,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        session: Session = self._session_factory()
        try:
            stmt = select(MemoryRecord).where(
                MemoryRecord.organization_id == organization_id
            )
            if case_id:
                stmt = stmt.where(MemoryRecord.case_id == case_id)
            if record_type:
                stmt = stmt.where(MemoryRecord.record_type == record_type)

            stmt = stmt.order_by(MemoryRecord.created_at.desc()).limit(limit * 3)
            records = session.execute(stmt).scalars().all()

            results: list[dict[str, Any]] = []
            tokens = [t.lower() for t in query.split() if len(t) > 2]

            for rec in records:
                payload = rec.payload or {}
                text_repr = json.dumps(payload).lower()
                
                score = 0.0
                if tokens:
                    matches = sum(1 for t in tokens if t in text_repr)
                    score = matches / len(tokens)
                else:
                    score = 0.5

                if not tokens or score > 0.0:
                    results.append({
                        "record_id": str(rec.id),
                        "record_type": rec.record_type,
                        "status": rec.status,
                        "case_id": rec.case_id,
                        "organization_id": rec.organization_id,
                        "payload": payload,
                        "metadata": rec.metadata_ or {},
                        "relevance_score": round(score, 3),
                    })

            results.sort(key=lambda x: x["relevance_score"], reverse=True)
            return results[offset : offset + limit]
        finally:
            session.close()


__all__ = [
    "SqlAlchemyMemoryStore",
    "SqlAlchemyObservationStore",
    "SqlAlchemyRetrievalStore",
]
