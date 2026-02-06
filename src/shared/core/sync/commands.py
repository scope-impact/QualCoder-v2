"""
Sync Context: Commands

Command objects representing sync operations.
Commands are immutable data structures that describe intent.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SyncPullCommand:
    """Command to pull remote changes from Convex (like 'git pull')."""

    entity_types: tuple[str, ...] = (
        "code",
        "category",
        "segment",
        "source",
        "folder",
        "case",
    )
    force: bool = False  # If True, override conflicts with remote


@dataclass(frozen=True)
class SyncStatusCommand:
    """Command to get current sync status."""

    include_pending_details: bool = False
