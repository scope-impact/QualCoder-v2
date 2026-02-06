"""
Sync Context: Domain Events

Immutable facts representing sync operations.
Events use past tense naming and are frozen dataclasses.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime


@dataclass(frozen=True)
class SyncPullStarted:
    """Pull operation started."""

    event_type: str = field(default="sync.pull_started", init=False)
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass(frozen=True)
class SyncPullCompleted:
    """Pull operation completed successfully."""

    entity_counts: dict[str, int] = field(default_factory=dict)
    conflicts_skipped: int = 0
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
    event_type: str = field(default="sync.pull_completed", init=False)


@dataclass(frozen=True)
class SyncPullFailed:
    """Pull operation failed with error details and suggestions."""

    reason: str = ""
    error_code: str = "PULL_FAILED"
    suggestions: tuple[str, ...] = ()
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
    event_type: str = field(default="sync.pull_failed", init=False)

    @classmethod
    def not_connected(cls) -> SyncPullFailed:
        """Create failure when not connected to Convex."""
        return cls(
            reason="Not connected to Convex",
            error_code="NOT_CONNECTED",
            suggestions=(
                "Enable cloud sync in settings",
                "Check Convex URL configuration",
            ),
        )

    @classmethod
    def partial_failure(cls, failed_types: list[str]) -> SyncPullFailed:
        """Create failure when some entity types failed."""
        return cls(
            reason=f"Failed to pull: {', '.join(failed_types)}",
            error_code="PARTIAL_FAILURE",
            suggestions=("Some data was synced", "Try pulling again"),
        )


@dataclass(frozen=True)
class RemoteChangesReceived:
    """Remote changes received and applied to local SQLite."""

    entity_type: str = ""
    items_applied: int = 0
    items_skipped: int = 0
    items_deleted: int = 0
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
    event_type: str = field(default="sync.remote_changes_received", init=False)
