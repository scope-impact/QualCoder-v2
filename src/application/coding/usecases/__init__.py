"""
Coding Use Cases.

Functional use cases for coding operations following the 5-step pattern.
"""

from src.application.coding.usecases.apply_code import apply_code
from src.application.coding.usecases.change_code_color import change_code_color
from src.application.coding.usecases.create_category import create_category
from src.application.coding.usecases.create_code import create_code
from src.application.coding.usecases.delete_category import delete_category
from src.application.coding.usecases.delete_code import delete_code
from src.application.coding.usecases.merge_codes import merge_codes
from src.application.coding.usecases.move_code_to_category import move_code_to_category
from src.application.coding.usecases.queries import (
    get_all_categories,
    get_all_codes,
    get_code,
    get_segments_for_code,
    get_segments_for_source,
)
from src.application.coding.usecases.remove_segment import remove_segment
from src.application.coding.usecases.rename_code import rename_code
from src.application.coding.usecases.update_code_memo import update_code_memo

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
