"""Shared test fixtures for Ring 1 test suite.

Provides:
- Fake LLM service
- Capability registry
- Mesh router
- Fully wired Ring 1 engines (in-memory and DB-backed)
"""

from __future__ import annotations

import pytest

from ai.core.services.llm_service import LLMService
from ai.providers.fake_provider import FakeLLMProvider
from app.ring1.contracts.capabilities import CapabilityRegistry
from app.ring1.engines.context import ContextEngine
from app.ring1.engines.memory import BasicMemoryEngine
from app.ring1.engines.observation import ObservationEngine
from app.ring1.engines.perception import PerceptionEngine
from app.ring1.engines.planning import PlanningEngine
from app.ring1.engines.retrieval import BasicRetrievalEngine
from app.ring1.mesh.router import MeshRouter


@pytest.fixture
def fake_llm_provider() -> FakeLLMProvider:
    """Deterministic fake LLM provider for testing."""
    return FakeLLMProvider()


@pytest.fixture
def fake_llm_service(fake_llm_provider: FakeLLMProvider) -> LLMService:
    """LLMService wrapping the fake provider."""
    return LLMService(provider=fake_llm_provider)


@pytest.fixture
def capability_registry() -> CapabilityRegistry:
    """Fresh capability registry instance."""
    return CapabilityRegistry()


@pytest.fixture
def mesh_router(capability_registry: CapabilityRegistry) -> MeshRouter:
    """Fresh mesh router instance."""
    return MeshRouter(registry=capability_registry, default_timeout_seconds=5.0)


@pytest.fixture
def ring1_mesh(
    capability_registry: CapabilityRegistry,
    mesh_router: MeshRouter,
    fake_llm_service: LLMService,
) -> dict:
    """A fully configured, fully registered in-memory Ring 1 mesh."""
    perception = PerceptionEngine(llm_service=fake_llm_service, mesh_router=mesh_router)
    observation = ObservationEngine(llm_service=fake_llm_service, mesh_router=mesh_router)
    context = ContextEngine(llm_service=fake_llm_service, mesh_router=mesh_router)
    memory = BasicMemoryEngine(llm_service=fake_llm_service, mesh_router=mesh_router)
    retrieval = BasicRetrievalEngine(
        llm_service=fake_llm_service,
        mesh_router=mesh_router,
        memory_engine=memory,
    )
    planning = PlanningEngine(llm_service=fake_llm_service, mesh_router=mesh_router)

    # Register all capabilities
    perception.register_capabilities(capability_registry)
    observation.register_capabilities(capability_registry)
    context.register_capabilities(capability_registry)
    memory.register_capabilities(capability_registry)
    retrieval.register_capabilities(capability_registry)
    planning.register_capabilities(capability_registry)

    return {
        "registry": capability_registry,
        "router": mesh_router,
        "perception": perception,
        "observation": observation,
        "context": context,
        "memory": memory,
        "retrieval": retrieval,
        "planning": planning,
        "llm_service": fake_llm_service,
    }
