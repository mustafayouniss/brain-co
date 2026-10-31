"""Compatibility shim for PlanStepExecutor.

Re-exports canonical PlanStepExecutor from brain.general.runtime.executor.
"""

from brain.general.runtime.executor import PlanStepExecutor

__all__ = ["PlanStepExecutor"]
