"""Typed engine error models for Ring 1.

These provide structured error information that engines return inside
MeshResponse.errors instead of exposing raw stack traces.
"""

from __future__ import annotations

from enum import Enum


class EngineErrorCode(str, Enum):
    """Standard error codes used across all Ring 1 engines."""

    # Validation
    INVALID_SCHEMA = "invalid_schema"
    INVALID_PAYLOAD = "invalid_payload"
    UNSUPPORTED_PROTOCOL_VERSION = "unsupported_protocol_version"
    UNKNOWN_CAPABILITY = "unknown_capability"
    CAPABILITY_NOT_FOUND = "capability_not_found"
    INVALID_CAPABILITY_ARGS = "invalid_capability_args"

    # Authorization / context
    UNAUTHORIZED = "unauthorized"
    AUTHORIZATION_DENIED = "authorization_denied"
    CONTEXT_MISSING = "context_missing"
    CONTEXT_AMBIGUOUS = "context_ambiguous"
    SCOPE_VIOLATION = "scope_violation"

    # Execution
    DETERMINISTIC_FAILURE = "deterministic_failure"
    PARSING_FAILED = "parsing_failed"
    LLM_FAILURE = "llm_failure"
    LLM_INVALID_OUTPUT = "llm_invalid_output"
    LLM_UNAVAILABLE = "llm_unavailable"
    PROVIDER_TIMEOUT = "provider_timeout"

    # Delegation
    DELEGATION_DEPTH_EXCEEDED = "delegation_depth_exceeded"
    PEER_FAILURE = "peer_failure"
    PEER_TIMEOUT = "peer_timeout"

    # Data
    RECORD_NOT_FOUND = "record_not_found"
    DATA_NOT_FOUND = "data_not_found"
    DUPLICATE_RECORD = "duplicate_record"
    DATABASE_ERROR = "database_error"
    NO_RESULTS = "no_results"

    # Planning
    PLAN_LIMIT_EXCEEDED = "plan_limit_exceeded"
    REPLAN_LIMIT_EXCEEDED = "replan_limit_exceeded"
    TERMINAL_FAILURE = "terminal_failure"
    CLARIFICATION_REQUIRED = "clarification_required"
    MISSING_PREREQUISITE = "missing_prerequisite"

    # General
    INTERNAL_ERROR = "internal_error"
    INTERNAL_EXECUTION_ERROR = "internal_execution_error"
    UNSUPPORTED_INPUT_TYPE = "unsupported_input_type"
