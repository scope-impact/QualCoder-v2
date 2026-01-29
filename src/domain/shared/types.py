"""
Shared domain types: Result monad, base event, typed identifiers
"""

from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from typing import TypeVar, Generic, Union, Callable
from uuid import uuid4


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

T = TypeVar('T')
E = TypeVar('E')


@dataclass(frozen=True)
class Success(Generic[T]):
    """Successful result containing a value"""
    value: T

    def is_success(self) -> bool:
        return True

    def is_failure(self) -> bool:
        return False

    def map(self, fn: Callable[[T], T]) -> Result[T, E]:
        return Success(fn(self.value))

    def unwrap(self) -> T:
        return self.value


@dataclass(frozen=True)
class Failure(Generic[E]):
    """Failed result containing an error"""
    error: E

    def is_success(self) -> bool:
        return False

    def is_failure(self) -> bool:
        return True

    def map(self, fn: Callable) -> Result[T, E]:
        return self

    def unwrap(self) -> None:
        raise ValueError(f"Cannot unwrap Failure: {self.error}")


Result = Union[Success[T], Failure[E]]


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
        return datetime.utcnow()


# ============================================================
# Failure Reasons (Discriminated Union)
# ============================================================

@dataclass(frozen=True)
class DuplicateName:
    name: str
    message: str = ""

    def __post_init__(self):
        object.__setattr__(self, 'message', f"Code name '{self.name}' already exists")


@dataclass(frozen=True)
class CodeNotFound:
    code_id: CodeId
    message: str = ""

    def __post_init__(self):
        object.__setattr__(self, 'message', f"Code with id {self.code_id.value} not found")


@dataclass(frozen=True)
class SourceNotFound:
    source_id: SourceId
    message: str = ""

    def __post_init__(self):
        object.__setattr__(self, 'message', f"Source with id {self.source_id.value} not found")


@dataclass(frozen=True)
class InvalidPosition:
    start: int
    end: int
    source_length: int
    message: str = ""

    def __post_init__(self):
        object.__setattr__(
            self, 'message',
            f"Position [{self.start}:{self.end}] invalid for source of length {self.source_length}"
        )


@dataclass(frozen=True)
class EmptyName:
    message: str = "Code name cannot be empty"


FailureReason = Union[DuplicateName, CodeNotFound, SourceNotFound, InvalidPosition, EmptyName]
