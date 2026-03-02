"""
Sync Context: Invariants

Pure predicate functions for sync validation.
These encode the business rules for sync operations.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .entities import RemoteItem


def can_apply_remote_item(item_id: str, pending_outbound: frozenset[str]) -> bool:
    """Check if a remote item can be safely applied (no pending local changes)."""
    return item_id not in pending_outbound


def is_deletion_candidate(
    local_id: str,
    remote_ids: frozenset[str],
    pending_outbound: frozenset[str],
) -> bool:
    """Check if local item should be deleted (not in remote, no pending changes)."""
    return local_id not in remote_ids and local_id not in pending_outbound


def is_valid_remote_item(item: RemoteItem) -> bool:
    """Check if a remote item has valid data (non-empty ID and entity type)."""
    return bool(item.id) and bool(item.entity_type)


def has_sync_conflicts(conflicts_count: int) -> bool:
    """Check if there were any sync conflicts."""
    return conflicts_count > 0
