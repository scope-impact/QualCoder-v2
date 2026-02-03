"""
Coding Context: Domain Events
Immutable records of things that happened in the domain.

These form the CONTRACT (Published Language) between contexts.
Other contexts subscribe to these events to react to changes.

Event type convention: coding.{entity}_{action}
"""

from dataclasses import dataclass
from typing import ClassVar

from src.contexts.coding.core.entities import BatchId, Color, TextPosition
from src.shared.common.types import (
    CategoryId,
    CodeId,
    DomainEvent,
    SegmentId,
    SourceId,
)

# ============================================================
# Code Events
# ============================================================


@dataclass(frozen=True)
class CodeCreated(DomainEvent):
    """A new code was created in the codebook"""

    event_type: ClassVar[str] = "coding.code_created"

    code_id: CodeId
    name: str
    color: Color
    memo: str | None = None
    category_id: CategoryId | None = None
    owner: str | None = None

    @classmethod
    def create(
        cls,
        code_id: CodeId,
        name: str,
        color: Color,
        memo: str | None = None,
        category_id: CategoryId | None = None,
        owner: str | None = None,
    ) -> "CodeCreated":
        return cls(
            event_id=cls._generate_id(),
            occurred_at=cls._now(),
            code_id=code_id,
            name=name,
            color=color,
            memo=memo,
            category_id=category_id,
            owner=owner,
        )


@dataclass(frozen=True)
class CodeRenamed(DomainEvent):
    """A code's name was changed"""

    event_type: ClassVar[str] = "coding.code_renamed"

    code_id: CodeId
    old_name: str
    new_name: str

    @classmethod
    def create(cls, code_id: CodeId, old_name: str, new_name: str) -> "CodeRenamed":
        return cls(
            event_id=cls._generate_id(),
            occurred_at=cls._now(),
            code_id=code_id,
            old_name=old_name,
            new_name=new_name,
        )


@dataclass(frozen=True)
class CodeColorChanged(DomainEvent):
    """A code's color was changed"""

    event_type: ClassVar[str] = "coding.code_color_changed"

    code_id: CodeId
    old_color: Color
    new_color: Color

    @classmethod
    def create(
        cls, code_id: CodeId, old_color: Color, new_color: Color
    ) -> "CodeColorChanged":
        return cls(
            event_id=cls._generate_id(),
            occurred_at=cls._now(),
            code_id=code_id,
            old_color=old_color,
            new_color=new_color,
        )


@dataclass(frozen=True)
class CodeMemoUpdated(DomainEvent):
    """A code's memo was updated"""

    event_type: ClassVar[str] = "coding.code_memo_updated"

    code_id: CodeId
    old_memo: str | None
    new_memo: str | None

    @classmethod
    def create(
        cls, code_id: CodeId, old_memo: str | None, new_memo: str | None
    ) -> "CodeMemoUpdated":
        return cls(
            event_id=cls._generate_id(),
            occurred_at=cls._now(),
            code_id=code_id,
            old_memo=old_memo,
            new_memo=new_memo,
        )


@dataclass(frozen=True)
class CodeDeleted(DomainEvent):
    """A code was removed from the codebook"""

    event_type: ClassVar[str] = "coding.code_deleted"

    code_id: CodeId
    name: str
    segments_removed: int = 0

    @classmethod
    def create(
        cls, code_id: CodeId, name: str, segments_removed: int = 0
    ) -> "CodeDeleted":
        return cls(
            event_id=cls._generate_id(),
            occurred_at=cls._now(),
            code_id=code_id,
            name=name,
            segments_removed=segments_removed,
        )


@dataclass(frozen=True)
class CodesMerged(DomainEvent):
    """Two codes were merged into one"""

    event_type: ClassVar[str] = "coding.codes_merged"

    source_code_id: CodeId
    source_code_name: str
    target_code_id: CodeId
    target_code_name: str
    segments_moved: int

    @classmethod
    def create(
        cls,
        source_code_id: CodeId,
        source_code_name: str,
        target_code_id: CodeId,
        target_code_name: str,
        segments_moved: int,
    ) -> "CodesMerged":
        return cls(
            event_id=cls._generate_id(),
            occurred_at=cls._now(),
            source_code_id=source_code_id,
            source_code_name=source_code_name,
            target_code_id=target_code_id,
            target_code_name=target_code_name,
            segments_moved=segments_moved,
        )


@dataclass(frozen=True)
class CodeMovedToCategory(DomainEvent):
    """A code was moved to a different category"""

    event_type: ClassVar[str] = "coding.code_moved_to_category"

    code_id: CodeId
    old_category_id: CategoryId | None
    new_category_id: CategoryId | None

    @classmethod
    def create(
        cls,
        code_id: CodeId,
        old_category_id: CategoryId | None,
        new_category_id: CategoryId | None,
    ) -> "CodeMovedToCategory":
        return cls(
            event_id=cls._generate_id(),
            occurred_at=cls._now(),
            code_id=code_id,
            old_category_id=old_category_id,
            new_category_id=new_category_id,
        )


# ============================================================
# Category Events
# ============================================================


@dataclass(frozen=True)
class CategoryCreated(DomainEvent):
    """A new category was created"""

    event_type: ClassVar[str] = "coding.category_created"

    category_id: CategoryId
    name: str
    parent_id: CategoryId | None = None
    memo: str | None = None

    @classmethod
    def create(
        cls,
        category_id: CategoryId,
        name: str,
        parent_id: CategoryId | None = None,
        memo: str | None = None,
    ) -> "CategoryCreated":
        return cls(
            event_id=cls._generate_id(),
            occurred_at=cls._now(),
            category_id=category_id,
            name=name,
            parent_id=parent_id,
            memo=memo,
        )


@dataclass(frozen=True)
class CategoryRenamed(DomainEvent):
    """A category was renamed"""

    event_type: ClassVar[str] = "coding.category_renamed"

    category_id: CategoryId
    old_name: str
    new_name: str

    @classmethod
    def create(
        cls, category_id: CategoryId, old_name: str, new_name: str
    ) -> "CategoryRenamed":
        return cls(
            event_id=cls._generate_id(),
            occurred_at=cls._now(),
            category_id=category_id,
            old_name=old_name,
            new_name=new_name,
        )


@dataclass(frozen=True)
class CategoryDeleted(DomainEvent):
    """A category was deleted"""

    event_type: ClassVar[str] = "coding.category_deleted"

    category_id: CategoryId
    name: str
    codes_orphaned: int = 0

    @classmethod
    def create(
        cls, category_id: CategoryId, name: str, codes_orphaned: int = 0
    ) -> "CategoryDeleted":
        return cls(
            event_id=cls._generate_id(),
            occurred_at=cls._now(),
            category_id=category_id,
            name=name,
            codes_orphaned=codes_orphaned,
        )


# ============================================================
# Segment Events
# ============================================================


@dataclass(frozen=True)
class SegmentCoded(DomainEvent):
    """A code was applied to a segment of content"""

    event_type: ClassVar[str] = "coding.segment_coded"

    segment_id: SegmentId
    code_id: CodeId
    code_name: str
    source_id: SourceId
    source_name: str
    position: TextPosition  # For text segments
    selected_text: str
    memo: str | None = None
    owner: str | None = None

    @classmethod
    def create(
        cls,
        segment_id: SegmentId,
        code_id: CodeId,
        code_name: str,
        source_id: SourceId,
        source_name: str,
        position: TextPosition,
        selected_text: str,
        memo: str | None = None,
        owner: str | None = None,
    ) -> "SegmentCoded":
        return cls(
            event_id=cls._generate_id(),
            occurred_at=cls._now(),
            segment_id=segment_id,
            code_id=code_id,
            code_name=code_name,
            source_id=source_id,
            source_name=source_name,
            position=position,
            selected_text=selected_text,
            memo=memo,
            owner=owner,
        )


@dataclass(frozen=True)
class SegmentUncoded(DomainEvent):
    """A code was removed from a segment"""

    event_type: ClassVar[str] = "coding.segment_uncoded"

    segment_id: SegmentId
    code_id: CodeId
    source_id: SourceId

    @classmethod
    def create(
        cls, segment_id: SegmentId, code_id: CodeId, source_id: SourceId
    ) -> "SegmentUncoded":
        return cls(
            event_id=cls._generate_id(),
            occurred_at=cls._now(),
            segment_id=segment_id,
            code_id=code_id,
            source_id=source_id,
        )


@dataclass(frozen=True)
class SegmentMemoUpdated(DomainEvent):
    """A segment's memo was updated"""

    event_type: ClassVar[str] = "coding.segment_memo_updated"

    segment_id: SegmentId
    old_memo: str | None
    new_memo: str | None

    @classmethod
    def create(
        cls, segment_id: SegmentId, old_memo: str | None, new_memo: str | None
    ) -> "SegmentMemoUpdated":
        return cls(
            event_id=cls._generate_id(),
            occurred_at=cls._now(),
            segment_id=segment_id,
            old_memo=old_memo,
            new_memo=new_memo,
        )


# ============================================================
# Batch Events (Auto-coding operations)
# ============================================================


@dataclass(frozen=True)
class BatchCreated(DomainEvent):
    """An auto-code batch was created with multiple segments."""

    event_type: ClassVar[str] = "coding.batch_created"

    batch_id: BatchId
    code_id: CodeId
    pattern: str
    segment_ids: tuple[SegmentId, ...]
    owner: str | None = None

    @classmethod
    def create(
        cls,
        batch_id: BatchId,
        code_id: CodeId,
        pattern: str,
        segment_ids: tuple[SegmentId, ...],
        owner: str | None = None,
    ) -> "BatchCreated":
        return cls(
            event_id=cls._generate_id(),
            occurred_at=cls._now(),
            batch_id=batch_id,
            code_id=code_id,
            pattern=pattern,
            segment_ids=segment_ids,
            owner=owner,
        )


@dataclass(frozen=True)
class BatchUndone(DomainEvent):
    """An auto-code batch was undone, removing all its segments."""

    event_type: ClassVar[str] = "coding.batch_undone"

    batch_id: BatchId
    segments_removed: int

    @classmethod
    def create(
        cls,
        batch_id: BatchId,
        segments_removed: int,
    ) -> "BatchUndone":
        return cls(
            event_id=cls._generate_id(),
            occurred_at=cls._now(),
            batch_id=batch_id,
            segments_removed=segments_removed,
        )


# ============================================================
# Type Aliases (Published Language)
# ============================================================

CodeEvent = (
    CodeCreated
    | CodeRenamed
    | CodeColorChanged
    | CodeMemoUpdated
    | CodeDeleted
    | CodesMerged
    | CodeMovedToCategory
)

CategoryEvent = CategoryCreated | CategoryRenamed | CategoryDeleted

SegmentEvent = SegmentCoded | SegmentUncoded | SegmentMemoUpdated

BatchEvent = BatchCreated | BatchUndone

# All events from the Coding context
CodingEvent = CodeEvent | CategoryEvent | SegmentEvent | BatchEvent
