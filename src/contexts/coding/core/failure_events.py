"""
Coding Context: Failure Events

Publishable failure events for the coding bounded context.
These events can be published to the event bus and trigger policies.

Event naming convention: {ENTITY}_NOT_{OPERATION}/{REASON}
"""

from __future__ import annotations

from dataclasses import dataclass

from src.contexts.coding.core.entities import BatchId
from src.contexts.shared.core.failure_events import FailureEvent
from src.contexts.shared.core.types import CategoryId, CodeId, SegmentId, SourceId

# ============================================================
# Code Failure Events
# ============================================================


@dataclass(frozen=True)
class CodeNotCreated(FailureEvent):
    """Failure event: Code creation failed."""

    name: str | None = None
    category_id: CategoryId | None = None

    @classmethod
    def empty_name(cls) -> CodeNotCreated:
        """Code name cannot be empty."""
        return cls(
            event_id=cls._generate_id(),
            occurred_at=cls._now(),
            event_type="CODE_NOT_CREATED/EMPTY_NAME",
        )

    @classmethod
    def duplicate_name(cls, name: str) -> CodeNotCreated:
        """A code with this name already exists."""
        return cls(
            event_id=cls._generate_id(),
            occurred_at=cls._now(),
            event_type="CODE_NOT_CREATED/DUPLICATE_NAME",
            name=name,
        )

    @classmethod
    def category_not_found(cls, category_id: CategoryId) -> CodeNotCreated:
        """The specified category does not exist."""
        return cls(
            event_id=cls._generate_id(),
            occurred_at=cls._now(),
            event_type="CODE_NOT_CREATED/CATEGORY_NOT_FOUND",
            category_id=category_id,
        )

    @property
    def message(self) -> str:
        """Human-readable error message."""
        match self.reason:
            case "EMPTY_NAME":
                return "Code name cannot be empty"
            case "DUPLICATE_NAME":
                return f"Code name '{self.name}' already exists"
            case "CATEGORY_NOT_FOUND":
                return f"Category with id {self.category_id.value if self.category_id else 'unknown'} not found"
            case _:
                return super().message


@dataclass(frozen=True)
class CodeNotRenamed(FailureEvent):
    """Failure event: Code rename failed."""

    code_id: CodeId | None = None
    new_name: str | None = None

    @classmethod
    def not_found(cls, code_id: CodeId) -> CodeNotRenamed:
        """Code does not exist."""
        return cls(
            event_id=cls._generate_id(),
            occurred_at=cls._now(),
            event_type="CODE_NOT_RENAMED/NOT_FOUND",
            code_id=code_id,
        )

    @classmethod
    def empty_name(cls, code_id: CodeId) -> CodeNotRenamed:
        """New name cannot be empty."""
        return cls(
            event_id=cls._generate_id(),
            occurred_at=cls._now(),
            event_type="CODE_NOT_RENAMED/EMPTY_NAME",
            code_id=code_id,
        )

    @classmethod
    def duplicate_name(cls, code_id: CodeId, new_name: str) -> CodeNotRenamed:
        """A code with this name already exists."""
        return cls(
            event_id=cls._generate_id(),
            occurred_at=cls._now(),
            event_type="CODE_NOT_RENAMED/DUPLICATE_NAME",
            code_id=code_id,
            new_name=new_name,
        )

    @property
    def message(self) -> str:
        """Human-readable error message."""
        match self.reason:
            case "NOT_FOUND":
                return f"Code with id {self.code_id.value if self.code_id else 'unknown'} not found"
            case "EMPTY_NAME":
                return "Code name cannot be empty"
            case "DUPLICATE_NAME":
                return f"Code name '{self.new_name}' already exists"
            case _:
                return super().message


@dataclass(frozen=True)
class CodeNotUpdated(FailureEvent):
    """Failure event: Code update (color/memo) failed."""

    code_id: CodeId | None = None

    @classmethod
    def not_found(cls, code_id: CodeId) -> CodeNotUpdated:
        """Code does not exist."""
        return cls(
            event_id=cls._generate_id(),
            occurred_at=cls._now(),
            event_type="CODE_NOT_UPDATED/NOT_FOUND",
            code_id=code_id,
        )

    @property
    def message(self) -> str:
        """Human-readable error message."""
        match self.reason:
            case "NOT_FOUND":
                return f"Code with id {self.code_id.value if self.code_id else 'unknown'} not found"
            case _:
                return super().message


@dataclass(frozen=True)
class CodeNotDeleted(FailureEvent):
    """Failure event: Code deletion failed."""

    code_id: CodeId | None = None
    reference_count: int = 0

    @classmethod
    def not_found(cls, code_id: CodeId) -> CodeNotDeleted:
        """Code does not exist."""
        return cls(
            event_id=cls._generate_id(),
            occurred_at=cls._now(),
            event_type="CODE_NOT_DELETED/NOT_FOUND",
            code_id=code_id,
        )

    @classmethod
    def has_references(cls, code_id: CodeId, reference_count: int) -> CodeNotDeleted:
        """Code has segments and cannot be deleted without force."""
        return cls(
            event_id=cls._generate_id(),
            occurred_at=cls._now(),
            event_type="CODE_NOT_DELETED/HAS_REFERENCES",
            code_id=code_id,
            reference_count=reference_count,
        )

    @property
    def message(self) -> str:
        """Human-readable error message."""
        match self.reason:
            case "NOT_FOUND":
                return f"Code with id {self.code_id.value if self.code_id else 'unknown'} not found"
            case "HAS_REFERENCES":
                return (
                    f"Code has {self.reference_count} segment(s) and cannot be deleted"
                )
            case _:
                return super().message


@dataclass(frozen=True)
class CodesNotMerged(FailureEvent):
    """Failure event: Code merge failed."""

    source_code_id: CodeId | None = None
    target_code_id: CodeId | None = None

    @classmethod
    def same_code(cls, code_id: CodeId) -> CodesNotMerged:
        """Cannot merge a code with itself."""
        return cls(
            event_id=cls._generate_id(),
            occurred_at=cls._now(),
            event_type="CODES_NOT_MERGED/SAME_CODE",
            source_code_id=code_id,
            target_code_id=code_id,
        )

    @classmethod
    def source_not_found(cls, code_id: CodeId) -> CodesNotMerged:
        """Source code does not exist."""
        return cls(
            event_id=cls._generate_id(),
            occurred_at=cls._now(),
            event_type="CODES_NOT_MERGED/SOURCE_NOT_FOUND",
            source_code_id=code_id,
        )

    @classmethod
    def target_not_found(
        cls, source_code_id: CodeId, target_code_id: CodeId
    ) -> CodesNotMerged:
        """Target code does not exist."""
        return cls(
            event_id=cls._generate_id(),
            occurred_at=cls._now(),
            event_type="CODES_NOT_MERGED/TARGET_NOT_FOUND",
            source_code_id=source_code_id,
            target_code_id=target_code_id,
        )

    @property
    def message(self) -> str:
        """Human-readable error message."""
        match self.reason:
            case "SAME_CODE":
                return "Cannot merge a code with itself"
            case "SOURCE_NOT_FOUND":
                return f"Source code with id {self.source_code_id.value if self.source_code_id else 'unknown'} not found"
            case "TARGET_NOT_FOUND":
                return f"Target code with id {self.target_code_id.value if self.target_code_id else 'unknown'} not found"
            case _:
                return super().message


@dataclass(frozen=True)
class CodeNotMoved(FailureEvent):
    """Failure event: Code category move failed."""

    code_id: CodeId | None = None
    category_id: CategoryId | None = None

    @classmethod
    def code_not_found(cls, code_id: CodeId) -> CodeNotMoved:
        """Code does not exist."""
        return cls(
            event_id=cls._generate_id(),
            occurred_at=cls._now(),
            event_type="CODE_NOT_MOVED/CODE_NOT_FOUND",
            code_id=code_id,
        )

    @classmethod
    def category_not_found(
        cls, code_id: CodeId, category_id: CategoryId
    ) -> CodeNotMoved:
        """Target category does not exist."""
        return cls(
            event_id=cls._generate_id(),
            occurred_at=cls._now(),
            event_type="CODE_NOT_MOVED/CATEGORY_NOT_FOUND",
            code_id=code_id,
            category_id=category_id,
        )

    @property
    def message(self) -> str:
        """Human-readable error message."""
        match self.reason:
            case "CODE_NOT_FOUND":
                return f"Code with id {self.code_id.value if self.code_id else 'unknown'} not found"
            case "CATEGORY_NOT_FOUND":
                return f"Category with id {self.category_id.value if self.category_id else 'unknown'} not found"
            case _:
                return super().message


# ============================================================
# Category Failure Events
# ============================================================


@dataclass(frozen=True)
class CategoryNotCreated(FailureEvent):
    """Failure event: Category creation failed."""

    name: str | None = None
    parent_id: CategoryId | None = None

    @classmethod
    def empty_name(cls) -> CategoryNotCreated:
        """Category name cannot be empty."""
        return cls(
            event_id=cls._generate_id(),
            occurred_at=cls._now(),
            event_type="CATEGORY_NOT_CREATED/EMPTY_NAME",
        )

    @classmethod
    def duplicate_name(cls, name: str) -> CategoryNotCreated:
        """A category with this name already exists."""
        return cls(
            event_id=cls._generate_id(),
            occurred_at=cls._now(),
            event_type="CATEGORY_NOT_CREATED/DUPLICATE_NAME",
            name=name,
        )

    @classmethod
    def parent_not_found(cls, parent_id: CategoryId) -> CategoryNotCreated:
        """The specified parent category does not exist."""
        return cls(
            event_id=cls._generate_id(),
            occurred_at=cls._now(),
            event_type="CATEGORY_NOT_CREATED/PARENT_NOT_FOUND",
            parent_id=parent_id,
        )

    @property
    def message(self) -> str:
        """Human-readable error message."""
        match self.reason:
            case "EMPTY_NAME":
                return "Category name cannot be empty"
            case "DUPLICATE_NAME":
                return f"Category name '{self.name}' already exists"
            case "PARENT_NOT_FOUND":
                return f"Parent category with id {self.parent_id.value if self.parent_id else 'unknown'} not found"
            case _:
                return super().message


@dataclass(frozen=True)
class CategoryNotRenamed(FailureEvent):
    """Failure event: Category rename failed."""

    category_id: CategoryId | None = None
    new_name: str | None = None

    @classmethod
    def not_found(cls, category_id: CategoryId) -> CategoryNotRenamed:
        """Category does not exist."""
        return cls(
            event_id=cls._generate_id(),
            occurred_at=cls._now(),
            event_type="CATEGORY_NOT_RENAMED/NOT_FOUND",
            category_id=category_id,
        )

    @classmethod
    def empty_name(cls, category_id: CategoryId) -> CategoryNotRenamed:
        """New name cannot be empty."""
        return cls(
            event_id=cls._generate_id(),
            occurred_at=cls._now(),
            event_type="CATEGORY_NOT_RENAMED/EMPTY_NAME",
            category_id=category_id,
        )

    @classmethod
    def duplicate_name(
        cls, category_id: CategoryId, new_name: str
    ) -> CategoryNotRenamed:
        """A category with this name already exists."""
        return cls(
            event_id=cls._generate_id(),
            occurred_at=cls._now(),
            event_type="CATEGORY_NOT_RENAMED/DUPLICATE_NAME",
            category_id=category_id,
            new_name=new_name,
        )

    @property
    def message(self) -> str:
        """Human-readable error message."""
        match self.reason:
            case "NOT_FOUND":
                return f"Category with id {self.category_id.value if self.category_id else 'unknown'} not found"
            case "EMPTY_NAME":
                return "Category name cannot be empty"
            case "DUPLICATE_NAME":
                return f"Category name '{self.new_name}' already exists"
            case _:
                return super().message


@dataclass(frozen=True)
class CategoryNotDeleted(FailureEvent):
    """Failure event: Category deletion failed."""

    category_id: CategoryId | None = None

    @classmethod
    def not_found(cls, category_id: CategoryId) -> CategoryNotDeleted:
        """Category does not exist."""
        return cls(
            event_id=cls._generate_id(),
            occurred_at=cls._now(),
            event_type="CATEGORY_NOT_DELETED/NOT_FOUND",
            category_id=category_id,
        )

    @property
    def message(self) -> str:
        """Human-readable error message."""
        match self.reason:
            case "NOT_FOUND":
                return f"Category with id {self.category_id.value if self.category_id else 'unknown'} not found"
            case _:
                return super().message


# ============================================================
# Segment Failure Events
# ============================================================


@dataclass(frozen=True)
class SegmentNotCoded(FailureEvent):
    """Failure event: Segment coding failed."""

    code_id: CodeId | None = None
    source_id: SourceId | None = None
    start: int | None = None
    end: int | None = None
    source_length: int | None = None

    @classmethod
    def code_not_found(cls, code_id: CodeId) -> SegmentNotCoded:
        """Code does not exist."""
        return cls(
            event_id=cls._generate_id(),
            occurred_at=cls._now(),
            event_type="SEGMENT_NOT_CODED/CODE_NOT_FOUND",
            code_id=code_id,
        )

    @classmethod
    def source_not_found(cls, source_id: SourceId) -> SegmentNotCoded:
        """Source does not exist."""
        return cls(
            event_id=cls._generate_id(),
            occurred_at=cls._now(),
            event_type="SEGMENT_NOT_CODED/SOURCE_NOT_FOUND",
            source_id=source_id,
        )

    @classmethod
    def invalid_position(
        cls, start: int, end: int, source_length: int
    ) -> SegmentNotCoded:
        """Text position is invalid."""
        return cls(
            event_id=cls._generate_id(),
            occurred_at=cls._now(),
            event_type="SEGMENT_NOT_CODED/INVALID_POSITION",
            start=start,
            end=end,
            source_length=source_length,
        )

    @property
    def message(self) -> str:
        """Human-readable error message."""
        match self.reason:
            case "CODE_NOT_FOUND":
                return f"Code with id {self.code_id.value if self.code_id else 'unknown'} not found"
            case "SOURCE_NOT_FOUND":
                return f"Source with id {self.source_id.value if self.source_id else 'unknown'} not found"
            case "INVALID_POSITION":
                return f"Position [{self.start}:{self.end}] invalid for source of length {self.source_length}"
            case _:
                return super().message


@dataclass(frozen=True)
class SegmentNotRemoved(FailureEvent):
    """Failure event: Segment removal failed."""

    segment_id: SegmentId | None = None

    @classmethod
    def not_found(cls, segment_id: SegmentId) -> SegmentNotRemoved:
        """Segment does not exist."""
        return cls(
            event_id=cls._generate_id(),
            occurred_at=cls._now(),
            event_type="SEGMENT_NOT_REMOVED/NOT_FOUND",
            segment_id=segment_id,
        )

    @property
    def message(self) -> str:
        """Human-readable error message."""
        match self.reason:
            case "NOT_FOUND":
                return f"Segment with id {self.segment_id.value if self.segment_id else 'unknown'} not found"
            case _:
                return super().message


@dataclass(frozen=True)
class SegmentNotUpdated(FailureEvent):
    """Failure event: Segment memo update failed."""

    segment_id: SegmentId | None = None

    @classmethod
    def not_found(cls, segment_id: SegmentId) -> SegmentNotUpdated:
        """Segment does not exist."""
        return cls(
            event_id=cls._generate_id(),
            occurred_at=cls._now(),
            event_type="SEGMENT_NOT_UPDATED/NOT_FOUND",
            segment_id=segment_id,
        )

    @property
    def message(self) -> str:
        """Human-readable error message."""
        match self.reason:
            case "NOT_FOUND":
                return f"Segment with id {self.segment_id.value if self.segment_id else 'unknown'} not found"
            case _:
                return super().message


# ============================================================
# Batch Failure Events
# ============================================================


@dataclass(frozen=True)
class BatchNotCreated(FailureEvent):
    """Failure event: Batch creation failed."""

    code_id: CodeId | None = None

    @classmethod
    def code_not_found(cls, code_id: CodeId) -> BatchNotCreated:
        """Code does not exist."""
        return cls(
            event_id=cls._generate_id(),
            occurred_at=cls._now(),
            event_type="BATCH_NOT_CREATED/CODE_NOT_FOUND",
            code_id=code_id,
        )

    @property
    def message(self) -> str:
        """Human-readable error message."""
        match self.reason:
            case "CODE_NOT_FOUND":
                return f"Code with id {self.code_id.value if self.code_id else 'unknown'} not found"
            case _:
                return super().message


@dataclass(frozen=True)
class BatchNotUndone(FailureEvent):
    """Failure event: Batch undo failed."""

    batch_id: BatchId | None = None

    @classmethod
    def not_found(cls, batch_id: BatchId) -> BatchNotUndone:
        """Batch does not exist."""
        return cls(
            event_id=cls._generate_id(),
            occurred_at=cls._now(),
            event_type="BATCH_NOT_UNDONE/NOT_FOUND",
            batch_id=batch_id,
        )

    @property
    def message(self) -> str:
        """Human-readable error message."""
        match self.reason:
            case "NOT_FOUND":
                return f"Batch with id {self.batch_id.value if self.batch_id else 'unknown'} not found"
            case _:
                return super().message


# ============================================================
# Type Unions
# ============================================================

CodeFailureEvent = (
    CodeNotCreated
    | CodeNotRenamed
    | CodeNotUpdated
    | CodeNotDeleted
    | CodesNotMerged
    | CodeNotMoved
)

CategoryFailureEvent = CategoryNotCreated | CategoryNotRenamed | CategoryNotDeleted

SegmentFailureEvent = SegmentNotCoded | SegmentNotRemoved | SegmentNotUpdated

BatchFailureEvent = BatchNotCreated | BatchNotUndone

# All failure events from the Coding context
CodingContextFailureEvent = (
    CodeFailureEvent | CategoryFailureEvent | SegmentFailureEvent | BatchFailureEvent
)


# ============================================================
# Exports
# ============================================================

__all__ = [
    # Code Failure Events
    "CodeNotCreated",
    "CodeNotRenamed",
    "CodeNotUpdated",
    "CodeNotDeleted",
    "CodesNotMerged",
    "CodeNotMoved",
    # Category Failure Events
    "CategoryNotCreated",
    "CategoryNotRenamed",
    "CategoryNotDeleted",
    # Segment Failure Events
    "SegmentNotCoded",
    "SegmentNotRemoved",
    "SegmentNotUpdated",
    # Batch Failure Events
    "BatchNotCreated",
    "BatchNotUndone",
    # Type Unions
    "CodeFailureEvent",
    "CategoryFailureEvent",
    "SegmentFailureEvent",
    "BatchFailureEvent",
    "CodingContextFailureEvent",
]
