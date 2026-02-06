"""
Sync Context: Derivers

Pure functions that derive sync decisions and events.
Pattern: (command/data, state) → Result/Event
"""

from __future__ import annotations

from dataclasses import dataclass

from .entities import PullResult, PullSummary, RemoteItem, SyncDomainState
from .events import SyncPullCompleted, SyncPullFailed
from .invariants import (
    can_apply_remote_item,
    is_deletion_candidate,
    is_valid_remote_item,
)


@dataclass(frozen=True)
class SyncDecision:
    """Result of sync decision - what to create/update/delete."""

    to_upsert: tuple[RemoteItem, ...]
    to_delete: tuple[str, ...]
    skipped_conflicts: tuple[str, ...]

    @property
    def has_changes(self) -> bool:
        return bool(self.to_upsert) or bool(self.to_delete)

    @property
    def conflict_count(self) -> int:
        return len(self.skipped_conflicts)


def derive_sync_changes(state: SyncDomainState) -> SyncDecision:
    """
    Derive what changes to apply from remote items.

    PURE FUNCTION - No I/O, ALL business logic.
    """
    to_upsert: list[RemoteItem] = []
    skipped: list[str] = []
    remote_ids = frozenset(item.id for item in state.remote_items)

    for item in state.remote_items:
        if not is_valid_remote_item(item):
            continue
        if can_apply_remote_item(item.id, state.pending_outbound):
            to_upsert.append(item)
        else:
            skipped.append(item.id)

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


def derive_pull_completed(summary: PullSummary) -> SyncPullCompleted | SyncPullFailed:
    """Derive final pull result event from summary."""
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
    """Derive pull result for a single entity type."""
    if error:
        return PullResult(entity_type=entity_type, error=error)

    return PullResult(
        entity_type=entity_type,
        fetched_count=len(decision.to_upsert) + len(decision.skipped_conflicts),
        applied_count=len(decision.to_upsert),
        skipped_count=len(decision.skipped_conflicts),
        deleted_count=len(decision.to_delete),
    )
