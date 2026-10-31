"""Tests verifying backward compatibility shims in backend/app/ring1 and backend/app/domains."""

from __future__ import annotations

import pytest

# General Brain Canonical
import brain.general.contracts.context as canon_ctx
import brain.general.contracts.domain as canon_domain
import brain.general.contracts.envelopes as canon_env
import brain.general.contracts.errors as canon_err
import brain.general.contracts.plan_models as canon_plan
import brain.general.contracts.protocols as canon_proto
import brain.general.engines.context as canon_eng_ctx
import brain.general.engines.memory as canon_eng_mem
import brain.general.engines.observation as canon_eng_obs
import brain.general.engines.perception as canon_eng_perc
import brain.general.engines.planning as canon_eng_plan
import brain.general.engines.retrieval as canon_eng_ret
import brain.general.policies.handoff as canon_handoff
import brain.general.runtime.dispatcher as canon_dispatcher
import brain.general.runtime.executor as canon_executor
import brain.general.runtime.router as canon_router
import brain.extensions.legal as canon_legal
import brain.extensions.logistics as canon_logistics
import brain.extensions.sales as canon_sales

import brain.general.contracts.capabilities as canon_caps

# Legacy Shims
import app.core.context as shim_ctx
import app.core.dispatcher as shim_core_dispatcher
import app.core.handoff as shim_core_handoff
import app.domains.contracts as shim_domain_contracts
import app.domains.legal as shim_legal
import app.domains.logistics as shim_logistics
import app.domains.sales as shim_sales
import app.ring1.contracts.capabilities as shim_caps
import app.ring1.contracts.context_ref as shim_context_ref
import app.ring1.contracts.envelopes as shim_env
import app.ring1.contracts.errors as shim_err
import app.ring1.contracts.plan_models as shim_plan_models
import app.ring1.contracts.protocols as shim_proto
import app.ring1.engines.context as shim_eng_ctx
import app.ring1.engines.memory as shim_eng_mem
import app.ring1.engines.observation as shim_eng_obs
import brain.general.engines.observation as canon_eng_obs_module
import app.ring1.engines.perception as shim_eng_perc
import app.ring1.engines.planning as shim_eng_plan
import app.ring1.engines.retrieval as shim_eng_ret
import app.ring1.execution.executor as shim_executor
import app.ring1.mesh.router as shim_router


def test_core_and_contracts_preserve_exact_identity():
    """Verify that contracts and domain-independent components preserve exact class identity."""
    assert shim_ctx.BrainContext is canon_ctx.BrainContext
    assert shim_core_handoff.HandoffPolicy is canon_handoff.HandoffPolicy
    assert shim_core_dispatcher.RuntimeDispatcher is canon_dispatcher.RuntimeDispatcher
    assert shim_domain_contracts.IDomainExtension is canon_domain.IDomainExtension

    # Envelopes & Capabilities
    assert shim_env.MeshRequest is canon_env.MeshRequest
    assert shim_env.MeshResponse is canon_env.MeshResponse
    assert shim_env.ResultStatus is canon_env.ResultStatus
    assert shim_caps.CapabilityRegistry is canon_caps.CapabilityRegistry

    # Engines without storage adapters
    assert shim_eng_perc.PerceptionEngine is canon_eng_perc.PerceptionEngine
    assert shim_eng_ctx.ContextEngine is canon_eng_ctx.ContextEngine
    assert shim_eng_plan.PlanningEngine is canon_eng_plan.PlanningEngine

    # Runtime
    assert shim_router.MeshRouter is canon_router.MeshRouter
    assert shim_executor.PlanStepExecutor is canon_executor.PlanStepExecutor


def test_domain_extensions_preserve_exact_identity():
    """Verify that domain extension implementations preserve exact class identity."""
    assert shim_legal.LegalDomainExtension is canon_legal.LegalDomainExtension
    assert shim_sales.SalesDomainExtension is canon_sales.SalesDomainExtension
    assert shim_logistics.LogisticsFleetDomainExtension is canon_logistics.LogisticsFleetDomainExtension


def test_storage_backed_engine_compatibility_hierarchy():
    """Verify that legacy storage-backed engines inherit from canonical engines."""
    from brain.general.stores import (
        InMemoryObservationStore,
        InMemoryMemoryStore,
        InMemoryRetrievalStore,
    )

    # Observation
    assert issubclass(shim_eng_obs.ObservationEngine, canon_eng_obs.ObservationEngine)
    obs_inst = shim_eng_obs.ObservationEngine(store=InMemoryObservationStore())
    assert isinstance(obs_inst, canon_eng_obs.ObservationEngine)

    # Memory
    assert issubclass(shim_eng_mem.BasicMemoryEngine, canon_eng_mem.BasicMemoryEngine)
    mem_inst = shim_eng_mem.BasicMemoryEngine(store=InMemoryMemoryStore())
    assert isinstance(mem_inst, canon_eng_mem.BasicMemoryEngine)

    # Retrieval
    assert issubclass(shim_eng_ret.BasicRetrievalEngine, canon_eng_ret.BasicRetrievalEngine)
    ret_inst = shim_eng_ret.BasicRetrievalEngine(
        store=InMemoryRetrievalStore(memory_store=InMemoryMemoryStore())
    )
    assert isinstance(ret_inst, canon_eng_ret.BasicRetrievalEngine)
