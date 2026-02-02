"""
Coding Context - Core Domain
Qualitative data coding and analysis.

This is the CORE domain - the heart of QualCoder.
It defines how researchers apply semantic codes to research data.

Contracts exported:
- Entities: Code, Category, TextSegment, ImageSegment, AVSegment
- Value Objects: Color, TextPosition, ImageRegion, TimeRange
- Events: CodeCreated, CodeDeleted, SegmentCoded, etc.
- Invariants: Business rule predicates
- Derivers: Pure event generators
"""

# Entities
# Derivers
from src.contexts.coding.core.derivers import (
    CodingState,
    derive_apply_code_to_text,
    derive_change_code_color,
    derive_create_batch,
    derive_create_category,
    derive_create_code,
    derive_delete_category,
    derive_delete_code,
    derive_merge_codes,
    derive_move_code_to_category,
    derive_remove_segment,
    derive_rename_category,
    derive_rename_code,
    derive_undo_batch,
    derive_update_code_memo,
    derive_update_segment_memo,
)
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

# Events
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

# Failure Events
from src.contexts.coding.core.failure_events import (
    BatchFailureEvent,
    BatchNotCreated,
    BatchNotUndone,
    CategoryFailureEvent,
    CategoryNotCreated,
    CategoryNotDeleted,
    CategoryNotRenamed,
    CodeFailureEvent,
    CodeNotCreated,
    CodeNotDeleted,
    CodeNotMoved,
    CodeNotRenamed,
    CodeNotUpdated,
    CodesNotMerged,
    CodingContextFailureEvent,
    SegmentFailureEvent,
    SegmentNotCoded,
    SegmentNotRemoved,
    SegmentNotUpdated,
)

# Invariants
from src.contexts.coding.core.invariants import (
    are_codes_mergeable,
    can_category_be_deleted,
    can_code_be_deleted,
    count_codes_in_category,
    count_segments_for_code,
    does_category_exist,
    does_code_exist,
    does_segment_overlap,
    does_source_exist,
    is_category_hierarchy_valid,
    is_category_name_unique,
    is_code_name_unique,
    is_valid_category_name,
    is_valid_code_name,
    is_valid_color,
    is_valid_image_region,
    is_valid_importance,
    is_valid_text_position,
    is_valid_time_range,
)

# Services
from src.contexts.coding.core.services import (
    MatchScope,
    MatchType,
    TextMatch,
    TextMatcher,
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
    "BatchId",
    "AutoCodeBatch",
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
    # Failure Events
    "CodeNotCreated",
    "CodeNotRenamed",
    "CodeNotUpdated",
    "CodeNotDeleted",
    "CodesNotMerged",
    "CodeNotMoved",
    "CategoryNotCreated",
    "CategoryNotRenamed",
    "CategoryNotDeleted",
    "SegmentNotCoded",
    "SegmentNotRemoved",
    "SegmentNotUpdated",
    "BatchNotCreated",
    "BatchNotUndone",
    "CodeFailureEvent",
    "CategoryFailureEvent",
    "SegmentFailureEvent",
    "BatchFailureEvent",
    "CodingContextFailureEvent",
    # Invariants
    "is_valid_code_name",
    "is_code_name_unique",
    "is_valid_color",
    "can_code_be_deleted",
    "are_codes_mergeable",
    "is_valid_category_name",
    "is_category_name_unique",
    "is_category_hierarchy_valid",
    "can_category_be_deleted",
    "is_valid_text_position",
    "is_valid_image_region",
    "is_valid_time_range",
    "is_valid_importance",
    "does_segment_overlap",
    "does_code_exist",
    "does_category_exist",
    "does_source_exist",
    "count_segments_for_code",
    "count_codes_in_category",
    # Derivers
    "CodingState",
    "derive_create_code",
    "derive_rename_code",
    "derive_change_code_color",
    "derive_update_code_memo",
    "derive_delete_code",
    "derive_merge_codes",
    "derive_move_code_to_category",
    "derive_create_category",
    "derive_rename_category",
    "derive_delete_category",
    "derive_apply_code_to_text",
    "derive_remove_segment",
    "derive_update_segment_memo",
    "derive_create_batch",
    "derive_undo_batch",
    # Services
    "MatchScope",
    "MatchType",
    "TextMatch",
    "TextMatcher",
]
