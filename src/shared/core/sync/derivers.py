"""
Sync Context: Derivers

Pure functions that derive sync decisions and events.
Pattern: (command/data, state) → Result/Event

These derivers contain ALL the business logic for sync operations.
They have NO I/O - only pure computations on immutable data.
"""

from __future__ import annotations

from dataclasses import dataclass

from .entities import PullResult, PullSummary, RemoteItem, SyncDomainState
from .events import (
    RemoteChangesReceived,
    SyncPullCompleted,
    SyncPullFailed,
)
from .invariants import (
    can_apply_remote_item,
    has_sync_conflicts,
    is_deletion_candidate,
    is_valid_remote_item,
)


@dataclass(frozen=True)
class SyncDecision:
    """
    Result of sync decision - what to create/update/delete.

    This is the output of derive_sync_changes() and represents
    the domain's decision about how to handle remote items.
    """

    to_upsert: tuple[RemoteItem, ...]
    to_delete: tuple[str, ...]
    skipped_conflicts: tuple[str, ...]

    @property
    def has_changes(self) -> bool:
        """Check if there are any changes to apply."""
        return bool(self.to_upsert) or bool(self.to_delete)

    @property
    def conflict_count(self) -> int:
        """Number of items skipped due to conflicts."""
        return len(self.skipped_conflicts)


def derive_sync_changes(state: SyncDomainState) -> SyncDecision:
    """
    Derive what changes to apply from remote items.

    PURE FUNCTION - No I/O, ALL business logic.

    Rules:
    1. Validate each remote item
    2. Skip items with pending outbound changes (conflict)
    3. Upsert items that can be safely applied
    4. Delete local items not in remote (unless pending)

    Args:
        state: Immutable state container with local_ids, remote_items, pending_outbound

    Returns:
        SyncDecision with to_upsert, to_delete, and skipped_conflicts
    """
    to_upsert: list[RemoteItem] = []
    skipped: list[str] = []

    # Build set of remote IDs for deletion check
    remote_ids = frozenset(item.id for item in state.remote_items)

    # Process each remote item
    for item in state.remote_items:
        # Skip invalid items
        if not is_valid_remote_item(item):
            continue

        # Check for conflicts with pending local changes
        if can_apply_remote_item(item.id, state.pending_outbound):
            to_upsert.append(item)
        else:
            skipped.append(item.id)

    # Find items to delete (in local but not in remote, and not pending)
    to_delete = tuple(
        local_id
        for local_id in state.local_ids
        if is_deletion_candidate(local_id, remote_ids, state.pending_outbound)
    )

    return SyncDecision(
        to_upsert=tuple(to_upsert),
        to_delete=to_delete,
        skipped_conflicts=tuple(skipped),
    )


def derive_pull_result_event(
    entity_type: str,
    fetched: int,
    applied: int,
    skipped: int,
    deleted: int,
) -> RemoteChangesReceived:
    """
    Derive event for a single entity type pull result.

    Args:
        entity_type: Type of entity pulled (e.g., "code", "source")
        fetched: Number of items fetched from remote
        applied: Number of items applied to local
        skipped: Number of items skipped (conflicts)
        deleted: Number of local items deleted

    Returns:
        RemoteChangesReceived event
    """
    return RemoteChangesReceived(
        entity_type=entity_type,
        items_applied=applied,
        items_skipped=skipped,
        items_deleted=deleted,
    )


def derive_pull_completed(
    summary: PullSummary,
) -> SyncPullCompleted | SyncPullFailed:
    """
    Derive final pull result event from summary.

    Args:
        summary: Complete pull summary with all entity results

    Returns:
        SyncPullCompleted on success, SyncPullFailed if any errors
    """
    # Check for errors
    if summary.has_errors:
        failed_types = [r.entity_type for r in summary.results if r.error]
        return SyncPullFailed.partial_failure(failed_types)

    return SyncPullCompleted(
        entity_counts=summary.entity_counts,
        conflicts_skipped=summary.total_conflicts,
        timestamp=summary.completed_at or summary.started_at,
    )


def derive_entity_pull_result(
    entity_type: str,
    decision: SyncDecision,
    error: str | None = None,
) -> PullResult:
    """
    Derive pull result for a single entity type.

    Args:
        entity_type: Type of entity
        decision: Sync decision from derive_sync_changes
        error: Optional error message if fetch failed

    Returns:
        PullResult with counts
    """
    if error:
        return PullResult(
            entity_type=entity_type,
            error=error,
        )

    return PullResult(
        entity_type=entity_type,
        fetched_count=len(decision.to_upsert) + len(decision.skipped_conflicts),
        applied_count=len(decision.to_upsert),
        skipped_count=len(decision.skipped_conflicts),
        deleted_count=len(decision.to_delete),
    )


def derive_should_notify_ui(
    entity_counts: dict[str, int],
    conflicts: int,
) -> bool:
    """
    Derive whether UI should be notified of pull results.

    Notify if:
    - Any items were synced
    - Any conflicts occurred

    Args:
        entity_counts: Count of items synced per entity type
        conflicts: Number of conflicts

    Returns:
        True if UI should be notified
    """
    has_items = any(count > 0 for count in entity_counts.values())
    return has_items or has_sync_conflicts(conflicts)
