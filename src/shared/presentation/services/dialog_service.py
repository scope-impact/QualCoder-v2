"""
Dialog Service - UI Dialog Integration.

Provides methods for showing common application dialogs
(open project, create project, settings) and handling their results.

This service is part of the refactoring from ApplicationCoordinator to AppContext.
It separates dialog presentation from infrastructure management.

Usage:
    dialog_service = DialogService(app_context)
    result = dialog_service.show_open_project_dialog(parent_widget)
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any, Protocol, runtime_checkable

from returns.result import Failure, Result

if TYPE_CHECKING:
    from src.contexts.settings.infra import UserSettingsRepository
    from src.shared.infra.event_bus import EventBus
    from src.shared.infra.lifecycle import ProjectLifecycle
    from src.shared.infra.state import ProjectState

# Conditional Qt import
try:
    HAS_QT = True
except ImportError:
    HAS_QT = False


@runtime_checkable
class AppContextProtocol(Protocol):
    """
    Protocol defining what DialogService needs from AppContext.

    This protocol allows DialogService to work with either:
    - The future AppContext (once created)
    - Any adapter that provides these properties and methods
    """

    @property
    def state(self) -> ProjectState:
        """Project state cache with recent_projects, project, etc."""
        ...

    @property
    def lifecycle(self) -> ProjectLifecycle:
        """Project lifecycle manager for database operations."""
        ...

    @property
    def event_bus(self) -> EventBus:
        """Event bus for publishing domain events."""
        ...

    @property
    def settings_repo(self) -> UserSettingsRepository:
        """User settings repository."""
        ...

    def open_project(self, path: str) -> Result:
        """Open an existing project."""
        ...

    def create_project(self, name: str, path: str) -> Result:
        """Create a new project."""
        ...


class DialogService:
    """
    Service for showing application dialogs.

    Provides a clean interface for showing common dialogs and handling
    their results. Works with AppContext to perform the underlying operations.

    This service is responsible for:
    - Showing dialogs and collecting user input
    - Delegating operations to AppContext
    - Returning results to the caller

    The caller is responsible for any post-operation wiring (e.g., sync handlers).

    Example:
        from returns.result import Success

        ctx = AppContext(...)
        dialog_service = DialogService(ctx)

        # Show open project dialog
        result = dialog_service.show_open_project_dialog(parent)
        if isinstance(result, Success):
            # Handle successful project open
            project = result.unwrap()
    """

    def __init__(self, ctx: AppContextProtocol) -> None:
        """
        Initialize DialogService with application context.

        Args:
            ctx: Application context providing state, lifecycle, event_bus,
                 settings_repo, and project operations (open_project, create_project)
        """
        self._ctx = ctx

    def show_open_project_dialog(self, parent: Any = None) -> Result:
        """
        Show the open project dialog and handle the result.

        Displays a dialog allowing the user to select a recently opened project
        or browse for a project file. If the user selects a project, it will
        be opened via the AppContext.

        Args:
            parent: Parent widget for the dialog (optional)

        Returns:
            Success with Project entity if project was opened
            Failure with error message if cancelled or failed
        """
        if not HAS_QT:
            return Failure("Qt not available")

        from src.contexts.projects.presentation.dialogs import OpenProjectDialog

        # Get recent projects from state
        recent = [
            {"name": r.name, "path": str(r.path)}
            for r in self._ctx.state.recent_projects
        ]

        dialog = OpenProjectDialog(recent_projects=recent, parent=parent)
        result = dialog.exec()

        if result:
            path = dialog.get_selected_path()
            if path:
                return self._ctx.open_project(path)

        return Failure("Dialog cancelled")

    def show_create_project_dialog(
        self, parent: Any = None, default_directory: str = ""
    ) -> Result:
        """
        Show the create project dialog and handle the result.

        Displays a dialog allowing the user to enter a project name and
        select a location for the new project. If the user confirms,
        the project will be created via the AppContext.

        Args:
            parent: Parent widget for the dialog (optional)
            default_directory: Default directory for the file browser.
                             If not provided, defaults to user's home directory.

        Returns:
            Success with Project entity if project was created
            Failure with error message if cancelled or failed
        """
        if not HAS_QT:
            return Failure("Qt not available")

        from src.contexts.projects.presentation.dialogs import CreateProjectDialog

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
                return self._ctx.create_project(name, path)

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

        Displays the application settings dialog allowing the user to configure
        theme, font, language, backup, and AV coding settings.

        Args:
            parent: Parent widget for the dialog (optional)
            colors: Color palette for theming (optional)
            config_path: Custom config path for testing (optional).
                        If provided, creates a temporary settings repository
                        instead of using the one from AppContext.
            blocking: If True, blocks until dialog is closed (exec).
                     If False, shows dialog non-blocking (show).

        Returns:
            The SettingsDialog instance (useful for testing)
        """
        if not HAS_QT:
            return None

        from src.contexts.settings.presentation import SettingsViewModel
        from src.contexts.settings.presentation.dialogs import SettingsDialog
        from src.shared.presentation.services.settings_service import SettingsService

        # Use custom config path for testing, or default settings from context
        if config_path is not None:
            from src.contexts.settings.infra import UserSettingsRepository

            temp_repo = UserSettingsRepository(config_path=config_path)
            settings_service = SettingsService(temp_repo)
        else:
            # Use context's settings_repo
            settings_service = SettingsService(self._ctx.settings_repo)

        viewmodel = SettingsViewModel(settings_provider=settings_service)
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
