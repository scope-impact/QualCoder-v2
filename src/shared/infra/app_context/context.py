"""
AppContext - Composition Root for QualCoder.

AppContext holds all application-wide services and bounded contexts directly.
No unnecessary abstraction layers.

Policies are configured at startup via context-specific configure_*_policies()
functions that subscribe to the event bus. See:
- src/contexts/coding/core/policies.py
- src/contexts/cases/core/policies.py
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from src.shared.common.operation_result import OperationResult
from src.shared.infra.event_bus import EventBus
from src.shared.infra.lifecycle import ProjectLifecycle
from src.shared.infra.state import ProjectState

from .bounded_contexts import (
    CasesContext,
    CodingContext,
    ProjectsContext,
    SourcesContext,
)

# Conditional imports for Qt (allows non-Qt tests to pass)
try:
    from src.shared.infra.signal_bridge.projects import ProjectSignalBridge

    HAS_QT = True
except ImportError:
    HAS_QT = False
    ProjectSignalBridge = None  # type: ignore[assignment, misc]

if TYPE_CHECKING:
    from src.contexts.settings.infra import UserSettingsRepository
    from src.shared.core.sync import SourceSyncHandler

logger = logging.getLogger(__name__)


@dataclass
class AppContext:
    """
    Application context - composition root for QualCoder.

    Holds all application-wide services and bounded contexts directly.

    Attributes:
        event_bus: Domain event pub/sub infrastructure
        lifecycle: Database connection management
        state: In-memory session state
        source_sync_handler: Cross-context synchronization
        settings_repo: User settings persistence (global, always available)
        signal_bridge: Qt signal bridge for UI updates (optional)

        sources_context: Sources bounded context (None if no project open)
        cases_context: Cases bounded context (None if no project open)
        coding_context: Coding bounded context (None if no project open)
        projects_context: Projects bounded context (None if no project open)
    """

    # Core infrastructure (always available)
    event_bus: EventBus
    lifecycle: ProjectLifecycle
    state: ProjectState
    source_sync_handler: SourceSyncHandler
    settings_repo: UserSettingsRepository

    # Optional Qt integration
    signal_bridge: ProjectSignalBridge | None = None

    # Bounded contexts (None when no project is open)
    sources_context: SourcesContext | None = None
    cases_context: CasesContext | None = None
    coding_context: CodingContext | None = None
    projects_context: ProjectsContext | None = None

    # Internal state
    _started: bool = field(default=False, init=False, repr=False)

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
        """
        if self._started:
            logger.warning("AppContext.start() called but already started")
            return

        logger.debug("Starting AppContext")

        if self.signal_bridge is not None:
            self.signal_bridge.start()

        self.source_sync_handler.start()
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

        self.source_sync_handler.stop()

        if self.signal_bridge is not None:
            self.signal_bridge.stop()

        self._started = False
        logger.info("AppContext stopped")

    # =========================================================================
    # Project Lifecycle
    # =========================================================================

    def open_project(self, path: str) -> OperationResult:
        """
        Open a project and initialize bounded contexts.

        Args:
            path: Path to the project file (.qda)

        Returns:
            OperationResult with Project entity on success, or error details on failure
        """
        from src.contexts.projects.core.commandHandlers import open_project
        from src.contexts.projects.core.commands import OpenProjectCommand

        command = OpenProjectCommand(path=path)
        result = open_project(
            command=command,
            lifecycle=self.lifecycle,
            state=self.state,
            event_bus=self.event_bus,
            get_contexts=self._create_contexts,
        )

        if result.is_success:
            # Wire sync handler with newly created contexts
            self._wire_sync_handler()

        return result

    def create_project(self, name: str, path: str) -> OperationResult:
        """
        Create a new project.

        This creates the project file and updates state, but does not
        initialize bounded contexts. The caller should open the project
        afterward if they need to work with project data.

        Args:
            name: Name of the project
            path: Path where the project file will be created

        Returns:
            OperationResult with Project entity on success, or error details on failure
        """
        from src.contexts.projects.core.commandHandlers import create_project
        from src.contexts.projects.core.commands import CreateProjectCommand

        command = CreateProjectCommand(name=name, path=path)
        return create_project(
            command=command,
            lifecycle=self.lifecycle,
            state=self.state,
            event_bus=self.event_bus,
        )

    def close_project(self) -> OperationResult:
        """
        Close the current project and cleanup contexts.

        Returns:
            OperationResult with None on success, or error details on failure
        """
        from src.contexts.projects.core.commandHandlers import close_project

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
        self.source_sync_handler.set_coding_context(self.coding_context)
        self.source_sync_handler.set_cases_context(self.cases_context)

    # =========================================================================
    # Properties
    # =========================================================================

    @property
    def is_started(self) -> bool:
        """Check if the context has been started."""
        return self._started

    @property
    def has_project(self) -> bool:
        """Check if a project is currently open."""
        return self.state.project is not None
