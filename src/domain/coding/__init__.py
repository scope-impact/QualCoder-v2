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
    # Value Objects
    Color,
    TextPosition,
    ImageRegion,
    TimeRange,
    # Entities
    Code,
    Category,
    TextSegment,
    ImageSegment,
    AVSegment,
    Segment,
)

from src.domain.coding.events import (
    # Code Events
    CodeCreated,
    CodeRenamed,
    CodeColorChanged,
    CodeMemoUpdated,
    CodeDeleted,
    CodesMerged,
    CodeMovedToCategory,
    # Category Events
    CategoryCreated,
    CategoryRenamed,
    CategoryDeleted,
    # Segment Events
    SegmentCoded,
    SegmentUncoded,
    SegmentMemoUpdated,
    # Type Aliases
    CodeEvent,
    CategoryEvent,
    SegmentEvent,
    CodingEvent,
)

__all__ = [
    # Value Objects
    'Color',
    'TextPosition',
    'ImageRegion',
    'TimeRange',
    # Entities
    'Code',
    'Category',
    'TextSegment',
    'ImageSegment',
    'AVSegment',
    'Segment',
    # Code Events
    'CodeCreated',
    'CodeRenamed',
    'CodeColorChanged',
    'CodeMemoUpdated',
    'CodeDeleted',
    'CodesMerged',
    'CodeMovedToCategory',
    # Category Events
    'CategoryCreated',
    'CategoryRenamed',
    'CategoryDeleted',
    # Segment Events
    'SegmentCoded',
    'SegmentUncoded',
    'SegmentMemoUpdated',
    # Type Aliases
    'CodeEvent',
    'CategoryEvent',
    'SegmentEvent',
    'CodingEvent',
]
