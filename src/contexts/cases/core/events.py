"""
Cases Context: Domain Events

Events emitted when case-related actions occur. All events are immutable.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from src.contexts.shared import CaseId


def _now() -> datetime:
    return datetime.now(UTC)


def _uuid() -> str:
    return str(uuid4())


# =============================================================================
# Case Lifecycle Events
# =============================================================================


@dataclass(frozen=True)
class CaseCreated:
    """Emitted when a new case is created."""

    event_type: str = field(default="cases.case_created", init=False)
    case_id: CaseId = field(default_factory=CaseId.new)
    name: str = ""
    description: str | None = None
    memo: str | None = None
    event_id: str = field(default_factory=_uuid)
    occurred_at: datetime = field(default_factory=_now)


@dataclass(frozen=True)
class CaseUpdated:
    """Emitted when a case is updated."""

    event_type: str = field(default="cases.case_updated", init=False)
    case_id: CaseId = field(default_factory=CaseId.new)
    name: str = ""
    description: str | None = None
    memo: str | None = None
    event_id: str = field(default_factory=_uuid)
    occurred_at: datetime = field(default_factory=_now)


@dataclass(frozen=True)
class CaseRemoved:
    """Emitted when a case is removed."""

    event_type: str = field(default="cases.case_removed", init=False)
    case_id: CaseId = field(default_factory=CaseId.new)
    event_id: str = field(default_factory=_uuid)
    occurred_at: datetime = field(default_factory=_now)


# =============================================================================
# Case Attribute Events
# =============================================================================


@dataclass(frozen=True)
class CaseAttributeSet:
    """Emitted when a case attribute is set or updated."""

    event_type: str = field(default="cases.attribute_set", init=False)
    case_id: CaseId = field(default_factory=CaseId.new)
    attr_name: str = ""
    attr_type: str = ""
    attr_value: Any = None
    event_id: str = field(default_factory=_uuid)
    occurred_at: datetime = field(default_factory=_now)


@dataclass(frozen=True)
class CaseAttributeRemoved:
    """Emitted when a case attribute is removed."""

    event_type: str = field(default="cases.attribute_removed", init=False)
    case_id: CaseId = field(default_factory=CaseId.new)
    attr_name: str = ""
    event_id: str = field(default_factory=_uuid)
    occurred_at: datetime = field(default_factory=_now)


# =============================================================================
# Case-Source Link Events
# =============================================================================


@dataclass(frozen=True)
class SourceLinkedToCase:
    """Emitted when a source is linked to a case."""

    event_type: str = field(default="cases.source_linked", init=False)
    case_id: CaseId = field(default_factory=CaseId.new)
    source_id: int = 0
    event_id: str = field(default_factory=_uuid)
    occurred_at: datetime = field(default_factory=_now)


@dataclass(frozen=True)
class SourceUnlinkedFromCase:
    """Emitted when a source is unlinked from a case."""

    event_type: str = field(default="cases.source_unlinked", init=False)
    case_id: CaseId = field(default_factory=CaseId.new)
    source_id: int = 0
    event_id: str = field(default_factory=_uuid)
    occurred_at: datetime = field(default_factory=_now)
