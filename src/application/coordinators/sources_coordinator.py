"""
Sources Coordinator - Source File Management.

Handles all source-related CRUD operations.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from returns.result import Result

from src.application.coordinators.base import BaseCoordinator

if TYPE_CHECKING:
    from src.contexts.projects.core.entities import Source


class SourcesCoordinator(BaseCoordinator):
    """
    Coordinator for source file operations.

    Manages:
    - Adding sources to the project
    - Removing sources
    - Opening sources for viewing/coding
    - Updating source metadata
    - Source queries

    Requires an open project for all operations.
    """

    # =========================================================================
    # Source Commands
    # =========================================================================

    def add_source(self, command) -> Result:
        """
        Add a source file to the current project.

        Args:
            command: AddSourceCommand with source path and metadata

        Returns:
            Success with Source entity, or Failure with error
        """
        from src.application.sources.usecases import add_source

        return add_source(
            command=command,
            state=self.state,
            sources_ctx=self.sources_context,
            event_bus=self.event_bus,
        )

    def remove_source(self, command) -> Result:
        """
        Remove a source from the current project.

        Args:
            command: RemoveSourceCommand with source ID

        Returns:
            Success with event, or Failure with error
        """
        from src.application.sources.usecases import remove_source

        return remove_source(
            command=command,
            state=self.state,
            sources_ctx=self.sources_context,
            coding_ctx=self.coding_context,
            event_bus=self.event_bus,
        )

    def open_source(self, command) -> Result:
        """
        Open a source for viewing/coding.

        Args:
            command: OpenSourceCommand with source ID

        Returns:
            Success with event, or Failure with error
        """
        from src.application.sources.usecases import open_source

        return open_source(
            command=command,
            state=self.state,
            event_bus=self.event_bus,
        )

    def update_source(self, command) -> Result:
        """
        Update source metadata.

        Args:
            command: UpdateSourceCommand with source ID and updates

        Returns:
            Success with updated Source, or Failure with error
        """
        from src.application.sources.usecases import update_source

        return update_source(
            command=command,
            state=self.state,
            sources_ctx=self.sources_context,
            event_bus=self.event_bus,
        )

    # =========================================================================
    # Source Queries
    # =========================================================================

    def get_sources(self) -> list[Source]:
        """Get all sources in the current project."""
        return list(self.state.sources)

    def get_source(self, source_id: int) -> Source | None:
        """Get a specific source by ID."""
        return self.state.get_source(source_id)

    def get_sources_by_type(self, source_type: str) -> list[Source]:
        """Get sources filtered by type."""
        return [s for s in self.state.sources if s.source_type.value == source_type]

    def get_current_source(self) -> Source | None:
        """Get the currently open source."""
        return self.state.current_source

    def get_segment_count_for_source(self, source_id: int) -> int:
        """
        Get the count of coded segments for a source.

        Useful for warning users before deleting a source that has coded data.
        """
        from src.contexts.shared.core.types import SourceId

        if self.coding_context is None or self.coding_context.segment_repo is None:
            return 0

        sid = SourceId(value=source_id)
        return self.coding_context.segment_repo.count_by_source(sid)
