"""Test that General Brain can run in a standalone subprocess with ONLY brain/src on PYTHONPATH."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
import pytest


REPO_ROOT = Path(__file__).resolve().parent.parent.parent
BRAIN_SRC = REPO_ROOT / "brain" / "src"


def test_general_brain_subprocess_standalone_execution():
    """Verify in an isolated subprocess that General Brain imports and executes without Backend."""
    standalone_code = """
import sys

# Ensure backend or app are NOT in sys.path
for p in list(sys.path):
    if "backend" in p or "app" in p:
        sys.path.remove(p)

import brain
from brain.general.contracts.context import BrainContext
from brain.general.contracts.envelopes import MeshRequest, ResultStatus
from brain.general.contracts.capabilities import (
    PERCEPTION_STRUCTURE_INPUT,
    OBSERVATION_RECORD_EVENT,
    CONTEXT_RESOLVE,
    MEMORY_STORE_RECORD,
    MEMORY_GET_RECORD,
    RETRIEVAL_QUERY,
    PLANNING_CREATE_PLAN,
    CapabilityRegistry,
)
from brain.general.stores import (
    InMemoryObservationStore,
    InMemoryMemoryStore,
    InMemoryRetrievalStore,
)
from brain.general.engines import (
    PerceptionEngine,
    ObservationEngine,
    ContextEngine,
    BasicMemoryEngine,
    BasicRetrievalEngine,
    PlanningEngine,
)
from brain.general.runtime import MeshRouter, RuntimeDispatcher

# Verify forbidden packages were NOT imported
forbidden = ["fastapi", "sqlalchemy", "redis", "arq", "backend", "app", "ai"]
for f in forbidden:
    assert f not in sys.modules, f"Forbidden module '{f}' was loaded into sys.modules"

# 1. Instantiate Stores
obs_store = InMemoryObservationStore()
mem_store = InMemoryMemoryStore()
ret_store = InMemoryRetrievalStore(memory_store=mem_store)

# 2. Instantiate Engines with explicit stores
perception = PerceptionEngine()
observation = ObservationEngine(store=obs_store)
context_engine = ContextEngine()
memory = BasicMemoryEngine(store=mem_store)
retrieval = BasicRetrievalEngine(store=ret_store)
planning = PlanningEngine()

# 3. Register with Router
registry = CapabilityRegistry()
registry.register(PERCEPTION_STRUCTURE_INPUT, "perception", perception.handle_structure_input)
registry.register(OBSERVATION_RECORD_EVENT, "observation", observation.handle_record_event)
registry.register(CONTEXT_RESOLVE, "context", context_engine.handle_resolve)
registry.register(MEMORY_STORE_RECORD, "memory", memory.handle_store_record)
registry.register(MEMORY_GET_RECORD, "memory", memory.handle_get_record)
registry.register(RETRIEVAL_QUERY, "retrieval", retrieval.handle_query)
registry.register(PLANNING_CREATE_PLAN, "planning", planning.handle_create_plan)
router = MeshRouter(registry)

# 4. Verify pure execution of engines via async runner
import asyncio
import uuid

async def run_pipeline():
    ctx = BrainContext(
        organization_id="org-standalone-1",
        case_id="case-001",
        user_id="user-standalone",
        correlation_id=uuid.uuid4(),
        validation_authority=True,
    )

    # Perception
    p_res = await perception.process("Invoice total: $500", ctx)
    assert p_res.data["content_type"] == "text"
    assert p_res.error is None

    # Observation
    o_res = await observation.record_observation({
        "event_type": "invoice.received",
        "payload": {"amount": 500},
        "idempotency_key": "inv-001",
    }, ctx)
    assert o_res.data["status"] == "recorded"

    # Memory candidate
    m_res = await memory.store_candidate({
        "record_type": "invoice",
        "payload": {"amount": 500},
        "idempotency_key": "mem-001",
    }, ctx)
    assert m_res.data["status"] == "candidate"
    rec_id = m_res.data["record_id"]

    # Memory validate
    v_res = await memory.validate_candidate(rec_id, "VALIDATE", ctx)
    assert v_res.data["status"] == "validated"

    # Retrieval
    r_res = await retrieval.search("amount", ctx)
    assert len(r_res.data["records"]) >= 1

    # Planning
    plan_res = await planning.create_plan("Review invoice and schedule payment", ctx)
    assert plan_res.plan_id is not None
    assert len(plan_res.steps) >= 1

    print("STANDALONE_SUCCESS")

asyncio.run(run_pipeline())
"""
    env = os.environ.copy()
    env["PYTHONPATH"] = str(BRAIN_SRC)

    proc = subprocess.run(
        [sys.executable, "-c", standalone_code],
        env=env,
        capture_output=True,
        text=True,
    )

    assert proc.returncode == 0, f"Standalone execution failed:\nSTDOUT: {proc.stdout}\nSTDERR: {proc.stderr}"
    assert "STANDALONE_SUCCESS" in proc.stdout
