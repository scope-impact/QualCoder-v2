"""
Sync Signal Bridge - Domain Events → Qt Signals for sync operations.

Bridges sync events to UI for status updates, notifications,
and reactive UI updates when sync operations complete.

Architecture:
    Sync Events (from command handlers)
         ↓ EventBus subscription
    SyncSignalBridge
         ↓ Converter (event → payload)
         ↓ Thread-safe emission
    Qt Signals (main thread)
         ↓
    AppShell status bar, notifications
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from PySide6.QtCore import Signal

from src.shared.infra.signal_bridge.base import BaseSignalBridge
from src.shared.infra.signal_bridge.payloads import (
    ActivityItem,
    ActivityStatus,
    SignalPayload,
)

if TYPE_CHECKING:
    from src.shared.core.sync.events import (
        RemoteChangesReceived,
        SyncPullCompleted,
        SyncPullFailed,
        SyncPullStarted,
    )


# =============================================================================
# Payloads (UI-friendly DTOs)
# =============================================================================


@dataclass(frozen=True)
class SyncStatusPayload(SignalPayload):
    """
    Payload for sync status updates.

    Used to update the status bar sync indicator.
    """

    status: str  # "offline", "connecting", "syncing", "synced", "error"
    pending_count: int = 0
    last_sync: str | None = None
    error_message: str | None = None

    @classmethod
    def pulling(cls) -> SyncStatusPayload:
        """Create payload for pull in progress."""
        return cls(
            timestamp=datetime.now(UTC),
            session_id="local",
            is_ai_action=False,
            event_type="sync.pull_started",
            status="syncing",
        )

    @classmethod
    def synced(
        cls,
        last_sync: datetime | None = None,
        pending: int = 0,
    ) -> SyncStatusPayload:
        """Create payload for synced state."""
        return cls(
            timestamp=datetime.now(UTC),
            session_id="local",
            is_ai_action=False,
            event_type="sync.pull_completed",
            status="synced",
            pending_count=pending,
            last_sync=last_sync.isoformat() if last_sync else None,
        )

    @classmethod
    def error(cls, message: str) -> SyncStatusPayload:
        """Create payload for error state."""
        return cls(
            timestamp=datetime.now(UTC),
            session_id="local",
            is_ai_action=False,
            event_type="sync.pull_failed",
            status="error",
            error_message=message,
        )


@dataclass(frozen=True)
class SyncResultPayload(SignalPayload):
    """
    Payload for sync completion with results.

    Used to show sync summary in notifications.
    """

    entity_counts: dict[str, int]
    conflicts_skipped: int = 0
    total_applied: int = 0


# =============================================================================
# Converters (Event → Payload)
# =============================================================================


class SyncPullStartedConverter:
    """Convert SyncPullStarted event to UI payload."""

    def convert(self, _event: SyncPullStarted) -> SyncStatusPayload:
        return SyncStatusPayload.pulling()


class SyncPullCompletedConverter:
    """Convert SyncPullCompleted event to payloads."""

    def convert(self, event: SyncPullCompleted) -> SyncStatusPayload:
        return SyncStatusPayload.synced(
            last_sync=event.timestamp,
            pending=0,
        )

    def to_result_payload(self, event: SyncPullCompleted) -> SyncResultPayload:
        """Convert to detailed result payload."""
        return SyncResultPayload(
            timestamp=event.timestamp,
            session_id="local",
            is_ai_action=False,
            event_type=event.event_type,
            entity_counts=event.entity_counts,
            conflicts_skipped=event.conflicts_skipped,
            total_applied=sum(event.entity_counts.values()),
        )


class SyncPullFailedConverter:
    """Convert SyncPullFailed event to UI payload."""

    def convert(self, event: SyncPullFailed) -> SyncStatusPayload:
        return SyncStatusPayload.error(event.reason)


class RemoteChangesReceivedConverter:
    """Convert RemoteChangesReceived to activity item."""

    def convert(self, event: RemoteChangesReceived) -> ActivityItem:
        total = event.items_applied + event.items_deleted
        if total == 0:
            description = f"Checked {event.entity_type}s (no changes)"
        else:
            parts = []
            if event.items_applied > 0:
                parts.append(f"{event.items_applied} updated")
            if event.items_deleted > 0:
                parts.append(f"{event.items_deleted} removed")
            description = f"Synced {event.entity_type}s: {', '.join(parts)}"

        return ActivityItem(
            timestamp=event.timestamp,
            session_id="local",
            description=description,
            status=ActivityStatus.COMPLETED,
            context="sync",
            entity_type=event.entity_type,
            is_ai_action=False,
            metadata={
                "applied": event.items_applied,
                "skipped": event.items_skipped,
                "deleted": event.items_deleted,
            },
        )


# =============================================================================
# Signal Bridge
# =============================================================================


class SyncSignalBridge(BaseSignalBridge):
    """
    Signal bridge for sync domain events.

    Converts sync events to Qt signals for UI updates:
    - sync_status_changed: Updates status bar indicator
    - sync_completed: Triggers completion notification
    - activity_logged: Adds items to activity feed
    """

    # Qt Signals
    sync_status_changed = Signal(object)  # SyncStatusPayload
    sync_completed = Signal(object)  # SyncResultPayload
    activity_logged = Signal(object)  # ActivityItem

    def _get_context_name(self) -> str:
        """Return context name for activity logging."""
        return "sync"

    def _register_converters(self) -> None:
        """Register event converters for sync events."""
        # Pull started → status update
        self.register_converter(
            "sync.pull_started",
            SyncPullStartedConverter(),
            "sync_status_changed",
        )

        # Pull completed → status update + completion signal
        self.register_converter(
            "sync.pull_completed",
            SyncPullCompletedConverter(),
            "sync_status_changed",
        )

        # Pull failed → status update (error)
        self.register_converter(
            "sync.pull_failed",
            SyncPullFailedConverter(),
            "sync_status_changed",
        )

        # Remote changes → activity feed
        self.register_converter(
            "sync.remote_changes_received",
            RemoteChangesReceivedConverter(),
            "activity_logged",
        )

    def _create_activity_item(
        self,
        event_type: str,
        payload: SignalPayload,
    ) -> ActivityItem | None:
        """
        Create activity item for sync events.

        Override to customize activity logging.
        """
        if event_type == "sync.pull_completed":
            result = payload
            if isinstance(result, SyncStatusPayload):
                return ActivityItem.completed(
                    description="Cloud sync completed",
                    context="sync",
                    entity_type="sync",
                    metadata={"status": result.status},
                )
        elif event_type == "sync.pull_failed":
            if isinstance(payload, SyncStatusPayload):
                return ActivityItem.failed(
                    description="Cloud sync failed",
                    context="sync",
                    entity_type="sync",
                    error=payload.error_message,
                )
        return None
