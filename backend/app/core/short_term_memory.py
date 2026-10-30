"""Short-Term Memory Service for Ring 1 Execution State.

Provides fast, temporary execution state caching (Redis with in-memory fallback).
Adheres strictly to the invariant: PostgreSQL remains authoritative for durable
task state. Short-term memory is ephemeral and scoped by organization and task.
"""

from __future__ import annotations

import json
import logging
import threading
import time
from typing import Any, Optional
from uuid import UUID

from app.core.config import settings

logger = logging.getLogger("app.core.short_term_memory")

DEFAULT_TTL_SECONDS: int = 3600  # 1 hour


class ShortTermMemoryService:
    """Ephemeral, organization-scoped short-term memory manager.
    
    Keys follow the standard format:
        org:{organization_id}:task:{task_id}:{key}
        
    Provides automatic fallback to an in-memory TTL store if Redis is unavailable
    or not installed, ensuring deterministic testing and zero stranded tasks.
    """

    _in_memory_store: dict[str, tuple[Any, float]] = {}
    _lock = threading.Lock()
    _redis_client: Any = None
    _redis_checked: bool = False

    @classmethod
    def _format_key(cls, organization_id: str, task_id: str | UUID, key: str) -> str:
        """Construct a standardized, tenant-isolated key."""
        org = organization_id.strip() if organization_id else "default"
        t_id = str(task_id).strip()
        k = key.strip()
        return f"org:{org}:task:{t_id}:{k}"

    @classmethod
    def _get_redis(cls) -> Optional[Any]:
        """Lazy initialization of optional Redis client."""
        if not cls._redis_checked:
            cls._redis_checked = True
            redis_url = getattr(settings, "REDIS_URL", None) or "redis://localhost:6379/0"
            try:
                import redis
                client = redis.from_url(redis_url, decode_responses=True, socket_timeout=1.0)
                client.ping()
                cls._redis_client = client
                logger.info("Connected to Redis for short-term memory at %s", redis_url)
            except Exception as e:
                cls._redis_client = None
                logger.info(
                    "Redis not reachable or not installed (%s). Using in-memory short-term memory store.",
                    str(e),
                )
        return cls._redis_client

    @classmethod
    def set(
        cls,
        organization_id: str,
        task_id: str | UUID,
        key: str,
        value: Any,
        ttl_seconds: int = DEFAULT_TTL_SECONDS,
    ) -> bool:
        """Store an ephemeral execution value under the scoped task key."""
        storage_key = cls._format_key(organization_id, task_id, key)
        serialized = json.dumps(value, default=str)

        redis_client = cls._get_redis()
        if redis_client is not None:
            try:
                redis_client.set(storage_key, serialized, ex=ttl_seconds)
                return True
            except Exception as e:
                logger.warning("Redis set failed for key %s: %s. Falling back to in-memory.", storage_key, str(e))

        # In-memory TTL storage
        expiry = time.time() + ttl_seconds
        with cls._lock:
            cls._in_memory_store[storage_key] = (serialized, expiry)
        return True

    @classmethod
    def get(
        cls,
        organization_id: str,
        task_id: str | UUID,
        key: str,
        default: Any = None,
    ) -> Any:
        """Retrieve an ephemeral execution value if not expired."""
        storage_key = cls._format_key(organization_id, task_id, key)

        redis_client = cls._get_redis()
        if redis_client is not None:
            try:
                raw = redis_client.get(storage_key)
                if raw is not None:
                    return json.loads(raw)
            except Exception as e:
                logger.warning("Redis get failed for key %s: %s. Falling back to in-memory.", storage_key, str(e))

        # In-memory TTL retrieval
        now = time.time()
        with cls._lock:
            item = cls._in_memory_store.get(storage_key)
            if item is not None:
                val_str, expiry = item
                if now < expiry:
                    return json.loads(val_str)
                else:
                    cls._in_memory_store.pop(storage_key, None)

        return default

    @classmethod
    def delete(
        cls,
        organization_id: str,
        task_id: str | UUID,
        key: Optional[str] = None,
    ) -> int:
        """Delete a single key or all keys associated with a task."""
        deleted_count = 0
        redis_client = cls._get_redis()

        if key is not None:
            storage_key = cls._format_key(organization_id, task_id, key)
            if redis_client is not None:
                try:
                    deleted_count += redis_client.delete(storage_key)
                except Exception:
                    pass
            with cls._lock:
                if cls._in_memory_store.pop(storage_key, None):
                    deleted_count += 1
            return deleted_count

        # Delete all keys for task prefix: org:{org_id}:task:{task_id}:*
        prefix = f"org:{organization_id.strip()}:task:{str(task_id).strip()}:"
        if redis_client is not None:
            try:
                keys = redis_client.keys(f"{prefix}*")
                if keys:
                    deleted_count += redis_client.delete(*keys)
            except Exception:
                pass

        with cls._lock:
            matching = [k for k in cls._in_memory_store if k.startswith(prefix)]
            for k in matching:
                cls._in_memory_store.pop(k, None)
                deleted_count += 1

        return deleted_count

    @classmethod
    def reset(cls) -> None:
        """Clear all in-memory entries (used for testing)."""
        with cls._lock:
            cls._in_memory_store.clear()
        cls._redis_checked = False
        cls._redis_client = None
