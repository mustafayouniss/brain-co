"""Compatibility shim for MeshRouter.

Re-exports canonical MeshRouter from brain.general.runtime.router.
"""

from brain.general.runtime.router import MeshRouter

__all__ = ["MeshRouter"]
