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

# Invariants - Business rule predicates
from src.domain.coding.invariants import (
    is_valid_code_name,
    is_code_name_unique,
    is_valid_color,
    can_code_be_deleted,
    are_codes_mergeable,
    is_valid_category_name,
    is_category_name_unique,
    is_category_hierarchy_valid,
    can_category_be_deleted,
    is_valid_text_position,
    does_code_exist,
    does_category_exist,
)

# Derivers - Pure event generators
from src.domain.coding.derivers import (
    CodingState,
    derive_create_code,
    derive_rename_code,
    derive_change_code_color,
    derive_update_code_memo,
    derive_delete_code,
    derive_merge_codes,
    derive_move_code_to_category,
    derive_create_category,
    derive_rename_category,
    derive_delete_category,
    derive_apply_code_to_text,
    derive_remove_segment,
    derive_update_segment_memo,
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
    # Invariants
    'is_valid_code_name',
    'is_code_name_unique',
    'is_valid_color',
    'can_code_be_deleted',
    'are_codes_mergeable',
    'is_valid_category_name',
    'is_category_name_unique',
    'is_category_hierarchy_valid',
    'can_category_be_deleted',
    'is_valid_text_position',
    'does_code_exist',
    'does_category_exist',
    # Derivers
    'CodingState',
    'derive_create_code',
    'derive_rename_code',
    'derive_change_code_color',
    'derive_update_code_memo',
    'derive_delete_code',
    'derive_merge_codes',
    'derive_move_code_to_category',
    'derive_create_category',
    'derive_rename_category',
    'derive_delete_category',
    'derive_apply_code_to_text',
    'derive_remove_segment',
    'derive_update_segment_memo',
]
