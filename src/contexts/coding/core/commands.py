"""
Coding Commands - Command DTOs for coding operations.

These dataclasses represent the input for coding use cases.
All commands are immutable (frozen) and contain only primitive types.
"""

from __future__ import annotations

from dataclasses import dataclass

# ============================================================
# Code Commands
# ============================================================


@dataclass(frozen=True)
class CreateCodeCommand:
    """Command to create a new code."""

    name: str
    color: str  # hex color
    memo: str | None = None
    category_id: int | None = None


@dataclass(frozen=True)
class RenameCodeCommand:
    """Command to rename an existing code."""

    code_id: int
    new_name: str


@dataclass(frozen=True)
class ChangeCodeColorCommand:
    """Command to change a code's color."""

    code_id: int
    new_color: str  # hex color


@dataclass(frozen=True)
class DeleteCodeCommand:
    """Command to delete a code."""

    code_id: int
    delete_segments: bool = (
        False  # If true, delete segments; if false, fail if segments exist
    )


@dataclass(frozen=True)
class UpdateCodeMemoCommand:
    """Command to update a code's memo."""

    code_id: int
    new_memo: str | None


@dataclass(frozen=True)
class MoveCodeToCategoryCommand:
    """Command to move a code to a different category."""

    code_id: int
    category_id: int | None  # None = uncategorized


@dataclass(frozen=True)
class MergeCodesCommand:
    """Command to merge one code into another."""

    source_code_id: int
    target_code_id: int


# ============================================================
# Segment Commands
# ============================================================


@dataclass(frozen=True)
class ApplyCodeCommand:
    """Command to apply a code to a segment of text."""

    code_id: int
    source_id: int
    start_position: int
    end_position: int
    memo: str | None = None
    importance: int = 0


@dataclass(frozen=True)
class RemoveCodeCommand:
    """Command to remove a code from a segment."""

    segment_id: int


@dataclass(frozen=True)
class BatchApplyCodesCommand:
    """
    Command to apply multiple codes to multiple text segments in a single batch.

    Designed for AI agents to efficiently apply multiple codes at once,
    reducing round-trips and improving performance.

    Each item in `operations` is an ApplyCodeCommand.
    """

    operations: tuple[ApplyCodeCommand, ...]


# ============================================================
# Category Commands
# ============================================================


@dataclass(frozen=True)
class CreateCategoryCommand:
    """Command to create a new category."""

    name: str
    parent_id: int | None = None
    memo: str | None = None


@dataclass(frozen=True)
class DeleteCategoryCommand:
    """Command to delete a category."""

    category_id: int
    orphan_strategy: str = "move_to_parent"  # "move_to_parent" | "delete_codes"
