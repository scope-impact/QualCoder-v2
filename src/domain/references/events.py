"""
References Context: Domain Events

Immutable events emitted by reference operations.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import uuid4

from src.domain.shared.types import ReferenceId, SegmentId


def _now() -> datetime:
    return datetime.now(UTC)


def _uuid() -> str:
    return str(uuid4())


@dataclass(frozen=True)
class ReferenceAdded:
    """Emitted when a reference is successfully added."""

    event_type: str = field(default="references.reference_added", init=False)
    reference_id: ReferenceId = field(default_factory=ReferenceId.new)
    title: str = ""
    authors: str = ""
    year: int | None = None
    source: str | None = None
    doi: str | None = None
    url: str | None = None
    memo: str | None = None
    event_id: str = field(default_factory=_uuid)
    occurred_at: datetime = field(default_factory=_now)


@dataclass(frozen=True)
class ReferenceUpdated:
    """Emitted when a reference is successfully updated."""

    event_type: str = field(default="references.reference_updated", init=False)
    reference_id: ReferenceId = field(default_factory=ReferenceId.new)
    title: str = ""
    authors: str = ""
    year: int | None = None
    source: str | None = None
    doi: str | None = None
    url: str | None = None
    memo: str | None = None
    event_id: str = field(default_factory=_uuid)
    occurred_at: datetime = field(default_factory=_now)


@dataclass(frozen=True)
class ReferenceRemoved:
    """Emitted when a reference is successfully removed."""

    event_type: str = field(default="references.reference_removed", init=False)
    reference_id: ReferenceId = field(default_factory=ReferenceId.new)
    event_id: str = field(default_factory=_uuid)
    occurred_at: datetime = field(default_factory=_now)


@dataclass(frozen=True)
class ReferenceLinkedToSegment:
    """Emitted when a reference is linked to a coded segment."""

    event_type: str = field(default="references.reference_linked_to_segment", init=False)
    reference_id: ReferenceId = field(default_factory=ReferenceId.new)
    segment_id: SegmentId = field(default_factory=SegmentId.new)
    event_id: str = field(default_factory=_uuid)
    occurred_at: datetime = field(default_factory=_now)


@dataclass(frozen=True)
class ReferenceUnlinkedFromSegment:
    """Emitted when a reference is unlinked from a coded segment."""

    event_type: str = field(
        default="references.reference_unlinked_from_segment", init=False
    )
    reference_id: ReferenceId = field(default_factory=ReferenceId.new)
    segment_id: SegmentId = field(default_factory=SegmentId.new)
    event_id: str = field(default_factory=_uuid)
    occurred_at: datetime = field(default_factory=_now)
