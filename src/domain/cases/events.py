"""
DEPRECATED: Use src.contexts.cases.core.events instead.

This module re-exports from the new bounded context location for backwards compatibility.
"""

from src.contexts.cases.core.events import (
    CaseAttributeRemoved,
    CaseAttributeSet,
    CaseCreated,
    CaseRemoved,
    CaseUpdated,
    SourceLinkedToCase,
    SourceUnlinkedFromCase,
)

__all__ = [
    # Case Lifecycle Events
    "CaseCreated",
    "CaseUpdated",
    "CaseRemoved",
    # Case Attribute Events
    "CaseAttributeSet",
    "CaseAttributeRemoved",
    # Case-Source Link Events
    "SourceLinkedToCase",
    "SourceUnlinkedFromCase",
]
