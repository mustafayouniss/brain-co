"""Compatibility shim for LogisticsFleetDomainExtension.

Re-exports canonical LogisticsFleetDomainExtension from brain.extensions.logistics.
"""

from brain.extensions.logistics.extension import LogisticsFleetDomainExtension

__all__ = ["LogisticsFleetDomainExtension"]
