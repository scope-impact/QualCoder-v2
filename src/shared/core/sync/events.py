"""
Sync Context: Domain Events

Immutable facts representing sync operations.
Events use past tense naming and are frozen dataclasses.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime


# =============================================================================
# Pull Events
# =============================================================================


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
    """
    Pull operation failed.

    Includes machine-readable error_code and recovery suggestions
    following the failure event pattern.
    """

    reason: str = ""
    error_code: str = "PULL_FAILED"
    suggestions: tuple[str, ...] = ()
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
    event_type: str = field(default="sync.pull_failed", init=False)

    @classmethod
    def network_error(cls, message: str) -> SyncPullFailed:
        """Create failure for network errors."""
        return cls(
            reason=f"Network error: {message}",
            error_code="NETWORK_ERROR",
            suggestions=(
                "Check your internet connection",
                "Verify Convex server is running",
                "Try again in a few moments",
            ),
        )

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


# =============================================================================
# Push Events
# =============================================================================


@dataclass(frozen=True)
class SyncChangeQueued:
    """Local change queued for sync to Convex."""

    entity_type: str = ""
    entity_id: str = ""
    change_type: str = ""  # "create", "update", "delete"
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
    event_type: str = field(default="sync.change_queued", init=False)


@dataclass(frozen=True)
class SyncChangePushed:
    """Local change successfully pushed to Convex."""

    entity_type: str = ""
    entity_id: str = ""
    change_type: str = ""
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
    event_type: str = field(default="sync.change_pushed", init=False)


@dataclass(frozen=True)
class SyncPushFailed:
    """Push operation failed for a specific change."""

    entity_type: str = ""
    entity_id: str = ""
    reason: str = ""
    error_code: str = "PUSH_FAILED"
    retry_count: int = 0
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
    event_type: str = field(default="sync.push_failed", init=False)


# =============================================================================
# Inbound Events (Remote → Local)
# =============================================================================


@dataclass(frozen=True)
class RemoteChangesReceived:
    """Remote changes received and applied to local SQLite."""

    entity_type: str = ""
    items_applied: int = 0
    items_skipped: int = 0
    items_deleted: int = 0
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
    event_type: str = field(default="sync.remote_changes_received", init=False)


@dataclass(frozen=True)
class SyncConflictDetected:
    """Conflict detected between local and remote changes."""

    entity_type: str = ""
    entity_id: str = ""
    conflict_type: str = ""  # "pending_outbound", "version_mismatch"
    resolution: str = "skipped"  # "skipped", "local_wins", "remote_wins"
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
    event_type: str = field(default="sync.conflict_detected", init=False)


# =============================================================================
# Status Events
# =============================================================================


@dataclass(frozen=True)
class SyncStatusChanged:
    """Sync status changed (for UI updates)."""

    status: str = ""  # "offline", "connecting", "syncing", "synced", "error"
    pending_count: int = 0
    error_message: str | None = None
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
    event_type: str = field(default="sync.status_changed", init=False)
