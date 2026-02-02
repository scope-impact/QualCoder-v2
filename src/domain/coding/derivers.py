"""
DEPRECATED: Use src.contexts.coding.core.derivers instead.

This module re-exports from the new bounded context location for backwards compatibility.
"""

from src.contexts.coding.core.derivers import (
    BatchNotFound,
    CategoryNotFound,
    CodingState,
    CyclicHierarchy,
    HasReferences,
    SameEntity,
    SegmentNotFound,
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

__all__ = [
    # State Containers
    "CodingState",
    # Failure Reasons
    "CategoryNotFound",
    "CyclicHierarchy",
    "HasReferences",
    "SameEntity",
    "SegmentNotFound",
    "BatchNotFound",
    # Code Derivers
    "derive_create_code",
    "derive_rename_code",
    "derive_change_code_color",
    "derive_update_code_memo",
    "derive_delete_code",
    "derive_merge_codes",
    "derive_move_code_to_category",
    # Category Derivers
    "derive_create_category",
    "derive_rename_category",
    "derive_delete_category",
    # Segment Derivers
    "derive_apply_code_to_text",
    "derive_remove_segment",
    "derive_update_segment_memo",
    # Batch Derivers
    "derive_create_batch",
    "derive_undo_batch",
]
