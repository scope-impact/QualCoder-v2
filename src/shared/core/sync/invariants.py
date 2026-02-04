"""
Sync Context: Invariants

Pure predicate functions for sync validation.
Named with is_* or can_* prefixes.

These invariants encode the business rules for sync operations:
- When to skip remote changes (conflicts)
- When to delete local items
- When it's safe to apply changes
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .entities import RemoteItem


def is_conflicting_change(item_id: str, pending_outbound: frozenset[str]) -> bool:
    """
    Check if remote change conflicts with pending local change.

    A conflict exists when we have local changes waiting to be pushed
    to Convex for the same item that remote is trying to update.

    Rule: Local changes take precedence - skip remote updates for
    items with pending outbound changes.
    """
    return item_id in pending_outbound


def can_apply_remote_item(item_id: str, pending_outbound: frozenset[str]) -> bool:
    """
    Check if a remote item can be safely applied to local SQLite.

    An item can be applied if there are no pending local changes
    for the same item.
    """
    return not is_conflicting_change(item_id, pending_outbound)


def is_deletion_candidate(
    local_id: str,
    remote_ids: frozenset[str],
    pending_outbound: frozenset[str],
) -> bool:
    """
    Check if local item should be deleted (not in remote anymore).

    A local item is a deletion candidate if:
    1. It's not present in the remote dataset
    2. It doesn't have pending local changes

    This handles the case where an item was deleted on another device
    and we need to sync that deletion locally.
    """
    not_in_remote = local_id not in remote_ids
    not_pending = local_id not in pending_outbound
    return not_in_remote and not_pending


def is_valid_remote_item(item: RemoteItem) -> bool:
    """
    Check if a remote item has valid data for sync.

    A valid item must have:
    - Non-empty ID
    - Non-empty entity type
    """
    return bool(item.id) and bool(item.entity_type)


def can_sync_entity_type(entity_type: str) -> bool:
    """
    Check if an entity type is supported for sync.

    Supported types are the core qualitative data entities.
    """
    supported_types = frozenset({
        "code",
        "category",
        "segment",
        "source",
        "folder",
        "case",
    })
    return entity_type in supported_types


def is_empty_pull_result(entity_counts: dict[str, int]) -> bool:
    """Check if a pull result contains no items."""
    return all(count == 0 for count in entity_counts.values())


def has_sync_conflicts(conflicts_count: int) -> bool:
    """Check if there were any sync conflicts."""
    return conflicts_count > 0
