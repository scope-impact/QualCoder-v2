"""
Cases Context: Policies

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

logger = logging.getLogger(__name__)

# Repository reference - set during initialization
_case_repo: Any = None


def set_repositories(
    case_repo: Any = None,
) -> None:
    """
    Configure repository references for policy handlers.

    Args:
        case_repo: Repository for case link operations
    """
    global _case_repo
    _case_repo = case_repo


# ============================================================
# Event Handlers (called by policies)
# ============================================================


def _handle_source_renamed(event: Any) -> None:
    """
    Handle source rename - sync denormalized source_name in case links.

    This reacts to SourceRenamed from the sources context.
    """
    if _case_repo is None:
        logger.debug("No case repo configured - skipping case link name sync")
        return

    try:
        if hasattr(_case_repo, "update_source_name"):
            _case_repo.update_source_name(event.source_id, event.new_name)
            logger.debug(
                "Synced case link source_name: %s -> %s (source_id=%d)",
                event.old_name,
                event.new_name,
                event.source_id.value,
            )
    except Exception as e:
        logger.error("Failed to sync case link source_name: %s", e)
        raise


def _handle_source_removed(event: Any) -> None:
    """
    Handle source removal - remove case links for the source.

    This reacts to SourceRemoved from the sources context.
    """
    if _case_repo is None:
        logger.debug("No case repo configured - skipping case unlink")
        return

    try:
        if hasattr(_case_repo, "remove_links_for_source"):
            _case_repo.remove_links_for_source(event.source_id)
            logger.debug(
                "Removed case links for source: %s (id=%d)",
                event.name,
                event.source_id.value,
            )
    except Exception as e:
        logger.error("Failed to unlink cases: %s", e)
        raise


# ============================================================
# Policy Configuration
# ============================================================


def configure_cases_policies(event_bus: EventBus) -> None:
    """
    Configure all policies for the cases context.

    Subscribes to relevant events and routes them to handlers.

    Args:
        event_bus: The application's event bus
    """
    # Cross-context events (from projects context)
    # Subscribe by event type string to avoid coupling to projects context imports
    event_bus.subscribe("projects.source_renamed", _handle_source_renamed)
    event_bus.subscribe("projects.source_removed", _handle_source_removed)

    logger.info("Cases context policies configured")


__all__ = [
    "configure_cases_policies",
    "set_repositories",
]
