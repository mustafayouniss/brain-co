"""Compatibility shim for RuntimeDispatcher.

Re-exports canonical RuntimeDispatcher from brain.general.runtime.dispatcher.
"""

from brain.general.runtime.dispatcher import DispatcherError, RuntimeDispatcher

__all__ = ["DispatcherError", "RuntimeDispatcher"]
