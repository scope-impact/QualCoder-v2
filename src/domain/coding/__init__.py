"""
Coding Context - Core Domain
Qualitative data coding and analysis.

This is the CORE domain - the heart of QualCoder.
It defines how researchers apply semantic codes to research data.

Contracts exported:
- Entities: Code, Category, TextSegment, ImageSegment, AVSegment
- Value Objects: Color, TextPosition, ImageRegion, TimeRange
- Events: CodeCreated, CodeDeleted, SegmentCoded, etc.
"""

from src.domain.coding.entities import (
    AVSegment,
    Category,
    # Entities
    Code,
    # Value Objects
    Color,
    ImageRegion,
    ImageSegment,
    Segment,
    TextPosition,
    TextSegment,
    TimeRange,
)
from src.domain.coding.events import (
    # Category Events
    CategoryCreated,
    CategoryDeleted,
    CategoryEvent,
    CategoryRenamed,
    CodeColorChanged,
    # Code Events
    CodeCreated,
    CodeDeleted,
    # Type Aliases
    CodeEvent,
    CodeMemoUpdated,
    CodeMovedToCategory,
    CodeRenamed,
    CodesMerged,
    CodingEvent,
    # Segment Events
    SegmentCoded,
    SegmentEvent,
    SegmentMemoUpdated,
    SegmentUncoded,
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
    # Type Aliases
    "CodeEvent",
    "CategoryEvent",
    "SegmentEvent",
    "CodingEvent",
]
