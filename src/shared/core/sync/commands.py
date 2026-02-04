"""
Sync Context: Commands

Command objects representing sync operations.
Commands are immutable data structures that describe intent.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class SyncPullCommand:
    """
    Command to pull remote changes from Convex.

    Similar to 'git pull' - fetches remote state and applies
    it to local SQLite.
    """

    entity_types: tuple[str, ...] = (
        "code",
        "category",
        "segment",
        "source",
        "folder",
        "case",
    )
    force: bool = False  # If True, override conflicts with remote

    def with_entity_types(self, *types: str) -> SyncPullCommand:
        """Return command for specific entity types."""
        return SyncPullCommand(entity_types=types, force=self.force)

    def with_force(self) -> SyncPullCommand:
        """Return command that forces remote to override local."""
        return SyncPullCommand(entity_types=self.entity_types, force=True)


@dataclass(frozen=True)
class SyncPushCommand:
    """
    Command to push local changes to Convex.

    Pushes pending changes from the outbound queue.
    """

    max_items: int = 50  # Maximum items to push in one batch
    entity_types: tuple[str, ...] | None = None  # None = all types


@dataclass(frozen=True)
class SyncStatusCommand:
    """
    Command to get current sync status.

    Used by MCP tools and UI to query sync state.
    """

    include_pending_details: bool = False  # Include list of pending items


@dataclass(frozen=True)
class SyncConnectCommand:
    """
    Command to connect to Convex backend.
    """

    url: str = ""
    project_id: str | None = None


@dataclass(frozen=True)
class SyncDisconnectCommand:
    """
    Command to disconnect from Convex backend.
    """

    reason: str = "user_requested"
