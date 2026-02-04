"""
QualCoder v2 - Main Application Entry Point

Run with: uv run python -m src.main
"""

from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication, QMessageBox

from design_system import get_colors
from src.contexts.cases.presentation import CaseManagerScreen

# Context-specific presentation imports
from src.contexts.coding.interface.signal_bridge import CodingSignalBridge
from src.contexts.coding.presentation import (
    CodingCoordinator,
    TextCodingScreen,
    TextCodingViewModel,
)
from src.contexts.coding.presentation.dialogs import CreateCodeDialog
from src.contexts.projects.presentation import ProjectScreen
from src.contexts.sources.presentation import FileManagerScreen, FileManagerViewModel
from src.shared.common.types import SourceId
from src.shared.infra.app_context import create_app_context
from src.shared.infra.mcp_server import MCPServerManager
from src.shared.infra.signal_bridge.projects import ProjectSignalBridge
from src.shared.infra.telemetry import init_telemetry
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
        # Initialize telemetry for performance monitoring (logs to file in dev mode)
        init_telemetry(service_name="qualcoder")

        self._app = QApplication(sys.argv)
        self._colors = get_colors()
        self._ctx = create_app_context()
        self._dialog_service = DialogService(self._ctx)
        # Create signal bridges for reactive UI updates
        self._project_signal_bridge = ProjectSignalBridge.instance(self._ctx.event_bus)
        self._project_signal_bridge.start()
        self._coding_signal_bridge = CodingSignalBridge.instance(self._ctx.event_bus)
        self._coding_signal_bridge.start()
        # Start embedded MCP server for AI agent access
        self._mcp_server = MCPServerManager(ctx=self._ctx)
        self._mcp_server.start()
        self._shell: AppShell | None = None
        self._screens: dict = {}

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
            segment_repo=(
                self._ctx.coding_context.segment_repo
                if self._ctx.coding_context
                else None
            ),
            signal_bridge=self._project_signal_bridge,
        )
        self._screens["files"].set_viewmodel(file_manager_viewmodel)

        # Create TextCodingViewModel with CodingCoordinator
        if self._ctx.coding_context:
            coding_coordinator = CodingCoordinator(
                code_repo=self._ctx.coding_context.code_repo,
                category_repo=self._ctx.coding_context.category_repo,
                segment_repo=self._ctx.coding_context.segment_repo,
                event_bus=self._ctx.event_bus,
            )
            text_coding_viewmodel = TextCodingViewModel(
                controller=coding_coordinator,
                signal_bridge=self._coding_signal_bridge,
            )
            self._screens["coding"].set_viewmodel(text_coding_viewmodel)

            # Connect "N" key (new code) to show CreateCodeDialog
            self._screens["coding"].code_created.connect(
                lambda _: self._on_show_create_code_dialog(text_coding_viewmodel)
            )

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

    def _on_show_create_code_dialog(self, viewmodel: TextCodingViewModel):
        """Show CreateCodeDialog and wire it to the viewmodel."""
        dialog = CreateCodeDialog(colors=self._colors, parent=self._shell)

        def on_code_created(name: str, color: str, _memo: str):
            """Handle code creation from dialog."""
            success = viewmodel.create_code(name=name, color=color)
            if success:
                dialog.accept()  # Close dialog on success

        dialog.code_created.connect(on_code_created)
        dialog.show()

    def _on_navigate_to_coding(self, source_id: str):
        """Handle navigation to coding screen with a specific source."""
        try:
            source_id_int = int(source_id)
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

    def _cleanup(self):
        """Clean up resources on app exit."""
        self._mcp_server.stop()
        self._ctx.stop()

    def run(self) -> int:
        """Run the application."""
        self._ctx.start()
        self._setup_shell()
        self._shell.show()

        # Ensure cleanup happens regardless of how app closes
        self._app.aboutToQuit.connect(self._cleanup)

        return self._app.exec()


def main():
    """Application entry point."""
    app = QualCoderApp()
    sys.exit(app.run())


if __name__ == "__main__":
    main()
