"""
DEPRECATED: Use src.contexts.coding.core.entities instead.

This module re-exports from the new bounded context location for backwards compatibility.
"""

from src.contexts.coding.core.entities import (
    AutoCodeBatch,
    AVSegment,
    BatchId,
    Category,
    Code,
    Color,
    ImageRegion,
    ImageSegment,
    Segment,
    TextPosition,
    TextSegment,
    TimeRange,
)

__all__ = [
    # Value Objects
    "Color",
    "TextPosition",
    "ImageRegion",
    "TimeRange",
    # Entities
    "Code",
    "Category",
    "TextSegment",
    "ImageSegment",
    "AVSegment",
    "Segment",
    # Batch Operations
    "BatchId",
    "AutoCodeBatch",
]
