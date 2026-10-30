"""Tests for Ring 1 HandoffPolicy governing capability delegations."""

import pytest

from app.core.handoff import HandoffPolicy, HandoffRejectionReason
from app.ring1.contracts.capabilities import (
    CONTEXT_RESOLVE,
    MEMORY_GET_RECORD,
    MEMORY_STORE_RECORD,
    OBSERVATION_RECORD_EVENT,
    PERCEPTION_STRUCTURE_INPUT,
    PLANNING_CREATE_PLAN,
    PLANNING_GET_PLAN_STATUS,
    PLANNING_REQUEST_REPLAN,
    RETRIEVAL_QUERY,
)


def test_permitted_handoff_transitions():
    policy = HandoffPolicy()

    # Perception -> Observation
    res = policy.validate_handoff(PERCEPTION_STRUCTURE_INPUT, OBSERVATION_RECORD_EVENT)
    assert res.is_permitted is True

    # Observation -> Context, Retrieval, Memory
    assert policy.validate_handoff(OBSERVATION_RECORD_EVENT, CONTEXT_RESOLVE).is_permitted is True
    assert policy.validate_handoff(OBSERVATION_RECORD_EVENT, RETRIEVAL_QUERY).is_permitted is True
    assert policy.validate_handoff(OBSERVATION_RECORD_EVENT, MEMORY_STORE_RECORD).is_permitted is True

    # Context -> Retrieval, Memory
    assert policy.validate_handoff(CONTEXT_RESOLVE, RETRIEVAL_QUERY).is_permitted is True
    assert policy.validate_handoff(CONTEXT_RESOLVE, MEMORY_GET_RECORD).is_permitted is True

    # Retrieval -> Memory, Context
    assert policy.validate_handoff(RETRIEVAL_QUERY, CONTEXT_RESOLVE).is_permitted is True
    assert policy.validate_handoff(RETRIEVAL_QUERY, MEMORY_GET_RECORD).is_permitted is True


def test_disallowed_handoff_transition():
    policy = HandoffPolicy()

    # Perception directly to Memory is disallowed without observation/context
    res = policy.validate_handoff(PERCEPTION_STRUCTURE_INPUT, MEMORY_STORE_RECORD)
    assert res.is_permitted is False
    assert res.reason == HandoffRejectionReason.DISALLOWED_TRANSITION


def test_observation_cannot_autonomously_initiate_planning():
    policy = HandoffPolicy()

    # Mandate 2.3: Observation cannot autonomously initiate planning
    res = policy.validate_handoff(OBSERVATION_RECORD_EVENT, PLANNING_CREATE_PLAN)
    assert res.is_permitted is False
    assert res.reason == HandoffRejectionReason.AUTONOMOUS_PLANNING_FORBIDDEN

    res_replan = policy.validate_handoff(OBSERVATION_RECORD_EVENT, PLANNING_REQUEST_REPLAN)
    assert res_replan.is_permitted is False
    assert res_replan.reason == HandoffRejectionReason.AUTONOMOUS_PLANNING_FORBIDDEN


def test_unknown_target_capability_rejected():
    policy = HandoffPolicy()

    res = policy.validate_handoff(PERCEPTION_STRUCTURE_INPUT, "UNREGISTERED_CAPABILITY_XYZ")
    assert res.is_permitted is False
    assert res.reason == HandoffRejectionReason.UNKNOWN_CAPABILITY


def test_cycle_detection_self_loop():
    policy = HandoffPolicy()

    res = policy.validate_handoff(CONTEXT_RESOLVE, CONTEXT_RESOLVE)
    assert res.is_permitted is False
    assert res.reason == HandoffRejectionReason.CYCLE_DETECTED


def test_cycle_detection_in_history():
    policy = HandoffPolicy()

    history = [
        CONTEXT_RESOLVE,
        RETRIEVAL_QUERY,
        CONTEXT_RESOLVE,
        RETRIEVAL_QUERY,
    ]
    # Attempting CONTEXT_RESOLVE again
    res = policy.validate_handoff(
        source_capability=RETRIEVAL_QUERY,
        target_capability=CONTEXT_RESOLVE,
        traversal_history=history,
    )
    assert res.is_permitted is False
    assert res.reason == HandoffRejectionReason.CYCLE_DETECTED


def test_max_depth_exceeded():
    policy = HandoffPolicy(max_depth=5)

    history = ["cap1", "cap2", "cap3", "cap4", "cap5"]
    res = policy.validate_handoff(
        source_capability=PERCEPTION_STRUCTURE_INPUT,
        target_capability=OBSERVATION_RECORD_EVENT,
        traversal_history=history,
    )
    assert res.is_permitted is False
    assert res.reason == HandoffRejectionReason.MAX_DEPTH_EXCEEDED
