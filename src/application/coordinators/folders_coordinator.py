"""
Folders Coordinator - Folder Management.

Handles all folder-related CRUD operations.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from returns.result import Result

from src.application.coordinators.base import BaseCoordinator

if TYPE_CHECKING:
    from src.contexts.projects.core.entities import Folder


class FoldersCoordinator(BaseCoordinator):
    """
    Coordinator for folder operations.

    Manages:
    - Creating folders
    - Renaming folders
    - Deleting folders
    - Moving sources to folders
    - Folder queries

    Requires an open project for all operations.
    """

    # =========================================================================
    # Folder Commands
    # =========================================================================

    def create_folder(self, command) -> Result:
        """Create a new folder."""
        from src.application.folders.usecases import create_folder

        return create_folder(
            command=command,
            state=self.state,
            sources_ctx=self.sources_context,
            event_bus=self.event_bus,
        )

    def rename_folder(self, command) -> Result:
        """Rename a folder."""
        from src.application.folders.usecases import rename_folder

        return rename_folder(
            command=command,
            state=self.state,
            sources_ctx=self.sources_context,
            event_bus=self.event_bus,
        )

    def delete_folder(self, command) -> Result:
        """Delete an empty folder."""
        from src.application.folders.usecases import delete_folder

        return delete_folder(
            command=command,
            state=self.state,
            sources_ctx=self.sources_context,
            event_bus=self.event_bus,
        )

    def move_source_to_folder(self, command) -> Result:
        """Move a source to a folder."""
        from src.application.folders.usecases import move_source_to_folder

        return move_source_to_folder(
            command=command,
            state=self.state,
            sources_ctx=self.sources_context,
            event_bus=self.event_bus,
        )

    # =========================================================================
    # Folder Queries
    # =========================================================================

    def get_folders(self) -> list[Folder]:
        """Get all folders in the current project."""
        return list(self.state.folders)
