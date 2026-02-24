"""
Folders Context: Policies

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


# ============================================================
# Event Handlers (called by policies)
# ============================================================


def _handle_source_removed(event: Any) -> None:
    """
    Handle source removal - audit log folder membership cleanup.

    The source row (with folder_id) is deleted by the projects/sources context.
    No folder-side cleanup needed since folders don't store source references.
    """
    logger.debug(
        "Source removed: %s (id=%d) - folder membership automatically cleaned up",
        event.name,
        event.source_id.value,
    )


# ============================================================
# Policy Configuration
# ============================================================


def configure_folders_policies(
    event_bus: EventBus,
    cascade_registry: CascadeRegistry,  # noqa: ARG001
) -> None:
    """
    Configure all policies for the folders context.

    Subscribes to relevant events and routes them to handlers.

    Args:
        event_bus: The application's event bus
        cascade_registry: Cascade registry (unused - audit-only handlers)
    """
    # --- Audit-only handlers (subscribe directly to event bus) ---
    event_bus.subscribe("projects.source_removed", _handle_source_removed)

    logger.info("Folders context policies configured")


__all__ = [
    "configure_folders_policies",
]
