"""
Sync Status Command Handler

Handles the SyncStatusCommand - returns current sync state.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from src.shared.common.operation_result import OperationResult
from src.shared.core.sync.commands import SyncStatusCommand

if TYPE_CHECKING:
    from src.shared.infra.sync.engine import SyncEngine, SyncState


@dataclass(frozen=True)
class SyncStatusResult:
    """Result of sync status query."""

    cloud_sync_enabled: bool = False
    connected: bool = False
    status: str = "offline"
    pending_changes: int = 0
    last_sync: str | None = None
    error_message: str | None = None

    def to_dict(self) -> dict:
        """Convert to dictionary for MCP response."""
        return {
            "cloud_sync_enabled": self.cloud_sync_enabled,
            "connected": self.connected,
            "status": self.status,
            "pending_changes": self.pending_changes,
            "last_sync": self.last_sync,
            "error": self.error_message,
        }


def handle_sync_status(
    cmd: SyncStatusCommand,
    sync_engine: SyncEngine | None,
    cloud_sync_enabled: bool = False,
) -> OperationResult:
    """
    Handle sync status command.

    Args:
        cmd: SyncStatusCommand
        sync_engine: Optional SyncEngine (None if sync not configured)
        cloud_sync_enabled: Whether cloud sync is enabled in settings

    Returns:
        OperationResult with SyncStatusResult
    """
    if sync_engine is None:
        result = SyncStatusResult(
            cloud_sync_enabled=cloud_sync_enabled,
            connected=False,
            status="offline",
        )
        return OperationResult(success=True, data=result.to_dict())

    state = sync_engine.state

    result = SyncStatusResult(
        cloud_sync_enabled=cloud_sync_enabled,
        connected=sync_engine.is_online,
        status=state.status.value,
        pending_changes=state.pending_changes,
        last_sync=state.last_sync.isoformat() if state.last_sync else None,
        error_message=state.error_message,
    )

    return OperationResult(success=True, data=result.to_dict())
