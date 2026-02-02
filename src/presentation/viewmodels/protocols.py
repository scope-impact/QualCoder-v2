"""
ViewModel Protocols

Defines the interfaces that ViewModels expect from their controllers.
This allows ViewModels to be decoupled from specific implementations.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

from returns.result import Result

if TYPE_CHECKING:
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
    from src.contexts.cases.core.entities import Case
    from src.contexts.projects.core.entities import Folder, ProjectSummary, Source


class FileManagerController(Protocol):
    """
    Protocol for FileManagerViewModel's controller.

    Defines the exact interface that FileManagerViewModel needs.
    This can be implemented by CoordinatorAdapter, mock objects for testing,
    or any other class that provides these methods.
    """

    # =========================================================================
    # Source Operations
    # =========================================================================

    def get_sources(self) -> list[Source]:
        """Get all sources in the current project."""
        ...

    def get_source(self, source_id: int) -> Source | None:
        """Get a specific source by ID."""
        ...

    def add_source(self, command: AddSourceCommand) -> Result:
        """Add a source file to the current project."""
        ...

    def remove_source(self, command: RemoveSourceCommand) -> Result:
        """Remove a source from the current project."""
        ...

    def open_source(self, command: OpenSourceCommand) -> Result:
        """Open a source for viewing/coding."""
        ...

    def update_source(self, command: UpdateSourceCommand) -> Result:
        """Update source metadata."""
        ...

    def get_segment_count_for_source(self, source_id: int) -> int:
        """Get the count of coded segments for a source."""
        ...

    # =========================================================================
    # Folder Operations
    # =========================================================================

    def get_folders(self) -> list[Folder]:
        """Get all folders in the current project."""
        ...

    def create_folder(self, command: CreateFolderCommand) -> Result:
        """Create a new folder."""
        ...

    def rename_folder(self, command: RenameFolderCommand) -> Result:
        """Rename a folder."""
        ...

    def delete_folder(self, command: DeleteFolderCommand) -> Result:
        """Delete an empty folder."""
        ...

    def move_source_to_folder(self, command: MoveSourceToFolderCommand) -> Result:
        """Move a source to a folder."""
        ...

    # =========================================================================
    # Case Operations
    # =========================================================================

    def get_cases(self) -> list[Case]:
        """Get all cases in the current project."""
        ...

    # =========================================================================
    # Project Operations
    # =========================================================================

    def get_project_summary(self) -> ProjectSummary | None:
        """Get summary statistics for the current project."""
        ...
