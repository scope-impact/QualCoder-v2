"""
QualCoder v2 - Main Application Entry Point

Run with: uv run python -m src.main
"""

from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication, QMessageBox

from design_system import get_colors
from src.contexts.cases.presentation import CaseManagerScreen

# Context-specific presentation imports
from src.contexts.coding.presentation import TextCodingScreen
from src.contexts.projects.presentation import ProjectScreen
from src.contexts.sources.presentation import FileManagerScreen, FileManagerViewModel
from src.shared.infra.app_context import create_app_context
from src.shared.infra.signal_bridge.projects import ProjectSignalBridge
from src.shared.presentation import create_empty_text_coding_data

# Shared presentation imports
from src.shared.presentation.services import DialogService
from src.shared.presentation.templates import AppShell


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
        self._ctx = create_app_context()
        self._dialog_service = DialogService(self._ctx)
        # Create signal bridge for reactive UI updates
        self._project_signal_bridge = ProjectSignalBridge.instance(self._ctx.event_bus)
        self._project_signal_bridge.start()
        self._shell: AppShell | None = None
        self._screens: dict = {}
        self._current_project_path: Path | None = None

    def _setup_shell(self):
        """Create and configure the main application shell."""
        self._shell = AppShell(colors=self._colors)

        # Load and apply saved settings at startup BEFORE setting screens
        # (apply_theme calls _refresh_ui which rebuilds the UI)
        self._shell.load_and_apply_settings(self._ctx.settings_repo)

        # Create screens (viewmodels are wired when a project is opened)
        self._screens = {
            "project": ProjectScreen(
                colors=self._colors,
                on_open=self._on_open_project,
                on_create=self._on_create_project,
            ),
            "files": FileManagerScreen(
                viewmodel=None,  # Set when project opens
                colors=self._colors,
            ),
            "cases": CaseManagerScreen(colors=self._colors),
            "coding": TextCodingScreen(
                data=create_empty_text_coding_data(),
                colors=self._colors,
            ),
        }

        # Set initial screen (project selection)
        self._shell.set_screen(self._screens["project"])
        self._shell.set_active_menu("project")

        # Connect navigation
        self._shell.menu_clicked.connect(self._on_menu_click)
        self._shell.tab_clicked.connect(self._on_tab_click)

        # Connect settings button to open dialog with live updates
        self._shell.settings_clicked.connect(self._on_settings_clicked)

        # Connect file manager navigation to coding screen
        self._screens["files"].navigate_to_coding.connect(self._on_navigate_to_coding)

        # Connect text coding screen to receive navigation events (direct signal wiring)
        if self._project_signal_bridge is not None:
            self._project_signal_bridge.navigated_to_segment.connect(
                self._screens["coding"].on_navigated_to_segment
            )

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

    def _on_settings_clicked(self):
        """Handle settings button click with live UI updates."""
        dialog = self._dialog_service.show_settings_dialog(
            parent=self._shell,
            colors=self._shell._colors,
        )
        # Live UI updates: re-apply theme/font after dialog closes
        if dialog:
            self._shell.load_and_apply_settings(self._ctx.settings_repo)

    def _wire_viewmodels(self):
        """Wire viewmodels to screens after a project is opened."""
        # Create FileManagerViewModel now that contexts are available
        file_manager_viewmodel = FileManagerViewModel(
            source_repo=self._ctx.sources_context.source_repo,
            folder_repo=self._ctx.sources_context.folder_repo,
            case_repo=self._ctx.cases_context.case_repo,
            state=self._ctx.state,
            event_bus=self._ctx.event_bus,
            _sources_ctx=self._ctx.sources_context,
            _coding_ctx=self._ctx.coding_context,
            segment_repo=(
                self._ctx.coding_context.segment_repo
                if self._ctx.coding_context
                else None
            ),
            signal_bridge=self._project_signal_bridge,
        )
        self._screens["files"].set_viewmodel(file_manager_viewmodel)

    def _on_open_project(self):
        """Handle open project request."""
        result = self._dialog_service.show_open_project_dialog(parent=self._shell)
        # Check success (OperationResult has .is_success, Failure doesn't)
        if getattr(result, "is_success", False):
            # Project opened successfully - wire viewmodels and switch to files view
            self._wire_viewmodels()
            self._screens["files"].refresh()
            self._shell.set_screen(self._screens["files"])
            self._shell.set_active_menu("files")
        elif hasattr(result, "error") and result.error:
            # Show error message (but not for "Dialog cancelled")
            QMessageBox.warning(
                self._shell,
                "Open Project Failed",
                result.error,
            )

    def _on_create_project(self):
        """Handle create project request."""
        result = self._dialog_service.show_create_project_dialog(parent=self._shell)
        # Check success (OperationResult has .is_success, Failure doesn't)
        if getattr(result, "is_success", False):
            # Project created - now open it to initialize bounded contexts
            project = result.unwrap()
            open_result = self._ctx.open_project(str(project.path))
            if open_result.is_success:
                # Wire viewmodels and switch to files view
                self._wire_viewmodels()
                self._screens["files"].refresh()
                self._shell.set_screen(self._screens["files"])
                self._shell.set_active_menu("files")
            else:
                # Project created but failed to open
                QMessageBox.warning(
                    self._shell,
                    "Open Project Failed",
                    open_result.error or "Failed to open the newly created project.",
                )
        elif hasattr(result, "error") and result.error:
            # Show error message (but not for "Dialog cancelled")
            QMessageBox.warning(
                self._shell,
                "Create Project Failed",
                result.error,
            )

    def _on_navigate_to_coding(self, source_id: str):
        """Handle navigation to coding screen with a specific source."""
        # Get the source from repo (source of truth)
        try:
            source_id_int = int(source_id)
            from src.shared.common.types import SourceId

            sources_ctx = self._ctx.sources_context
            if sources_ctx:
                source = sources_ctx.source_repo.get_by_id(
                    SourceId(value=source_id_int)
                )
                if source and source.fulltext:
                    # Load the source content into the coding screen
                    self._screens["coding"].set_document(
                        title=source.name,
                        badge=source.source_type.value,
                        text=source.fulltext,
                    )
                    self._screens["coding"].set_current_source(source_id_int)
        except (ValueError, TypeError):
            pass  # Invalid source_id, just show the screen

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
