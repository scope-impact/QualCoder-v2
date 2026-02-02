"""
DEPRECATED: Use src.contexts.coding.core.failure_events instead.

This module re-exports from the new bounded context location for backwards compatibility.
"""

from src.contexts.coding.core.failure_events import (
    BatchFailureEvent,
    # Batch Failure Events
    BatchNotCreated,
    BatchNotUndone,
    CategoryFailureEvent,
    # Category Failure Events
    CategoryNotCreated,
    CategoryNotDeleted,
    CategoryNotRenamed,
    # Type Unions
    CodeFailureEvent,
    # Code Failure Events
    CodeNotCreated,
    CodeNotDeleted,
    CodeNotMoved,
    CodeNotRenamed,
    CodeNotUpdated,
    CodesNotMerged,
    CodingContextFailureEvent,
    SegmentFailureEvent,
    # Segment Failure Events
    SegmentNotCoded,
    SegmentNotRemoved,
    SegmentNotUpdated,
)

__all__ = [
    # Code Failure Events
    "CodeNotCreated",
    "CodeNotRenamed",
    "CodeNotUpdated",
    "CodeNotDeleted",
    "CodesNotMerged",
    "CodeNotMoved",
    # Category Failure Events
    "CategoryNotCreated",
    "CategoryNotRenamed",
    "CategoryNotDeleted",
    # Segment Failure Events
    "SegmentNotCoded",
    "SegmentNotRemoved",
    "SegmentNotUpdated",
    # Batch Failure Events
    "BatchNotCreated",
    "BatchNotUndone",
    # Type Unions
    "CodeFailureEvent",
    "CategoryFailureEvent",
    "SegmentFailureEvent",
    "BatchFailureEvent",
    "CodingContextFailureEvent",
]
