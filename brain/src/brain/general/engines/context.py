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

import logging
from typing import Any, Callable, Optional

from brain.general.contracts.capabilities import CONTEXT_RESOLVE, CapabilityRegistry
from brain.general.contracts.context import BrainContext
from brain.general.contracts.context_ref import ContextRef, ResolutionStatus
from brain.general.contracts.envelopes import MeshRequest, MeshResponse, ResultStatus
from brain.general.contracts.errors import EngineErrorCode
from brain.general.contracts.protocols import EngineResult, IContextEngine
from brain.general.engines.base import BaseEngine

logger = logging.getLogger(__name__)


class ContextEngine(BaseEngine, IContextEngine):
    """General Brain Context Engine [GB].

    Resolves contextual scope boundaries for tasks, observations, and records.
    Derives organization scope strictly from server-side authenticated context and
    rejects client-side organization overrides.
    """

    def __init__(
        self,
        llm_client: Optional[ILLMClient] = None,
        mesh_router: Optional[MeshRouter] = None,
        llm_service: Optional[ILLMClient] = None,
        case_validator: Optional[Callable[[str, str, Optional[str]], bool]] = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(
            llm_client=llm_client,
            mesh_router=mesh_router,
            llm_service=llm_service,
            **kwargs,
        )
        self._case_validator = case_validator

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
    # Case authorization boundary helper
    # -----------------------------------------------------------------

    def _validate_case(
        self,
        org_id: str,
        case_id: str,
        user_id: Optional[str] = None,
    ) -> tuple[bool, str]:
        """Validate case scope within organization boundary.
        
        Fails closed:
        - Rejects empty or whitespace-only case identifiers.
        - Fails closed if no validator is configured.
        - Fails closed if validator returns False/falsy.
        - Fails closed if validator raises an exception, logging the internal
          details and returning a safe generic authorization error.
        """
        if not case_id or not str(case_id).strip():
            return False, "Case identifier cannot be empty or whitespace."

        norm_case_id = str(case_id).strip()

        if self._case_validator is None:
            return (
                False,
                f"Access denied to case '{norm_case_id}': no case validator configured to verify case scope.",
            )

        try:
            is_valid = self._case_validator(org_id, norm_case_id, user_id)
            if not is_valid:
                return False, f"Access denied to case '{norm_case_id}' in organization '{org_id}'"
            return True, ""
        except Exception as exc:
            logger.error(
                "Case validator raised an exception while verifying case '%s' in organization '%s': %s",
                norm_case_id,
                org_id,
                exc,
                exc_info=True,
            )
            return False, f"Access denied to case '{norm_case_id}': authorization check failed."

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

        # Server case scope from context
        raw_server_case = getattr(context, "effective_scope_id", None) or context.case_id
        server_case = str(raw_server_case).strip() if raw_server_case else None

        raw_client_case = request_scope.get("case_id") or request_scope.get("scope_id")
        if raw_client_case is not None and isinstance(raw_client_case, str) and not raw_client_case.strip():
            return EngineResult(
                error={
                    "code": "INVALID_SCOPE",
                    "message": "Provided case_id or scope_id cannot be empty or whitespace.",
                }
            )
        client_case = str(raw_client_case).strip() if raw_client_case else None

        # Cross-scope case override attempt check
        if server_case and client_case and client_case != server_case:
            return EngineResult(
                error={
                    "code": "FORBIDDEN_CASE_OVERRIDE",
                    "message": f"Client attempted case override '{client_case}' does not match server scope '{server_case}'",
                }
            )

        if server_case:
            if self._case_validator:
                valid, err_msg = self._validate_case(context.organization_id, server_case, context.user_id)
                if not valid:
                    return EngineResult(
                        error={
                            "code": "AUTHORIZATION_DENIED",
                            "message": err_msg,
                        }
                    )
            case_id = server_case
            res_status = ResolutionStatus.EXPLICIT
        elif client_case:
            valid, err_msg = self._validate_case(context.organization_id, client_case, context.user_id)
            if not valid:
                return EngineResult(
                    error={
                        "code": "AUTHORIZATION_DENIED",
                        "message": err_msg,
                    }
                )
            case_id = client_case
            res_status = ResolutionStatus.EXPLICIT
        else:
            case_id = None
            res_status = ResolutionStatus.AMBIGUOUS

        domain_id = request_scope.get("domain_id") or context.domain_id
        user_id = context.user_id or request_scope.get("user_id")

        context_ref = self._resolve_deterministic(
            org_id=context.organization_id,
            domain_id=domain_id,
            case_id=case_id,
            user_id=user_id,
            source_ref=request_scope.get("source_ref"),
            forced_status=res_status,
        )

        data = {
            "context_ref": context_ref.context_ref_id,
            "organization_id": context.organization_id,
            "domain_id": domain_id,
            "case_id": case_id,
            "scope_id": case_id,
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
        if server_org:
            server_org = str(server_org).strip()

        hint_org = context_hint.get("organization_id")
        if hint_org:
            hint_org = str(hint_org).strip()

        # Invariant: Organization identity MUST be derived strictly from verified
        # server-side context. Client hints cannot fabricate tenant identity.
        if not server_org:
            return self._error(
                request,
                ResultStatus.FAILED,
                EngineErrorCode.CONTEXT_MISSING,
                "Server context requires a verified organization_id. Client hints cannot establish tenant identity.",
            )

        if hint_org and hint_org != server_org:
            return self._error(
                request,
                ResultStatus.FAILED,
                EngineErrorCode.AUTHORIZATION_DENIED,
                f"Client attempted organization override '{hint_org}' does not match context scope '{server_org}'",
            )

        org_id = server_org

        # Case boundary enforcement: server context is authoritative
        raw_server_case = (
            getattr(request.context_ref, "case_id", None)
            or getattr(request.context_ref, "scope_id", None)
            if request.context_ref
            else None
        )
        server_case = str(raw_server_case).strip() if raw_server_case else None

        raw_hint_case = context_hint.get("case_id") or context_hint.get("scope_id")
        if raw_hint_case is not None and isinstance(raw_hint_case, str) and not raw_hint_case.strip():
            return self._error(
                request,
                ResultStatus.FAILED,
                EngineErrorCode.INVALID_PAYLOAD,
                "Provided case_id or scope_id in context_hint cannot be empty or whitespace.",
            )
        hint_case = str(raw_hint_case).strip() if raw_hint_case else None

        user_id = (
            getattr(request.context_ref, "user_id", None)
            if request.context_ref
            else getattr(request, "actor_ref", None)
        ) or context_hint.get("user_id")

        if server_case:
            # Cross-scope case override check
            if hint_case and hint_case != server_case:
                return self._error(
                    request,
                    ResultStatus.FAILED,
                    EngineErrorCode.AUTHORIZATION_DENIED,
                    f"Client attempted case override '{hint_case}' does not match context scope '{server_case}'",
                )

            # Trusted server case provenance check:
            # External client cannot bypass case validation merely by passing case_id in ContextRef
            if request.sender_engine == "client":
                valid, err_msg = self._validate_case(server_org, server_case, user_id)
                if not valid:
                    return self._error(
                        request,
                        ResultStatus.FAILED,
                        EngineErrorCode.AUTHORIZATION_DENIED,
                        err_msg,
                    )
            else:
                # Internal engine delegation: if validator is configured, validate
                if self._case_validator:
                    valid, err_msg = self._validate_case(server_org, server_case, user_id)
                    if not valid:
                        return self._error(
                            request,
                            ResultStatus.FAILED,
                            EngineErrorCode.AUTHORIZATION_DENIED,
                            err_msg,
                        )

            case_id = server_case
            resolution_status = ResolutionStatus.EXPLICIT
        elif hint_case:
            valid, err_msg = self._validate_case(server_org, hint_case, user_id)
            if not valid:
                return self._error(
                    request,
                    ResultStatus.FAILED,
                    EngineErrorCode.AUTHORIZATION_DENIED,
                    err_msg,
                )
            case_id = hint_case
            resolution_status = ResolutionStatus.EXPLICIT
        else:
            case_id = None
            resolution_status = ResolutionStatus.INSUFFICIENT_DATA

        domain_id = context_hint.get("domain_id") or (
            getattr(request.context_ref, "domain_id", None) if request.context_ref else "general"
        )
        user_id = (
            getattr(request.context_ref, "user_id", None)
            if request.context_ref
            else getattr(request, "actor_ref", None)
        ) or context_hint.get("user_id")

        context_ref = self._resolve_deterministic(
            org_id=org_id,
            domain_id=domain_id,
            case_id=case_id,
            user_id=user_id,
            source_ref=source_ref,
            forced_status=resolution_status,
        )

        if context_ref.resolution_status == ResolutionStatus.INSUFFICIENT_DATA:
            llm_context = await self._try_llm_resolution(payload, server_org=server_org)
            if llm_context is not None:
                if llm_context.case_id:
                    valid, err_msg = self._validate_case(server_org, llm_context.case_id, user_id)
                    if not valid:
                        llm_context = llm_context.model_copy(
                            update={
                                "case_id": None,
                                "scope_id": None,
                                "resolution_status": ResolutionStatus.AMBIGUOUS,
                                "ambiguities": [
                                    f"Inferred case '{llm_context.case_id}' could not be verified by case validator: {err_msg}"
                                ],
                                "scope_constraints": [f"organization_id={server_org}"],
                            }
                        )
                context_ref = llm_context
            else:
                context_ref = ContextRef(
                    organization_id=server_org,
                    domain_id=domain_id,
                    case_id=None,
                    user_id=user_id,
                    resolution_status=ResolutionStatus.AMBIGUOUS,
                    ambiguities=["Missing required case_id / scope_id for boundary enforcement."],
                    scope_constraints=[f"organization_id={server_org}"],
                )

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
            "scope_id": context_ref.case_id,
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
        forced_status: Optional[ResolutionStatus] = None,
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

            status = forced_status or ResolutionStatus.EXPLICIT
            return ContextRef(
                organization_id=org_id,
                domain_id=domain_id,
                case_id=case_id,
                user_id=user_id,
                resolution_status=status,
                scope_constraints=scope_constraints,
            )

        if has_org and not has_case:
            ambiguities.append("Missing required case_id / scope_id for boundary enforcement.")
            scope_constraints.append(f"organization_id={org_id}")
            status = forced_status or ResolutionStatus.INSUFFICIENT_DATA
            return ContextRef(
                organization_id=org_id,
                domain_id=domain_id,
                case_id=None,
                user_id=user_id,
                resolution_status=status,
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

    async def _try_llm_resolution(
        self,
        payload: dict[str, Any],
        server_org: Optional[str] = None,
    ) -> Optional[ContextRef]:
        """Attempt to infer context using LLM when deterministic resolution is insufficient."""
        if not self._llm_client:
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

        raw_case_id = result.get("case_id")
        case_id = str(raw_case_id).strip() if raw_case_id else None

        if case_id:
            return ContextRef(
                organization_id=server_org,
                domain_id=result.get("domain_id"),
                case_id=case_id,
                user_id=result.get("user_id"),
                resolution_status=ResolutionStatus.EXPLICIT,
                scope_constraints=[f"case_id={case_id}"],
            )

        return None
