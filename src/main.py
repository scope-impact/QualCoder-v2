"""
QualCoder v2 - Main Application Entry Point

Run with: uv run python -m src.main
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import TYPE_CHECKING

from PySide6.QtWidgets import QApplication

from design_system import get_colors
from src.application.app_context import AppContext, get_app_context
from src.application.coordinators import (
    CasesCoordinator,
    CoordinatorInfrastructure,
    FoldersCoordinator,
    ProjectsCoordinator,
    SourcesCoordinator,
)
from src.application.navigation.service import NavigationService
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


class CoordinatorAdapter:
    """
    Adapter that provides coordinator-like interface from AppContext.

    This adapter wraps AppContext and provides access to sub-coordinators
    (sources, folders, cases, projects) that some ViewModels expect.
    The sub-coordinators share AppContext's infrastructure.

    This is a temporary migration pattern - eventually ViewModels should
    use use cases directly or through dedicated services.
    """

    def __init__(self, ctx: AppContext) -> None:
        """Initialize adapter with AppContext."""
        self._ctx = ctx

        # Create infrastructure that references AppContext's components
        # Note: The contexts are properties that will be evaluated when accessed
        self._infra = CoordinatorInfrastructure(
            event_bus=ctx.event_bus,
            state=ctx.state,
            lifecycle=ctx.lifecycle,
            settings_repo=ctx.settings_repo,
            signal_bridge=ctx.signal_bridge,
        )

        # Create sub-coordinators using shared infrastructure
        self._sources = SourcesCoordinator(self._infra)
        self._folders = FoldersCoordinator(self._infra)
        self._cases = CasesCoordinator(self._infra)
        self._projects = ProjectsCoordinator(self._infra)

    def _sync_contexts(self) -> None:
        """Sync bounded contexts from AppContext to infrastructure."""
        self._infra.sources_context = self._ctx.sources_context
        self._infra.cases_context = self._ctx.cases_context
        self._infra.coding_context = self._ctx.coding_context
        self._infra.projects_context = self._ctx.projects_context

    @property
    def sources(self) -> SourcesCoordinator:
        """Get sources coordinator."""
        self._sync_contexts()
        return self._sources

    @property
    def folders(self) -> FoldersCoordinator:
        """Get folders coordinator."""
        self._sync_contexts()
        return self._folders

    @property
    def cases(self) -> CasesCoordinator:
        """Get cases coordinator."""
        self._sync_contexts()
        return self._cases

    @property
    def projects(self) -> ProjectsCoordinator:
        """Get projects coordinator."""
        self._sync_contexts()
        return self._projects

    @property
    def event_bus(self) -> EventBus:
        """Get event bus."""
        return self._ctx.event_bus


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
