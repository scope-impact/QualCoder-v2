"""
Coding Context: Policies

Reactive handlers that respond to domain events.
Each policy subscribes to events and calls command handlers within THIS context.

Following the DDD Workshop pattern:
- Policies live inside the bounded context
- Policies call the context's own command handlers
- Each context manages its own data
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from src.shared.infra.event_bus import EventBus

from src.contexts.coding.core.events import (
    CategoryDeleted,
    CodeDeleted,
    CodesMerged,
)

logger = logging.getLogger(__name__)

# Repository reference - set during initialization
_code_repo: Any = None
_segment_repo: Any = None


def set_repositories(
    code_repo: Any = None,
    segment_repo: Any = None,
) -> None:
    """
    Configure repository references for policy handlers.

    Args:
        code_repo: Repository for code operations
        segment_repo: Repository for segment operations
    """
    global _code_repo, _segment_repo
    _code_repo = code_repo
    _segment_repo = segment_repo


# ============================================================
# Event Handlers (called by policies)
# ============================================================


def _handle_category_deleted(event: CategoryDeleted) -> None:
    """
    Handle orphaned codes when their category is deleted.

    Moves codes to uncategorized (category_id = NULL).
    """
    logger.debug(
        "Category deleted: %s (id=%d), codes_orphaned=%d",
        event.name,
        event.category_id.value,
        event.codes_orphaned,
    )

    if _code_repo is None:
        logger.debug("No code repo configured - skipping orphan codes")
        return

    if event.codes_orphaned == 0:
        return

    try:
        if hasattr(_code_repo, "uncategorize_codes_in_category"):
            _code_repo.uncategorize_codes_in_category(event.category_id)
            logger.debug(
                "Orphaned %d codes from category %s",
                event.codes_orphaned,
                event.name,
            )
    except Exception as e:
        logger.error("Failed to orphan codes: %s", e)
        raise


def _handle_code_deleted(event: CodeDeleted) -> None:
    """
    Handle code deletion - audit logging.

    Segments are cascade-deleted by the database.
    """
    logger.info(
        "Code deleted: %s (id=%d), segments_removed=%d",
        event.name,
        event.code_id.value,
        event.segments_removed,
    )


def _handle_codes_merged(event: CodesMerged) -> None:
    """
    Handle codes merge - audit logging.
    """
    logger.info(
        "Codes merged: %s (id=%d) -> %s (id=%d), segments_moved=%d",
        event.source_code_name,
        event.source_code_id.value,
        event.target_code_name,
        event.target_code_id.value,
        event.segments_moved,
    )


def _handle_source_renamed(event: Any) -> None:
    """
    Handle source rename - sync denormalized source_name in segments.

    This reacts to SourceRenamed from the sources context.
    """
    if _segment_repo is None:
        logger.debug("No segment repo configured - skipping segment name sync")
        return

    try:
        if hasattr(_segment_repo, "update_source_name"):
            _segment_repo.update_source_name(event.source_id, event.new_name)
            logger.debug(
                "Synced segment source_name: %s -> %s (source_id=%d)",
                event.old_name,
                event.new_name,
                event.source_id.value,
            )
    except Exception as e:
        logger.error("Failed to sync segment source_name: %s", e)
        raise


def _handle_source_removed(event: Any) -> None:
    """
    Handle source removal - log segment cleanup.

    Segments are typically cascade-deleted by the database.
    """
    logger.debug(
        "Source removed: %s (id=%d), segments will be cascade-deleted",
        event.name,
        event.source_id.value,
    )


# ============================================================
# Policy Configuration
# ============================================================


def configure_coding_policies(event_bus: EventBus) -> None:
    """
    Configure all policies for the coding context.

    Subscribes to relevant events and routes them to handlers.

    Args:
        event_bus: The application's event bus
    """
    # Internal coding events
    event_bus.subscribe_type(CategoryDeleted, _handle_category_deleted)
    event_bus.subscribe_type(CodeDeleted, _handle_code_deleted)
    event_bus.subscribe_type(CodesMerged, _handle_codes_merged)

    # Cross-context events (from projects context)
    # Subscribe by event type string to avoid coupling to projects context imports
    event_bus.subscribe("projects.source_renamed", _handle_source_renamed)
    event_bus.subscribe("projects.source_removed", _handle_source_removed)

    logger.info("Coding context policies configured")


__all__ = [
    "configure_coding_policies",
    "set_repositories",
]
