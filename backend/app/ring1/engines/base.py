"""Compatibility shim for BaseEngine.

Re-exports canonical BaseEngine from brain.general.engines.base.
"""

from brain.general.engines.base import BaseEngine

__all__ = ["BaseEngine"]
