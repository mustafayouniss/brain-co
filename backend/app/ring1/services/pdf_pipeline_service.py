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


class PdfPipelineService:
    """Service managing PDF document ingestion, extraction, and persistence."""

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

    async def execute_pdf(
        self,
        pdf_bytes: bytes,
        filename: str,
        organization_id: str,
        case_id: str,
        mode: str = "normal",
    ) -> AsyncGenerator[dict[str, Any], None]:
        """Generator yielding structured real-time events for real PDF ingestion and knowledge persistence.

        Pipeline sequence:
        PDF Bytes -> PDFExtractor -> StructuredKnowledgeExtractor -> Perception ->
        Observation (PostgreSQL) -> Context -> Planning -> PlanStepExecutor (Memory in PostgreSQL,
        Retrieval) -> Separate Retrieval Verification -> Final Scorecard.
        """
        run_id = f"pdf-run-{uuid.uuid4().hex[:10]}"
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
            if source_engine not in ("client", "operator", "system"):
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

        # ContextRef for this run
        ctx_ref = ContextRef(
            context_ref_id=f"ctx:pdf:{case_id}",
            organization_id=organization_id,
            case_id=case_id,
            domain_id="legal",
            resolution_status=ResolutionStatus.EXPLICIT,
        )

        # -------------------------------------------------------------
        # 1. Extraction: Real PDF Parsing & Validation
        # -------------------------------------------------------------
        t0 = time.perf_counter()
        yield record_event(
            source_engine="client",
            destination_engine="extractor",
            capability="pdf.extract_text",
            event_type="extraction_started",
            status="running",
            details={"filename": filename, "bytes_count": len(pdf_bytes)},
        )

        extractor = PDFExtractor()
        try:
            extraction_res: PDFExtractionResult = extractor.extract(pdf_bytes, filename=filename)
        except Exception as exc:
            dur_ext = round((time.perf_counter() - t0) * 1000, 2)
            yield record_event(
                source_engine="client",
                destination_engine="extractor",
                capability="pdf.extract_text",
                event_type="extraction_failed",
                status="failed",
                duration_ms=dur_ext,
                details={"errors": [str(exc)], "filename": filename},
            )
            total_dur = round((time.perf_counter() - start_time) * 1000, 2)
            summary_fail = {
                "run_id": run_id,
                "mode": mode,
                "status": "failed",
                "duration_ms": total_dur,
                "total_events": len(events) + 1,
                "invoked_engines": sorted(list(invoked_engines)),
                "skipped_engines": [],
                "delegation_edges": delegation_edges,
                "error": str(exc),
            }
            final_evt = record_event(
                source_engine="system",
                destination_engine="client",
                capability="mesh.summary",
                event_type="run_completed",
                status="failed",
                duration_ms=total_dur,
                details=summary_fail,
            )
            test_run_registry.save_run(run_id, {**summary_fail, "timestamp": _utcnow_iso(), "events": events})
            yield final_evt
            return

        dur_ext = round((time.perf_counter() - t0) * 1000, 2)

        if extraction_res.errors:
            yield record_event(
                source_engine="client",
                destination_engine="extractor",
                capability="pdf.extract_text",
                event_type="extraction_failed",
                status="failed",
                duration_ms=dur_ext,
                details={"errors": extraction_res.errors, "filename": filename},
            )
            total_dur = round((time.perf_counter() - start_time) * 1000, 2)
            summary_fail = {
                "run_id": run_id,
                "mode": mode,
                "status": "failed",
                "duration_ms": total_dur,
                "total_events": len(events) + 1,
                "invoked_engines": sorted(list(invoked_engines)),
                "skipped_engines": [],
                "delegation_edges": delegation_edges,
                "error": extraction_res.errors[0] if extraction_res.errors else "Extraction failed",
            }
            final_evt = record_event(
                source_engine="system",
                destination_engine="client",
                capability="mesh.summary",
                event_type="run_completed",
                status="failed",
                duration_ms=total_dur,
                details=summary_fail,
            )
            test_run_registry.save_run(run_id, {**summary_fail, "timestamp": _utcnow_iso(), "events": events})
            yield final_evt
            return

        yield record_event(
            source_engine="client",
            destination_engine="extractor",
            capability="pdf.extract_text",
            event_type="extraction_completed",
            status="completed",
            duration_ms=dur_ext,
            details={
                "pages_count": len(extraction_res.pages),
                "total_characters": extraction_res.total_characters,
                "file_hash": extraction_res.file_hash,
                "requires_ocr": extraction_res.requires_ocr,
                "warnings": extraction_res.warnings,
            },
        )

        # -------------------------------------------------------------
        # 2. Structured Knowledge Extraction
        # -------------------------------------------------------------
        t0 = time.perf_counter()
        knowledge_extractor = StructuredKnowledgeExtractor(llm_service=self.llm_service)
        structured_doc: DocumentStructuredKnowledge = await knowledge_extractor.extract(extraction_res)
        dur_struct = round((time.perf_counter() - t0) * 1000, 2)

        yield record_event(
            source_engine="extractor",
            destination_engine="perception",
            capability="pdf.structure_knowledge",
            event_type="knowledge_structured",
            status="completed",
            duration_ms=dur_struct,
            details={
                "document_title": structured_doc.title,
                "document_type": structured_doc.document_type,
                "facts_count": len(structured_doc.facts),
                "entities_count": len(structured_doc.entities),
                "obligations_count": len(structured_doc.obligations),
                "summary": structured_doc.summary,
            },
        )

        # -------------------------------------------------------------
        # 3. Perception Engine: Structure Input Representation
        # -------------------------------------------------------------
        t0 = time.perf_counter()
        req_p = MeshRequest(
            sender_engine="client",
            recipient_capability=PERCEPTION_STRUCTURE_INPUT,
            context_ref=ctx_ref,
            payload={
                "raw_content": extraction_res.combined_text[:4000],
                "input_type": "text",
                "metadata": {
                    "filename": filename,
                    "pages_count": len(extraction_res.pages),
                    "file_hash": extraction_res.file_hash,
                    "document_title": structured_doc.title,
                },
            },
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

        # -------------------------------------------------------------
        # 4. Observation Engine: Ingest Event Recorded in PostgreSQL
        # -------------------------------------------------------------
        t0 = time.perf_counter()
        obs_idempotency_key = f"evt-pdf-{extraction_res.file_hash[:16]}-{case_id[:8]}"
        req_obs = MeshRequest(
            sender_engine="perception",
            recipient_capability=OBSERVATION_RECORD_EVENT,
            context_ref=ctx_ref,
            payload={
                "event_type": "pdf_document_ingested",
                "source": "pdf_extractor",
                "idempotency_key": obs_idempotency_key,
                "payload": {
                    "filename": filename,
                    "file_hash": extraction_res.file_hash,
                    "pages_count": len(extraction_res.pages),
                    "facts_count": len(structured_doc.facts),
                    "entities_count": len(structured_doc.entities),
                    "obligations_count": len(structured_doc.obligations),
                    "document_title": structured_doc.title,
                },
                "auto_delegate": False,
            },
        )
        yield record_event(
            source_engine="perception",
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
            source_engine="perception",
            destination_engine="observation",
            capability=OBSERVATION_RECORD_EVENT,
            event_type="observation_persisted",
            status="completed" if resp_obs.status == ResultStatus.SUCCESS else "failed",
            duration_ms=dur_obs,
            response_envelope=resp_obs.model_dump(mode="json"),
            details={"observation_id": obs_id, "duplicate": resp_obs.payload.get("duplicate")},
        )

        # -------------------------------------------------------------
        # 5. Context Engine: Resolve & Verify Explicit Case Boundaries
        # -------------------------------------------------------------
        t0 = time.perf_counter()
        req_c = MeshRequest(
            sender_engine="observation",
            recipient_capability=CONTEXT_RESOLVE,
            payload={
                "context_hint": {
                    "organization_id": organization_id,
                    "case_id": case_id,
                    "domain_id": "legal",
                }
            },
        )
        yield record_event(
            source_engine="observation",
            destination_engine="context",
            capability=CONTEXT_RESOLVE,
            event_type="request_dispatched",
            status="running",
            request_envelope=req_c.model_dump(mode="json"),
        )
        resp_c = await self.router.dispatch(req_c)
        dur_c = round((time.perf_counter() - t0) * 1000, 2)
        yield record_event(
            source_engine="observation",
            destination_engine="context",
            capability=CONTEXT_RESOLVE,
            event_type="context_resolved",
            status="completed" if resp_c.status == ResultStatus.SUCCESS else "failed",
            duration_ms=dur_c,
            response_envelope=resp_c.model_dump(mode="json"),
            details={"case_id": case_id, "organization_id": organization_id},
        )

        # -------------------------------------------------------------
        # 6. Planning Engine: Create Knowledge Ingestion Plan
        # -------------------------------------------------------------
        t0 = time.perf_counter()
        req_plan = MeshRequest(
            sender_engine="client",
            recipient_capability=PLANNING_CREATE_PLAN,
            context_ref=ctx_ref,
            payload={
                "goal": f"Ingest and persist validated structured knowledge from PDF {filename} into case memory and verify retrieval",
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
        plan_steps = initial_plan_payload.get("steps", [])

        yield record_event(
            source_engine="client",
            destination_engine="planning",
            capability=PLANNING_CREATE_PLAN,
            event_type="plan_created",
            status="completed",
            duration_ms=dur_plan,
            plan_version=plan_v,
            response_envelope=resp_plan.model_dump(mode="json"),
            details={"plan_id": plan_id, "version": plan_v, "steps_count": len(plan_steps)},
        )

        plan_model = self.planning._plans.get(plan_id)
        if not plan_model:
            return

        # Prepare capability payloads
        mem_idempotency_key = f"mem-pdf-{extraction_res.file_hash[:16]}-{case_id[:8]}"
        search_query = structured_doc.facts[0].fact_text[:100] if structured_doc.facts else filename

        step_payloads = {
            CONTEXT_RESOLVE: {
                "context_hint": {
                    "organization_id": organization_id,
                    "case_id": case_id,
                    "domain_id": "legal",
                }
            },
            MEMORY_STORE_RECORD: {
                "record_type": "pdf_knowledge",
                "payload": {
                    "filename": filename,
                    "file_hash": extraction_res.file_hash,
                    "title": structured_doc.title,
                    "document_type": structured_doc.document_type,
                    "facts_count": len(structured_doc.facts),
                    "facts": [f.model_dump() for f in structured_doc.facts],
                    "entities": [e.model_dump() for e in structured_doc.entities],
                    "obligations": [o.model_dump() for o in structured_doc.obligations],
                    "summary": structured_doc.summary,
                },
                "source_observation_id": obs_id,
                "idempotency_key": mem_idempotency_key,
            },
            RETRIEVAL_QUERY: {
                "query": search_query,
                "record_type": "pdf_knowledge",
                "top_k": 5,
            },
        }

        # -------------------------------------------------------------
        # 7. Plan Execution (Normal vs Failure-Recovery)
        # -------------------------------------------------------------
        if mode == "normal":
            # Real step-by-step execution through PlanStepExecutor
            async for step_evt in self.executor.execute_plan(
                plan=plan_model,
                context_ref=ctx_ref,
                step_payloads=step_payloads,
            ):
                dest = step_evt.get("capability", "mesh").split(".")[0]
                yield record_event(
                    source_engine="plan_executor",
                    destination_engine=dest,
                    capability=step_evt.get("capability", "mesh.step"),
                    event_type=step_evt["event_type"],
                    status=step_evt["status"],
                    duration_ms=step_evt.get("duration_ms"),
                    plan_version=step_evt.get("plan_version", plan_v),
                    response_envelope=step_evt.get("response_envelope"),
                    details=step_evt.get("result", {}),
                )
        else:
            # FAILURE & BOUNDED RECOVERY MODE:
            # Step 1 fault injection: context resolution fails because case_id is omitted/ambiguous
            step_1 = plan_model.steps[0]
            def boundary_fault_injector(s: PlanStep, req: MeshRequest) -> MeshRequest:
                if s.step_id == step_1.step_id:
                    return MeshRequest(
                        task_id=req.task_id,
                        plan_version=req.plan_version,
                        sender_engine=req.sender_engine,
                        recipient_capability=req.recipient_capability,
                        context_ref=ContextRef(
                            organization_id=organization_id,
                            case_id=None,
                            resolution_status=ResolutionStatus.INSUFFICIENT_DATA,
                        ),
                        payload={"context_hint": {"organization_id": organization_id}},  # missing case_id
                    )
                return req

            fault_executor = PlanStepExecutor(
                router=self.router,
                registry=self.registry,
                fault_injector=boundary_fault_injector,
            )

            # Execute Step 1 with fault injection
            t0 = time.perf_counter()
            resp_step1, status_step1 = await fault_executor.execute_step(
                plan_model,
                step_1,
                context_ref=ctx_ref,
                custom_payload=step_payloads.get(step_1.capability),
            )
            dur_step1 = round((time.perf_counter() - t0) * 1000, 2)

            failure_evidence = {
                "fault_injection": "test_boundary_missing_case_id",
                "status": resp_step1.status.value,
                "errors": [e.model_dump() for e in resp_step1.errors] if resp_step1.errors else [],
                "missing_attributes": ["case_id"],
            }

            yield record_event(
                source_engine="plan_executor",
                destination_engine="context",
                capability=step_1.capability,
                event_type="step_failed",
                status="failed",
                duration_ms=dur_step1,
                plan_version=plan_v,
                response_envelope=resp_step1.model_dump(mode="json"),
                details={
                    "step_id": step_1.step_id,
                    "reason_code": ReplanReasonCode.CONTEXT_INSUFFICIENT.value,
                    "evidence": failure_evidence,
                },
            )

            # Downstream steps Step 2 and Step 3 are BLOCKED due to prerequisite failure
            for downstream in plan_model.steps[1:]:
                downstream.status = StepStatus.BLOCKED
                downstream.actual_result = {
                    "error": f"Prerequisite step '{step_1.step_id}' ({step_1.capability}) failed.",
                    "code": EngineErrorCode.MISSING_PREREQUISITE.value,
                }
                yield record_event(
                    source_engine="plan_executor",
                    destination_engine=downstream.capability.split(".")[0],
                    capability=downstream.capability,
                    event_type="step_blocked",
                    status="blocked",
                    plan_version=plan_v,
                    details=downstream.actual_result,
                )

            # Trigger Evidence-Based Replan via Planning Engine
            t0 = time.perf_counter()
            req_replan = MeshRequest(
                sender_engine="plan_executor",
                recipient_capability=PLANNING_REQUEST_REPLAN,
                context_ref=ctx_ref,
                payload={
                    "plan_id": plan_id,
                    "failed_step_id": step_1.step_id,
                    "reason_code": ReplanReasonCode.CONTEXT_INSUFFICIENT.value,
                    "evidence": failure_evidence,
                    "actual_result": step_1.actual_result,
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
                    "old_version": plan_v,
                    "new_version": new_v,
                    "steps_retained": replanned_payload.get("steps_retained", []),
                    "steps_added": replanned_payload.get("steps_added", []),
                },
            )

            # Execute Revised Plan v2 Steps with real PlanStepExecutor (no fault injector)
            revised_plan = self.planning._plans.get(plan_id)
            if revised_plan:
                async for step_evt in self.executor.execute_plan(
                    plan=revised_plan,
                    context_ref=ctx_ref,
                    step_payloads=step_payloads,
                ):
                    dest = step_evt.get("capability", "mesh").split(".")[0]
                    yield record_event(
                        source_engine="plan_executor",
                        destination_engine=dest,
                        capability=step_evt.get("capability", "mesh.step"),
                        event_type=step_evt["event_type"],
                        status=step_evt["status"],
                        duration_ms=step_evt.get("duration_ms"),
                        plan_version=new_v,
                        response_envelope=step_evt.get("response_envelope"),
                        details=step_evt.get("result", {}),
                    )

        # -------------------------------------------------------------
        # 8. Final Independent Retrieval Verification
        # -------------------------------------------------------------
        t0 = time.perf_counter()
        req_ret_verify = MeshRequest(
            sender_engine="client",
            recipient_capability=RETRIEVAL_QUERY,
            context_ref=ctx_ref,
            payload={
                "query": search_query,
                "record_type": "pdf_knowledge",
                "top_k": 5,
            },
        )
        resp_ret_verify = await self.router.dispatch(req_ret_verify)
        dur_verify = round((time.perf_counter() - t0) * 1000, 2)
        verified_records = resp_ret_verify.payload.get("records", [])

        # Cross-case isolation check
        adv_case_id = f"case-adv-{uuid.uuid4().hex[:6]}"
        ctx_ref_adv = ContextRef(
            context_ref_id=f"ctx:adv:{adv_case_id}",
            organization_id=organization_id,
            case_id=adv_case_id,
            domain_id="legal",
            resolution_status=ResolutionStatus.EXPLICIT,
        )
        req_iso_verify = MeshRequest(
            sender_engine="client",
            recipient_capability=RETRIEVAL_QUERY,
            context_ref=ctx_ref_adv,
            payload={"query": search_query, "record_type": "pdf_knowledge"},
        )
        resp_iso_verify = await self.router.dispatch(req_iso_verify)
        adv_records = resp_iso_verify.payload.get("records", [])
        isolation_passed = (len(adv_records) == 0)

        yield record_event(
            source_engine="client",
            destination_engine="retrieval",
            capability=RETRIEVAL_QUERY,
            event_type="verification_completed",
            status="completed" if verified_records and isolation_passed else "failed",
            duration_ms=dur_verify,
            response_envelope=resp_ret_verify.model_dump(mode="json"),
            details={
                "retrieved_records_count": len(verified_records),
                "case_id": case_id,
                "isolation_passed": isolation_passed,
                "adversary_records_found": len(adv_records),
            },
        )

        # -------------------------------------------------------------
        # 9. Final Scorecard and Run Summary
        # -------------------------------------------------------------
        total_dur = round((time.perf_counter() - start_time) * 1000, 2)
        all_engines = ["extractor", "perception", "observation", "context", "memory", "retrieval", "planning"]
        skipped_engines = [eng for eng in all_engines if eng not in invoked_engines]

        current_plan_model = None
        if initial_plan_payload and "plan_id" in initial_plan_payload:
            p_obj = self.planning._plans.get(initial_plan_payload["plan_id"])
            if p_obj:
                current_plan_model = p_obj.model_dump(mode="json")

        persisted_count = len(structured_doc.facts) if verified_records else 0
        validated_count = len([f for f in structured_doc.facts if f.validation_status == "validated"])

        summary_data = {
            "run_id": run_id,
            "mode": mode,
            "status": "completed" if (verified_records and isolation_passed) else "failed",
            "duration_ms": total_dur,
            "total_events": len(events) + 1,
            "invoked_engines": sorted(list(invoked_engines)),
            "skipped_engines": skipped_engines,
            "delegation_edges": delegation_edges,
            "initial_plan": initial_plan_payload,
            "replanned_payload": replanned_payload,
            "current_plan": current_plan_model,
            "scorecard": {
                "processing_outcome": "RECOVERED" if replanned_payload else "SUCCESS",
                "pages_processed": len(extraction_res.pages),
                "candidate_facts": len(structured_doc.facts),
                "validated_facts": validated_count,
                "persisted_facts": persisted_count,
                "retrieved_facts": len(verified_records),
                "isolation_verified": isolation_passed,
                "requires_ocr": extraction_res.requires_ocr,
                "warnings": extraction_res.warnings,
            },
            "structured_knowledge": structured_doc.model_dump(),
            "pages": [p.model_dump() for p in extraction_res.pages],
        }

        final_evt = record_event(
            source_engine="system",
            destination_engine="client",
            capability="mesh.summary",
            event_type="run_completed",
            status="completed" if (verified_records and isolation_passed) else "failed",
            duration_ms=total_dur,
            details=summary_data,
        )

        test_run_registry.save_run(
            run_id,
            {
                **summary_data,
                "timestamp": _utcnow_iso(),
                "events": events,
            },
        )

        yield final_evt


    def query_saved_knowledge(
        self,
        organization_id: str,
        case_id: str,
        query: str = "",
    ) -> list[dict[str, Any]]:
        """Retrieve persisted knowledge records for a case directly from PostgreSQL."""
        stmt = (
            sa.select(MemoryRecord)
            .where(
                MemoryRecord.organization_id == organization_id,
                MemoryRecord.case_id == case_id,
            )
            .order_by(MemoryRecord.created_at.desc())
        )
        records = self.db_session.scalars(stmt).all()
        result = []
        for r in records:
            if query and query.lower() not in json.dumps(r.payload).lower():
                continue
            result.append({
                "record_id": str(r.id),
                "record_type": r.record_type,
                "created_at": r.created_at.isoformat() if r.created_at else None,
                "payload": r.payload,
                "case_id": r.case_id,
                "organization_id": r.organization_id,
                "provenance": r.metadata_,
            })
        return result
