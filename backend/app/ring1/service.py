"""Ring 1 Test Execution Service & Thin Façade.

Coordinates live execution of the six Ring 1 engines by delegating to focused services:
- TestScenarioService (live multi-engine scenarios and fault injection)
- PdfPipelineService (PDF extraction, structuring, and case-isolated persistence)
- Ring1TestRunRegistry (thread-safe recent run inspection registry)

Preserves backward compatibility with existing API endpoints and test runners.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator
from datetime import datetime, timezone
from typing import Any
import uuid

from sqlalchemy.orm import Session

from ai.core.services.llm_service import LLMService
from ai.providers.fake_provider import FakeLLMProvider
from app.ring1.contracts.capabilities import CapabilityRegistry
from app.ring1.engines.context import ContextEngine
from app.ring1.engines.memory import BasicMemoryEngine
from app.ring1.engines.observation import ObservationEngine
from app.ring1.engines.perception import PerceptionEngine
from app.ring1.engines.planning import PlanningEngine
from app.ring1.engines.retrieval import BasicRetrievalEngine
from app.ring1.execution.executor import PlanStepExecutor
from app.ring1.mesh.router import MeshRouter
from app.ring1.services.registry import Ring1TestRunRegistry, test_run_registry
from app.ring1.services.pdf_pipeline_service import PdfPipelineService
from app.ring1.services.test_scenario_service import TestScenarioService


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class Ring1TestRunner:
    """Thin façade executing live scenarios across all 6 Ring 1 engines.
    
    Delegates focused domain responsibilities to TestScenarioService and PdfPipelineService.
    """

    def __init__(self, db_session: Session, llm_service: LLMService | None = None) -> None:
        self.db_session = db_session
        self.fake_provider = FakeLLMProvider()
        if llm_service is not None:
            self.llm_service = llm_service
        else:
            try:
                from ai.config.ai_config import ai_config
                self.llm_service = ai_config.create_service()
            except Exception:
                self.llm_service = LLMService(provider=self.fake_provider)

        self.registry = CapabilityRegistry()
        self.router = MeshRouter(registry=self.registry, default_timeout_seconds=15.0)

        session_factory = lambda: self.db_session

        self.perception = PerceptionEngine(llm_service=self.llm_service, mesh_router=self.router)
        self.observation = ObservationEngine(
            db_session_factory=session_factory,
            llm_service=self.llm_service,
            mesh_router=self.router,
        )
        self.context = ContextEngine(llm_service=self.llm_service, mesh_router=self.router)
        self.memory = BasicMemoryEngine(
            db_session_factory=session_factory,
            llm_service=self.llm_service,
            mesh_router=self.router,
        )
        self.retrieval = BasicRetrievalEngine(
            db_session_factory=session_factory,
            memory_engine=self.memory,
            llm_service=self.llm_service,
            mesh_router=self.router,
        )
        self.planning = PlanningEngine(llm_service=self.llm_service, mesh_router=self.router)

        # Register all 6 engines
        self.perception.register_capabilities(self.registry)
        self.observation.register_capabilities(self.registry)
        self.context.register_capabilities(self.registry)
        self.memory.register_capabilities(self.registry)
        self.retrieval.register_capabilities(self.registry)
        self.planning.register_capabilities(self.registry)

        # Plan step executor for genuine runtime execution
        self.executor = PlanStepExecutor(router=self.router, registry=self.registry)

        # Delegate services
        self._scenario_service = TestScenarioService(self)
        self._pdf_service = PdfPipelineService(self)

    async def execute(
        self,
        mode: str = "e2e",
        custom_prompt: str | None = None,
    ) -> AsyncGenerator[dict[str, Any], None]:
        """Delegate scenario execution to TestScenarioService."""
        async for event in self._scenario_service.execute(
            mode=mode,
            custom_prompt=custom_prompt,
        ):
            yield event

    async def execute_pdf(
        self,
        pdf_bytes: bytes,
        filename: str,
        organization_id: str,
        case_id: str,
        mode: str = "normal",
    ) -> AsyncGenerator[dict[str, Any], None]:
        """Delegate PDF ingestion pipeline to PdfPipelineService."""
        async for event in self._pdf_service.execute_pdf(
            pdf_bytes=pdf_bytes,
            filename=filename,
            organization_id=organization_id,
            case_id=case_id,
            mode=mode,
        ):
            yield event

    def query_saved_knowledge(
        self,
        organization_id: str,
        case_id: str,
        query: str = "",
    ) -> list[dict[str, Any]]:
        """Delegate case knowledge query to PdfPipelineService."""
        return self._pdf_service.query_saved_knowledge(
            organization_id=organization_id,
            case_id=case_id,
            query=query,
        )
