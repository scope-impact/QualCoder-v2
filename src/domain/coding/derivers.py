"""
Coding Context: Derivers (Pure Event Generators)

Pure functions that compose invariants and derive domain events.
These are the core of the Functional DDD pattern.

Architecture:
    Deriver: (command, state) -> SuccessEvent | FailureEvent
    - Pure function, no I/O, no side effects
    - Composes multiple invariants
    - Returns a discriminated union (success or failure event)
    - Fully testable in isolation
"""

from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from typing import Iterable, Callable, Optional, Union
from uuid import uuid4

from src.domain.shared.types import (
    CodeId,
    CategoryId,
    SourceId,
    SegmentId,
    Success,
    Failure,
    DuplicateName,
    CodeNotFound,
    SourceNotFound,
    InvalidPosition,
    EmptyName,
)
from src.domain.coding.entities import (
    Code,
    Category,
    TextSegment,
    Color,
    TextPosition,
    Segment,
)
from src.domain.coding.events import (
    CodeCreated,
    CodeRenamed,
    CodeColorChanged,
    CodeMemoUpdated,
    CodeDeleted,
    CodesMerged,
    CodeMovedToCategory,
    CategoryCreated,
    CategoryRenamed,
    CategoryDeleted,
    SegmentCoded,
    SegmentUncoded,
    SegmentMemoUpdated,
)
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
    count_segments_for_code,
    count_codes_in_category,
)


# ============================================================
# State Containers (Input to Derivers)
# ============================================================

@dataclass(frozen=True)
class CodingState:
    """
    State container for coding context derivers.

    Contains all the context needed to validate operations.
    Passed to derivers along with the command.
    """
    existing_codes: tuple[Code, ...] = ()
    existing_categories: tuple[Category, ...] = ()
    existing_segments: tuple[Segment, ...] = ()
    source_length: Optional[int] = None  # For text segment validation
    source_exists: bool = True


# ============================================================
# Failure Reasons (Additional to shared types)
# ============================================================

@dataclass(frozen=True)
class CategoryNotFound:
    """Category does not exist."""
    category_id: CategoryId
    message: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(
            self, 'message',
            f"Category with id {self.category_id.value} not found"
        )


@dataclass(frozen=True)
class CyclicHierarchy:
    """Operation would create a cycle in category hierarchy."""
    category_id: CategoryId
    parent_id: CategoryId
    message: str = "Operation would create a cycle in category hierarchy"


@dataclass(frozen=True)
class HasReferences:
    """Entity has references and cannot be deleted."""
    entity_type: str
    entity_id: int
    reference_count: int
    message: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(
            self, 'message',
            f"{self.entity_type} has {self.reference_count} references"
        )


@dataclass(frozen=True)
class SameEntity:
    """Cannot perform operation on the same entity."""
    entity_type: str
    message: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(
            self, 'message',
            f"Cannot merge {self.entity_type} with itself"
        )


# ============================================================
# Code Derivers
# ============================================================

def derive_create_code(
    name: str,
    color: Color,
    memo: Optional[str],
    category_id: Optional[CategoryId],
    owner: Optional[str],
    state: CodingState,
) -> CodeCreated | Failure:
    """
    Derive a CodeCreated event or failure.

    Args:
        name: Name for the new code
        color: Color for the new code
        memo: Optional memo
        category_id: Optional category to place code in
        owner: Owner identifier
        state: Current coding state

    Returns:
        CodeCreated event or Failure with reason
    """
    # Validate name
    if not is_valid_code_name(name):
        return Failure(EmptyName())

    # Check uniqueness
    if not is_code_name_unique(name, state.existing_codes):
        return Failure(DuplicateName(name))

    # Validate category exists if specified
    if category_id is not None:
        if not does_category_exist(category_id, state.existing_categories):
            return Failure(CategoryNotFound(category_id))

    # Generate new ID and create event
    new_id = CodeId.new()

    return CodeCreated.create(
        code_id=new_id,
        name=name,
        color=color,
        memo=memo,
        category_id=category_id,
        owner=owner,
    )


def derive_rename_code(
    code_id: CodeId,
    new_name: str,
    state: CodingState,
) -> CodeRenamed | Failure:
    """
    Derive a CodeRenamed event or failure.

    Args:
        code_id: ID of code to rename
        new_name: New name for the code
        state: Current coding state

    Returns:
        CodeRenamed event or Failure with reason
    """
    # Find the code
    code = next((c for c in state.existing_codes if c.id == code_id), None)
    if code is None:
        return Failure(CodeNotFound(code_id))

    # Validate new name
    if not is_valid_code_name(new_name):
        return Failure(EmptyName())

    # Check uniqueness (excluding current code)
    if not is_code_name_unique(new_name, state.existing_codes, exclude_code_id=code_id):
        return Failure(DuplicateName(new_name))

    return CodeRenamed.create(
        code_id=code_id,
        old_name=code.name,
        new_name=new_name,
    )


def derive_change_code_color(
    code_id: CodeId,
    new_color: Color,
    state: CodingState,
) -> CodeColorChanged | Failure:
    """
    Derive a CodeColorChanged event or failure.

    Args:
        code_id: ID of code to update
        new_color: New color for the code
        state: Current coding state

    Returns:
        CodeColorChanged event or Failure with reason
    """
    # Find the code
    code = next((c for c in state.existing_codes if c.id == code_id), None)
    if code is None:
        return Failure(CodeNotFound(code_id))

    return CodeColorChanged.create(
        code_id=code_id,
        old_color=code.color,
        new_color=new_color,
    )


def derive_update_code_memo(
    code_id: CodeId,
    new_memo: Optional[str],
    state: CodingState,
) -> CodeMemoUpdated | Failure:
    """
    Derive a CodeMemoUpdated event or failure.

    Args:
        code_id: ID of code to update
        new_memo: New memo content
        state: Current coding state

    Returns:
        CodeMemoUpdated event or Failure with reason
    """
    code = next((c for c in state.existing_codes if c.id == code_id), None)
    if code is None:
        return Failure(CodeNotFound(code_id))

    return CodeMemoUpdated.create(
        code_id=code_id,
        old_memo=code.memo,
        new_memo=new_memo,
    )


def derive_delete_code(
    code_id: CodeId,
    delete_segments: bool,
    state: CodingState,
) -> CodeDeleted | Failure:
    """
    Derive a CodeDeleted event or failure.

    Args:
        code_id: ID of code to delete
        delete_segments: If True, also delete associated segments
        state: Current coding state

    Returns:
        CodeDeleted event or Failure with reason
    """
    code = next((c for c in state.existing_codes if c.id == code_id), None)
    if code is None:
        return Failure(CodeNotFound(code_id))

    # Check if can be deleted
    if not can_code_be_deleted(code_id, state.existing_segments, delete_segments):
        count = count_segments_for_code(code_id, state.existing_segments)
        return Failure(HasReferences("Code", code_id.value, count))

    segments_removed = count_segments_for_code(code_id, state.existing_segments) if delete_segments else 0

    return CodeDeleted.create(
        code_id=code_id,
        name=code.name,
        segments_removed=segments_removed,
    )


def derive_merge_codes(
    source_code_id: CodeId,
    target_code_id: CodeId,
    state: CodingState,
) -> CodesMerged | Failure:
    """
    Derive a CodesMerged event or failure.

    Args:
        source_code_id: Code to merge from (will be deleted)
        target_code_id: Code to merge into (will remain)
        state: Current coding state

    Returns:
        CodesMerged event or Failure with reason
    """
    if source_code_id == target_code_id:
        return Failure(SameEntity("code"))

    source_code = next((c for c in state.existing_codes if c.id == source_code_id), None)
    if source_code is None:
        return Failure(CodeNotFound(source_code_id))

    target_code = next((c for c in state.existing_codes if c.id == target_code_id), None)
    if target_code is None:
        return Failure(CodeNotFound(target_code_id))

    segments_moved = count_segments_for_code(source_code_id, state.existing_segments)

    return CodesMerged.create(
        source_code_id=source_code_id,
        source_code_name=source_code.name,
        target_code_id=target_code_id,
        target_code_name=target_code.name,
        segments_moved=segments_moved,
    )


def derive_move_code_to_category(
    code_id: CodeId,
    new_category_id: Optional[CategoryId],
    state: CodingState,
) -> CodeMovedToCategory | Failure:
    """
    Derive a CodeMovedToCategory event or failure.

    Args:
        code_id: ID of code to move
        new_category_id: Target category (None = uncategorized)
        state: Current coding state

    Returns:
        CodeMovedToCategory event or Failure with reason
    """
    code = next((c for c in state.existing_codes if c.id == code_id), None)
    if code is None:
        return Failure(CodeNotFound(code_id))

    if new_category_id is not None:
        if not does_category_exist(new_category_id, state.existing_categories):
            return Failure(CategoryNotFound(new_category_id))

    return CodeMovedToCategory.create(
        code_id=code_id,
        old_category_id=code.category_id,
        new_category_id=new_category_id,
    )


# ============================================================
# Category Derivers
# ============================================================

def derive_create_category(
    name: str,
    parent_id: Optional[CategoryId],
    memo: Optional[str],
    owner: Optional[str],
    state: CodingState,
) -> CategoryCreated | Failure:
    """
    Derive a CategoryCreated event or failure.

    Args:
        name: Name for the new category
        parent_id: Optional parent category
        memo: Optional memo
        owner: Owner identifier
        state: Current coding state

    Returns:
        CategoryCreated event or Failure with reason
    """
    if not is_valid_category_name(name):
        return Failure(EmptyName())

    if not is_category_name_unique(name, state.existing_categories):
        return Failure(DuplicateName(name))

    if parent_id is not None:
        if not does_category_exist(parent_id, state.existing_categories):
            return Failure(CategoryNotFound(parent_id))

    new_id = CategoryId(value=int(uuid4().int % 1_000_000))

    return CategoryCreated.create(
        category_id=new_id,
        name=name,
        parent_id=parent_id,
        memo=memo,
    )


def derive_rename_category(
    category_id: CategoryId,
    new_name: str,
    state: CodingState,
) -> CategoryRenamed | Failure:
    """
    Derive a CategoryRenamed event or failure.
    """
    category = next((c for c in state.existing_categories if c.id == category_id), None)
    if category is None:
        return Failure(CategoryNotFound(category_id))

    if not is_valid_category_name(new_name):
        return Failure(EmptyName())

    if not is_category_name_unique(new_name, state.existing_categories, exclude_category_id=category_id):
        return Failure(DuplicateName(new_name))

    return CategoryRenamed.create(
        category_id=category_id,
        old_name=category.name,
        new_name=new_name,
    )


def derive_delete_category(
    category_id: CategoryId,
    orphan_strategy: str,  # "move_to_parent" | "delete_codes"
    state: CodingState,
) -> CategoryDeleted | Failure:
    """
    Derive a CategoryDeleted event or failure.

    Args:
        category_id: ID of category to delete
        orphan_strategy: How to handle orphaned codes
        state: Current coding state

    Returns:
        CategoryDeleted event or Failure with reason
    """
    category = next((c for c in state.existing_categories if c.id == category_id), None)
    if category is None:
        return Failure(CategoryNotFound(category_id))

    # With a strategy, deletion is allowed
    codes_orphaned = count_codes_in_category(category_id, state.existing_codes)

    return CategoryDeleted.create(
        category_id=category_id,
        name=category.name,
        codes_orphaned=codes_orphaned,
    )


# ============================================================
# Segment Derivers
# ============================================================

def derive_apply_code_to_text(
    code_id: CodeId,
    source_id: SourceId,
    start: int,
    end: int,
    selected_text: str,
    memo: Optional[str],
    importance: int,
    owner: Optional[str],
    state: CodingState,
) -> SegmentCoded | Failure:
    """
    Derive a SegmentCoded event or failure for text coding.

    Args:
        code_id: Code to apply
        source_id: Source document
        start: Start position in text
        end: End position in text
        selected_text: The selected text content
        memo: Optional memo
        importance: Importance level (0-2)
        owner: Owner identifier
        state: Current coding state

    Returns:
        SegmentCoded event or Failure with reason
    """
    # Check code exists
    code = next((c for c in state.existing_codes if c.id == code_id), None)
    if code is None:
        return Failure(CodeNotFound(code_id))

    # Check source exists
    if not state.source_exists:
        return Failure(SourceNotFound(source_id))

    # Validate position
    try:
        position = TextPosition(start=start, end=end)
    except ValueError:
        return Failure(InvalidPosition(start, end, state.source_length or 0))

    if state.source_length is not None:
        if not is_valid_text_position(position, state.source_length):
            return Failure(InvalidPosition(start, end, state.source_length))

    # Generate segment ID
    segment_id = SegmentId.new()

    # Find source name (placeholder - would come from source repository)
    source_name = f"Source-{source_id.value}"

    return SegmentCoded.create(
        segment_id=segment_id,
        code_id=code_id,
        code_name=code.name,
        source_id=source_id,
        source_name=source_name,
        position=position,
        selected_text=selected_text,
        memo=memo,
        owner=owner,
    )


def derive_remove_segment(
    segment_id: SegmentId,
    state: CodingState,
) -> SegmentUncoded | Failure:
    """
    Derive a SegmentUncoded event or failure.

    Args:
        segment_id: ID of segment to remove
        state: Current coding state

    Returns:
        SegmentUncoded event or Failure with reason
    """
    # Find the segment
    segment = next(
        (s for s in state.existing_segments if s.id == segment_id),
        None
    )

    if segment is None:
        # Segment not found - this is actually a no-op, return failure
        @dataclass(frozen=True)
        class SegmentNotFound:
            segment_id: SegmentId
            message: str = ""

            def __post_init__(self) -> None:
                object.__setattr__(
                    self, 'message',
                    f"Segment with id {self.segment_id.value} not found"
                )

        return Failure(SegmentNotFound(segment_id))

    return SegmentUncoded.create(
        segment_id=segment_id,
        code_id=segment.code_id,
        source_id=segment.source_id,
    )


def derive_update_segment_memo(
    segment_id: SegmentId,
    new_memo: Optional[str],
    state: CodingState,
) -> SegmentMemoUpdated | Failure:
    """
    Derive a SegmentMemoUpdated event or failure.
    """
    segment = next(
        (s for s in state.existing_segments if s.id == segment_id),
        None
    )

    if segment is None:
        @dataclass(frozen=True)
        class SegmentNotFound:
            segment_id: SegmentId
            message: str = ""

            def __post_init__(self) -> None:
                object.__setattr__(
                    self, 'message',
                    f"Segment with id {self.segment_id.value} not found"
                )

        return Failure(SegmentNotFound(segment_id))

    old_memo = getattr(segment, 'memo', None)

    return SegmentMemoUpdated.create(
        segment_id=segment_id,
        old_memo=old_memo,
        new_memo=new_memo,
    )
