"""Compatibility shim for SalesDomainExtension.

Re-exports canonical SalesDomainExtension from brain.extensions.sales.
"""

from brain.extensions.sales.extension import SalesDomainExtension

__all__ = ["SalesDomainExtension"]
