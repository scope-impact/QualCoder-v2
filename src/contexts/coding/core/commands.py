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
    category_id: str | None = None


@dataclass(frozen=True)
class RenameCodeCommand:
    """Command to rename an existing code."""

    code_id: str
    new_name: str


@dataclass(frozen=True)
class ChangeCodeColorCommand:
    """Command to change a code's color."""

    code_id: str
    new_color: str  # hex color


@dataclass(frozen=True)
class DeleteCodeCommand:
    """Command to delete a code."""

    code_id: str
    delete_segments: bool = (
        False  # If true, delete segments; if false, fail if segments exist
    )


@dataclass(frozen=True)
class UpdateCodeMemoCommand:
    """Command to update a code's memo."""

    code_id: str
    new_memo: str | None


@dataclass(frozen=True)
class MoveCodeToCategoryCommand:
    """Command to move a code to a different category."""

    code_id: str
    category_id: str | None  # None = uncategorized


@dataclass(frozen=True)
class MergeCodesCommand:
    """Command to merge one code into another."""

    source_code_id: str
    target_code_id: str


# ============================================================
# Segment Commands
# ============================================================


@dataclass(frozen=True)
class ApplyCodeCommand:
    """Command to apply a code to a segment of text."""

    code_id: str
    source_id: str
    start_position: int
    end_position: int
    memo: str | None = None
    importance: int = 0


@dataclass(frozen=True)
class RemoveCodeCommand:
    """Command to remove a code from a segment."""

    segment_id: str


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
    parent_id: str | None = None
    memo: str | None = None


@dataclass(frozen=True)
class DeleteCategoryCommand:
    """Command to delete a category."""

    category_id: str
    orphan_strategy: str = "move_to_parent"  # "move_to_parent" | "delete_codes"
