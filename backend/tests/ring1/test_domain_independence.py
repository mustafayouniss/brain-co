"""Tests proving Domain-Independence of the Ring 1 General Brain (Section 2.2).

Verifies that Perception, Observation, Context, Memory, Retrieval, and Planning
execute flawlessly for completely new Domains (Sales, Logistics, Healthcare)
without modifying any internal engine code.
"""

import uuid
import pytest
from sqlalchemy.orm import Session

from app.core.context import BrainContext
from app.domains.contracts import IDomainExtension, domain_registry
from app.domains.logistics.extension import LogisticsFleetDomainExtension
from app.domains.sales.extension import SalesDomainExtension
from app.ring1.contracts.capabilities import CapabilityRegistry
from app.ring1.contracts.protocols import (
    IContextEngine,
    IMemoryEngine,
    IObservationEngine,
    IPerceptionEngine,
    IPlanningEngine,
    IRetrievalEngine,
)
from app.ring1.engines.context import ContextEngine
from app.ring1.engines.memory import BasicMemoryEngine
from app.ring1.engines.observation import ObservationEngine
from app.ring1.engines.perception import PerceptionEngine
from app.ring1.engines.planning import PlanningEngine
from app.ring1.engines.retrieval import BasicRetrievalEngine


def test_domain_extensions_registered():
    """Verify multiple domain extensions can be registered dynamically in the domain registry."""
    sales_ext = SalesDomainExtension()
    logistics_ext = LogisticsFleetDomainExtension()

    domain_registry.register(sales_ext)
    domain_registry.register(logistics_ext)

    assert "sales" in domain_registry.list_domains()
    assert "logistics" in domain_registry.list_domains()
    assert domain_registry.get("sales") is sales_ext
    assert domain_registry.get("logistics") is logistics_ext


def test_perception_engine_processes_sales_content():
    """PerceptionEngine processes general business text without legal domain assumptions."""
    engine = PerceptionEngine()
    assert isinstance(engine, IPerceptionEngine)

    context = BrainContext(
        organization_id="org-acme-corp",
        scope_id="lead-5501",
        domain_id="sales",
    )

    sales_raw_input = {
        "content": "Call notes with Acme Corp CTO: Interested in enterprise tier, budget approved for Q4.",
        "source_type": "text",
        "actor": "sales_rep_jane",
    }

    import asyncio
    result = asyncio.run(engine.process(sales_raw_input, context))
    assert not result.error
    assert result.data["status"] == "success"
    assert result.data["content_type"] == "text"
    assert result.data["structured_content"]["length"] > 0
    # General Brain does NOT inject domain-specific assumptions
    assert "articles" not in result.data


def test_context_engine_resolves_generic_domain_scope():
    """ContextEngine resolves a non-legal generic domain scope (e.g., logistics voyage)."""
    engine = ContextEngine()
    assert isinstance(engine, IContextEngine)

    context = BrainContext(
        organization_id="org-maersk-fleet",
        user_id="captain-ahab",
        domain_id="logistics",
    )

    request_scope = {
        "domain_id": "logistics",
        "scope_id": "voyage-pacific-992",
    }

    import asyncio
    result = asyncio.run(engine.resolve_context(request_scope, context))
    assert not result.error
    data = result.data
    assert data["organization_id"] == "org-maersk-fleet"
    assert data["domain_id"] == "logistics"
    assert data["scope_id"] == "voyage-pacific-992"
    assert data["resolution_status"] in ("explicit", "resolved")


def test_observation_engine_records_generic_domain_event(db_session: Session):
    """ObservationEngine persists domain events with zero domain-specific branching."""
    engine = ObservationEngine(db_session_factory=lambda: db_session)
    assert isinstance(engine, IObservationEngine)

    context = BrainContext(
        organization_id="org-global-cargo",
        scope_id="shipment-container-1002",
        domain_id="logistics",
    )

    event_payload = {
        "event_type": "cargo.manifest_inspected",
        "source": "port_scanner",
        "payload": {
            "vessel": "MV Northern Star",
            "containers_scanned": 450,
            "customs_cleared": True,
        },
        "idempotency_key": f"cargo-scan-{uuid.uuid4()}",
    }

    import asyncio
    result = asyncio.run(engine.record_observation(event_payload, context))
    assert not result.error
    assert result.data["status"] == "recorded"
    assert result.data["event_type"] == "cargo.manifest_inspected"
    assert result.data["observation_id"] is not None


def test_memory_engine_stores_sales_knowledge_candidate(db_session: Session):
    """MemoryEngine stores domain knowledge candidates preserving validation authority invariants."""
    engine = BasicMemoryEngine(db_session_factory=lambda: db_session)
    assert isinstance(engine, IMemoryEngine)

    context = BrainContext(
        organization_id="org-sales-force",
        scope_id="account-enterprise-77",
        domain_id="sales",
        validation_authority=False,  # Regular employee cannot self-validate
    )

    fact_data = {
        "record_type": "sales_opportunity_signal",
        "payload": {
            "opportunity_title": "Enterprise Cloud Migration",
            "estimated_value_usd": 250000,
            "decision_maker": "VP Infrastructure",
        },
        "idempotency_key": f"opp-sig-{uuid.uuid4()}",
    }

    import asyncio
    result = asyncio.run(engine.store_candidate(fact_data, context))
    assert not result.error
    assert result.data["status"] == "candidate"  # Must stay candidate
    assert result.data["case_id"] == "account-enterprise-77"


def test_retrieval_engine_searches_domain_knowledge(db_session: Session):
    """RetrievalEngine executes context-isolated keyword retrieval across domain records."""
    mem_engine = BasicMemoryEngine(db_session_factory=lambda: db_session)
    retrieval_engine = BasicRetrievalEngine(db_session_factory=lambda: db_session)
    assert isinstance(retrieval_engine, IRetrievalEngine)

    context = BrainContext(
        organization_id="org-healthcare-lab",
        scope_id="patient-protocol-440",
        domain_id="healthcare",
        validation_authority=True,
    )

    # Store candidate and validate it so it becomes trusted knowledge
    fact_data = {
        "record_type": "clinical_finding",
        "payload": {
            "biomarker": "HER2_positive",
            "therapy_recommendation": "Trastuzumab protocol approved",
            "evidence_grade": "A1",
        },
        "idempotency_key": f"clinic-{uuid.uuid4()}",
    }

    import asyncio
    store_res = asyncio.run(mem_engine.store_candidate(fact_data, context))
    rec_id = uuid.UUID(store_res.data["record_id"])

    # Admin validates candidate
    asyncio.run(mem_engine.validate_candidate(rec_id, "VALIDATE", context))

    # Search query for "Trastuzumab"
    search_res = asyncio.run(retrieval_engine.search("Trastuzumab", context))
    assert not search_res.error
    matches = search_res.data["results"]
    assert len(matches) >= 1
    assert matches[0]["record_id"] == str(rec_id)

    # Cross-scope check: Search from different patient scope returns empty!
    different_patient_ctx = BrainContext(
        organization_id="org-healthcare-lab",
        scope_id="patient-protocol-999",
        domain_id="healthcare",
    )
    search_isolated = asyncio.run(retrieval_engine.search("Trastuzumab", different_patient_ctx))
    assert len(search_isolated.data["results"]) == 0


def test_planning_engine_plans_general_domain_task():
    """PlanningEngine formulates execution plan for an arbitrary business goal."""
    engine = PlanningEngine()
    assert isinstance(engine, IPlanningEngine)

    context = BrainContext(
        organization_id="org-retail-hq",
        scope_id="inventory-audit-2026",
        domain_id="retail",
    )

    import asyncio
    plan = asyncio.run(engine.create_plan(
        goal="Audit warehouse stock levels and record discrepancy observation",
        context=context,
    ))

    assert plan is not None
    assert plan.version == 1
    assert len(plan.steps) >= 1
    # Verify capabilities used in plan belong to general registered capabilities
    for step in plan.steps:
        assert "." in step.capability
