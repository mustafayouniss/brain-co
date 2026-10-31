"""Compatibility shim for CapabilityRegistry and constants.

Re-exports canonical capability contracts from brain.general.contracts.capabilities.
"""

from brain.general.contracts.capabilities import (
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
    CapabilityEntry,
    CapabilityRegistry,
)

__all__ = [
    "ALL_CAPABILITIES",
    "CONTEXT_RESOLVE",
    "CapabilityEntry",
    "CapabilityRegistry",
    "MEMORY_GET_RECORD",
    "MEMORY_STORE_RECORD",
    "OBSERVATION_RECORD_EVENT",
    "PERCEPTION_STRUCTURE_INPUT",
    "PLANNING_CREATE_PLAN",
    "PLANNING_GET_PLAN_STATUS",
    "PLANNING_REQUEST_REPLAN",
    "RETRIEVAL_QUERY",
]
