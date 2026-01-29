"""
Coding Context: Domain Events
Immutable records of things that happened in the domain.

These form the CONTRACT (Published Language) between contexts.
Other contexts subscribe to these events to react to changes.
"""

from dataclasses import dataclass
from typing import Optional, Union

from src.domain.shared.types import (
    DomainEvent,
    CodeId,
    SegmentId,
    SourceId,
    CategoryId,
)
from src.domain.coding.entities import Color, TextPosition, ImageRegion, TimeRange


# ============================================================
# Code Events
# ============================================================

@dataclass(frozen=True)
class CodeCreated(DomainEvent):
    """A new code was created in the codebook"""
    code_id: CodeId
    name: str
    color: Color
    memo: Optional[str] = None
    category_id: Optional[CategoryId] = None
    owner: Optional[str] = None

    @classmethod
    def create(
        cls,
        code_id: CodeId,
        name: str,
        color: Color,
        memo: Optional[str] = None,
        category_id: Optional[CategoryId] = None,
        owner: Optional[str] = None
    ) -> 'CodeCreated':
        return cls(
            event_id=cls._generate_id(),
            occurred_at=cls._now(),
            code_id=code_id,
            name=name,
            color=color,
            memo=memo,
            category_id=category_id,
            owner=owner
        )


@dataclass(frozen=True)
class CodeRenamed(DomainEvent):
    """A code's name was changed"""
    code_id: CodeId
    old_name: str
    new_name: str

    @classmethod
    def create(cls, code_id: CodeId, old_name: str, new_name: str) -> 'CodeRenamed':
        return cls(
            event_id=cls._generate_id(),
            occurred_at=cls._now(),
            code_id=code_id,
            old_name=old_name,
            new_name=new_name
        )


@dataclass(frozen=True)
class CodeColorChanged(DomainEvent):
    """A code's color was changed"""
    code_id: CodeId
    old_color: Color
    new_color: Color

    @classmethod
    def create(cls, code_id: CodeId, old_color: Color, new_color: Color) -> 'CodeColorChanged':
        return cls(
            event_id=cls._generate_id(),
            occurred_at=cls._now(),
            code_id=code_id,
            old_color=old_color,
            new_color=new_color
        )


@dataclass(frozen=True)
class CodeMemoUpdated(DomainEvent):
    """A code's memo was updated"""
    code_id: CodeId
    old_memo: Optional[str]
    new_memo: Optional[str]

    @classmethod
    def create(cls, code_id: CodeId, old_memo: Optional[str], new_memo: Optional[str]) -> 'CodeMemoUpdated':
        return cls(
            event_id=cls._generate_id(),
            occurred_at=cls._now(),
            code_id=code_id,
            old_memo=old_memo,
            new_memo=new_memo
        )


@dataclass(frozen=True)
class CodeDeleted(DomainEvent):
    """A code was removed from the codebook"""
    code_id: CodeId
    name: str
    segments_removed: int = 0

    @classmethod
    def create(cls, code_id: CodeId, name: str, segments_removed: int = 0) -> 'CodeDeleted':
        return cls(
            event_id=cls._generate_id(),
            occurred_at=cls._now(),
            code_id=code_id,
            name=name,
            segments_removed=segments_removed
        )


@dataclass(frozen=True)
class CodesMerged(DomainEvent):
    """Two codes were merged into one"""
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
        segments_moved: int
    ) -> 'CodesMerged':
        return cls(
            event_id=cls._generate_id(),
            occurred_at=cls._now(),
            source_code_id=source_code_id,
            source_code_name=source_code_name,
            target_code_id=target_code_id,
            target_code_name=target_code_name,
            segments_moved=segments_moved
        )


@dataclass(frozen=True)
class CodeMovedToCategory(DomainEvent):
    """A code was moved to a different category"""
    code_id: CodeId
    old_category_id: Optional[CategoryId]
    new_category_id: Optional[CategoryId]

    @classmethod
    def create(
        cls,
        code_id: CodeId,
        old_category_id: Optional[CategoryId],
        new_category_id: Optional[CategoryId]
    ) -> 'CodeMovedToCategory':
        return cls(
            event_id=cls._generate_id(),
            occurred_at=cls._now(),
            code_id=code_id,
            old_category_id=old_category_id,
            new_category_id=new_category_id
        )


# ============================================================
# Category Events
# ============================================================

@dataclass(frozen=True)
class CategoryCreated(DomainEvent):
    """A new category was created"""
    category_id: CategoryId
    name: str
    parent_id: Optional[CategoryId] = None
    memo: Optional[str] = None

    @classmethod
    def create(
        cls,
        category_id: CategoryId,
        name: str,
        parent_id: Optional[CategoryId] = None,
        memo: Optional[str] = None
    ) -> 'CategoryCreated':
        return cls(
            event_id=cls._generate_id(),
            occurred_at=cls._now(),
            category_id=category_id,
            name=name,
            parent_id=parent_id,
            memo=memo
        )


@dataclass(frozen=True)
class CategoryRenamed(DomainEvent):
    """A category was renamed"""
    category_id: CategoryId
    old_name: str
    new_name: str

    @classmethod
    def create(cls, category_id: CategoryId, old_name: str, new_name: str) -> 'CategoryRenamed':
        return cls(
            event_id=cls._generate_id(),
            occurred_at=cls._now(),
            category_id=category_id,
            old_name=old_name,
            new_name=new_name
        )


@dataclass(frozen=True)
class CategoryDeleted(DomainEvent):
    """A category was deleted"""
    category_id: CategoryId
    name: str
    codes_orphaned: int = 0

    @classmethod
    def create(cls, category_id: CategoryId, name: str, codes_orphaned: int = 0) -> 'CategoryDeleted':
        return cls(
            event_id=cls._generate_id(),
            occurred_at=cls._now(),
            category_id=category_id,
            name=name,
            codes_orphaned=codes_orphaned
        )


# ============================================================
# Segment Events
# ============================================================

@dataclass(frozen=True)
class SegmentCoded(DomainEvent):
    """A code was applied to a segment of content"""
    segment_id: SegmentId
    code_id: CodeId
    code_name: str
    source_id: SourceId
    source_name: str
    position: TextPosition  # For text segments
    selected_text: str
    memo: Optional[str] = None
    owner: Optional[str] = None

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
        memo: Optional[str] = None,
        owner: Optional[str] = None
    ) -> 'SegmentCoded':
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
            owner=owner
        )


@dataclass(frozen=True)
class SegmentUncoded(DomainEvent):
    """A code was removed from a segment"""
    segment_id: SegmentId
    code_id: CodeId
    source_id: SourceId

    @classmethod
    def create(cls, segment_id: SegmentId, code_id: CodeId, source_id: SourceId) -> 'SegmentUncoded':
        return cls(
            event_id=cls._generate_id(),
            occurred_at=cls._now(),
            segment_id=segment_id,
            code_id=code_id,
            source_id=source_id
        )


@dataclass(frozen=True)
class SegmentMemoUpdated(DomainEvent):
    """A segment's memo was updated"""
    segment_id: SegmentId
    old_memo: Optional[str]
    new_memo: Optional[str]

    @classmethod
    def create(cls, segment_id: SegmentId, old_memo: Optional[str], new_memo: Optional[str]) -> 'SegmentMemoUpdated':
        return cls(
            event_id=cls._generate_id(),
            occurred_at=cls._now(),
            segment_id=segment_id,
            old_memo=old_memo,
            new_memo=new_memo
        )


# ============================================================
# Type Aliases (Published Language)
# ============================================================

CodeEvent = Union[
    CodeCreated,
    CodeRenamed,
    CodeColorChanged,
    CodeMemoUpdated,
    CodeDeleted,
    CodesMerged,
    CodeMovedToCategory,
]

CategoryEvent = Union[
    CategoryCreated,
    CategoryRenamed,
    CategoryDeleted,
]

SegmentEvent = Union[
    SegmentCoded,
    SegmentUncoded,
    SegmentMemoUpdated,
]

# All events from the Coding context
CodingEvent = Union[CodeEvent, CategoryEvent, SegmentEvent]
