"""
Application Coordinator - Central Facade for QualCoder.

This coordinator is a thin facade that composes specialized per-context
coordinators. Each coordinator owns a specific bounded context:

- settings: Theme, font, language, backup, AV coding settings
- projects: Project lifecycle (open/create/close)
- sources: Source CRUD operations
- cases: Case CRUD and linking
- folders: Folder CRUD
- coding: Code and segment operations
- navigation: Screen and segment navigation

Usage:
    from src.application.coordinator import ApplicationCoordinator

    coordinator = ApplicationCoordinator()
    coordinator.start()

    # Use sub-coordinators directly
    coordinator.projects.open_project("/path/to/project.qda")
    coordinator.settings.change_theme("dark")
    coordinator.sources.add_source(command)
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

from returns.result import Failure, Result, Success

from src.application.coordinators import (
    CasesCoordinator,
    CodingCoordinator,
    CoordinatorInfrastructure,
    FoldersCoordinator,
    NavigationCoordinator,
    ProjectsCoordinator,
    SettingsCoordinator,
    SourcesCoordinator,
)
from src.application.event_bus import EventBus
from src.application.lifecycle import ProjectLifecycle
from src.application.policies import PolicyExecutor
from src.application.policies.coding_policies import configure_coding_policies
from src.application.policies.projects_policies import configure_projects_policies
from src.application.state import ProjectState
from src.application.sync import SourceSyncHandler

# Conditional imports for Qt (allows non-Qt tests to pass)
try:
    from src.application.projects.signal_bridge import ProjectSignalBridge

    HAS_QT = True
except ImportError:
    HAS_QT = False
    ProjectSignalBridge = None

if TYPE_CHECKING:
    from src.application.contexts import (
        CasesContext,
        CodingContext,
        ProjectsContext,
        SourcesContext,
    )
    from src.contexts.settings.infra import UserSettingsRepository
    from src.infrastructure.mcp.project_tools import ProjectTools


class ApplicationCoordinator:
    """
    Central facade for the QualCoder application.

    Composes specialized per-context coordinators and provides:
    - Infrastructure setup (event bus, lifecycle, state)
    - Sub-coordinator access via properties
    - Dialog integration
    - MCP tools

    All domain operations are performed via sub-coordinators:
        coordinator.sources.add_source(command)
        coordinator.projects.open_project(path)
        coordinator.settings.change_theme("dark")
    """

    def __init__(self, settings_repo: UserSettingsRepository | None = None) -> None:
        """
        Initialize the coordinator with all dependencies.

        Args:
            settings_repo: Optional settings repository (created if not provided)
        """
        # Create core infrastructure
        self._event_bus = EventBus(history_size=100)
        self._lifecycle = ProjectLifecycle()
        self._state = ProjectState()

        # Create settings repository (global, always available)
        if settings_repo is None:
            from src.contexts.settings.infra import UserSettingsRepository

            settings_repo = UserSettingsRepository()
        self._settings_repo: UserSettingsRepository = settings_repo

        # Create signal bridge (only if Qt is available)
        self._signal_bridge: ProjectSignalBridge | None = None
        if HAS_QT and ProjectSignalBridge is not None:
            self._signal_bridge = ProjectSignalBridge.instance(self._event_bus)

        # Create shared infrastructure for all coordinators
        self._infra = CoordinatorInfrastructure(
            event_bus=self._event_bus,
            state=self._state,
            lifecycle=self._lifecycle,
            settings_repo=self._settings_repo,
            signal_bridge=self._signal_bridge,
        )

        # Create per-context coordinators
        self._settings = SettingsCoordinator(self._infra)
        self._projects = ProjectsCoordinator(self._infra)
        self._sources = SourcesCoordinator(self._infra)
        self._cases = CasesCoordinator(self._infra)
        self._folders = FoldersCoordinator(self._infra)
        self._coding = CodingCoordinator(self._infra)
        self._navigation = NavigationCoordinator(self._infra)

        # Cross-context sync handler (legacy - will be replaced by policies)
        self._source_sync_handler = SourceSyncHandler(event_bus=self._event_bus)

        # Policy infrastructure
        self._configure_policies()
        self._policy_executor = PolicyExecutor(self._event_bus)

        # MCP tools (created lazily)
        self._mcp_tools: ProjectTools | None = None

    def _configure_policies(self) -> None:
        """Configure all declarative policies."""
        configure_projects_policies()
        configure_coding_policies()

    def start(self) -> None:
        """Start the coordinator and signal bridge."""
        if self._signal_bridge is not None:
            self._signal_bridge.start()
        self._source_sync_handler.start()
        self._policy_executor.start()

    def stop(self) -> None:
        """Stop the coordinator and cleanup."""
        self._policy_executor.stop()
        self._source_sync_handler.stop()
        if self._signal_bridge is not None:
            self._signal_bridge.stop()
        self.projects.close_project()

    # =========================================================================
    # Sub-Coordinator Access
    # =========================================================================

    @property
    def settings(self) -> SettingsCoordinator:
        """Settings coordinator for theme, font, language, backup."""
        return self._settings

    @property
    def projects(self) -> ProjectsCoordinator:
        """Projects coordinator for open/create/close project."""
        return self._projects

    @property
    def sources(self) -> SourcesCoordinator:
        """Sources coordinator for source CRUD."""
        return self._sources

    @property
    def cases(self) -> CasesCoordinator:
        """Cases coordinator for case CRUD and linking."""
        return self._cases

    @property
    def folders(self) -> FoldersCoordinator:
        """Folders coordinator for folder CRUD."""
        return self._folders

    @property
    def coding(self) -> CodingCoordinator:
        """Coding coordinator for codes and segments."""
        return self._coding

    @property
    def navigation(self) -> NavigationCoordinator:
        """Navigation coordinator for screen and segment navigation."""
        return self._navigation

    # =========================================================================
    # Infrastructure Access
    # =========================================================================

    @property
    def event_bus(self) -> EventBus:
        """Get the event bus."""
        return self._event_bus

    @property
    def signal_bridge(self) -> ProjectSignalBridge | None:
        """Get the signal bridge (None if Qt not available)."""
        return self._signal_bridge

    @property
    def lifecycle(self) -> ProjectLifecycle:
        """Get the project lifecycle manager."""
        return self._lifecycle

    @property
    def state(self) -> ProjectState:
        """Get the project state cache."""
        return self._state

    @property
    def settings_repo(self) -> UserSettingsRepository:
        """Get the settings repository."""
        return self._settings_repo

    @property
    def policy_executor(self) -> PolicyExecutor:
        """Get the policy executor."""
        return self._policy_executor

    # =========================================================================
    # Context Access (for advanced usage)
    # =========================================================================

    @property
    def sources_context(self) -> SourcesContext | None:
        """Get the Sources context (None if no project open)."""
        return self._infra.sources_context

    @property
    def coding_context(self) -> CodingContext | None:
        """Get the Coding context (None if no project open)."""
        return self._infra.coding_context

    @property
    def cases_context(self) -> CasesContext | None:
        """Get the Cases context (None if no project open)."""
        return self._infra.cases_context

    @property
    def projects_context(self) -> ProjectsContext | None:
        """Get the Projects context (None if no project open)."""
        return self._infra.projects_context

    # =========================================================================
    # Dialog Integration
    # =========================================================================

    def show_open_project_dialog(self, parent: Any = None) -> Result:
        """Show the open project dialog and handle the result."""
        if not HAS_QT:
            return Failure("Qt not available")

        from src.presentation.dialogs.project_dialog import OpenProjectDialog

        recent = [
            {"name": r.name, "path": str(r.path)} for r in self._state.recent_projects
        ]

        dialog = OpenProjectDialog(recent_projects=recent, parent=parent)
        result = dialog.exec()

        if result:
            path = dialog.get_selected_path()
            if path:
                open_result = self._projects.open_project(path)
                if isinstance(open_result, Success):
                    self._wire_sync_handler()
                return open_result

        return Failure("Dialog cancelled")

    def show_create_project_dialog(
        self, parent: Any = None, default_directory: str = ""
    ) -> Result:
        """Show the create project dialog and handle the result."""
        if not HAS_QT:
            return Failure("Qt not available")

        from src.presentation.dialogs.project_dialog import CreateProjectDialog

        if not default_directory:
            default_directory = str(Path.home())

        dialog = CreateProjectDialog(
            default_directory=default_directory,
            parent=parent,
        )
        result = dialog.exec()

        if result:
            name = dialog.get_project_name()
            path = dialog.get_project_path()
            if name and path:
                return self._projects.create_project(name, path)

        return Failure("Dialog cancelled")

    def show_settings_dialog(
        self,
        parent: Any = None,
        colors: Any = None,
        config_path: Path | None = None,
        blocking: bool = True,
    ) -> Any:
        """Show the settings dialog."""
        if not HAS_QT:
            return None

        from src.presentation.dialogs.settings_dialog import SettingsDialog
        from src.presentation.viewmodels import SettingsViewModel

        # Use custom config path for testing, or default settings coordinator
        if config_path is not None:
            from src.contexts.settings.infra import UserSettingsRepository

            temp_repo = UserSettingsRepository(config_path=config_path)
            temp_infra = CoordinatorInfrastructure(
                event_bus=self._event_bus,
                state=self._state,
                lifecycle=self._lifecycle,
                settings_repo=temp_repo,
            )
            settings_coordinator = SettingsCoordinator(temp_infra)
        else:
            settings_coordinator = self._settings

        viewmodel = SettingsViewModel(settings_provider=settings_coordinator)
        dialog = SettingsDialog(
            viewmodel=viewmodel,
            colors=colors,
            parent=parent,
        )

        if blocking:
            dialog.exec()
        else:
            dialog.show()

        return dialog

    # =========================================================================
    # MCP Tools
    # =========================================================================

    def get_mcp_tools(self) -> ProjectTools:
        """Get MCP project tools for agent integration."""
        if self._mcp_tools is None:
            from src.infrastructure.mcp.project_tools import ProjectTools

            self._mcp_tools = ProjectTools(coordinator=self)

        return self._mcp_tools

    # =========================================================================
    # Internal Helpers
    # =========================================================================

    def _wire_sync_handler(self) -> None:
        """Wire contexts to sync handler after project opens."""
        self._source_sync_handler.set_coding_context(self._infra.coding_context)
        self._source_sync_handler.set_cases_context(self._infra.cases_context)


# =============================================================================
# Singleton Instance
# =============================================================================

_coordinator_instance: ApplicationCoordinator | None = None


def get_coordinator() -> ApplicationCoordinator:
    """Get the global coordinator instance."""
    global _coordinator_instance
    if _coordinator_instance is None:
        _coordinator_instance = ApplicationCoordinator()
    return _coordinator_instance


def reset_coordinator() -> None:
    """Reset the coordinator instance (for testing)."""
    global _coordinator_instance
    if _coordinator_instance is not None:
        _coordinator_instance.stop()
    _coordinator_instance = None
