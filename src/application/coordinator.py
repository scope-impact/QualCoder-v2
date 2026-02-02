"""
Application Coordinator - Central Wiring for QualCoder

This coordinator connects all the pieces of the application:
- Event bus for domain events
- Controllers for handling commands
- Signal bridges for UI updates
- MCP tools for agent access

Implements QC-026 integration:
- Wires project dialogs to controller commands
- Connects signal bridge to screens
- Exposes MCP tools for agent integration

Usage:
    from src.application.coordinator import ApplicationCoordinator

    coordinator = ApplicationCoordinator()
    coordinator.start()

    # Open project via dialog
    coordinator.show_open_project_dialog()

    # Create project via dialog
    coordinator.show_create_project_dialog()

    # Connect screen to navigation events
    coordinator.connect_text_coding_screen(screen)
"""

from __future__ import annotations

import contextlib
from pathlib import Path
from typing import TYPE_CHECKING, Any

from returns.result import Failure, Result

from src.application.event_bus import EventBus
from src.application.projects.controller import (
    CreateProjectCommand,
    NavigateToSegmentCommand,
    OpenProjectCommand,
    ProjectControllerImpl,
)

# Conditional imports for Qt (allows non-Qt tests to pass)
try:
    from PySide6.QtCore import QObject

    from src.application.projects.signal_bridge import ProjectSignalBridge

    HAS_QT = True
except ImportError:
    HAS_QT = False
    QObject = object
    ProjectSignalBridge = None

if TYPE_CHECKING:
    from pathlib import Path

    from src.infrastructure.mcp.project_tools import ProjectTools
    from src.presentation.screens.text_coding import TextCodingScreen


class ApplicationCoordinator:
    """
    Central coordinator for the QualCoder application.

    Manages:
    - Event bus for domain event publication
    - Project controller for command handling
    - Signal bridge for UI event propagation
    - MCP tools for agent integration

    This class serves as the composition root, wiring all dependencies
    together and providing a clean API for the presentation layer.
    """

    def __init__(self) -> None:
        """Initialize the coordinator with all dependencies."""
        # Create event bus
        self._event_bus = EventBus(history_size=100)

        # Create project controller
        self._project_controller = ProjectControllerImpl(
            event_bus=self._event_bus,
            source_repo=None,  # Will be injected when database layer is ready
            project_repo=None,
        )

        # Create signal bridge (only if Qt is available)
        self._signal_bridge: ProjectSignalBridge | None = None
        if HAS_QT and ProjectSignalBridge is not None:
            self._signal_bridge = ProjectSignalBridge.instance(self._event_bus)

        # MCP tools (created lazily)
        self._mcp_tools: ProjectTools | None = None

        # Connected screens
        self._text_coding_screen: TextCodingScreen | None = None

    def start(self) -> None:
        """Start the coordinator and signal bridge."""
        if self._signal_bridge is not None:
            self._signal_bridge.start()

    def stop(self) -> None:
        """Stop the coordinator and cleanup."""
        if self._signal_bridge is not None:
            self._signal_bridge.stop()

    # =========================================================================
    # Property Access
    # =========================================================================

    @property
    def event_bus(self) -> EventBus:
        """Get the event bus."""
        return self._event_bus

    @property
    def project_controller(self) -> ProjectControllerImpl:
        """Get the project controller."""
        return self._project_controller

    @property
    def signal_bridge(self) -> ProjectSignalBridge | None:
        """Get the signal bridge (None if Qt not available)."""
        return self._signal_bridge

    # =========================================================================
    # Project Commands (AC #1, AC #2)
    # =========================================================================

    def open_project(self, path: str) -> Result:
        """
        Open an existing project.

        Args:
            path: Path to the project file (.qda)

        Returns:
            Success with project, or Failure with error
        """
        command = OpenProjectCommand(path=path)
        return self._project_controller.open_project(command)

    def create_project(self, name: str, path: str) -> Result:
        """
        Create a new project.

        Args:
            name: Project name
            path: Path for the new project file

        Returns:
            Success with project, or Failure with error
        """
        command = CreateProjectCommand(name=name, path=path)
        return self._project_controller.create_project(command)

    def close_project(self) -> Result:
        """Close the current project."""
        return self._project_controller.close_project()

    # =========================================================================
    # Navigation Commands (AC #4, AC #6)
    # =========================================================================

    def navigate_to_segment(
        self, source_id: int, start_pos: int, end_pos: int, highlight: bool = True
    ) -> Result:
        """
        Navigate to a specific segment in a source.

        Implements AC #6: Agent can navigate to a specific source or segment.

        Args:
            source_id: The source document ID
            start_pos: Start character position
            end_pos: End character position
            highlight: Whether to highlight the segment

        Returns:
            Success or Failure
        """
        command = NavigateToSegmentCommand(
            source_id=source_id,
            start_pos=start_pos,
            end_pos=end_pos,
            highlight=highlight,
        )
        return self._project_controller.navigate_to_segment(command)

    # =========================================================================
    # Dialog Integration (AC #1, AC #2)
    # =========================================================================

    def show_open_project_dialog(self, parent: Any = None) -> Result:
        """
        Show the open project dialog and handle the result.

        Implements AC #1: Researcher can open an existing project file.

        Args:
            parent: Parent widget for the dialog

        Returns:
            Success with opened project, or Failure if cancelled/error
        """
        if not HAS_QT:
            return Failure("Qt not available")

        from src.presentation.dialogs.project_dialog import OpenProjectDialog

        # Get recent projects
        recent = [
            {"name": r.name, "path": str(r.path)}
            for r in self._project_controller.get_recent_projects()
        ]

        dialog = OpenProjectDialog(recent_projects=recent, parent=parent)
        result = dialog.exec()

        if result:
            path = dialog.get_selected_path()
            if path:
                return self.open_project(path)

        return Failure("Dialog cancelled")

    def show_create_project_dialog(
        self, parent: Any = None, default_directory: str = ""
    ) -> Result:
        """
        Show the create project dialog and handle the result.

        Implements AC #2: Researcher can create a new project.

        Args:
            parent: Parent widget for the dialog
            default_directory: Default directory for project creation

        Returns:
            Success with created project, or Failure if cancelled/error
        """
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
                return self.create_project(name, path)

        return Failure("Dialog cancelled")

    def show_settings_dialog(
        self,
        parent: Any = None,
        colors: Any = None,
        config_path: Path | None = None,
        blocking: bool = True,
    ) -> Any:
        """
        Show the settings dialog.

        Implements QC-038: Settings and Preferences.

        Args:
            parent: Parent widget for the dialog
            colors: Color configuration for theming
            config_path: Optional custom config path (for testing)
            blocking: Whether to block with exec() (default True)

        Returns:
            The dialog instance (for non-blocking mode)
        """
        if not HAS_QT:
            return None

        from src.application.settings import SettingsControllerImpl
        from src.infrastructure.settings import UserSettingsRepository
        from src.presentation.dialogs.settings_dialog import SettingsDialog
        from src.presentation.viewmodels import SettingsViewModel

        # Create settings stack with event bus for reactive updates
        repo = UserSettingsRepository(config_path=config_path)
        controller = SettingsControllerImpl(
            settings_repo=repo,
            event_bus=self._event_bus,
        )
        viewmodel = SettingsViewModel(settings_controller=controller)

        # Create and show dialog
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
    # Screen Connection (AC #6)
    # =========================================================================

    def connect_text_coding_screen(self, screen: TextCodingScreen) -> None:
        """
        Connect a TextCodingScreen to receive navigation events.

        Implements AC #6: Agent can navigate to a specific source or segment.

        When the signal bridge emits navigated_to_segment, the screen
        will scroll to and highlight the specified segment.

        Args:
            screen: The TextCodingScreen to connect
        """
        self._text_coding_screen = screen

        if self._signal_bridge is not None:
            self._signal_bridge.navigated_to_segment.connect(
                screen.on_navigated_to_segment
            )

    def disconnect_text_coding_screen(self, screen: TextCodingScreen) -> None:
        """Disconnect a TextCodingScreen from navigation events."""
        if self._signal_bridge is not None:
            with contextlib.suppress(RuntimeError):
                self._signal_bridge.navigated_to_segment.disconnect(
                    screen.on_navigated_to_segment
                )

        if self._text_coding_screen is screen:
            self._text_coding_screen = None

    # =========================================================================
    # MCP Tools (AC #5, AC #6)
    # =========================================================================

    def get_mcp_tools(self) -> ProjectTools:
        """
        Get MCP project tools for agent integration.

        Implements AC #5: Agent can query current project context.
        Implements AC #6: Agent can navigate to a specific source or segment.

        Returns:
            ProjectTools instance for MCP registration
        """
        if self._mcp_tools is None:
            from src.infrastructure.mcp.project_tools import ProjectTools

            self._mcp_tools = ProjectTools(controller=self._project_controller)

        return self._mcp_tools

    # =========================================================================
    # Query Delegation (AC #5)
    # =========================================================================

    def get_project_context(self) -> dict[str, Any]:
        """
        Get current project context for agents.

        Implements AC #5: Agent can query current project context.

        Returns:
            Dict with project state information
        """
        return self._project_controller.get_project_context()

    def get_sources(self) -> list:
        """Get all sources in the current project."""
        return self._project_controller.get_sources()

    def get_current_screen(self) -> str | None:
        """Get the current screen name."""
        return self._project_controller.get_current_screen()


# =============================================================================
# Singleton Instance
# =============================================================================

_coordinator_instance: ApplicationCoordinator | None = None


def get_coordinator() -> ApplicationCoordinator:
    """
    Get the global coordinator instance.

    Returns:
        The singleton ApplicationCoordinator
    """
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
