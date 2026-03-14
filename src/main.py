"""
QualCoder v2 - Main Application Entry Point

Run with: uv run python -m src.main
"""

from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

import qasync
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
from src.contexts.projects.presentation import (
    ProjectScreen,
    VersionControlViewModel,
    VersionHistoryScreen,
)
from src.contexts.sources.presentation import FileManagerScreen, FileManagerViewModel
from src.contexts.storage.interface.signal_bridge import StorageSignalBridge
from src.contexts.storage.presentation.viewmodels.data_store_viewmodel import (
    DataStoreViewModel,
)
from src.shared.common.types import SourceId
from src.shared.infra.app_context import create_app_context
from src.shared.infra.logging_config import configure_logging
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
        # Load saved observability settings for logging configuration
        from src.contexts.settings.infra.user_settings_repository import (
            UserSettingsRepository,
        )

        _boot_repo = UserSettingsRepository()
        _obs = _boot_repo.load().observability

        # Dev mode overrides saved level; env var overrides everything (inside configure_logging)
        _log_level = "DEBUG" if os.environ.get("QUALCODER_DEV") else _obs.log_level
        _log_file = (
            Path.home() / ".qualcoder" / "qualcoder.log"
            if _obs.enable_file_logging
            else None
        )
        configure_logging(level=_log_level, log_file=_log_file)

        # Initialize telemetry for performance monitoring (logs to file in dev mode)
        init_telemetry(service_name="qualcoder")

        self._app = QApplication(sys.argv)
        self._colors = get_colors()
        self._ctx = create_app_context(settings_repo=_boot_repo)
        self._dialog_service = DialogService(self._ctx)
        # Create signal bridges for reactive UI updates
        self._project_signal_bridge = ProjectSignalBridge.instance(self._ctx.event_bus)
        self._project_signal_bridge.start()
        self._coding_signal_bridge = CodingSignalBridge.instance(self._ctx.event_bus)
        self._coding_signal_bridge.start()
        self._storage_signal_bridge = StorageSignalBridge.instance(self._ctx.event_bus)
        self._storage_signal_bridge.start()
        # MCP server — started as asyncio task in run() on the unified loop
        self._mcp_server = MCPServerManager(ctx=self._ctx)
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
            "history": VersionHistoryScreen(colors=self._colors),
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
        if menu_id in self._screens and self._shell is not None:
            self._shell.set_screen(self._screens[menu_id])
            self._shell.set_active_menu(menu_id)

    def _on_settings_clicked(self):
        """Handle settings button click with live UI updates."""
        dialog = self._dialog_service.show_settings_dialog(
            parent=self._shell,
            colors=self._shell._colors,
            data_store_vm=getattr(self, "_data_store_vm", None),
        )
        # Live UI updates: re-apply theme/font after dialog closes
        if dialog:
            self._shell.load_and_apply_settings(self._ctx.settings_repo)

    def _wire_policy_repositories(self):
        """Wire repository references for policies now that contexts are available."""
        from src.contexts.coding.core.policies import (
            set_repositories as set_coding_repos,
        )
        from src.contexts.sources.core.policies import (
            set_repositories as set_sources_repos,
        )

        if self._ctx.coding_context:
            set_coding_repos(
                code_repo=self._ctx.coding_context.code_repo,
                segment_repo=self._ctx.coding_context.segment_repo,
            )
        if self._ctx.sources_context:
            set_sources_repos(
                source_repo=self._ctx.sources_context.source_repo,
            )

    def _wire_viewmodels(self):
        """Wire viewmodels to screens after a project is opened."""
        # Wire policy repositories now that contexts are available
        self._wire_policy_repositories()

        # Create FileManagerViewModel now that contexts are available
        file_manager_viewmodel = FileManagerViewModel(
            source_repo=self._ctx.sources_context.source_repo,
            folder_repo=self._ctx.folders_context.folder_repo,
            case_repo=self._ctx.cases_context.case_repo,
            state=self._ctx.state,
            event_bus=self._ctx.event_bus,
            segment_repo=(
                self._ctx.coding_context.segment_repo
                if self._ctx.coding_context
                else None
            ),
            signal_bridge=self._project_signal_bridge,
            session=self._ctx.session,
        )
        self._screens["files"].set_viewmodel(file_manager_viewmodel)

        # Create ExchangeCoordinator + ViewModel for import/export in FileManager
        from src.contexts.exchange.presentation.coordinator import ExchangeCoordinator
        from src.contexts.exchange.presentation.viewmodels.exchange_viewmodel import (
            ExchangeViewModel,
        )

        exchange_coordinator = ExchangeCoordinator(
            code_repo=self._ctx.coding_context.code_repo
            if self._ctx.coding_context
            else None,
            category_repo=self._ctx.coding_context.category_repo
            if self._ctx.coding_context
            else None,
            segment_repo=self._ctx.coding_context.segment_repo
            if self._ctx.coding_context
            else None,
            source_repo=self._ctx.sources_context.source_repo,
            case_repo=self._ctx.cases_context.case_repo,
            event_bus=self._ctx.event_bus,
            session=self._ctx.session,
        )
        exchange_viewmodel = ExchangeViewModel(coordinator=exchange_coordinator)
        self._screens["files"].set_exchange_viewmodel(exchange_viewmodel)

        # Create DataStoreViewModel for S3 import/push
        if self._ctx.storage_context:
            data_store_vm = DataStoreViewModel(
                store_repo=self._ctx.storage_context.store_repo,
                source_repo=self._ctx.sources_context.source_repo,
                s3_scanner=self._ctx.storage_context.s3_scanner,
                dvc_gateway=self._ctx.storage_context.dvc_gateway,
                event_bus=self._ctx.event_bus,
                state=self._ctx.state,
                session=self._ctx.session,
            )
            self._screens["files"].set_data_store_viewmodel(data_store_vm)
            self._data_store_vm = data_store_vm

        # Create TextCodingViewModel with CodingCoordinator
        if self._ctx.coding_context:
            coding_coordinator = CodingCoordinator(
                code_repo=self._ctx.coding_context.code_repo,
                category_repo=self._ctx.coding_context.category_repo,
                segment_repo=self._ctx.coding_context.segment_repo,
                event_bus=self._ctx.event_bus,
                session=self._ctx.session,
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

        # Create VersionControlViewModel for history screen
        if self._ctx.projects_context and self._ctx.state.project:
            projects_ctx = self._ctx.projects_context
            if projects_ctx.git_adapter and projects_ctx.diffable_adapter:
                vcs_viewmodel = VersionControlViewModel(
                    project_path=Path(self._ctx.state.project.path),
                    diffable_adapter=projects_ctx.diffable_adapter,
                    git_adapter=projects_ctx.git_adapter,
                    event_bus=self._ctx.event_bus,
                    signal_bridge=self._project_signal_bridge,
                )
                self._screens["history"].set_viewmodel(vcs_viewmodel)

    def _auto_init_vcs(self):
        """Auto-initialize VCS for newly created projects."""
        from src.contexts.projects.core.commandHandlers import (
            initialize_version_control,
        )
        from src.contexts.projects.core.vcs_commands import (
            InitializeVersionControlCommand,
        )

        projects_ctx = self._ctx.projects_context
        if not projects_ctx or not self._ctx.state.project:
            return

        if not projects_ctx.git_adapter or not projects_ctx.diffable_adapter:
            return

        # Skip if already initialized
        if projects_ctx.git_adapter.is_initialized():
            return

        project_path = Path(self._ctx.state.project.path)
        command = InitializeVersionControlCommand(project_path=str(project_path))
        result = initialize_version_control(
            command=command,
            diffable_adapter=projects_ctx.diffable_adapter,
            git_adapter=projects_ctx.git_adapter,
            event_bus=self._ctx.event_bus,
        )

        # Warn user if VCS init failed (e.g., git not installed)
        if result.is_failure and "CLI_NOT_FOUND" in (result.error_code or ""):
            QMessageBox.warning(
                self._shell,
                "Version Control Unavailable",
                "Git is not installed. Version history will not be available.\n\n"
                "Install Git from https://git-scm.com/downloads to enable "
                "automatic change tracking and restore capabilities.",
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
                # Auto-initialize VCS for new projects
                self._auto_init_vcs()
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
        sources_ctx = self._ctx.sources_context
        if sources_ctx:
            source = sources_ctx.source_repo.get_by_id(SourceId(value=source_id))
            if source and source.fulltext:
                # Load the source content into the coding screen
                self._screens["coding"].set_document(
                    title=source.name,
                    badge=source.source_type.value,
                    text=source.fulltext,
                )
                self._screens["coding"].set_current_source(source_id)

        if self._shell is not None:
            self._shell.set_screen(self._screens["coding"])
            self._shell.set_active_menu("coding")

    def _cleanup(self):
        """Clean up resources on app exit."""
        self._mcp_server.stop()
        self._ctx.stop()

    def run(self) -> int:
        """Run the application with unified asyncio + Qt event loop via qasync."""
        self._ctx.start()
        self._setup_shell()
        assert self._shell is not None
        self._shell.show()

        # Ensure cleanup happens regardless of how app closes
        self._app.aboutToQuit.connect(self._cleanup)

        # Create unified event loop: asyncio coroutines and Qt events
        # share a single loop — no need for a separate MCP server thread.
        loop = qasync.QEventLoop(self._app)
        asyncio.set_event_loop(loop)

        with loop:
            # Start MCP server as an asyncio task on the unified loop
            loop.create_task(self._mcp_server.serve_async())
            loop.run_forever()

        return 0


def main():
    """Application entry point."""
    app = QualCoderApp()
    sys.exit(app.run())


if __name__ == "__main__":
    main()
