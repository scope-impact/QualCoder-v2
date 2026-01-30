"""
Shared domain types: Result monad, base event, typed identifiers

Result type provided by the 'returns' library.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import uuid4

from returns.result import Failure, Result, Success

# ============================================================
# Typed Identifiers
# ============================================================


@dataclass(frozen=True)
class CodeId:
    value: int

    @classmethod
    def new(cls) -> CodeId:
        return cls(value=int(uuid4().int % 1_000_000))


@dataclass(frozen=True)
class SegmentId:
    value: int

    @classmethod
    def new(cls) -> SegmentId:
        return cls(value=int(uuid4().int % 1_000_000))


@dataclass(frozen=True)
class SourceId:
    value: int


@dataclass(frozen=True)
class CategoryId:
    value: int


# ============================================================
# Result Type (Success | Failure)
# ============================================================
# Re-exported from 'returns' library for monadic composition.
# Use: Success(value), Failure(error)
# Access: result.unwrap() for success, result.failure() for error
# Check: isinstance(result, Success) or isinstance(result, Failure)

__all__ = ["Success", "Failure", "Result"]


# ============================================================
# Base Domain Event
# ============================================================


@dataclass(frozen=True)
class DomainEvent:
    """Base class for all domain events"""

    event_id: str
    occurred_at: datetime

    @classmethod
    def _generate_id(cls) -> str:
        return str(uuid4())

    @classmethod
    def _now(cls) -> datetime:
        return datetime.now(UTC)


# ============================================================
# Failure Reasons (Discriminated Union)
# ============================================================


@dataclass(frozen=True)
class DuplicateName:
    name: str
    message: str = ""

    def __post_init__(self):
        object.__setattr__(self, "message", f"Code name '{self.name}' already exists")


@dataclass(frozen=True)
class CodeNotFound:
    code_id: CodeId
    message: str = ""

    def __post_init__(self):
        object.__setattr__(
            self, "message", f"Code with id {self.code_id.value} not found"
        )


@dataclass(frozen=True)
class SourceNotFound:
    source_id: SourceId
    message: str = ""

    def __post_init__(self):
        object.__setattr__(
            self, "message", f"Source with id {self.source_id.value} not found"
        )


@dataclass(frozen=True)
class InvalidPosition:
    start: int
    end: int
    source_length: int
    message: str = ""

    def __post_init__(self):
        object.__setattr__(
            self,
            "message",
            f"Position [{self.start}:{self.end}] invalid for source of length {self.source_length}",
        )


@dataclass(frozen=True)
class EmptyName:
    message: str = "Code name cannot be empty"


FailureReason = (
    DuplicateName | CodeNotFound | SourceNotFound | InvalidPosition | EmptyName
)
