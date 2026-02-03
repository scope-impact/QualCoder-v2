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
from uuid import uuid4

from src.contexts.coding.core.entities import (
    AutoCodeBatch,
    BatchId,
    Category,
    Code,
    Color,
    Segment,
    TextPosition,
)
from src.contexts.coding.core.events import (
    BatchCreated,
    BatchUndone,
    CategoryCreated,
    CategoryDeleted,
    CategoryRenamed,
    CodeColorChanged,
    CodeCreated,
    CodeDeleted,
    CodeMemoUpdated,
    CodeMovedToCategory,
    CodeRenamed,
    CodesMerged,
    SegmentCoded,
    SegmentMemoUpdated,
    SegmentUncoded,
)
from src.contexts.coding.core.failure_events import (
    BatchNotCreated,
    BatchNotUndone,
    CategoryNotCreated,
    CategoryNotDeleted,
    CategoryNotRenamed,
    CodeNotCreated,
    CodeNotDeleted,
    CodeNotMoved,
    CodeNotRenamed,
    CodeNotUpdated,
    CodesNotMerged,
    SegmentNotCoded,
    SegmentNotRemoved,
    SegmentNotUpdated,
)
from src.contexts.coding.core.invariants import (
    can_code_be_deleted,
    count_codes_in_category,
    count_segments_for_code,
    does_category_exist,
    is_category_name_unique,
    is_code_name_unique,
    is_valid_category_name,
    is_valid_code_name,
    is_valid_text_position,
)
from src.shared.common.types import (
    CategoryId,
    CodeId,
    SegmentId,
    SourceId,
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
    existing_batches: tuple[AutoCodeBatch, ...] = ()
    source_length: int | None = None  # For text segment validation
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
            self, "message", f"Category with id {self.category_id.value} not found"
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
            self, "message", f"{self.entity_type} has {self.reference_count} references"
        )


@dataclass(frozen=True)
class SameEntity:
    """Cannot perform operation on the same entity."""

    entity_type: str
    message: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "message", f"Cannot merge {self.entity_type} with itself"
        )


@dataclass(frozen=True)
class SegmentNotFound:
    """Segment with given ID was not found."""

    segment_id: SegmentId
    message: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "message", f"Segment with id {self.segment_id.value} not found"
        )


@dataclass(frozen=True)
class BatchNotFound:
    """Batch with given ID was not found."""

    batch_id: BatchId
    message: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "message", f"Batch with id {self.batch_id.value} not found"
        )


# ============================================================
# Code Derivers
# ============================================================


def derive_create_code(
    name: str,
    color: Color,
    memo: str | None,
    category_id: CategoryId | None,
    owner: str | None,
    state: CodingState,
) -> CodeCreated | CodeNotCreated:
    """
    Derive a CodeCreated event or failure event.

    Args:
        name: Name for the new code
        color: Color for the new code
        memo: Optional memo
        category_id: Optional category to place code in
        owner: Owner identifier
        state: Current coding state

    Returns:
        CodeCreated event or CodeNotCreated failure event
    """
    # Validate name
    if not is_valid_code_name(name):
        return CodeNotCreated.empty_name()

    # Check uniqueness
    if not is_code_name_unique(name, state.existing_codes):
        return CodeNotCreated.duplicate_name(name)

    # Validate category exists if specified
    if category_id is not None and not does_category_exist(
        category_id, state.existing_categories
    ):
        return CodeNotCreated.category_not_found(category_id)

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
) -> CodeRenamed | CodeNotRenamed:
    """
    Derive a CodeRenamed event or failure event.

    Args:
        code_id: ID of code to rename
        new_name: New name for the code
        state: Current coding state

    Returns:
        CodeRenamed event or CodeNotRenamed failure event
    """
    # Find the code
    code = next((c for c in state.existing_codes if c.id == code_id), None)
    if code is None:
        return CodeNotRenamed.not_found(code_id)

    # Validate new name
    if not is_valid_code_name(new_name):
        return CodeNotRenamed.empty_name(code_id)

    # Check uniqueness (excluding current code)
    if not is_code_name_unique(new_name, state.existing_codes, exclude_code_id=code_id):
        return CodeNotRenamed.duplicate_name(code_id, new_name)

    return CodeRenamed.create(
        code_id=code_id,
        old_name=code.name,
        new_name=new_name,
    )


def derive_change_code_color(
    code_id: CodeId,
    new_color: Color,
    state: CodingState,
) -> CodeColorChanged | CodeNotUpdated:
    """
    Derive a CodeColorChanged event or failure event.

    Args:
        code_id: ID of code to update
        new_color: New color for the code
        state: Current coding state

    Returns:
        CodeColorChanged event or CodeNotUpdated failure event
    """
    # Find the code
    code = next((c for c in state.existing_codes if c.id == code_id), None)
    if code is None:
        return CodeNotUpdated.not_found(code_id)

    return CodeColorChanged.create(
        code_id=code_id,
        old_color=code.color,
        new_color=new_color,
    )


def derive_update_code_memo(
    code_id: CodeId,
    new_memo: str | None,
    state: CodingState,
) -> CodeMemoUpdated | CodeNotUpdated:
    """
    Derive a CodeMemoUpdated event or failure event.

    Args:
        code_id: ID of code to update
        new_memo: New memo content
        state: Current coding state

    Returns:
        CodeMemoUpdated event or CodeNotUpdated failure event
    """
    code = next((c for c in state.existing_codes if c.id == code_id), None)
    if code is None:
        return CodeNotUpdated.not_found(code_id)

    return CodeMemoUpdated.create(
        code_id=code_id,
        old_memo=code.memo,
        new_memo=new_memo,
    )


def derive_delete_code(
    code_id: CodeId,
    delete_segments: bool,
    state: CodingState,
) -> CodeDeleted | CodeNotDeleted:
    """
    Derive a CodeDeleted event or failure event.

    Args:
        code_id: ID of code to delete
        delete_segments: If True, also delete associated segments
        state: Current coding state

    Returns:
        CodeDeleted event or CodeNotDeleted failure event
    """
    code = next((c for c in state.existing_codes if c.id == code_id), None)
    if code is None:
        return CodeNotDeleted.not_found(code_id)

    # Check if can be deleted
    if not can_code_be_deleted(code_id, state.existing_segments, delete_segments):
        count = count_segments_for_code(code_id, state.existing_segments)
        return CodeNotDeleted.has_references(code_id, count)

    segments_removed = (
        count_segments_for_code(code_id, state.existing_segments)
        if delete_segments
        else 0
    )

    return CodeDeleted.create(
        code_id=code_id,
        name=code.name,
        segments_removed=segments_removed,
    )


def derive_merge_codes(
    source_code_id: CodeId,
    target_code_id: CodeId,
    state: CodingState,
) -> CodesMerged | CodesNotMerged:
    """
    Derive a CodesMerged event or failure event.

    Args:
        source_code_id: Code to merge from (will be deleted)
        target_code_id: Code to merge into (will remain)
        state: Current coding state

    Returns:
        CodesMerged event or CodesNotMerged failure event
    """
    if source_code_id == target_code_id:
        return CodesNotMerged.same_code(source_code_id)

    source_code = next(
        (c for c in state.existing_codes if c.id == source_code_id), None
    )
    if source_code is None:
        return CodesNotMerged.source_not_found(source_code_id)

    target_code = next(
        (c for c in state.existing_codes if c.id == target_code_id), None
    )
    if target_code is None:
        return CodesNotMerged.target_not_found(source_code_id, target_code_id)

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
    new_category_id: CategoryId | None,
    state: CodingState,
) -> CodeMovedToCategory | CodeNotMoved:
    """
    Derive a CodeMovedToCategory event or failure event.

    Args:
        code_id: ID of code to move
        new_category_id: Target category (None = uncategorized)
        state: Current coding state

    Returns:
        CodeMovedToCategory event or CodeNotMoved failure event
    """
    code = next((c for c in state.existing_codes if c.id == code_id), None)
    if code is None:
        return CodeNotMoved.code_not_found(code_id)

    if new_category_id is not None and not does_category_exist(
        new_category_id, state.existing_categories
    ):
        return CodeNotMoved.category_not_found(code_id, new_category_id)

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
    parent_id: CategoryId | None,
    memo: str | None,
    owner: str | None,  # noqa: ARG001 - reserved for audit trail
    state: CodingState,
) -> CategoryCreated | CategoryNotCreated:
    """
    Derive a CategoryCreated event or failure event.

    Args:
        name: Name for the new category
        parent_id: Optional parent category
        memo: Optional memo
        owner: Owner identifier
        state: Current coding state

    Returns:
        CategoryCreated event or CategoryNotCreated failure event
    """
    if not is_valid_category_name(name):
        return CategoryNotCreated.empty_name()

    if not is_category_name_unique(name, state.existing_categories):
        return CategoryNotCreated.duplicate_name(name)

    if parent_id is not None and not does_category_exist(
        parent_id, state.existing_categories
    ):
        return CategoryNotCreated.parent_not_found(parent_id)

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
) -> CategoryRenamed | CategoryNotRenamed:
    """
    Derive a CategoryRenamed event or failure event.
    """
    category = next((c for c in state.existing_categories if c.id == category_id), None)
    if category is None:
        return CategoryNotRenamed.not_found(category_id)

    if not is_valid_category_name(new_name):
        return CategoryNotRenamed.empty_name(category_id)

    if not is_category_name_unique(
        new_name, state.existing_categories, exclude_category_id=category_id
    ):
        return CategoryNotRenamed.duplicate_name(category_id, new_name)

    return CategoryRenamed.create(
        category_id=category_id,
        old_name=category.name,
        new_name=new_name,
    )


def derive_delete_category(
    category_id: CategoryId,
    orphan_strategy: str,  # noqa: ARG001 - reserved for "move_to_parent" | "delete_codes"
    state: CodingState,
) -> CategoryDeleted | CategoryNotDeleted:
    """
    Derive a CategoryDeleted event or failure event.

    Args:
        category_id: ID of category to delete
        orphan_strategy: How to handle orphaned codes
        state: Current coding state

    Returns:
        CategoryDeleted event or CategoryNotDeleted failure event
    """
    category = next((c for c in state.existing_categories if c.id == category_id), None)
    if category is None:
        return CategoryNotDeleted.not_found(category_id)

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
    memo: str | None,
    importance: int,  # noqa: ARG001 - reserved for importance levels
    owner: str | None,  # noqa: ARG001 - reserved for audit trail
    state: CodingState,
) -> SegmentCoded | SegmentNotCoded:
    """
    Derive a SegmentCoded event or failure event for text coding.

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
        SegmentCoded event or SegmentNotCoded failure event
    """
    # Check code exists
    code = next((c for c in state.existing_codes if c.id == code_id), None)
    if code is None:
        return SegmentNotCoded.code_not_found(code_id)

    # Check source exists
    if not state.source_exists:
        return SegmentNotCoded.source_not_found(source_id)

    # Validate position
    try:
        position = TextPosition(start=start, end=end)
    except ValueError:
        return SegmentNotCoded.invalid_position(start, end, state.source_length or 0)

    if state.source_length is not None and not is_valid_text_position(
        position, state.source_length
    ):
        return SegmentNotCoded.invalid_position(start, end, state.source_length)

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
) -> SegmentUncoded | SegmentNotRemoved:
    """
    Derive a SegmentUncoded event or failure event.

    Args:
        segment_id: ID of segment to remove
        state: Current coding state

    Returns:
        SegmentUncoded event or SegmentNotRemoved failure event
    """
    # Find the segment
    segment = next((s for s in state.existing_segments if s.id == segment_id), None)

    if segment is None:
        return SegmentNotRemoved.not_found(segment_id)

    return SegmentUncoded.create(
        segment_id=segment_id,
        code_id=segment.code_id,
        source_id=segment.source_id,
    )


def derive_update_segment_memo(
    segment_id: SegmentId,
    new_memo: str | None,
    state: CodingState,
) -> SegmentMemoUpdated | SegmentNotUpdated:
    """
    Derive a SegmentMemoUpdated event or failure event.
    """
    segment = next((s for s in state.existing_segments if s.id == segment_id), None)

    if segment is None:
        return SegmentNotUpdated.not_found(segment_id)

    old_memo = getattr(segment, "memo", None)

    return SegmentMemoUpdated.create(
        segment_id=segment_id,
        old_memo=old_memo,
        new_memo=new_memo,
    )


# ============================================================
# Batch Derivers (Auto-coding operations)
# ============================================================


def derive_create_batch(
    code_id: CodeId,
    pattern: str,
    segment_ids: tuple[SegmentId, ...],
    owner: str | None,
    state: CodingState,
) -> BatchCreated | BatchNotCreated:
    """
    Derive a BatchCreated event or failure event.

    Args:
        code_id: Code to apply in this batch
        pattern: The search pattern used
        segment_ids: IDs of segments created in this batch
        owner: Owner identifier
        state: Current coding state

    Returns:
        BatchCreated event or BatchNotCreated failure event
    """
    # Verify code exists
    code = next((c for c in state.existing_codes if c.id == code_id), None)
    if code is None:
        return BatchNotCreated.code_not_found(code_id)

    # Generate new batch ID
    batch_id = BatchId.new()

    return BatchCreated.create(
        batch_id=batch_id,
        code_id=code_id,
        pattern=pattern,
        segment_ids=segment_ids,
        owner=owner,
    )


def derive_undo_batch(
    batch_id: BatchId,
    state: CodingState,
) -> BatchUndone | BatchNotUndone:
    """
    Derive a BatchUndone event or failure event.

    Args:
        batch_id: ID of the batch to undo
        state: Current coding state

    Returns:
        BatchUndone event or BatchNotUndone failure event
    """
    # Find the batch
    batch = next((b for b in state.existing_batches if b.id == batch_id), None)

    if batch is None:
        return BatchNotUndone.not_found(batch_id)

    return BatchUndone.create(
        batch_id=batch_id,
        segments_removed=len(batch.segment_ids),
    )
