"""
Sync Helpers - Shared logic for synced repositories.

Provides helper functions that use domain derivers to make sync decisions.
This centralizes the business logic that was previously duplicated in each
synced repository's _handle_remote_change method.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Callable, TypeVar

from src.shared.core.sync.derivers import derive_sync_changes
from src.shared.core.sync.entities import RemoteItem, SyncDomainState

if TYPE_CHECKING:
    from src.shared.core.sync.derivers import SyncDecision

logger = logging.getLogger(__name__)

T = TypeVar("T")  # Entity type


def process_remote_changes(
    entity_type: str,
    remote_items: list[dict],
    local_ids: set[str],
    pending_outbound: set[str],
    entity_builder: Callable[[dict], T | None],
    save_entity: Callable[[T], None],
    delete_entity: Callable[[str], None],
) -> tuple[int, int, int]:
    """
    Process remote changes using domain derivers.

    This function encapsulates the sync decision logic:
    1. Build RemoteItem objects from raw data
    2. Create SyncDomainState with local context
    3. Call derive_sync_changes (PURE - domain decides)
    4. Apply the decision (I/O)

    Args:
        entity_type: Type of entity (for logging)
        remote_items: Raw items from Convex
        local_ids: Set of local entity IDs
        pending_outbound: IDs with pending outbound changes
        entity_builder: Function to build entity from remote data
        save_entity: Function to save entity to local repo
        delete_entity: Function to delete entity by ID

    Returns:
        Tuple of (applied_count, skipped_count, deleted_count)
    """
    # Build RemoteItem objects
    remote_item_objs = []
    for item in remote_items:
        item_id = item.get("_id") or item.get("id")
        if item_id:
            remote_item_objs.append(RemoteItem.from_convex(entity_type, item))

    # Build state for deriver
    state = SyncDomainState.create(
        local_ids=local_ids,
        remote_items=remote_item_objs,
        pending_outbound=pending_outbound,
    )

    # Call domain deriver (PURE - domain decides)
    decision = derive_sync_changes(state)

    # Apply decision
    applied = 0
    for remote_item in decision.to_upsert:
        try:
            entity = entity_builder(remote_item.data)
            if entity is not None:
                save_entity(entity)
                applied += 1
                logger.debug(f"Synced {entity_type} from remote: {remote_item.id}")
        except Exception as e:
            logger.warning(f"Failed to apply remote {entity_type} {remote_item.id}: {e}")

    deleted = 0
    for entity_id in decision.to_delete:
        try:
            delete_entity(entity_id)
            deleted += 1
            logger.debug(f"Deleted {entity_type} from remote sync: {entity_id}")
        except Exception as e:
            logger.warning(f"Failed to delete {entity_type} {entity_id}: {e}")

    skipped = len(decision.skipped_conflicts)
    if skipped > 0:
        logger.debug(f"Skipped {skipped} {entity_type}(s) with pending outbound changes")

    return applied, skipped, deleted


def clear_pending_after_sync(
    remote_items: list[dict],
    pending_outbound: set[str],
) -> None:
    """
    Clear pending outbound IDs that have been seen in remote.

    Call this after processing remote changes to clear IDs that
    have been confirmed synced.

    Args:
        remote_items: Items received from remote
        pending_outbound: Set of pending IDs (modified in place)
    """
    for item in remote_items:
        item_id = item.get("_id") or item.get("id")
        if item_id and item_id in pending_outbound:
            pending_outbound.discard(item_id)
