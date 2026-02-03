"""
File Manager ViewModel

Connects the FileManagerScreen to a controller that implements FileManagerController.
Handles data transformation between domain entities and UI DTOs.

Architecture:
    User Action → ViewModel → Controller → Use Case → Domain → Events
                                                                   ↓
    UI Update ← ViewModel ← SignalBridge ←─────────────────────────┘
                    ↓
    ViewModel signals → Screen
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import QObject, Signal

from src.application.projects.commands import (
    AddSourceCommand,
    CreateFolderCommand,
    DeleteFolderCommand,
    MoveSourceToFolderCommand,
    OpenSourceCommand,
    RemoveSourceCommand,
    RenameFolderCommand,
    UpdateSourceCommand,
)
from src.application.projects.signal_bridge import (
    FolderPayload,
    ProjectSignalBridge,
    SourceMovedPayload,
    SourcePayload,
)
from src.contexts.projects.core.entities import Folder, Source
from src.presentation.dto import FolderDTO, ProjectSummaryDTO, SourceDTO
from src.presentation.viewmodels.protocols import FileManagerController

if TYPE_CHECKING:
    from src.application.event_bus import EventBus


class FileManagerViewModel(QObject):
    """
    ViewModel for the File Manager screen.

    Responsibilities:
    - Transform domain Source entities to UI DTOs
    - Handle user actions by calling controller commands
    - React to domain events via SignalBridge
    - Provide filtering and search capabilities
    - Track selection state for bulk operations

    Follows SKILL.md pattern:
    - Queries → Direct to controller (which queries repo)
    - Commands → Controller use cases
    - Events → SignalBridge → ViewModel signals → Screen

    Signals:
        sources_changed: Emitted when source list changes (add/remove)
        source_updated: Emitted when a source is updated (payload: SourceDTO)
        source_opened: Emitted when a source is opened (payload: SourceDTO)
        folders_changed: Emitted when folder list changes (create/delete/rename)
        source_moved: Emitted when a source is moved to a folder
        summary_changed: Emitted when summary statistics change
        error_occurred: Emitted on errors (payload: str)
    """

    # Signals for UI updates
    sources_changed = Signal()  # Emitted when source list changes
    source_updated = Signal(object)  # SourceDTO
    source_opened = Signal(object)  # SourceDTO
    folders_changed = Signal()  # Emitted when folder list changes
    source_moved = Signal(object)  # SourceMovedPayload
    summary_changed = Signal()  # Emitted when summary changes
    error_occurred = Signal(str)  # Error message

    def __init__(
        self,
        controller: FileManagerController,
        event_bus: EventBus,
        signal_bridge: ProjectSignalBridge | None = None,
        parent: QObject | None = None,
    ) -> None:
        """
        Initialize the ViewModel.

        Args:
            controller: Controller implementing FileManagerController protocol
            event_bus: The event bus for reactive updates
            signal_bridge: Signal bridge for reactive updates (optional)
            parent: Qt parent object
        """
        super().__init__(parent)
        self._controller = controller
        self._event_bus = event_bus
        self._signal_bridge = signal_bridge

        # Selection state
        self._selected_source_ids: set[int] = set()
        self._current_source_id: int | None = None

        # Connect to signal bridge if provided
        if self._signal_bridge is not None:
            self._connect_signals()

    def _connect_signals(self) -> None:
        """Connect to ProjectSignalBridge signals for reactive updates."""
        if self._signal_bridge is None:
            return

        # Source events
        self._signal_bridge.source_added.connect(self._on_source_added)
        self._signal_bridge.source_removed.connect(self._on_source_removed)
        self._signal_bridge.source_renamed.connect(self._on_source_renamed)
        self._signal_bridge.source_opened.connect(self._on_source_opened)
        self._signal_bridge.source_status_changed.connect(
            self._on_source_status_changed
        )

        # Folder events
        self._signal_bridge.folder_created.connect(self._on_folder_created)
        self._signal_bridge.folder_renamed.connect(self._on_folder_renamed)
        self._signal_bridge.folder_deleted.connect(self._on_folder_deleted)
        self._signal_bridge.source_moved.connect(self._on_source_moved)

    # =========================================================================
    # Signal Bridge Handlers - React to domain events
    # =========================================================================

    def _on_source_added(self, _payload: SourcePayload) -> None:
        """Handle source added event."""
        self.sources_changed.emit()
        self.summary_changed.emit()

    def _on_source_removed(self, payload: SourcePayload) -> None:
        """Handle source removed event."""
        # Clear selection if deleted source was selected
        self._selected_source_ids.discard(payload.source_id)
        if self._current_source_id == payload.source_id:
            self._current_source_id = None
        self.sources_changed.emit()
        self.summary_changed.emit()

    def _on_source_renamed(self, payload: SourcePayload) -> None:
        """Handle source renamed event."""
        source_dto = self.get_source(payload.source_id)
        if source_dto:
            self.source_updated.emit(source_dto)

    def _on_source_opened(self, payload: SourcePayload) -> None:
        """Handle source opened event."""
        self._current_source_id = payload.source_id
        source_dto = self.get_source(payload.source_id)
        if source_dto:
            self.source_opened.emit(source_dto)

    def _on_source_status_changed(self, payload: SourcePayload) -> None:
        """Handle source status changed event."""
        source_dto = self.get_source(payload.source_id)
        if source_dto:
            self.source_updated.emit(source_dto)
        self.summary_changed.emit()

    def _on_folder_created(self, _payload: FolderPayload) -> None:
        """Handle folder created event."""
        self.folders_changed.emit()

    def _on_folder_renamed(self, _payload: FolderPayload) -> None:
        """Handle folder renamed event."""
        self.folders_changed.emit()

    def _on_folder_deleted(self, _payload: FolderPayload) -> None:
        """Handle folder deleted event."""
        self.folders_changed.emit()

    def _on_source_moved(self, payload: SourceMovedPayload) -> None:
        """Handle source moved to folder event."""
        self.source_moved.emit(payload)
        self.folders_changed.emit()  # Folder source counts changed

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

    def get_source(self, source_id: int) -> SourceDTO | None:
        """
        Get a specific source by ID.

        Args:
            source_id: ID of the source to retrieve

        Returns:
            SourceDTO if found, None otherwise
        """
        source = self._controller.get_source(source_id)
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

        return result.is_success

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

        if result.is_success:
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

    def get_segment_count_for_source(self, source_id: int) -> int:
        """
        Get the count of coded segments for a source.

        Use this before deleting a source to warn users if coded data exists.

        Args:
            source_id: ID of source to check

        Returns:
            Number of coded segments for this source
        """
        return self._controller.get_segment_count_for_source(source_id)

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

        if result.is_success:
            self._current_source_id = source_id
            return True

        return False

    def update_source(
        self,
        source_id: int,
        memo: str | None = None,
        origin: str | None = None,
        status: str | None = None,
    ) -> bool:
        """
        Update source properties.

        Args:
            source_id: ID of source to update
            memo: Optional memo text
            origin: Optional origin/category
            status: Optional status

        Returns:
            True if successful, False otherwise
        """
        command = UpdateSourceCommand(
            source_id=source_id,
            memo=memo,
            origin=origin,
            status=status,
        )

        result = self._controller.update_source(command)

        return result.is_success

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
    # Folder Commands
    # =========================================================================

    def create_folder(self, name: str, parent_id: int | None = None) -> bool:
        """
        Create a new folder.

        Args:
            name: Name of the folder to create
            parent_id: Optional parent folder ID for nested folders

        Returns:
            True if successful, False otherwise
        """
        command = CreateFolderCommand(name=name, parent_id=parent_id)
        result = self._controller.create_folder(command)

        return result.is_success

    def rename_folder(self, folder_id: int, new_name: str) -> bool:
        """
        Rename a folder.

        Args:
            folder_id: ID of the folder to rename
            new_name: New name for the folder

        Returns:
            True if successful, False otherwise
        """
        command = RenameFolderCommand(folder_id=folder_id, new_name=new_name)
        result = self._controller.rename_folder(command)

        return result.is_success

    def delete_folder(self, folder_id: int) -> bool:
        """
        Delete an empty folder.

        Args:
            folder_id: ID of the folder to delete

        Returns:
            True if successful, False otherwise
        """
        command = DeleteFolderCommand(folder_id=folder_id)
        result = self._controller.delete_folder(command)

        return result.is_success

    def move_source_to_folder(self, source_id: int, folder_id: int | None) -> bool:
        """
        Move a source to a folder (or root if None).

        Args:
            source_id: ID of the source to move
            folder_id: Target folder ID, or None to move to root

        Returns:
            True if successful, False otherwise
        """
        command = MoveSourceToFolderCommand(source_id=source_id, folder_id=folder_id)
        result = self._controller.move_source_to_folder(command)

        return result.is_success

    def get_folders(self) -> list[FolderDTO]:
        """
        Get all folders as DTOs.

        Returns:
            List of FolderDTO objects for UI display
        """
        folders = self._controller.get_folders()
        return [self._folder_to_dto(f) for f in folders]

    # =========================================================================
    # Private Helpers
    # =========================================================================

    def _source_to_dto(self, source: Source) -> SourceDTO:
        """Convert a Source entity to DTO."""
        # Find all cases that contain this source
        source_id_value = source.id.value
        case_names = [
            case.name
            for case in self._controller.get_cases()
            if source_id_value in case.source_ids
        ]

        return SourceDTO(
            id=str(source.id.value),
            name=source.name,
            source_type=source.source_type.value,
            status=source.status.value,
            file_size=source.file_size,
            code_count=source.code_count,
            memo=source.memo,
            origin=source.origin,
            cases=case_names,
            modified_at=source.modified_at.isoformat() if source.modified_at else None,
        )

    def _folder_to_dto(self, folder: Folder) -> FolderDTO:
        """Convert a Folder entity to DTO."""
        # Count sources in this folder
        sources = self._controller.get_sources()
        source_count = sum(
            1 for s in sources if s.folder_id and s.folder_id.value == folder.id.value
        )

        return FolderDTO(
            id=str(folder.id.value),
            name=folder.name,
            parent_id=str(folder.parent_id.value) if folder.parent_id else None,
            source_count=source_count,
        )
