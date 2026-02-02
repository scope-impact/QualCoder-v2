"""
Application layer for the Coding bounded context.

Provides functional use cases for coding operations and
CodingSignalBridge for reactive UI updates.
"""

from src.application.coding.signal_bridge import (
    CategoryPayload,
    CodeMergePayload,
    CodePayload,
    CodingSignalBridge,
    SegmentPayload,
)
from src.application.coding.usecases import (
    apply_code,
    change_code_color,
    create_category,
    create_code,
    delete_category,
    delete_code,
    get_all_categories,
    get_all_codes,
    get_code,
    get_segments_for_code,
    get_segments_for_source,
    merge_codes,
    move_code_to_category,
    remove_segment,
    rename_code,
    update_code_memo,
)

__all__ = [
    # Signal Bridge
    "CategoryPayload",
    "CodeMergePayload",
    "CodePayload",
    "CodingSignalBridge",
    "SegmentPayload",
    # Use cases
    "apply_code",
    "change_code_color",
    "create_category",
    "create_code",
    "delete_category",
    "delete_code",
    "get_all_categories",
    "get_all_codes",
    "get_code",
    "get_segments_for_code",
    "get_segments_for_source",
    "merge_codes",
    "move_code_to_category",
    "remove_segment",
    "rename_code",
    "update_code_memo",
]
