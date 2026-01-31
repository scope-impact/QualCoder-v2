"""
File Manager ViewModel

Connects the FileManagerScreen to the ProjectController.
Handles data transformation between domain entities and UI DTOs.

Architecture:
    User Action → ViewModel → Controller → Domain → Events
                                                       ↓
    UI Update ← ViewModel ← EventBus ←────────────────┘
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from returns.result import Success

from src.application.projects.controller import (
    AddSourceCommand,
    OpenSourceCommand,
    RemoveSourceCommand,
)
from src.domain.projects.entities import Source
from src.presentation.dto import ProjectSummaryDTO, SourceDTO

if TYPE_CHECKING:
    from src.application.event_bus import EventBus
    from src.application.projects.controller import ProjectControllerImpl


class FileManagerViewModel:
    """
    ViewModel for the File Manager screen.

    Responsibilities:
    - Transform domain Source entities to UI DTOs
    - Handle user actions by calling controller commands
    - React to domain events via EventBus
    - Provide filtering and search capabilities
    - Track selection state for bulk operations

    This is a pure Python class (no Qt dependency) so it can be
    tested without a Qt event loop.
    """

    def __init__(
        self,
        controller: ProjectControllerImpl,
        event_bus: EventBus,
    ) -> None:
        """
        Initialize the ViewModel.

        Args:
            controller: The project controller for commands
            event_bus: The event bus for reactive updates
        """
        self._controller = controller
        self._event_bus = event_bus

        # Selection state
        self._selected_source_ids: set[int] = set()
        self._current_source_id: int | None = None

        # Connect to events
        self._connect_events()

    def _connect_events(self) -> None:
        """Connect to relevant domain events."""
        # Events will trigger UI updates via callbacks
        # For now, this is a placeholder - actual connections
        # would be made when using Qt signals
        pass

    # =========================================================================
    # Load Data
    # =========================================================================

    def load_sources(self) -> list[SourceDTO]:
        """
        Load all sources and return as DTOs.

        Returns:
            List of SourceDTO objects for UI display
        """
        sources = self._controller.get_sources()
        return [self._source_to_dto(s) for s in sources]

    def get_summary(self) -> ProjectSummaryDTO:
        """
        Get project summary statistics.

        Returns:
            ProjectSummaryDTO with counts by type
        """
        summary = self._controller.get_project_summary()

        if summary is None:
            return ProjectSummaryDTO()

        return ProjectSummaryDTO(
            total_sources=summary.total_sources,
            text_count=summary.text_count,
            audio_count=summary.audio_count,
            video_count=summary.video_count,
            image_count=summary.image_count,
            pdf_count=summary.pdf_count,
            total_codes=summary.total_codes,
            total_segments=summary.total_segments,
        )

    def get_current_source(self) -> SourceDTO | None:
        """
        Get the currently open source.

        Returns:
            SourceDTO if a source is open, None otherwise
        """
        if self._current_source_id is None:
            return None

        source = self._controller.get_source(self._current_source_id)
        return self._source_to_dto(source) if source else None

    # =========================================================================
    # Source Commands
    # =========================================================================

    def add_source(
        self,
        path: str,
        origin: str | None = None,
        memo: str | None = None,
    ) -> bool:
        """
        Add a source file to the project.

        Args:
            path: Path to the source file
            origin: Optional origin/category
            memo: Optional memo

        Returns:
            True if successful, False otherwise
        """
        command = AddSourceCommand(
            source_path=path,
            origin=origin,
            memo=memo,
        )

        result = self._controller.add_source(command)

        return isinstance(result, Success)

    def remove_source(self, source_id: int) -> bool:
        """
        Remove a source from the project.

        Args:
            source_id: ID of source to remove

        Returns:
            True if successful, False otherwise
        """
        command = RemoveSourceCommand(source_id=source_id)
        result = self._controller.remove_source(command)

        if isinstance(result, Success):
            self._selected_source_ids.discard(source_id)
            if self._current_source_id == source_id:
                self._current_source_id = None
            return True

        return False

    def remove_sources(self, source_ids: list[int]) -> bool:
        """
        Remove multiple sources from the project.

        Args:
            source_ids: List of source IDs to remove

        Returns:
            True if all successful, False if any failed
        """
        all_success = True
        for source_id in source_ids:
            if not self.remove_source(source_id):
                all_success = False

        return all_success

    def open_source(self, source_id: int) -> bool:
        """
        Open a source for viewing/coding.

        Args:
            source_id: ID of source to open

        Returns:
            True if successful, False otherwise
        """
        command = OpenSourceCommand(source_id=source_id)
        result = self._controller.open_source(command)

        if isinstance(result, Success):
            self._current_source_id = source_id
            return True

        return False

    # =========================================================================
    # Selection
    # =========================================================================

    def select_sources(self, source_ids: list[int]) -> None:
        """
        Set the selected sources.

        Args:
            source_ids: List of source IDs to select
        """
        self._selected_source_ids = set(source_ids)

    def toggle_source_selection(self, source_id: int) -> None:
        """
        Toggle selection state of a source.

        Args:
            source_id: ID of source to toggle
        """
        if source_id in self._selected_source_ids:
            self._selected_source_ids.discard(source_id)
        else:
            self._selected_source_ids.add(source_id)

    def clear_selection(self) -> None:
        """Clear all selected sources."""
        self._selected_source_ids.clear()

    def get_selected_sources(self) -> list[SourceDTO]:
        """
        Get the currently selected sources.

        Returns:
            List of selected SourceDTO objects
        """
        sources = self._controller.get_sources()
        return [
            self._source_to_dto(s)
            for s in sources
            if s.id.value in self._selected_source_ids
        ]

    def get_selected_count(self) -> int:
        """Get the number of selected sources."""
        return len(self._selected_source_ids)

    # =========================================================================
    # Filtering and Search
    # =========================================================================

    def filter_sources(
        self,
        source_type: str | None = None,
        status: str | None = None,
    ) -> list[SourceDTO]:
        """
        Filter sources by type and/or status.

        Args:
            source_type: Filter by type (text, audio, video, image, pdf)
            status: Filter by status (imported, coded, etc.)

        Returns:
            Filtered list of SourceDTO objects
        """
        sources = self._controller.get_sources()

        if source_type:
            sources = [s for s in sources if s.source_type.value == source_type]

        if status:
            sources = [s for s in sources if s.status.value == status]

        return [self._source_to_dto(s) for s in sources]

    def search_sources(self, query: str) -> list[SourceDTO]:
        """
        Search sources by name.

        Args:
            query: Search query (case-insensitive)

        Returns:
            List of matching SourceDTO objects
        """
        sources = self._controller.get_sources()
        query_lower = query.lower()

        matching = [s for s in sources if query_lower in s.name.lower()]

        return [self._source_to_dto(s) for s in matching]

    # =========================================================================
    # Private Helpers
    # =========================================================================

    def _source_to_dto(self, source: Source) -> SourceDTO:
        """Convert a Source entity to DTO."""
        return SourceDTO(
            id=str(source.id.value),
            name=source.name,
            source_type=source.source_type.value,
            status=source.status.value,
            file_size=source.file_size,
            code_count=source.code_count,
            memo=source.memo,
            origin=source.origin,
            cases=[],  # TODO: Load from case associations
            modified_at=source.modified_at.isoformat() if source.modified_at else None,
        )
