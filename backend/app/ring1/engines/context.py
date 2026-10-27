"""Context Engine — resolves and maintains contextual boundaries for tasks.

Deterministic Core:
- Accept explicit context hints (organization_id, domain_id, case_id, user_id)
- Validate provided identifiers
- Produce a ContextRef with resolution status
- Report ambiguity for missing or incomplete identifiers

Intelligence Layer:
- Attempt context inference from payload metadata when hints are insufficient

Must not: guess missing identifiers, treat context resolution as authorization,
expand task scope, override isolation rules.
"""

from __future__ import annotations

from typing import Any, Optional

from app.ring1.contracts.capabilities import CONTEXT_RESOLVE, CapabilityRegistry
from app.ring1.contracts.context_ref import ContextRef, ResolutionStatus
from app.ring1.contracts.envelopes import MeshRequest, MeshResponse, ResultStatus
from app.ring1.contracts.errors import EngineErrorCode
from app.ring1.engines.base import BaseEngine


class ContextEngine(BaseEngine):
    """Ring 1 Context Engine [GB].

    Resolves contextual scope boundaries for tasks, observations, and records.
    Produces a ContextRef that downstream engines carry through reads/writes
    to enforce data isolation.
    """

    @property
    def engine_name(self) -> str:
        return "context"

    def register_capabilities(self, registry: CapabilityRegistry) -> None:
        registry.register(
            CONTEXT_RESOLVE,
            self.engine_name,
            self.handle_resolve,
            description="Resolve contextual boundaries for a task or observation.",
        )

    # -----------------------------------------------------------------
    # Capability handler
    # -----------------------------------------------------------------

    async def handle_resolve(self, request: MeshRequest) -> MeshResponse:
        """Resolve context scope from provided hints and source references.

        Decision order:
        1. Validate request
        2. Extract context hints from payload
        3. Attempt deterministic resolution
        4. Report ambiguity or insufficient data if resolution fails
        5. Return typed ContextRef
        """
        # Step 1: Validate
        validation_err = self.validate_request(request)
        if validation_err:
            return validation_err

        payload = request.payload
        context_hint = payload.get("context_hint", {})
        source_ref = payload.get("source_ref")

        # Step 2: Extract explicit hints
        org_id = context_hint.get("organization_id")
        domain_id = context_hint.get("domain_id")
        case_id = context_hint.get("case_id")
        user_id = context_hint.get("user_id")

        # Step 3: Deterministic resolution
        context_ref = self._resolve_deterministic(
            org_id=org_id,
            domain_id=domain_id,
            case_id=case_id,
            user_id=user_id,
            source_ref=source_ref,
        )

        # Step 4: If insufficient, try LLM inference (only for ambiguity)
        if context_ref.resolution_status == ResolutionStatus.INSUFFICIENT_DATA:
            llm_context = await self._try_llm_resolution(payload)
            if llm_context is not None:
                context_ref = llm_context

        # Step 5: Build response
        status = ResultStatus.SUCCESS
        if context_ref.resolution_status == ResolutionStatus.AMBIGUOUS:
            status = ResultStatus.NEEDS_CLARIFICATION
        elif context_ref.resolution_status == ResolutionStatus.INSUFFICIENT_DATA:
            status = ResultStatus.NEEDS_CLARIFICATION
        elif context_ref.resolution_status == ResolutionStatus.FAILED:
            status = ResultStatus.FAILED

        response_payload = {
            "context_ref": context_ref.context_ref_id,
            "organization_id": context_ref.organization_id,
            "domain_id": context_ref.domain_id,
            "case_id": context_ref.case_id,
            "user_id": context_ref.user_id,
            "status": context_ref.resolution_status.value,
            "resolution_status": context_ref.resolution_status.value,
            "ambiguities": context_ref.ambiguities,
            "ambiguity_reasons": context_ref.ambiguities,
            "scope_constraints": context_ref.scope_constraints,
        }

        if status == ResultStatus.SUCCESS:
            return self._success(
                request,
                response_payload,
                context_ref=context_ref.context_ref_id,
            )
        else:
            return MeshResponse(
                in_reply_to=request.message_id,
                task_id=request.task_id,
                trace_id=request.trace_id,
                sender_engine=self.engine_name,
                status=status,
                payload=response_payload,
                context_ref=context_ref.context_ref_id,
                plan_version=request.plan_version,
            )

    # -----------------------------------------------------------------
    # Deterministic core
    # -----------------------------------------------------------------

    @staticmethod
    def _resolve_deterministic(
        *,
        org_id: Optional[str],
        domain_id: Optional[str],
        case_id: Optional[str],
        user_id: Optional[str],
        source_ref: Optional[str],
    ) -> ContextRef:
        """Resolve context from explicit identifiers.

        Resolution rules:
        - If case_id is provided → explicit resolution (case is the primary isolation key)
        - If org_id provided without case_id → ambiguous (case_id required for isolation)
        - If no identifiers → ambiguous
        """
        ambiguities: list[str] = []
        scope_constraints: list[str] = []

        # Check what we have
        has_case = bool(case_id)
        has_org = bool(org_id)
        has_user = bool(user_id)

        if has_case:
            # Case-level resolution: the strongest isolation scope
            scope_constraints.append(f"case_id={case_id}")
            if has_org:
                scope_constraints.append(f"organization_id={org_id}")

            return ContextRef(
                organization_id=org_id,
                domain_id=domain_id,
                case_id=case_id,
                user_id=user_id,
                resolution_status=ResolutionStatus.EXPLICIT,
                scope_constraints=scope_constraints,
            )

        if has_org and not has_case:
            # Org-level without case is ambiguous for case-scoped operations
            ambiguities.append("Missing required case_id for case-level boundary enforcement.")
            scope_constraints.append(f"organization_id={org_id}")
            return ContextRef(
                organization_id=org_id,
                domain_id=domain_id,
                user_id=user_id,
                resolution_status=ResolutionStatus.AMBIGUOUS,
                ambiguities=ambiguities,
                scope_constraints=scope_constraints,
            )

        if has_user and not has_org and not has_case:
            ambiguities.append("user_id provided without organization_id or case_id")
            return ContextRef(
                user_id=user_id,
                domain_id=domain_id,
                resolution_status=ResolutionStatus.AMBIGUOUS,
                ambiguities=ambiguities,
            )

        # No identifiers at all
        return ContextRef(
            resolution_status=ResolutionStatus.AMBIGUOUS,
            ambiguities=["No context identifiers provided (missing case_id)."],
        )


    # -----------------------------------------------------------------
    # Intelligence Layer
    # -----------------------------------------------------------------

    async def _try_llm_resolution(
        self, payload: dict[str, Any]
    ) -> Optional[ContextRef]:
        """Attempt to infer context from payload metadata using the LLM.

        This is only called when deterministic resolution produced
        INSUFFICIENT_DATA. The LLM can suggest identifiers based on
        source references or metadata, but CANNOT fabricate IDs.
        """
        source_ref = payload.get("source_ref")
        metadata = payload.get("metadata", {})

        if not source_ref and not metadata:
            return None

        system_prompt = (
            "You are a context resolution engine. Given the metadata below, "
            "determine if you can identify the organization_id, case_id, or user_id. "
            "Return a JSON object with keys: organization_id, case_id, user_id "
            "(null if not determinable), and confidence (float 0-1). "
            "NEVER fabricate identifiers. If unsure, return null for each field."
        )

        user_content = f"source_ref: {source_ref}\nmetadata: {metadata}"
        result = await self._call_llm_json(system_prompt, user_content, temperature=0.1)

        if result is None:
            return None

        # Only use LLM suggestions if confidence is high
        confidence = result.get("confidence", 0)
        if confidence < 0.8:
            return None

        inferred_org = result.get("organization_id")
        inferred_case = result.get("case_id")
        inferred_user = result.get("user_id")

        if not inferred_org and not inferred_case and not inferred_user:
            return None

        return self._resolve_deterministic(
            org_id=inferred_org,
            domain_id=payload.get("context_hint", {}).get("domain_id"),
            case_id=inferred_case,
            user_id=inferred_user,
            source_ref=source_ref,
        )
