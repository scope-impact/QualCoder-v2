"""
Cases Context: Domain Events

Events emitted when case-related actions occur. All events are immutable
and inherit from DomainEvent base class.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from src.shared.common.types import CaseId, DomainEvent

# =============================================================================
# Case Lifecycle Events
# =============================================================================


@dataclass(frozen=True)
class CaseCreated(DomainEvent):
    """Emitted when a new case is created."""

    event_type: str = field(default="cases.case_created", init=False)
    case_id: CaseId = field(default_factory=CaseId.new)
    name: str = ""
    description: str | None = None
    memo: str | None = None

    @classmethod
    def create(
        cls,
        name: str,
        description: str | None = None,
        memo: str | None = None,
        case_id: CaseId | None = None,
    ) -> CaseCreated:
        """Factory method to create event with auto-generated metadata."""
        return cls(
            event_id=cls._generate_id(),
            occurred_at=cls._now(),
            case_id=case_id or CaseId.new(),
            name=name,
            description=description,
            memo=memo,
        )


@dataclass(frozen=True)
class CaseUpdated(DomainEvent):
    """Emitted when a case is updated."""

    event_type: str = field(default="cases.case_updated", init=False)
    case_id: CaseId = field(default_factory=CaseId.new)
    name: str = ""
    description: str | None = None
    memo: str | None = None

    @classmethod
    def create(
        cls,
        case_id: CaseId,
        name: str,
        description: str | None = None,
        memo: str | None = None,
    ) -> CaseUpdated:
        """Factory method to create event with auto-generated metadata."""
        return cls(
            event_id=cls._generate_id(),
            occurred_at=cls._now(),
            case_id=case_id,
            name=name,
            description=description,
            memo=memo,
        )


@dataclass(frozen=True)
class CaseRemoved(DomainEvent):
    """Emitted when a case is removed."""

    event_type: str = field(default="cases.case_removed", init=False)
    case_id: CaseId = field(default_factory=CaseId.new)

    @classmethod
    def create(cls, case_id: CaseId) -> CaseRemoved:
        """Factory method to create event with auto-generated metadata."""
        return cls(
            event_id=cls._generate_id(),
            occurred_at=cls._now(),
            case_id=case_id,
        )


# =============================================================================
# Case Attribute Events
# =============================================================================


@dataclass(frozen=True)
class CaseAttributeSet(DomainEvent):
    """Emitted when a case attribute is set or updated."""

    event_type: str = field(default="cases.attribute_set", init=False)
    case_id: CaseId = field(default_factory=CaseId.new)
    attr_name: str = ""
    attr_type: str = ""
    attr_value: Any = None

    @classmethod
    def create(
        cls,
        case_id: CaseId,
        attr_name: str,
        attr_type: str,
        attr_value: Any,
    ) -> CaseAttributeSet:
        """Factory method to create event with auto-generated metadata."""
        return cls(
            event_id=cls._generate_id(),
            occurred_at=cls._now(),
            case_id=case_id,
            attr_name=attr_name,
            attr_type=attr_type,
            attr_value=attr_value,
        )


@dataclass(frozen=True)
class CaseAttributeRemoved(DomainEvent):
    """Emitted when a case attribute is removed."""

    event_type: str = field(default="cases.attribute_removed", init=False)
    case_id: CaseId = field(default_factory=CaseId.new)
    attr_name: str = ""

    @classmethod
    def create(cls, case_id: CaseId, attr_name: str) -> CaseAttributeRemoved:
        """Factory method to create event with auto-generated metadata."""
        return cls(
            event_id=cls._generate_id(),
            occurred_at=cls._now(),
            case_id=case_id,
            attr_name=attr_name,
        )


# =============================================================================
# Case-Source Link Events
# =============================================================================


@dataclass(frozen=True)
class SourceLinkedToCase(DomainEvent):
    """Emitted when a source is linked to a case."""

    event_type: str = field(default="cases.source_linked", init=False)
    case_id: CaseId = field(default_factory=CaseId.new)
    source_id: int = 0

    @classmethod
    def create(cls, case_id: CaseId, source_id: int) -> SourceLinkedToCase:
        """Factory method to create event with auto-generated metadata."""
        return cls(
            event_id=cls._generate_id(),
            occurred_at=cls._now(),
            case_id=case_id,
            source_id=source_id,
        )


@dataclass(frozen=True)
class SourceUnlinkedFromCase(DomainEvent):
    """Emitted when a source is unlinked from a case."""

    event_type: str = field(default="cases.source_unlinked", init=False)
    case_id: CaseId = field(default_factory=CaseId.new)
    source_id: int = 0

    @classmethod
    def create(cls, case_id: CaseId, source_id: int) -> SourceUnlinkedFromCase:
        """Factory method to create event with auto-generated metadata."""
        return cls(
            event_id=cls._generate_id(),
            occurred_at=cls._now(),
            case_id=case_id,
            source_id=source_id,
        )
