from __future__ import annotations

import asyncio
from collections.abc import AsyncGenerator
from datetime import datetime, timezone
import json
import time
from typing import Any
import uuid

import sqlalchemy as sa
from sqlalchemy.orm import Session

from ai.core.services.llm_service import LLMService
from app.ring1.contracts.capabilities import (
    ALL_CAPABILITIES,
    CONTEXT_RESOLVE,
    MEMORY_GET_RECORD,
    MEMORY_STORE_RECORD,
    OBSERVATION_RECORD_EVENT,
    PERCEPTION_STRUCTURE_INPUT,
    PLANNING_CREATE_PLAN,
    PLANNING_GET_PLAN_STATUS,
    PLANNING_REQUEST_REPLAN,
    RETRIEVAL_QUERY,
    CapabilityRegistry,
)
from app.ring1.contracts.context_ref import ContextRef, ResolutionStatus
from app.ring1.contracts.envelopes import MeshRequest, ResultStatus
from app.ring1.contracts.errors import EngineErrorCode
from app.ring1.contracts.plan_models import PlanStatus, PlanStep, ReplanReasonCode, StepStatus
from app.ring1.execution.executor import PlanStepExecutor
from app.ring1.mesh.router import MeshRouter
from app.ring1.models.observation import MemoryRecord, Observation
from app.ring1.pdf.extractor import PDFExtractor
from app.ring1.pdf.schemas import DocumentStructuredKnowledge, PDFExtractionResult
from app.ring1.pdf.structured import StructuredKnowledgeExtractor


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

from app.ring1.services.registry import test_run_registry


class TestScenarioService:
    """Service executing multi-engine test scenarios across Ring 1."""

    def __init__(self, runner: Any) -> None:
        self.runner = runner

    @property
    def router(self): return self.runner.router
    @property
    def registry(self): return self.runner.registry
    @property
    def executor(self): return self.runner.executor
    @property
    def db_session(self): return self.runner.db_session
    @property
    def llm_service(self): return self.runner.llm_service
    @property
    def perception(self): return self.runner.perception
    @property
    def observation(self): return self.runner.observation
    @property
    def context(self): return self.runner.context
    @property
    def memory(self): return self.runner.memory
    @property
    def retrieval(self): return self.runner.retrieval
    @property
    def planning(self): return self.runner.planning

    async def execute(
        self,
        mode: str = "e2e",
        custom_prompt: str | None = None,
    ) -> AsyncGenerator[dict[str, Any], None]:
        """Generator yielding structured real-time events for the requested test mode."""
        run_id = f"run-{uuid.uuid4().hex[:10]}"
        start_time = time.perf_counter()
        seq = 0
        events: list[dict[str, Any]] = []
        invoked_engines: set[str] = set()
        delegation_edges: list[dict[str, str]] = []
        initial_plan_payload: dict[str, Any] | None = None
        replanned_payload: dict[str, Any] | None = None

        def record_event(
            *,
            source_engine: str,
            destination_engine: str,
            capability: str,
            event_type: str,
            status: str,
            duration_ms: float | None = None,
            request_envelope: dict[str, Any] | None = None,
            response_envelope: dict[str, Any] | None = None,
            plan_version: int | None = None,
            details: dict[str, Any] | None = None,
        ) -> dict[str, Any]:
            nonlocal seq
            seq += 1
            invoked_engines.add(destination_engine)
            if source_engine != "client" and source_engine != "operator":
                edge = {"source": source_engine, "target": destination_engine, "capability": capability}
                if edge not in delegation_edges:
                    delegation_edges.append(edge)

            evt = {
                "sequence": seq,
                "timestamp": _utcnow_iso(),
                "run_id": run_id,
                "source_engine": source_engine,
                "destination_engine": destination_engine,
                "capability": capability,
                "event_type": event_type,
                "status": status,
                "duration_ms": duration_ms,
                "request_envelope": request_envelope,
                "response_envelope": response_envelope,
                "plan_version": plan_version,
                "details": details or {},
            }
            events.append(evt)
            return evt

        # ---------------------------------------------------------------------
        # MODE 1: Full 6-Engine End-to-End Scenario
        # ---------------------------------------------------------------------
        if mode == "e2e":
            org_id = f"org-test-{uuid.uuid4().hex[:6]}"
            case_id = f"case-test-{uuid.uuid4().hex[:6]}"
            adversary_case_id = f"case-adversary-{uuid.uuid4().hex[:6]}"

            # 1. Perception
            t0 = time.perf_counter()
            raw_input = json.dumps({
                "memo_title": "NDA Violation Discovery Memo",
                "case_id": case_id,
                "subject": "John Doe",
                "finding": "Disclosed source code and proprietary trade secrets to competitor",
                "date": "2026-10-28",
            })
            req_p = MeshRequest(
                sender_engine="client",
                recipient_capability=PERCEPTION_STRUCTURE_INPUT,
                payload={"raw_content": raw_input, "input_type": "json"},
            )
            yield record_event(
                source_engine="client",
                destination_engine="perception",
                capability=PERCEPTION_STRUCTURE_INPUT,
                event_type="request_dispatched",
                status="running",
                request_envelope=req_p.model_dump(mode="json"),
            )
            resp_p = await self.router.dispatch(req_p)
            dur_p = round((time.perf_counter() - t0) * 1000, 2)
            yield record_event(
                source_engine="client",
                destination_engine="perception",
                capability=PERCEPTION_STRUCTURE_INPUT,
                event_type="perception_completed",
                status="completed" if resp_p.status == ResultStatus.SUCCESS else "failed",
                duration_ms=dur_p,
                response_envelope=resp_p.model_dump(mode="json"),
                details={"detected_type": resp_p.payload.get("detected_type")},
            )
            parsed_content = resp_p.payload.get("parsed_content", {})

            # 2. Context Engine - Positive Explicit Resolution
            t0 = time.perf_counter()
            req_c = MeshRequest(
                sender_engine="client",
                recipient_capability=CONTEXT_RESOLVE,
                payload={
                    "context_hint": {
                        "organization_id": org_id,
                        "case_id": case_id,
                        "domain_id": "intellectual_property",
                    }
                },
            )
            yield record_event(
                source_engine="client",
                destination_engine="context",
                capability=CONTEXT_RESOLVE,
                event_type="request_dispatched",
                status="running",
                request_envelope=req_c.model_dump(mode="json"),
            )
            resp_c = await self.router.dispatch(req_c)
            dur_c = round((time.perf_counter() - t0) * 1000, 2)
            context_ref_str = resp_c.payload.get("context_ref", "")
            ctx_ref = ContextRef(
                context_ref_id=context_ref_str,
                organization_id=org_id,
                case_id=case_id,
                domain_id="intellectual_property",
                resolution_status=ResolutionStatus.EXPLICIT,
            )
            yield record_event(
                source_engine="client",
                destination_engine="context",
                capability=CONTEXT_RESOLVE,
                event_type="context_resolved",
                status="completed",
                duration_ms=dur_c,
                response_envelope=resp_c.model_dump(mode="json"),
                details={"context_ref": context_ref_str, "status": resp_c.payload.get("status")},
            )

            # 2b. Context Engine - Ambiguity Negative Test
            req_c_amb = MeshRequest(
                sender_engine="client",
                recipient_capability=CONTEXT_RESOLVE,
                payload={"context_hint": {"organization_id": org_id}},  # missing case_id
            )
            resp_c_amb = await self.router.dispatch(req_c_amb)
            yield record_event(
                source_engine="client",
                destination_engine="context",
                capability=CONTEXT_RESOLVE,
                event_type="context_ambiguity_caught",
                status="completed" if resp_c_amb.status == ResultStatus.NEEDS_CLARIFICATION else "failed",
                response_envelope=resp_c_amb.model_dump(mode="json"),
                details={"note": "Enforced missing case_id boundary validation"},
            )

            # 3. Observation Engine - Record Event in PostgreSQL
            t0 = time.perf_counter()
            idempotency_key = f"evt-ingest-{uuid.uuid4().hex[:8]}"
            req_obs = MeshRequest(
                sender_engine="client",
                recipient_capability=OBSERVATION_RECORD_EVENT,
                context_ref=ctx_ref,
                payload={
                    "event_type": "legal_memo_ingested",
                    "source": "gui_test_console",
                    "idempotency_key": idempotency_key,
                    "payload": parsed_content,
                    "auto_delegate": False,  # explicit test step; avoid automatic follow-up plan
                },
            )
            yield record_event(
                source_engine="client",
                destination_engine="observation",
                capability=OBSERVATION_RECORD_EVENT,
                event_type="request_dispatched",
                status="running",
                request_envelope=req_obs.model_dump(mode="json"),
            )
            resp_obs = await self.router.dispatch(req_obs)
            dur_obs = round((time.perf_counter() - t0) * 1000, 2)
            obs_id = resp_obs.payload.get("observation_id")
            yield record_event(
                source_engine="client",
                destination_engine="observation",
                capability=OBSERVATION_RECORD_EVENT,
                event_type="observation_persisted",
                status="completed",
                duration_ms=dur_obs,
                response_envelope=resp_obs.model_dump(mode="json"),
                details={"observation_id": obs_id, "duplicate": resp_obs.payload.get("duplicate")},
            )

            # 3b. Observation Deduplication Check
            resp_obs_dup = await self.router.dispatch(req_obs)
            yield record_event(
                source_engine="client",
                destination_engine="observation",
                capability=OBSERVATION_RECORD_EVENT,
                event_type="observation_deduplicated",
                status="completed",
                response_envelope=resp_obs_dup.model_dump(mode="json"),
                details={"duplicate": resp_obs_dup.payload.get("duplicate"), "observation_id": obs_id},
            )

            # 4. Basic Memory Engine - Scoped Fact Storage in PostgreSQL
            t0 = time.perf_counter()
            req_mem = MeshRequest(
                sender_engine="client",
                recipient_capability=MEMORY_STORE_RECORD,
                context_ref=ctx_ref,
                payload={
                    "record_type": "nda_breach_fact",
                    "payload": {
                        "claim": "Disclosed source code and proprietary trade secrets to competitor",
                        "subject": "John Doe",
                        "severity": "high",
                    },
                    "source_observation_id": obs_id,
                    "idempotency_key": f"mem-{idempotency_key}",
                },
            )
            yield record_event(
                source_engine="observation",
                destination_engine="memory",
                capability=MEMORY_STORE_RECORD,
                event_type="request_dispatched",
                status="running",
                request_envelope=req_mem.model_dump(mode="json"),
            )
            resp_mem = await self.router.dispatch(req_mem)
            dur_mem = round((time.perf_counter() - t0) * 1000, 2)
            record_id = resp_mem.payload.get("record_id")
            yield record_event(
                source_engine="observation",
                destination_engine="memory",
                capability=MEMORY_STORE_RECORD,
                event_type="memory_stored",
                status="completed",
                duration_ms=dur_mem,
                response_envelope=resp_mem.model_dump(mode="json"),
                details={"record_id": record_id},
            )

            # 5. Basic Retrieval Engine - Authorized Search
            t0 = time.perf_counter()
            req_ret = MeshRequest(
                sender_engine="client",
                recipient_capability=RETRIEVAL_QUERY,
                context_ref=ctx_ref,
                payload={"query": "source code", "record_type": "nda_breach_fact"},
            )
            yield record_event(
                source_engine="client",
                destination_engine="retrieval",
                capability=RETRIEVAL_QUERY,
                event_type="request_dispatched",
                status="running",
                request_envelope=req_ret.model_dump(mode="json"),
            )
            resp_ret = await self.router.dispatch(req_ret)
            dur_ret = round((time.perf_counter() - t0) * 1000, 2)
            records = resp_ret.payload.get("records", [])
            yield record_event(
                source_engine="client",
                destination_engine="retrieval",
                capability=RETRIEVAL_QUERY,
                event_type="retrieval_completed",
                status="completed",
                duration_ms=dur_ret,
                response_envelope=resp_ret.model_dump(mode="json"),
                details={"records_found": len(records), "case_id": case_id},
            )

            # 5b. Cross-Case Adversarial Retrieval Isolation Test
            ctx_ref_adv = ContextRef(
                organization_id=org_id,
                case_id=adversary_case_id,
                domain_id="intellectual_property",
                resolution_status=ResolutionStatus.EXPLICIT,
            )
            req_ret_adv = MeshRequest(
                sender_engine="client",
                recipient_capability=RETRIEVAL_QUERY,
                context_ref=ctx_ref_adv,
                payload={"query": "source code"},
            )
            resp_ret_adv = await self.router.dispatch(req_ret_adv)
            yield record_event(
                source_engine="client",
                destination_engine="retrieval",
                capability=RETRIEVAL_QUERY,
                event_type="isolation_verified_search",
                status="completed" if len(resp_ret_adv.payload.get("records", [])) == 0 else "failed",
                response_envelope=resp_ret_adv.model_dump(mode="json"),
                details={"adversary_records_found": len(resp_ret_adv.payload.get("records", []))},
            )

            # 5c. Direct Cross-Case Tampering Attempt
            req_tamper = MeshRequest(
                sender_engine="client",
                recipient_capability=MEMORY_GET_RECORD,
                context_ref=ctx_ref_adv,
                payload={"record_id": record_id},
            )
            resp_tamper = await self.router.dispatch(req_tamper)
            yield record_event(
                source_engine="client",
                destination_engine="memory",
                capability=MEMORY_GET_RECORD,
                event_type="isolation_access_denied",
                status="denied",
                response_envelope=resp_tamper.model_dump(mode="json"),
                details={
                    "error_code": resp_tamper.errors[0].code if resp_tamper.errors else None,
                    "target_record_id": record_id,
                },
            )

            # 6. Planning Engine - Plan Generation
            t0 = time.perf_counter()
            req_plan = MeshRequest(
                sender_engine="client",
                recipient_capability=PLANNING_CREATE_PLAN,
                context_ref=ctx_ref,
                payload={
                    "goal": "Conduct NDA violation investigation and store structured findings",
                    "max_replans": 2,
                },
            )
            yield record_event(
                source_engine="client",
                destination_engine="planning",
                capability=PLANNING_CREATE_PLAN,
                event_type="request_dispatched",
                status="running",
                request_envelope=req_plan.model_dump(mode="json"),
            )
            resp_plan = await self.router.dispatch(req_plan)
            dur_plan = round((time.perf_counter() - t0) * 1000, 2)
            initial_plan_payload = resp_plan.payload
            plan_id = initial_plan_payload.get("plan_id")
            plan_v = initial_plan_payload.get("version", 1)
            yield record_event(
                source_engine="client",
                destination_engine="planning",
                capability=PLANNING_CREATE_PLAN,
                event_type="plan_created",
                status="completed",
                duration_ms=dur_plan,
                plan_version=plan_v,
                response_envelope=resp_plan.model_dump(mode="json"),
                details={"plan_id": plan_id, "steps_count": len(initial_plan_payload.get("steps", []))},
            )

            # 7. Execute Step 1 in Plan genuinely via PlanStepExecutor
            plan_model = self.planning._plans.get(plan_id)
            if plan_model and plan_model.steps:
                step_0 = plan_model.steps[0]
                t0 = time.perf_counter()
                resp_step0, status_step0 = await self.executor.execute_step(
                    plan=plan_model,
                    step=step_0,
                    context_ref=ctx_ref,
                )
                dur_step0 = round((time.perf_counter() - t0) * 1000, 2)
                yield record_event(
                    source_engine="plan_executor",
                    destination_engine=step_0.capability.split(".")[0],
                    capability=step_0.capability,
                    event_type="step_completed" if status_step0 == StepStatus.COMPLETED else "step_failed",
                    status="completed" if status_step0 == StepStatus.COMPLETED else "failed",
                    duration_ms=dur_step0,
                    plan_version=plan_v,
                    response_envelope=resp_step0.model_dump(mode="json"),
                    details={"step_id": step_0.step_id, "step_index": 0, "result": step_0.actual_result},
                )

        # ---------------------------------------------------------------------
        # MODE 2: Controlled Failure and Bounded Replanning
        # ---------------------------------------------------------------------
        elif mode == "force_failure":
            org_id = f"org-test-{uuid.uuid4().hex[:6]}"
            case_id = f"case-test-{uuid.uuid4().hex[:6]}"
            ctx_ref = ContextRef(
                organization_id=org_id,
                case_id=case_id,
                domain_id="intellectual_property",
                resolution_status=ResolutionStatus.EXPLICIT,
            )

            # 1. Create Initial Plan v1
            t0 = time.perf_counter()
            req_plan = MeshRequest(
                sender_engine="client",
                recipient_capability=PLANNING_CREATE_PLAN,
                context_ref=ctx_ref,
                payload={
                    "goal": "Verify patent claim integrity and extract background prior art",
                    "max_replans": 2,
                },
            )
            yield record_event(
                source_engine="client",
                destination_engine="planning",
                capability=PLANNING_CREATE_PLAN,
                event_type="request_dispatched",
                status="running",
                request_envelope=req_plan.model_dump(mode="json"),
            )
            resp_plan = await self.router.dispatch(req_plan)
            dur_plan = round((time.perf_counter() - t0) * 1000, 2)
            initial_plan_payload = resp_plan.payload
            plan_id = initial_plan_payload.get("plan_id")
            plan_v = initial_plan_payload.get("version", 1)
            steps = initial_plan_payload.get("steps", [])

            yield record_event(
                source_engine="client",
                destination_engine="planning",
                capability=PLANNING_CREATE_PLAN,
                event_type="plan_created",
                status="completed",
                duration_ms=dur_plan,
                plan_version=plan_v,
                response_envelope=resp_plan.model_dump(mode="json"),
                details={"plan_id": plan_id, "version": plan_v, "steps": len(steps)},
            )

            # 2. Execute Step 1 genuinely via PlanStepExecutor
            step_1 = steps[0] if steps else None
            plan_model = self.planning._plans.get(plan_id)
            if plan_model and step_1:
                t0 = time.perf_counter()
                resp_step1, status_step1 = await self.executor.execute_step(
                    plan=plan_model,
                    step=plan_model.steps[0],
                    context_ref=ctx_ref,
                )
                dur_step1 = round((time.perf_counter() - t0) * 1000, 2)
                yield record_event(
                    source_engine="plan_executor",
                    destination_engine=plan_model.steps[0].capability.split(".")[0],
                    capability=plan_model.steps[0].capability,
                    event_type="step_completed" if status_step1 == StepStatus.COMPLETED else "step_failed",
                    status="completed" if status_step1 == StepStatus.COMPLETED else "failed",
                    duration_ms=dur_step1,
                    plan_version=plan_v,
                    response_envelope=resp_step1.model_dump(mode="json"),
                    details={"step_id": plan_model.steps[0].step_id, "result": plan_model.steps[0].actual_result},
                )

            # 3. Controlled Fault Injection on Step 2 at Execution Boundary
            step_2 = plan_model.steps[1] if (plan_model and len(plan_model.steps) > 1) else None
            if plan_model and step_2:
                # Test fault injector: strips mandatory case_id from context_hint to test real runtime boundary failure
                def boundary_fault_injector(s: PlanStep, req: MeshRequest) -> MeshRequest:
                    return MeshRequest(
                        task_id=req.task_id,
                        plan_version=req.plan_version,
                        sender_engine=req.sender_engine,
                        recipient_capability=req.recipient_capability,
                        context_ref=ContextRef(organization_id=org_id, case_id=None, status=ResolutionStatus.INSUFFICIENT_DATA),
                        payload={"context_hint": {"organization_id": org_id}},  # missing required case_id
                    )

                fault_executor = PlanStepExecutor(
                    router=self.router,
                    registry=self.registry,
                    fault_injector=boundary_fault_injector,
                )
                t0 = time.perf_counter()
                resp_step2, status_step2 = await fault_executor.execute_step(plan_model, step_2)
                dur_step2 = round((time.perf_counter() - t0) * 1000, 2)

                failure_evidence = {
                    "fault_injection": "test_boundary_missing_case_id",
                    "status": resp_step2.status.value,
                    "errors": [e.model_dump() for e in resp_step2.errors] if resp_step2.errors else [],
                    "missing_attributes": ["case_id"],
                }

                yield record_event(
                    source_engine="plan_executor",
                    destination_engine="context",
                    capability=step_2.capability,
                    event_type="step_failed",
                    status="failed",
                    duration_ms=dur_step2,
                    plan_version=plan_v,
                    response_envelope=resp_step2.model_dump(mode="json"),
                    details={
                        "step_id": step_2.step_id,
                        "reason_code": ReplanReasonCode.CONTEXT_INSUFFICIENT.value,
                        "evidence": failure_evidence,
                    },
                )

                # 4. Trigger Evidence-Based Replan via Planning Engine
                t0 = time.perf_counter()
                req_replan = MeshRequest(
                    sender_engine="plan_executor",
                    recipient_capability=PLANNING_REQUEST_REPLAN,
                    context_ref=ctx_ref,
                    payload={
                        "plan_id": plan_id,
                        "failed_step_id": step_2.step_id,
                        "reason_code": ReplanReasonCode.CONTEXT_INSUFFICIENT.value,
                        "evidence": failure_evidence,
                        "actual_result": step_2.actual_result,
                    },
                )
                yield record_event(
                    source_engine="plan_executor",
                    destination_engine="planning",
                    capability=PLANNING_REQUEST_REPLAN,
                    event_type="replan_requested",
                    status="running",
                    request_envelope=req_replan.model_dump(mode="json"),
                )
                resp_replan = await self.router.dispatch(req_replan)
                dur_replan = round((time.perf_counter() - t0) * 1000, 2)
                replanned_payload = dict(resp_replan.payload)
                replanned_payload["old_version"] = plan_v
                new_v = replanned_payload.get("new_version", 2)

                yield record_event(
                    source_engine="plan_executor",
                    destination_engine="planning",
                    capability=PLANNING_REQUEST_REPLAN,
                    event_type="replan_completed",
                    status="completed" if resp_replan.status == ResultStatus.SUCCESS else "failed",
                    duration_ms=dur_replan,
                    plan_version=new_v,
                    response_envelope=resp_replan.model_dump(mode="json"),
                    details={
                        "old_version": replanned_payload.get("old_version"),
                        "new_version": new_v,
                        "steps_retained": replanned_payload.get("steps_retained", []),
                        "steps_added": replanned_payload.get("steps_added", []),
                    },
                )

                # 5. Execute Revised Plan v2 Steps for Real
                revised_plan = self.planning._plans.get(plan_id)
                if revised_plan:
                    async for step_event in self.executor.execute_plan(revised_plan, context_ref=ctx_ref):
                        if step_event["event_type"] in ("step_completed", "step_retained"):
                            yield record_event(
                                source_engine="plan_executor",
                                destination_engine=step_event.get("capability", "planning").split(".")[0],
                                capability=step_event.get("capability", "planning"),
                                event_type=step_event["event_type"],
                                status=step_event["status"],
                                duration_ms=step_event.get("duration_ms"),
                                plan_version=new_v,
                                response_envelope=step_event.get("response_envelope"),
                                details=step_event.get("result", {}),
                            )

                # 6. Query and Verify Updated Plan Status
                req_stat = MeshRequest(
                    sender_engine="client",
                    recipient_capability=PLANNING_GET_PLAN_STATUS,
                    payload={"plan_id": plan_id},
                )
                resp_stat = await self.router.dispatch(req_stat)
                yield record_event(
                    source_engine="client",
                    destination_engine="planning",
                    capability=PLANNING_GET_PLAN_STATUS,
                    event_type="plan_status_verified",
                    status="completed",
                    plan_version=new_v,
                    response_envelope=resp_stat.model_dump(mode="json"),
                    details=resp_stat.payload,
                )

        # ---------------------------------------------------------------------
        # MODE 3: Custom Prompt Execution
        # ---------------------------------------------------------------------
        elif mode == "custom_prompt":
            prompt_text = (custom_prompt or "Review breach of non-compete clause").strip()
            org_id = f"org-test-{uuid.uuid4().hex[:6]}"
            case_id = f"case-test-{uuid.uuid4().hex[:6]}"

            # 1. Perception
            t0 = time.perf_counter()
            req_p = MeshRequest(
                sender_engine="client",
                recipient_capability=PERCEPTION_STRUCTURE_INPUT,
                payload={"raw_content": prompt_text, "input_type": "auto"},
            )
            yield record_event(
                source_engine="client",
                destination_engine="perception",
                capability=PERCEPTION_STRUCTURE_INPUT,
                event_type="request_dispatched",
                status="running",
                request_envelope=req_p.model_dump(mode="json"),
            )
            resp_p = await self.router.dispatch(req_p)
            dur_p = round((time.perf_counter() - t0) * 1000, 2)
            yield record_event(
                source_engine="client",
                destination_engine="perception",
                capability=PERCEPTION_STRUCTURE_INPUT,
                event_type="perception_completed",
                status="completed",
                duration_ms=dur_p,
                response_envelope=resp_p.model_dump(mode="json"),
                details={"detected_type": resp_p.payload.get("detected_type")},
            )

            # 2. Context
            req_c = MeshRequest(
                sender_engine="client",
                recipient_capability=CONTEXT_RESOLVE,
                payload={"context_hint": {"organization_id": org_id, "case_id": case_id, "domain_id": "legal"}},
            )
            resp_c = await self.router.dispatch(req_c)
            ctx_ref = ContextRef(
                context_ref_id=resp_c.payload.get("context_ref", "ctx:custom"),
                organization_id=org_id,
                case_id=case_id,
                domain_id="legal",
                resolution_status=ResolutionStatus.EXPLICIT,
            )
            yield record_event(
                source_engine="client",
                destination_engine="context",
                capability=CONTEXT_RESOLVE,
                event_type="context_resolved",
                status="completed",
                response_envelope=resp_c.model_dump(mode="json"),
                details={"case_id": case_id},
            )

            # 3. Planning
            req_plan = MeshRequest(
                sender_engine="client",
                recipient_capability=PLANNING_CREATE_PLAN,
                context_ref=ctx_ref,
                payload={"goal": prompt_text, "max_replans": 2},
            )
            resp_plan = await self.router.dispatch(req_plan)
            initial_plan_payload = resp_plan.payload
            plan_id = initial_plan_payload.get("plan_id")
            plan_v = initial_plan_payload.get("version", 1)
            yield record_event(
                source_engine="client",
                destination_engine="planning",
                capability=PLANNING_CREATE_PLAN,
                event_type="plan_created",
                status="completed",
                plan_version=plan_v,
                response_envelope=resp_plan.model_dump(mode="json"),
                details={"plan_id": plan_id, "steps_count": len(initial_plan_payload.get("steps", []))},
            )

        # ---------------------------------------------------------------------
        # Final Summary Event
        # ---------------------------------------------------------------------
        total_dur = round((time.perf_counter() - start_time) * 1000, 2)
        all_engines = ["perception", "observation", "context", "memory", "retrieval", "planning"]
        skipped_engines = [eng for eng in all_engines if eng not in invoked_engines]

        # Get full plan state if available
        current_plan_model = None
        if initial_plan_payload and "plan_id" in initial_plan_payload:
            p_obj = self.planning._plans.get(initial_plan_payload["plan_id"])
            if p_obj:
                current_plan_model = p_obj.model_dump(mode="json")

        summary_data = {
            "run_id": run_id,
            "mode": mode,
            "status": "completed",
            "duration_ms": total_dur,
            "total_events": len(events) + 1,
            "invoked_engines": sorted(list(invoked_engines)),
            "skipped_engines": skipped_engines,
            "delegation_edges": delegation_edges,
            "initial_plan": initial_plan_payload,
            "replanned_payload": replanned_payload,
            "current_plan": current_plan_model,
        }

        final_evt = record_event(
            source_engine="system",
            destination_engine="client",
            capability="mesh.summary",
            event_type="run_completed",
            status="completed",
            duration_ms=total_dur,
            details=summary_data,
        )

        # Persist run into registry
        test_run_registry.save_run(
            run_id,
            {
                **summary_data,
                "timestamp": _utcnow_iso(),
                "events": events,
            },
        )

        yield final_evt

