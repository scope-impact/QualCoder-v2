"""
DEPRECATED: Use src.contexts.cases.core.entities instead.

This module re-exports from the new bounded context location for backwards compatibility.
"""

from src.contexts.cases.core.entities import (
    AttributeType,
    Case,
    CaseAttribute,
)

__all__ = [
    "AttributeType",
    "CaseAttribute",
    "Case",
]
