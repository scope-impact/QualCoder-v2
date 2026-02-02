"""
Source Sync Handler - Cross-Context Denormalization Sync.

Handles synchronization of denormalized source data across bounded contexts
when source events occur. This keeps source_name columns in sync in:
- cod_segment (Coding context)
- cas_source_link (Cases context)
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from src.contexts.projects.core.events import SourceRemoved, SourceRenamed

if TYPE_CHECKING:
    from src.application.contexts.cases import CasesContext
    from src.application.contexts.coding import CodingContext
    from src.application.event_bus import EventBus

logger = logging.getLogger(__name__)


class SourceSyncHandler:
    """
    Handler for keeping denormalized source data in sync across contexts.

    When a source is renamed:
    - Updates cod_segment.source_name for all segments of that source
    - Updates cas_source_link.source_name for all case links to that source

    When a source is deleted:
    - Segments are cascade-deleted by the Coding context
    - Case links should be marked as orphaned or removed
    """

    def __init__(
        self,
        event_bus: EventBus,
        coding_context: CodingContext | None = None,
        cases_context: CasesContext | None = None,
    ) -> None:
        """
        Initialize the sync handler.

        Args:
            event_bus: Event bus to subscribe to
            coding_context: Coding context for segment updates (optional)
            cases_context: Cases context for case link updates (optional)
        """
        self._event_bus = event_bus
        self._coding_context = coding_context
        self._cases_context = cases_context
        self._subscribed = False

    def set_coding_context(self, context: CodingContext) -> None:
        """Set or update the coding context."""
        self._coding_context = context

    def set_cases_context(self, context: CasesContext) -> None:
        """Set or update the cases context."""
        self._cases_context = context

    def start(self) -> None:
        """Subscribe to source events."""
        if self._subscribed:
            return

        self._event_bus.subscribe(SourceRenamed, self._on_source_renamed)
        self._event_bus.subscribe(SourceRemoved, self._on_source_removed)
        self._subscribed = True
        logger.debug("SourceSyncHandler started")

    def stop(self) -> None:
        """Unsubscribe from source events."""
        if not self._subscribed:
            return

        self._event_bus.unsubscribe(SourceRenamed, self._on_source_renamed)
        self._event_bus.unsubscribe(SourceRemoved, self._on_source_removed)
        self._subscribed = False
        logger.debug("SourceSyncHandler stopped")

    def _on_source_renamed(self, event: SourceRenamed) -> None:
        """
        Handle source renamed event.

        Updates denormalized source_name in:
        - cod_segment table (Coding context)
        - cas_source_link table (Cases context)
        """
        logger.debug(
            f"Syncing source rename: {event.old_name} -> {event.new_name} "
            f"(id={event.source_id.value})"
        )

        # Update Coding context
        if self._coding_context is not None:
            try:
                self._coding_context.segment_repo.update_source_name(
                    event.source_id, event.new_name
                )
                logger.debug(
                    f"Updated source_name in cod_segment for source {event.source_id.value}"
                )
            except Exception as e:
                logger.error(f"Failed to update cod_segment.source_name: {e}")

        # Update Cases context
        if self._cases_context is not None:
            try:
                self._cases_context.case_repo.update_source_name(
                    event.source_id, event.new_name
                )
                logger.debug(
                    f"Updated source_name in cas_source_link for source {event.source_id.value}"
                )
            except Exception as e:
                logger.error(f"Failed to update cas_source_link.source_name: {e}")

    def _on_source_removed(self, event: SourceRemoved) -> None:
        """
        Handle source removed event.

        The Coding context handles segment deletion via CASCADE.
        Cases context may want to mark links as orphaned.
        """
        logger.debug(
            f"Source removed: {event.name} (id={event.source_id.value}), "
            f"segments_removed={event.segments_removed}"
        )

        # Cases context: could mark links as orphaned or remove them
        # For now, we leave this to the Cases context's own logic
        # since different applications may want different behavior
