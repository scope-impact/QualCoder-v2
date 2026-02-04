"""
Coding Command Handlers.

Functional command handlers for coding operations following the 5-step pattern.
Following ddd-workshop pattern, these handlers live inside the bounded context.
"""

from src.contexts.coding.core.commandHandlers.apply_code import apply_code
from src.contexts.coding.core.commandHandlers.batch_apply_codes import (
    BatchApplyCodesResult,
    BatchOperationResult,
    batch_apply_codes,
)
from src.contexts.coding.core.commandHandlers.change_code_color import change_code_color
from src.contexts.coding.core.commandHandlers.create_category import create_category
from src.contexts.coding.core.commandHandlers.create_code import create_code
from src.contexts.coding.core.commandHandlers.delete_category import delete_category
from src.contexts.coding.core.commandHandlers.delete_code import delete_code
from src.contexts.coding.core.commandHandlers.merge_codes import merge_codes
from src.contexts.coding.core.commandHandlers.move_code_to_category import (
    move_code_to_category,
)
from src.contexts.coding.core.commandHandlers.queries import (
    get_all_categories,
    get_all_codes,
    get_code,
    get_segments_for_code,
    get_segments_for_source,
)
from src.contexts.coding.core.commandHandlers.remove_segment import remove_segment
from src.contexts.coding.core.commandHandlers.rename_code import rename_code
from src.contexts.coding.core.commandHandlers.update_code_memo import update_code_memo

__all__ = [
    # Code use cases
    "create_code",
    "rename_code",
    "change_code_color",
    "delete_code",
    "merge_codes",
    "update_code_memo",
    "move_code_to_category",
    # Segment use cases
    "apply_code",
    "batch_apply_codes",
    "BatchApplyCodesResult",
    "BatchOperationResult",
    "remove_segment",
    # Category use cases
    "create_category",
    "delete_category",
    # Queries
    "get_all_codes",
    "get_code",
    "get_segments_for_source",
    "get_segments_for_code",
    "get_all_categories",
]
