"""Tests for ShortTermMemoryService (Section 11.1).

Verifies ephemeral execution state caching, organization and task key scoping,
TTL expiration, and cross-tenant isolation.
"""

import time
import uuid

import pytest

from app.core.short_term_memory import ShortTermMemoryService


@pytest.fixture(autouse=True)
def reset_short_term_memory():
    ShortTermMemoryService.reset()
    yield
    ShortTermMemoryService.reset()


def test_short_term_memory_key_scoping():
    """Verify keys are strictly scoped by organization_id and task_id."""
    org_id = "org-enterprise-alpha"
    task_id = uuid.uuid4()

    key = ShortTermMemoryService._format_key(org_id, task_id, "current_step")
    assert key == f"org:{org_id}:task:{task_id}:current_step"


def test_short_term_memory_set_and_get():
    """Verify storing and retrieving temporary execution state."""
    org_id = "org-test"
    task_id = uuid.uuid4()

    state = {
        "current_step": "step-2",
        "plan_version": 2,
        "completed_steps": ["step-1"],
        "intermediate_data": {"extracted_tokens": 142},
    }

    assert ShortTermMemoryService.set(org_id, task_id, "state", state, ttl_seconds=60)
    retrieved = ShortTermMemoryService.get(org_id, task_id, "state")
    assert retrieved == state


def test_short_term_memory_cross_tenant_isolation():
    """Verify org A cannot access org B's execution state even with same task_id."""
    task_id = uuid.uuid4()

    ShortTermMemoryService.set("org-a", task_id, "scratchpad", {"key": "secret_a"})
    ShortTermMemoryService.set("org-b", task_id, "scratchpad", {"key": "secret_b"})

    res_a = ShortTermMemoryService.get("org-a", task_id, "scratchpad")
    res_b = ShortTermMemoryService.get("org-b", task_id, "scratchpad")

    assert res_a == {"key": "secret_a"}
    assert res_b == {"key": "secret_b"}


def test_short_term_memory_cross_task_isolation():
    """Verify different tasks in the same org do not share keys."""
    org_id = "org-test"
    task_1 = uuid.uuid4()
    task_2 = uuid.uuid4()

    ShortTermMemoryService.set(org_id, task_1, "cursor", 100)
    assert ShortTermMemoryService.get(org_id, task_2, "cursor") is None


def test_short_term_memory_ttl_expiration():
    """Verify values expire after TTL seconds."""
    org_id = "org-test"
    task_id = uuid.uuid4()

    # Set with 0-second TTL (instant expiration)
    ShortTermMemoryService.set(org_id, task_id, "temp", "ephemeral", ttl_seconds=0)
    time.sleep(0.01)

    assert ShortTermMemoryService.get(org_id, task_id, "temp") is None


def test_short_term_memory_delete_single_and_all():
    """Verify selective and task-wide deletion of short-term state."""
    org_id = "org-test"
    task_id = uuid.uuid4()

    ShortTermMemoryService.set(org_id, task_id, "k1", "val1")
    ShortTermMemoryService.set(org_id, task_id, "k2", "val2")

    # Delete single key
    ShortTermMemoryService.delete(org_id, task_id, "k1")
    assert ShortTermMemoryService.get(org_id, task_id, "k1") is None
    assert ShortTermMemoryService.get(org_id, task_id, "k2") == "val2"

    # Delete all keys for task
    ShortTermMemoryService.delete(org_id, task_id)
    assert ShortTermMemoryService.get(org_id, task_id, "k2") is None
