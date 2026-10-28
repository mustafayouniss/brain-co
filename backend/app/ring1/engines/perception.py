"""Perception Engine — transforms raw inputs into structured representations.

Deterministic Core:
- Parse known JSON payloads
- Validate required fields
- Detect supported input types (text, json, system_event, document)
- Reject explicitly unsupported input types (e.g. binary_executable)

Intelligence Layer:
- Classify unfamiliar or ambiguous inputs via LLM
- Extract structured meaning from irregular free text

Must not: grant access, fabricate context, promote observations to knowledge,
or invoke an LLM for every input.
"""

from __future__ import annotations

import json
from typing import Any, Optional

from app.ring1.contracts.capabilities import (
    OBSERVATION_RECORD_EVENT,
    PERCEPTION_STRUCTURE_INPUT,
    CapabilityRegistry,
)
from app.ring1.contracts.envelopes import MeshRequest, MeshResponse, ResultStatus
from app.ring1.contracts.errors import EngineErrorCode
from app.ring1.engines.base import BaseEngine


# Supported input types for deterministic processing
_KNOWN_SOURCE_TYPES = frozenset({"text", "json", "system_event", "document"})

# Known unsupported input types
_UNSUPPORTED_SOURCE_TYPES = frozenset({
    "binary_executable",
    "executable",
    "binary",
    "video_raw",
})


class PerceptionEngine(BaseEngine):
    """Ring 1 Perception Engine [GB].

    Processes raw inputs into structured representations using deterministic
    parsers for known formats and the Intelligence Layer for ambiguous inputs.
    """

    @property
    def engine_name(self) -> str:
        return "perception"

    def register_capabilities(self, registry: CapabilityRegistry) -> None:
        registry.register(
            PERCEPTION_STRUCTURE_INPUT,
            self.engine_name,
            self.handle_structure_input,
            description="Transform raw input into a structured representation.",
        )

    # -----------------------------------------------------------------
    # Capability handler
    # -----------------------------------------------------------------

    async def handle_structure_input(self, request: MeshRequest) -> MeshResponse:
        """Structure a raw input into a validated representation.

        Decision order:
        1. Validate request schema
        2. Check source_type and select processing mode
        3. Use deterministic parser for known formats
        4. Use LLM only for unknown/ambiguous inputs
        5. Validate output
        6. Return typed result
        """
        # Step 1: Validate request
        validation_err = self.validate_request(request)
        if validation_err:
            return validation_err

        payload = request.payload
        source_type = (payload.get("source_type") or payload.get("input_type") or "").strip().lower()
        raw_content = payload.get("raw_content")
        input_id = payload.get("input_id", request.message_id)

        if not raw_content and not payload.get("raw_content_ref"):
            return self._error(
                request,
                ResultStatus.INVALID_REQUEST,
                EngineErrorCode.INVALID_PAYLOAD,
                "Either 'raw_content' or 'raw_content_ref' is required.",
            )

        # Explicitly check for unsupported formats
        if source_type in _UNSUPPORTED_SOURCE_TYPES:
            return self._error(
                request,
                ResultStatus.FAILED,
                EngineErrorCode.UNSUPPORTED_INPUT_TYPE,
                f"Unsupported input type '{source_type}'.",
            )

        # Detect source_type if not provided
        if not source_type:
            if isinstance(raw_content, dict):
                source_type = "json"
            elif isinstance(raw_content, str):
                trimmed = raw_content.strip()
                if trimmed.startswith("{") and trimmed.endswith("}"):
                    source_type = "json"
                else:
                    source_type = "text"

        # Step 2–3: Deterministic processing for known types
        if source_type in _KNOWN_SOURCE_TYPES:
            result = self._process_deterministic(
                source_type, raw_content, payload.get("metadata", {})
            )
            if result is not None:
                meta = result.get("metadata", {})
                resp_payload = {
                    "input_id": input_id,
                    "content_type": source_type,
                    "detected_type": source_type,
                    "structured_content": result["content"],
                    "parsed_content": result["content"],
                    "metadata": meta,
                    "extracted_metadata": meta,
                    "processing_mode": "deterministic",
                    "status": "success",
                    "uncertainty": [],
                    "errors": [],
                }

                # Optional genuine delegation to ObservationEngine
                if (
                    payload.get("record_observation", False)
                    and self._mesh_router is not None
                    and request.constraints.max_delegations_remaining > 0
                ):
                    try:
                        obs_resp = await self._delegate(
                            parent_request=request,
                            recipient_capability=OBSERVATION_RECORD_EVENT,
                            payload={
                                "event_type": "input_structured",
                                "source": "perception",
                                "payload": result["content"],
                            },
                        )
                        resp_payload["delegated_observation"] = {
                            "status": obs_resp.status.value,
                            "payload": obs_resp.payload,
                        }
                    except Exception as exc:
                        self._logger.warning("Delegation from perception to observation failed: %s", exc)

                return self._success(request, resp_payload)

        # Step 4: LLM-assisted processing for unknown/ambiguous inputs
        llm_result = await self._process_with_llm(source_type, raw_content)
        if llm_result is not None:
            c_type = llm_result.get("content_type", source_type or "unknown")
            s_content = llm_result.get("structured_content", {})
            meta = llm_result.get("metadata", {})
            return self._success(request, {
                "input_id": input_id,
                "content_type": c_type,
                "detected_type": c_type,
                "structured_content": s_content,
                "parsed_content": s_content,
                "metadata": meta,
                "extracted_metadata": meta,
                "processing_mode": "llm",
                "status": "success",
                "uncertainty": llm_result.get("uncertainty", []),
                "errors": [],
            })

        # Step 5: Fallback — return partial result with raw content
        raw_struct = {"raw": raw_content} if isinstance(raw_content, str) else raw_content
        meta = payload.get("metadata", {})
        return self._success(request, {
            "input_id": input_id,
            "content_type": source_type or "unknown",
            "detected_type": source_type or "unknown",
            "structured_content": raw_struct,
            "parsed_content": raw_struct,
            "metadata": meta,
            "extracted_metadata": meta,
            "processing_mode": "fallback",
            "status": "partial",
            "uncertainty": ["Could not fully structure the input."],
            "errors": [],
        })

    # -----------------------------------------------------------------
    # Deterministic core
    # -----------------------------------------------------------------

    def _process_deterministic(
        self,
        source_type: str,
        raw_content: Any,
        metadata: dict[str, Any],
    ) -> Optional[dict[str, Any]]:
        """Attempt deterministic parsing for known formats."""
        if source_type == "json":
            return self._parse_json(raw_content)
        elif source_type == "text":
            return self._parse_text(raw_content, metadata)
        elif source_type == "system_event":
            return self._parse_system_event(raw_content)
        elif source_type == "document":
            return self._parse_document_metadata(raw_content, metadata)
        return None

    @staticmethod
    def _parse_json(raw_content: Any) -> Optional[dict[str, Any]]:
        """Parse raw JSON string or dict into structured content."""
        if isinstance(raw_content, dict):
            return {
                "content": raw_content,
                "metadata": {"parsed_from": "dict", "key_count": len(raw_content)},
            }
        if isinstance(raw_content, str):
            try:
                parsed = json.loads(raw_content)
                if isinstance(parsed, dict):
                    return {
                        "content": parsed,
                        "metadata": {"parsed_from": "json_string", "key_count": len(parsed)},
                    }
            except (json.JSONDecodeError, ValueError):
                return None
        return None

    @staticmethod
    def _parse_text(raw_content: Any, metadata: dict[str, Any]) -> Optional[dict[str, Any]]:
        """Structure plain text content."""
        if not isinstance(raw_content, str):
            return None
        text = raw_content.strip()
        if not text:
            return None
        lines = [line for line in text.split("\n") if line.strip()]
        line_count = len(lines) if lines else 1
        word_count = len(text.split())
        return {
            "content": {
                "text": text,
                "length": len(text),
                "word_count": word_count,
                "line_count": line_count,
            },
            "metadata": {
                "parsed_from": "text",
                "line_count": line_count,
                "word_count": word_count,
                **{k: v for k, v in metadata.items() if k != "parsed_from"},
            },
        }

    @staticmethod
    def _parse_system_event(raw_content: Any) -> Optional[dict[str, Any]]:
        """Parse a system event."""
        if isinstance(raw_content, dict):
            return {
                "content": raw_content,
                "metadata": {"parsed_from": "system_event"},
            }
        if isinstance(raw_content, str):
            try:
                parsed = json.loads(raw_content)
                if isinstance(parsed, dict):
                    return {
                        "content": parsed,
                        "metadata": {"parsed_from": "system_event_json"},
                    }
            except (json.JSONDecodeError, ValueError):
                pass
        return None

    @staticmethod
    def _parse_document_metadata(
        raw_content: Any,
        metadata: dict[str, Any],
    ) -> Optional[dict[str, Any]]:
        """Extract basic metadata from a document reference."""
        content: dict[str, Any] = {}
        if isinstance(raw_content, dict):
            content = raw_content
        elif isinstance(raw_content, str):
            content = {"reference": raw_content}
        else:
            return None

        return {
            "content": content,
            "metadata": {
                "parsed_from": "document",
                **metadata,
            },
        }

    # -----------------------------------------------------------------
    # Intelligence Layer: LLM processing
    # -----------------------------------------------------------------

    async def _process_with_llm(
        self,
        source_type: str,
        raw_content: Any,
    ) -> Optional[dict[str, Any]]:
        """Classify and extract structure from ambiguous inputs via LLM."""
        if not self._llm_service:
            return None

        content_str = (
            raw_content
            if isinstance(raw_content, str)
            else json.dumps(raw_content, default=str)
        )

        prompt = (
            "You are the Perception Engine of Ring 1 General Brain. "
            "Analyze the following input. Classify its content type and extract key "
            "entities, intent, and summary. Return a JSON object with keys: "
            "'content_type' (str), 'structured_content' (dict), 'metadata' (dict), "
            "'uncertainty' (list of str, if any)."
        )

        result = await self._call_llm_json(prompt, content_str)
        if result is None or not isinstance(result, dict):
            return None

        if "structured_content" not in result:
            result["structured_content"] = {"raw": raw_content}

        return result
