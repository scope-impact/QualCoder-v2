"""
QualCoder v2 - Main Application Entry Point

Run with: uv run python -m src.main
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import TYPE_CHECKING

from PySide6.QtWidgets import QApplication
from returns.result import Result

from design_system import get_colors
from src.application.app_context import AppContext, get_app_context
from src.application.navigation.service import NavigationService
from src.contexts.projects.core.entities import ProjectSummary, SourceType
from src.contexts.shared.core.types import SourceId
from src.presentation.screens import (
    CaseManagerScreen,
    FileManagerScreen,
    ProjectScreen,
    TextCodingScreen,
)
from src.presentation.services import DialogService
from src.presentation.templates.app_shell import AppShell
from src.presentation.viewmodels import FileManagerViewModel

if TYPE_CHECKING:
    from src.application.event_bus import EventBus
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
    from src.contexts.projects.core.entities import Folder, Source


class CoordinatorAdapter:
    """
    Adapter implementing FileManagerController protocol.

    Provides the interface that FileManagerViewModel expects by calling
    use cases directly. This replaces the sub-coordinator pattern.
    """

    def __init__(self, ctx: AppContext) -> None:
        """Initialize adapter with AppContext."""
        self._ctx = ctx

    @property
    def event_bus(self) -> EventBus:
        """Get event bus."""
        return self._ctx.event_bus

    # =========================================================================
    # Source Operations (implements FileManagerController protocol)
    # =========================================================================

    def get_sources(self) -> list[Source]:
        """Get all sources in the current project."""
        return list(self._ctx.state.sources)

    def get_source(self, source_id: int) -> Source | None:
        """Get a specific source by ID."""
        return self._ctx.state.get_source(source_id)

    def add_source(self, command: AddSourceCommand) -> Result:
        """Add a source file to the current project."""
        from src.application.sources.usecases import add_source

        return add_source(
            command=command,
            state=self._ctx.state,
            sources_ctx=self._ctx.sources_context,
            event_bus=self._ctx.event_bus,
        )

    def remove_source(self, command: RemoveSourceCommand) -> Result:
        """Remove a source from the current project."""
        from src.application.sources.usecases import remove_source

        return remove_source(
            command=command,
            state=self._ctx.state,
            sources_ctx=self._ctx.sources_context,
            coding_ctx=self._ctx.coding_context,
            event_bus=self._ctx.event_bus,
        )

    def open_source(self, command: OpenSourceCommand) -> Result:
        """Open a source for viewing/coding."""
        from src.application.sources.usecases import open_source

        return open_source(
            command=command,
            state=self._ctx.state,
            event_bus=self._ctx.event_bus,
        )

    def update_source(self, command: UpdateSourceCommand) -> Result:
        """Update source metadata."""
        from src.application.sources.usecases import update_source

        return update_source(
            command=command,
            state=self._ctx.state,
            sources_ctx=self._ctx.sources_context,
            event_bus=self._ctx.event_bus,
        )

    def get_segment_count_for_source(self, source_id: int) -> int:
        """Get the count of coded segments for a source."""
        coding_ctx = self._ctx.coding_context
        if coding_ctx is None or coding_ctx.segment_repo is None:
            return 0

        sid = SourceId(value=source_id)
        return coding_ctx.segment_repo.count_by_source(sid)

    # =========================================================================
    # Folder Operations
    # =========================================================================

    def get_folders(self) -> list[Folder]:
        """Get all folders in the current project."""
        return list(self._ctx.state.folders)

    def create_folder(self, command: CreateFolderCommand) -> Result:
        """Create a new folder."""
        from src.application.folders.usecases import create_folder

        return create_folder(
            command=command,
            state=self._ctx.state,
            sources_ctx=self._ctx.sources_context,
            event_bus=self._ctx.event_bus,
        )

    def rename_folder(self, command: RenameFolderCommand) -> Result:
        """Rename a folder."""
        from src.application.folders.usecases import rename_folder

        return rename_folder(
            command=command,
            state=self._ctx.state,
            sources_ctx=self._ctx.sources_context,
            event_bus=self._ctx.event_bus,
        )

    def delete_folder(self, command: DeleteFolderCommand) -> Result:
        """Delete an empty folder."""
        from src.application.folders.usecases import delete_folder

        return delete_folder(
            command=command,
            state=self._ctx.state,
            sources_ctx=self._ctx.sources_context,
            event_bus=self._ctx.event_bus,
        )

    def move_source_to_folder(self, command: MoveSourceToFolderCommand) -> Result:
        """Move a source to a folder."""
        from src.application.folders.usecases import move_source_to_folder

        return move_source_to_folder(
            command=command,
            state=self._ctx.state,
            sources_ctx=self._ctx.sources_context,
            event_bus=self._ctx.event_bus,
        )

    # =========================================================================
    # Case Operations
    # =========================================================================

    def get_cases(self) -> list[Case]:
        """Get all cases in the current project."""
        return list(self._ctx.state.cases)

    def create_case(self, command) -> Result:
        """Create a new case in the current project."""
        from src.application.cases.usecases import create_case

        return create_case(
            command=command,
            state=self._ctx.state,
            cases_ctx=self._ctx.cases_context,
            event_bus=self._ctx.event_bus,
        )

    def link_source_to_case(self, command) -> Result:
        """Link a source to a case."""
        from src.application.cases.usecases import link_source_to_case

        return link_source_to_case(
            command=command,
            state=self._ctx.state,
            cases_ctx=self._ctx.cases_context,
            event_bus=self._ctx.event_bus,
        )

    @property
    def coding_context(self):
        """Get coding context (for tests that need segment access)."""
        return self._ctx.coding_context

    # =========================================================================
    # Project Operations
    # =========================================================================

    def get_project_summary(self) -> ProjectSummary | None:
        """Get summary statistics for the current project."""
        if self._ctx.state.project is None:
            return None

        return ProjectSummary(
            total_sources=len(self._ctx.state.sources),
            text_count=sum(
                1 for s in self._ctx.state.sources if s.source_type == SourceType.TEXT
            ),
            audio_count=sum(
                1 for s in self._ctx.state.sources if s.source_type == SourceType.AUDIO
            ),
            video_count=sum(
                1 for s in self._ctx.state.sources if s.source_type == SourceType.VIDEO
            ),
            image_count=sum(
                1 for s in self._ctx.state.sources if s.source_type == SourceType.IMAGE
            ),
            pdf_count=sum(
                1 for s in self._ctx.state.sources if s.source_type == SourceType.PDF
            ),
            total_codes=0,  # Would come from coding context
            total_segments=0,
        )


class QualCoderApp:
    """
    Main application class.

    Wires together all layers:
    - Infrastructure (repositories, database)
    - Application (controllers, event bus)
    - Presentation (screens, viewmodels)
    """

    def __init__(self):
        self._app = QApplication(sys.argv)
        self._colors = get_colors()
        self._ctx = get_app_context()
        self._dialog_service = DialogService(self._ctx)
        self._navigation_service = NavigationService(self._ctx)
        # Adapter provides coordinator-like interface for ViewModels
        self._coordinator_adapter = CoordinatorAdapter(self._ctx)
        self._shell: AppShell | None = None
        self._screens: dict = {}
        self._current_project_path: Path | None = None

    def _setup_shell(self):
        """Create and configure the main application shell."""
        self._shell = AppShell(colors=self._colors)

        # Create ViewModels
        # CoordinatorAdapter provides the sources/folders/cases/projects interface
        self._file_manager_viewmodel = FileManagerViewModel(
            controller=self._coordinator_adapter,
            event_bus=self._ctx.event_bus,
        )

        # Create screens
        self._screens = {
            "project": ProjectScreen(
                colors=self._colors,
                on_open=self._on_open_project,
                on_create=self._on_create_project,
            ),
            "files": FileManagerScreen(
                viewmodel=self._file_manager_viewmodel,
                colors=self._colors,
            ),
            "cases": CaseManagerScreen(colors=self._colors),
            "coding": TextCodingScreen(colors=self._colors),
        }

        # Set initial screen (project selection)
        self._shell.set_screen(self._screens["project"])
        self._shell.set_active_menu("project")

        # Connect navigation
        self._shell.menu_clicked.connect(self._on_menu_click)
        self._shell.tab_clicked.connect(self._on_tab_click)

        # Connect settings button
        self._shell.settings_clicked.connect(
            lambda: self._dialog_service.show_settings_dialog(
                parent=self._shell, colors=self._colors
            )
        )

        # Connect file manager navigation to coding screen
        self._screens["files"].navigate_to_coding.connect(self._on_navigate_to_coding)

        # Connect text coding screen to receive navigation events
        self._navigation_service.connect_text_coding_screen(self._screens["coding"])

    def _on_menu_click(self, menu_id: str):
        """Handle menu item clicks."""
        if menu_id in self._screens:
            self._shell.set_screen(self._screens[menu_id])
            self._shell.set_active_menu(menu_id)

    def _on_tab_click(self, tab_id: str):
        """Handle tab clicks."""
        tab_to_menu = {
            "coding": "coding",
            "reports": "reports",
            "manage": "files",
            "action_log": "project",
        }
        menu_id = tab_to_menu.get(tab_id, tab_id)
        if menu_id in self._screens:
            self._shell.set_screen(self._screens[menu_id])
            self._shell.set_active_tab(tab_id)

    def _on_open_project(self):
        """Handle open project request."""
        result = self._dialog_service.show_open_project_dialog(parent=self._shell)
        if result:
            # Project opened successfully - refresh file manager and switch to files view
            self._screens["files"].refresh()
            self._shell.set_screen(self._screens["files"])
            self._shell.set_active_menu("files")

    def _on_create_project(self):
        """Handle create project request."""
        result = self._dialog_service.show_create_project_dialog(parent=self._shell)
        if result:
            # Project created successfully - refresh file manager and switch to files view
            self._screens["files"].refresh()
            self._shell.set_screen(self._screens["files"])
            self._shell.set_active_menu("files")

    def _on_navigate_to_coding(self, _source_id: str):
        """Handle navigation to coding screen with a specific source."""
        self._shell.set_screen(self._screens["coding"])
        self._shell.set_active_menu("coding")

    def run(self) -> int:
        """Run the application."""
        self._ctx.start()
        self._setup_shell()
        self._shell.show()

        exit_code = self._app.exec()

        self._ctx.stop()
        return exit_code


def main():
    """Application entry point."""
    app = QualCoderApp()
    sys.exit(app.run())


if __name__ == "__main__":
    main()
