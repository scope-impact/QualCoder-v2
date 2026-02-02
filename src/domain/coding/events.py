"""
DEPRECATED: Use src.contexts.coding.core.events instead.

This module re-exports from the new bounded context location for backwards compatibility.
"""

from src.contexts.coding.core.events import (
    BatchCreated,
    BatchEvent,
    BatchUndone,
    CategoryCreated,
    CategoryDeleted,
    CategoryEvent,
    CategoryRenamed,
    CodeColorChanged,
    CodeCreated,
    CodeDeleted,
    CodeEvent,
    CodeMemoUpdated,
    CodeMovedToCategory,
    CodeRenamed,
    CodesMerged,
    CodingEvent,
    SegmentCoded,
    SegmentEvent,
    SegmentMemoUpdated,
    SegmentUncoded,
)

__all__ = [
    # Code Events
    "CodeCreated",
    "CodeRenamed",
    "CodeColorChanged",
    "CodeMemoUpdated",
    "CodeDeleted",
    "CodesMerged",
    "CodeMovedToCategory",
    # Category Events
    "CategoryCreated",
    "CategoryRenamed",
    "CategoryDeleted",
    # Segment Events
    "SegmentCoded",
    "SegmentUncoded",
    "SegmentMemoUpdated",
    # Batch Events
    "BatchCreated",
    "BatchUndone",
    # Type Aliases
    "CodeEvent",
    "CategoryEvent",
    "SegmentEvent",
    "BatchEvent",
    "CodingEvent",
]
