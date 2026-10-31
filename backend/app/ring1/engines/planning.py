"""Compatibility shim for PlanningEngine.

Re-exports canonical PlanningEngine preserving exact class identity.
"""

from brain.general.engines.planning import PlanningEngine

__all__ = ["PlanningEngine"]
