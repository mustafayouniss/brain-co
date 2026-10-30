"""Context Engine — resolves and maintains contextual boundaries for tasks.

Deterministic Core:
- Accept explicit context hints (organization_id, domain_id, case_id, user_id)
- Validate provided identifiers against server-side BrainContext
- Reject caller-controlled organization overrides
- Produce a ContextRef with resolution status
- Report ambiguity for missing or incomplete identifiers

Intelligence Layer:
- Attempt context inference from payload metadata when hints are insufficient

Must not: guess missing identifiers, treat client hints as authorization,
permit cross-organization overrides, expand task scope, override isolation rules.
"""

from __future__ import annotations

from typing import Any, Optional

from app.core.context import BrainContext
from app.ring1.contracts.capabilities import CONTEXT_RESOLVE, CapabilityRegistry
from app.ring1.contracts.context_ref import ContextRef, ResolutionStatus
from app.ring1.contracts.envelopes import MeshRequest, MeshResponse, ResultStatus
from app.ring1.contracts.errors import EngineErrorCode
from app.ring1.contracts.protocols import EngineResult, IContextEngine
from app.ring1.engines.base import BaseEngine


class ContextEngine(BaseEngine, IContextEngine):
    """Ring 1 Context Engine [GB].

    Resolves contextual scope boundaries for tasks, observations, and records.
    Derives organization scope strictly from server-side authenticated context and
    rejects client-side organization overrides.
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
    # Pure Engine Protocol implementation (Decoupled from Transport)
    # -----------------------------------------------------------------

    async def resolve_context(
        self,
        request_scope: dict[str, Any],
        context: BrainContext,
    ) -> EngineResult:
        """Resolve and validate context boundaries against authenticated BrainContext.
        
        Rejects client attempts to override organization_id. Validates case_id.
        """
        if not context or not context.organization_id:
            return EngineResult(
                error={"code": "INVALID_CONTEXT", "message": "Valid BrainContext with organization_id required"}
            )

        client_org = request_scope.get("organization_id")
        if client_org and client_org != context.organization_id:
            return EngineResult(
                error={
                    "code": "FORBIDDEN_ORG_OVERRIDE",
                    "message": f"Client attempted organization override '{client_org}' does not match server scope '{context.organization_id}'",
                }
            )

        case_id = request_scope.get("case_id") or context.case_id
        domain_id = request_scope.get("domain_id")
        user_id = context.user_id or request_scope.get("user_id")

        context_ref = self._resolve_deterministic(
            org_id=context.organization_id,
            domain_id=domain_id,
            case_id=case_id,
            user_id=user_id,
            source_ref=request_scope.get("source_ref"),
        )

        data = {
            "context_ref": context_ref.context_ref_id,
            "organization_id": context.organization_id,
            "domain_id": domain_id,
            "case_id": case_id,
            "user_id": user_id,
            "status": context_ref.resolution_status.value,
            "resolution_status": context_ref.resolution_status.value,
            "ambiguities": context_ref.ambiguities,
            "scope_constraints": context_ref.scope_constraints,
        }

        return EngineResult(data=data, is_terminal=True)

    # -----------------------------------------------------------------
    # Capability handler (Mesh Adapter for Backward Compatibility)
    # -----------------------------------------------------------------

    async def handle_resolve(self, request: MeshRequest) -> MeshResponse:
        """Resolve context scope from provided hints and source references."""
        validation_err = self.validate_request(request)
        if validation_err:
            return validation_err

        payload = request.payload
        context_hint = payload.get("context_hint", {})
        source_ref = payload.get("source_ref")

        # Server-side context validation
        server_org = getattr(request.context_ref, "organization_id", None) if request.context_ref else None
        hint_org = context_hint.get("organization_id")

        if server_org and hint_org and hint_org != server_org:
            return self._error(
                request,
                ResultStatus.FAILED,
                EngineErrorCode.PERMISSION_DENIED,
                f"Client attempted organization override '{hint_org}' does not match context scope '{server_org}'",
            )

        org_id = server_org or hint_org
        domain_id = context_hint.get("domain_id")
        case_id = context_hint.get("case_id") or (getattr(request.context_ref, "case_id", None) if request.context_ref else None)
        user_id = context_hint.get("user_id") or getattr(request.context_ref, "user_id", None) if request.context_ref else getattr(request, "actor_ref", None)

        context_ref = self._resolve_deterministic(
            org_id=org_id,
            domain_id=domain_id,
            case_id=case_id,
            user_id=user_id,
            source_ref=source_ref,
        )

        if context_ref.resolution_status == ResolutionStatus.INSUFFICIENT_DATA:
            llm_context = await self._try_llm_resolution(payload)
            if llm_context is not None:
                context_ref = llm_context

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
        """Resolve context from explicit identifiers."""
        ambiguities: list[str] = []
        scope_constraints: list[str] = []

        has_case = bool(case_id)
        has_org = bool(org_id)

        if has_case:
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
            ambiguities.append("Missing required case_id for case-level boundary enforcement.")
            scope_constraints.append(f"organization_id={org_id}")
            return ContextRef(
                organization_id=org_id,
                domain_id=domain_id,
                case_id=None,
                user_id=user_id,
                resolution_status=ResolutionStatus.AMBIGUOUS,
                ambiguities=ambiguities,
                scope_constraints=scope_constraints,
            )

        ambiguities.append("No contextual identifiers provided in hints.")
        return ContextRef(
            organization_id=None,
            domain_id=None,
            case_id=None,
            user_id=user_id,
            resolution_status=ResolutionStatus.AMBIGUOUS,
            ambiguities=ambiguities,
        )

    # -----------------------------------------------------------------
    # Intelligence Layer: LLM resolution fallback
    # -----------------------------------------------------------------

    async def _try_llm_resolution(self, payload: dict[str, Any]) -> Optional[ContextRef]:
        """Attempt to infer context using LLM when deterministic resolution is insufficient."""
        if not self._llm_service:
            return None

        prompt = (
            "You are the Context Engine of Ring 1 General Brain. "
            "Analyze the following request payload and infer the contextual boundaries. "
            "Extract: organization_id, domain_id, case_id, user_id if present or strongly implied. "
            "Do NOT guess or invent identifiers that are not supported by the data. "
            "Return JSON: {'organization_id': str|null, 'domain_id': str|null, "
            "'case_id': str|null, 'user_id': str|null, 'confidence': float}."
        )

        result = await self._call_llm_json(prompt, str(payload))
        if result is None or not isinstance(result, dict):
            return None

        confidence = result.get("confidence", 0.0)
        if confidence < 0.7:
            return None

        case_id = result.get("case_id")
        org_id = result.get("organization_id")

        if case_id:
            return ContextRef(
                organization_id=org_id,
                domain_id=result.get("domain_id"),
                case_id=case_id,
                user_id=result.get("user_id"),
                resolution_status=ResolutionStatus.EXPLICIT,
                scope_constraints=[f"case_id={case_id}"],
            )

        return None
