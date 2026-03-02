"""
Sync Context: Domain Entities

Immutable entities and value objects for sync operations.
PURE - no I/O, no side effects.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime


@dataclass(frozen=True)
class RemoteItem:
    """
    Represents an item fetched from Convex.

    This is a normalized representation of any entity type
    that can be synced between SQLite and Convex.
    """

    id: str
    entity_type: str  # "code", "source", "segment", etc.
    data: dict = field(default_factory=dict)
    updated_at: datetime | None = None

    @classmethod
    def from_convex(cls, entity_type: str, item: dict) -> RemoteItem:
        """Create RemoteItem from Convex response."""
        return cls(
            id=str(item.get("_id", "")),
            entity_type=entity_type,
            data=item,
            updated_at=None,  # Convex doesn't expose timestamps
        )


@dataclass(frozen=True)
class SyncDomainState:
    """
    Immutable state container for sync derivers.

    Provides all the context needed to make sync decisions
    without any I/O operations.
    """

    local_ids: frozenset[str] = field(default_factory=frozenset)
    remote_items: tuple[RemoteItem, ...] = ()
    pending_outbound: frozenset[str] = field(default_factory=frozenset)

    @classmethod
    def create(
        cls,
        local_ids: set[str] | frozenset[str],
        remote_items: list[RemoteItem] | tuple[RemoteItem, ...],
        pending_outbound: set[str] | frozenset[str],
    ) -> SyncDomainState:
        """Create state from mutable collections."""
        return cls(
            local_ids=frozenset(local_ids),
            remote_items=tuple(remote_items),
            pending_outbound=frozenset(pending_outbound),
        )


@dataclass(frozen=True)
class PullResult:
    """
    Result of a pull operation for a single entity type.

    Used to track what was fetched and applied.
    """

    entity_type: str
    fetched_count: int = 0
    applied_count: int = 0
    skipped_count: int = 0
    deleted_count: int = 0
    error: str | None = None


@dataclass(frozen=True)
class PullSummary:
    """
    Summary of a complete pull operation across all entity types.
    """

    results: tuple[PullResult, ...] = ()
    started_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    completed_at: datetime | None = None
    total_conflicts: int = 0

    @property
    def entity_counts(self) -> dict[str, int]:
        """Get count of applied items per entity type."""
        return {r.entity_type: r.applied_count for r in self.results}

    @property
    def total_applied(self) -> int:
        """Total items applied across all entity types."""
        return sum(r.applied_count for r in self.results)

    @property
    def has_errors(self) -> bool:
        """Check if any entity type had errors."""
        return any(r.error is not None for r in self.results)

    def with_completed(self, completed_at: datetime | None = None) -> PullSummary:
        """Return new summary with completion timestamp."""
        return PullSummary(
            results=self.results,
            started_at=self.started_at,
            completed_at=completed_at or datetime.now(UTC),
            total_conflicts=self.total_conflicts,
        )
