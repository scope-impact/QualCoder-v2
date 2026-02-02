"""
Application Context - Dependency Container for QualCoder.

AppContext is a simple dependency container that holds:
- Infrastructure (event_bus, state, lifecycle, settings_repo, signal_bridge)
- Bounded contexts (sources_context, cases_context, coding_context, projects_context)

It does NOT contain use case methods or dialog methods - those are handled
by direct use case calls and the DialogService respectively.

Usage:
    from src.application.app_context import get_app_context

    ctx = get_app_context()
    ctx.start()

    # Use cases are called directly, passing dependencies from ctx
    from src.application.sources.usecases import add_source
    result = add_source(command, ctx.state, ctx.sources_context, ctx.event_bus)
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from returns.result import Result, Success

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
    ProjectSignalBridge = None  # type: ignore[assignment, misc]

if TYPE_CHECKING:
    from src.application.contexts import (
        CasesContext,
        CodingContext,
        ProjectsContext,
        SourcesContext,
    )
    from src.contexts.projects.core.entities import Project
    from src.contexts.settings.infra import UserSettingsRepository

logger = logging.getLogger(__name__)


@dataclass
class AppContext:
    """
    Application context - dependency container for QualCoder.

    This is a simple container that holds all the infrastructure and bounded
    contexts needed by the application. It provides lifecycle management for
    starting/stopping services and opening/closing projects.

    Attributes:
        event_bus: Domain event pub/sub infrastructure
        state: In-memory cache of project data
        lifecycle: Database connection management
        settings_repo: User settings persistence
        signal_bridge: Qt signal bridge for UI updates (optional)

        sources_context: Sources bounded context (None if no project open)
        cases_context: Cases bounded context (None if no project open)
        coding_context: Coding bounded context (None if no project open)
        projects_context: Projects bounded context (None if no project open)
    """

    event_bus: EventBus
    state: ProjectState
    lifecycle: ProjectLifecycle
    settings_repo: UserSettingsRepository
    signal_bridge: ProjectSignalBridge | None = None

    # Bounded contexts (populated when project opens)
    sources_context: SourcesContext | None = field(default=None)
    cases_context: CasesContext | None = field(default=None)
    coding_context: CodingContext | None = field(default=None)
    projects_context: ProjectsContext | None = field(default=None)

    # Internal services (managed by start/stop)
    _source_sync_handler: SourceSyncHandler = field(init=False, repr=False)
    _policy_executor: PolicyExecutor = field(init=False, repr=False)
    _started: bool = field(default=False, init=False, repr=False)

    def __post_init__(self) -> None:
        """Initialize internal services after dataclass creation."""
        # Configure declarative policies
        configure_projects_policies()
        configure_coding_policies()

        # Create sync handler (wires contexts when project opens)
        self._source_sync_handler = SourceSyncHandler(event_bus=self.event_bus)

        # Create policy executor
        self._policy_executor = PolicyExecutor(self.event_bus)

    # =========================================================================
    # Lifecycle Methods
    # =========================================================================

    def start(self) -> None:
        """
        Start the application context and all services.

        This should be called once during application startup.
        It starts:
        - Signal bridge (if Qt available)
        - Source sync handler
        - Policy executor
        """
        if self._started:
            logger.warning("AppContext.start() called but already started")
            return

        logger.debug("Starting AppContext")

        if self.signal_bridge is not None:
            self.signal_bridge.start()

        self._source_sync_handler.start()
        self._policy_executor.start()
        self._started = True

        logger.info("AppContext started")

    def stop(self) -> None:
        """
        Stop the application context and cleanup.

        This should be called once during application shutdown.
        It stops all services and closes any open project.
        """
        if not self._started:
            logger.warning("AppContext.stop() called but not started")
            return

        logger.debug("Stopping AppContext")

        # Close any open project first
        self.close_project()

        self._policy_executor.stop()
        self._source_sync_handler.stop()

        if self.signal_bridge is not None:
            self.signal_bridge.stop()

        self._started = False
        logger.info("AppContext stopped")

    # =========================================================================
    # Project Lifecycle
    # =========================================================================

    def open_project(self, path: str) -> Result[Project, str]:
        """
        Open a project and initialize bounded contexts.

        Args:
            path: Path to the project file (.qda)

        Returns:
            Success with Project entity, or Failure with error message
        """
        from src.application.projects.commands import OpenProjectCommand
        from src.application.projects.usecases import open_project

        command = OpenProjectCommand(path=path)
        result = open_project(
            command=command,
            lifecycle=self.lifecycle,
            state=self.state,
            event_bus=self.event_bus,
            get_contexts=self._create_contexts,
        )

        if isinstance(result, Success):
            # Wire sync handler with newly created contexts
            self._wire_sync_handler()

        return result

    def create_project(self, name: str, path: str) -> Result[Project, str]:
        """
        Create a new project.

        This creates the project file and updates state, but does not
        initialize bounded contexts. The caller should open the project
        afterward if they need to work with project data.

        Args:
            name: Name of the project
            path: Path where the project file will be created

        Returns:
            Success with Project entity, or Failure with error message
        """
        from src.application.projects.commands import CreateProjectCommand
        from src.application.projects.usecases import create_project

        command = CreateProjectCommand(name=name, path=path)
        return create_project(
            command=command,
            lifecycle=self.lifecycle,
            state=self.state,
            event_bus=self.event_bus,
        )

    def close_project(self) -> Result[None, str]:
        """
        Close the current project and cleanup contexts.

        Returns:
            Success with None, or Failure with error message
        """
        from src.application.projects.usecases import close_project

        result = close_project(
            lifecycle=self.lifecycle,
            state=self.state,
            event_bus=self.event_bus,
        )

        # Clear bounded contexts
        self._clear_contexts()

        return result

    # =========================================================================
    # Context Management (Internal)
    # =========================================================================

    def _create_contexts(self, connection) -> dict:
        """
        Create bounded context objects for the open project.

        Called by open_project use case after connection is established.

        Args:
            connection: SQLAlchemy Connection object

        Returns:
            Dict of context name to context object
        """
        from src.application.contexts import (
            CasesContext,
            CodingContext,
            ProjectsContext,
            SourcesContext,
        )

        self.sources_context = SourcesContext.create(connection)
        self.coding_context = CodingContext.create(connection)
        self.cases_context = CasesContext.create(connection)
        self.projects_context = ProjectsContext.create(connection)

        logger.debug("Created bounded contexts for project")

        return {
            "sources": self.sources_context,
            "cases": self.cases_context,
            "coding": self.coding_context,
            "folders": self.sources_context,  # Folders are in sources context
            "projects": self.projects_context,
        }

    def _clear_contexts(self) -> None:
        """Clear bounded context objects when project closes."""
        self.sources_context = None
        self.cases_context = None
        self.coding_context = None
        self.projects_context = None
        logger.debug("Cleared bounded contexts")

    def _wire_sync_handler(self) -> None:
        """Wire contexts to sync handler after project opens."""
        self._source_sync_handler.set_coding_context(self.coding_context)
        self._source_sync_handler.set_cases_context(self.cases_context)

    # =========================================================================
    # Properties
    # =========================================================================

    @property
    def policy_executor(self) -> PolicyExecutor:
        """Get the policy executor."""
        return self._policy_executor

    @property
    def is_started(self) -> bool:
        """Check if the context has been started."""
        return self._started

    @property
    def has_project(self) -> bool:
        """Check if a project is currently open."""
        return self.state.project is not None


# =============================================================================
# Factory Function
# =============================================================================


def create_app_context(
    settings_repo: UserSettingsRepository | None = None,
) -> AppContext:
    """
    Create a new AppContext instance with all dependencies.

    Args:
        settings_repo: Optional settings repository (created if not provided)

    Returns:
        Configured AppContext instance
    """
    # Create core infrastructure
    event_bus = EventBus(history_size=100)
    lifecycle = ProjectLifecycle()
    state = ProjectState()

    # Create settings repository (global, always available)
    if settings_repo is None:
        from src.contexts.settings.infra import UserSettingsRepository

        settings_repo = UserSettingsRepository()

    # Create signal bridge (only if Qt is available)
    signal_bridge: ProjectSignalBridge | None = None
    if HAS_QT and ProjectSignalBridge is not None:
        signal_bridge = ProjectSignalBridge.instance(event_bus)

    return AppContext(
        event_bus=event_bus,
        state=state,
        lifecycle=lifecycle,
        settings_repo=settings_repo,
        signal_bridge=signal_bridge,
    )


# =============================================================================
# Singleton Instance
# =============================================================================

_app_context_instance: AppContext | None = None


def get_app_context() -> AppContext:
    """
    Get the global AppContext instance.

    Creates the instance on first call using default configuration.
    """
    global _app_context_instance
    if _app_context_instance is None:
        _app_context_instance = create_app_context()
    return _app_context_instance


def set_app_context(ctx: AppContext) -> None:
    """
    Set the global AppContext instance.

    Useful for testing or custom configuration.

    Args:
        ctx: AppContext instance to use as the global instance
    """
    global _app_context_instance
    _app_context_instance = ctx


def reset_app_context() -> None:
    """
    Reset the global AppContext instance.

    Stops the current instance if running, then clears it.
    Useful for testing.
    """
    global _app_context_instance
    if _app_context_instance is not None:
        if _app_context_instance.is_started:
            _app_context_instance.stop()
        _app_context_instance = None
