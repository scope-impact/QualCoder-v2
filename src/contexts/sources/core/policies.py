"""
Sources Context: Policies

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
    from src.shared.infra.cascade_registry import CascadeRegistry
    from src.shared.infra.event_bus import EventBus

logger = logging.getLogger(__name__)

# Repository reference - set during initialization
_source_repo: Any = None


def set_repositories(source_repo: Any = None) -> None:
    """Configure repository references for policy handlers."""
    global _source_repo
    _source_repo = source_repo


# ============================================================
# Event Handlers (called by policies)
# ============================================================


def _handle_folder_deleted(event: Any) -> None:
    """
    Handle folder deletion - unassign sources from the deleted folder.

    Sets folder_id=NULL for all sources that were in the deleted folder.
    This reacts to FolderDeleted from the folders context.
    """
    if _source_repo is None:
        logger.debug("No source repo configured - skipping folder unassignment")
        return

    count = _source_repo.clear_folder_assignment(event.folder_id)
    logger.debug(
        "Unassigned %d sources from deleted folder (id=%d)",
        count,
        event.folder_id.value,
    )


def _handle_case_removed(event: Any) -> None:
    """
    Handle case removal - audit log for source metadata cleanup.

    Case-source links are managed by the cases context.
    Sources don't store case references directly, so no cleanup needed here.
    """
    logger.debug(
        "Case removed (id=%d) - source metadata unaffected",
        event.case_id.value,
    )


# ============================================================
# Policy Configuration
# ============================================================


def configure_sources_policies(
    event_bus: EventBus,
    cascade_registry: CascadeRegistry,
) -> None:
    """
    Configure all policies for the sources context.

    Subscribes to relevant events and routes them to handlers.

    Args:
        event_bus: The application's event bus
        cascade_registry: Cascade registry for declarative cascade rules
    """
    from src.shared.infra.cascade_registry import CascadeRule

    # --- Cascade rules (data-modifying) ---
    cascade_registry.register(
        CascadeRule(
            trigger_event_type="folders.folder_deleted",
            handler=_handle_folder_deleted,
            description="Unassign sources from deleted folder (set folder_id=NULL)",
            context="sources",
        )
    )

    # --- Audit-only handlers (subscribe directly to event bus) ---
    event_bus.subscribe("cases.case_removed", _handle_case_removed)

    logger.info("Sources context policies configured")


__all__ = [
    "configure_sources_policies",
    "set_repositories",
]
