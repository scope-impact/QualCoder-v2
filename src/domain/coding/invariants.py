"""
DEPRECATED: Use src.contexts.coding.core.invariants instead.

This module re-exports from the new bounded context location for backwards compatibility.
"""

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

__all__ = [
    # Code Invariants
    "is_valid_code_name",
    "is_code_name_unique",
    "is_valid_color",
    "can_code_be_deleted",
    "are_codes_mergeable",
    # Category Invariants
    "is_valid_category_name",
    "is_category_name_unique",
    "is_category_hierarchy_valid",
    "can_category_be_deleted",
    # Segment Invariants
    "is_valid_text_position",
    "is_valid_image_region",
    "is_valid_time_range",
    "is_valid_importance",
    "does_segment_overlap",
    # Cross-Entity Invariants
    "does_code_exist",
    "does_category_exist",
    "does_source_exist",
    "count_segments_for_code",
    "count_codes_in_category",
]
