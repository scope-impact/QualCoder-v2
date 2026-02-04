"""
Sync Pull Command Handler

Handles the SyncPullCommand - fetches remote data and applies it locally.
Follows the command handler pattern: orchestration only, domain decides.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from src.shared.common.operation_result import OperationResult
from src.shared.core.sync.commands import SyncPullCommand
from src.shared.core.sync.derivers import (
    derive_entity_pull_result,
    derive_pull_completed,
    derive_sync_changes,
)
from src.shared.core.sync.entities import (
    PullResult,
    PullSummary,
    RemoteItem,
    SyncDomainState,
)
from src.shared.core.sync.events import (
    RemoteChangesReceived,
    SyncPullFailed,
    SyncPullStarted,
)

if TYPE_CHECKING:
    from src.shared.infra.event_bus import EventBus
    from src.shared.infra.sync.engine import SyncEngine

logger = logging.getLogger(__name__)


def handle_sync_pull(
    cmd: SyncPullCommand,
    sync_engine: SyncEngine,
    event_bus: EventBus,
) -> OperationResult:
    """
    Handle sync pull command - orchestration only.

    Pattern:
    1. Publish start event
    2. For each entity type:
       a. Fetch remote data (I/O)
       b. Load local state (I/O)
       c. Derive sync decision (PURE - domain decides)
       d. Apply changes (I/O)
       e. Publish per-entity event
    3. Derive final result (PURE)
    4. Publish completion event
    5. Return OperationResult

    Args:
        cmd: SyncPullCommand with entity types to pull
        sync_engine: SyncEngine for I/O operations
        event_bus: EventBus for publishing domain events

    Returns:
        OperationResult with entity counts on success
    """
    # Validate connection
    if not sync_engine.is_online:
        failure = SyncPullFailed.not_connected()
        event_bus.publish(failure)
        return OperationResult(
            success=False,
            error=failure.reason,
            error_code=failure.error_code,
            suggestions=list(failure.suggestions),
        )

    # 1. Publish start event
    event_bus.publish(SyncPullStarted())
    logger.info(f"Starting sync pull for: {cmd.entity_types}")

    # Track results
    results: list[PullResult] = []
    total_conflicts = 0
    started_at = datetime.now(UTC)

    # 2. Process each entity type
    for entity_type in cmd.entity_types:
        result = _pull_entity_type(
            entity_type=entity_type,
            sync_engine=sync_engine,
            event_bus=event_bus,
            force=cmd.force,
        )
        results.append(result)
        total_conflicts += result.skipped_count

    # 3. Create summary and derive final event
    summary = PullSummary(
        results=tuple(results),
        started_at=started_at,
        total_conflicts=total_conflicts,
    ).with_completed()

    # 4. Derive and publish completion event (DOMAIN DECIDES)
    completion_event = derive_pull_completed(summary)
    event_bus.publish(completion_event)

    # 5. Return OperationResult
    if isinstance(completion_event, SyncPullFailed):
        return OperationResult(
            success=False,
            error=completion_event.reason,
            error_code=completion_event.error_code,
            suggestions=list(completion_event.suggestions),
        )

    logger.info(f"Sync pull completed: {summary.entity_counts}")
    return OperationResult(
        success=True,
        data={
            "entity_counts": summary.entity_counts,
            "total_applied": summary.total_applied,
            "conflicts_skipped": total_conflicts,
        },
    )


def _pull_entity_type(
    entity_type: str,
    sync_engine: SyncEngine,
    event_bus: EventBus,
    force: bool = False,
) -> PullResult:
    """
    Pull a single entity type from remote.

    Args:
        entity_type: Type of entity to pull
        sync_engine: SyncEngine for I/O
        event_bus: EventBus for events
        force: If True, override conflicts

    Returns:
        PullResult with counts
    """
    try:
        # a. Fetch remote data (I/O)
        remote_data = _fetch_remote_data(entity_type, sync_engine)
        if remote_data is None:
            return PullResult(
                entity_type=entity_type,
                error=f"Failed to fetch {entity_type}",
            )

        # Convert to RemoteItems
        remote_items = tuple(
            RemoteItem.from_convex(entity_type, item) for item in remote_data
        )

        # b. Load local state (I/O)
        local_ids = _get_local_ids(entity_type, sync_engine)
        pending = sync_engine.get_pending_ids(entity_type) if not force else frozenset()

        # c. Build state and derive sync decision (PURE - domain decides)
        state = SyncDomainState.create(
            local_ids=local_ids,
            remote_items=remote_items,
            pending_outbound=pending,
        )
        decision = derive_sync_changes(state)

        # d. Apply changes (I/O)
        applied = _apply_sync_decision(entity_type, decision, sync_engine)

        # e. Publish per-entity event
        event = RemoteChangesReceived(
            entity_type=entity_type,
            items_applied=applied,
            items_skipped=decision.conflict_count,
            items_deleted=len(decision.to_delete),
        )
        event_bus.publish(event)

        # Return result using deriver
        return derive_entity_pull_result(entity_type, decision)

    except Exception as e:
        logger.warning(f"Failed to pull {entity_type}: {e}")
        return PullResult(
            entity_type=entity_type,
            error=str(e),
        )


def _fetch_remote_data(entity_type: str, sync_engine: SyncEngine) -> list[dict] | None:
    """Fetch remote data for an entity type via SyncEngine."""
    convex = sync_engine._convex
    if convex is None:
        return None

    # Map entity type to Convex query method
    fetch_methods = {
        "code": convex.get_all_codes,
        "category": convex.get_all_categories,
        "segment": convex.get_all_segments,
        "source": convex.get_all_sources,
        "folder": convex.get_all_folders,
        "case": convex.get_all_cases,
    }

    method = fetch_methods.get(entity_type)
    if method is None:
        logger.warning(f"Unknown entity type for fetch: {entity_type}")
        return None

    try:
        return method()
    except Exception as e:
        logger.warning(f"Convex fetch failed for {entity_type}: {e}")
        return None


def _get_local_ids(entity_type: str, sync_engine: SyncEngine) -> frozenset[str]:
    """Get local IDs for an entity type."""
    # This would need to query the local repos
    # For now, delegate to sync_engine which has listener access
    listeners = sync_engine._change_listeners.get(entity_type, [])
    # Listeners don't give us local IDs directly
    # We'll need to track this differently or get from repos
    # For now return empty - deletions won't be detected
    return frozenset()


def _apply_sync_decision(
    entity_type: str,
    decision,  # SyncDecision
    sync_engine: SyncEngine,
) -> int:
    """
    Apply sync decision by notifying listeners.

    Returns count of items notified.
    """
    if not decision.has_changes:
        return 0

    # Notify listeners with items to upsert
    items_data = [item.data for item in decision.to_upsert]
    sync_engine._notify_listeners(entity_type, items_data)

    return len(decision.to_upsert)
