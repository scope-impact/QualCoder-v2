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
from typing import TYPE_CHECKING, Any

from src.shared.common.operation_result import OperationResult
from src.shared.infra.event_bus import EventBus
from src.shared.infra.lifecycle import ProjectLifecycle
from src.shared.infra.repositories import BackendType
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
    from src.shared.infra.convex import ConvexClientWrapper

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

    # Optional Convex client for cloud backend
    convex_client: ConvexClientWrapper | None = None

    # Optional sync engine for SQLite-Convex sync
    _sync_engine: Any = field(default=None, init=False, repr=False)

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
        Uses the configured backend type from settings.

        Args:
            connection: SQLAlchemy Connection object

        Returns:
            Dict of context name to context object
        """
        # Determine backend type from settings
        # SQLite is always primary; Convex is optional cloud sync
        backend_config = self.settings_repo.get_backend_config()
        backend_type = BackendType.SQLITE  # Always SQLite as primary

        # Initialize Convex client and SyncEngine if cloud sync is enabled
        sync_engine = None
        if backend_config.uses_convex and self.convex_client is None:
            from src.shared.infra.convex import ConvexClientWrapper

            try:
                self.convex_client = ConvexClientWrapper(backend_config.convex_url)
                logger.info(f"Connected to Convex for cloud sync: {backend_config.convex_url}")
            except Exception as e:
                logger.warning(f"Failed to connect to Convex (sync disabled): {e}")
                # Continue without cloud sync - SQLite works offline
                self.convex_client = None

        # Create SyncEngine BEFORE contexts so repos can use it
        if backend_config.uses_convex and self.convex_client:
            from src.shared.infra.sync import SyncEngine

            self._sync_engine = SyncEngine(connection, self.convex_client)
            sync_engine = self._sync_engine
            logger.info("SyncEngine created for SQLite-Convex cloud sync")

        # Create contexts with sync support
        self.sources_context = SourcesContext.create(
            connection=connection,
            convex_client=self.convex_client,
            backend_type=backend_type,
            sync_engine=sync_engine,
        )
        self.coding_context = CodingContext.create(
            connection=connection,
            convex_client=self.convex_client,
            backend_type=backend_type,
            sync_engine=sync_engine,
        )
        self.cases_context = CasesContext.create(
            connection=connection,
            convex_client=self.convex_client,
            backend_type=backend_type,
            sync_engine=sync_engine,
        )
        # ProjectsContext always uses SQLite for local project file management
        self.projects_context = ProjectsContext.create(
            connection=connection,
            convex_client=self.convex_client,
            backend_type=BackendType.SQLITE,
        )

        # Start sync engine after contexts are created
        if self._sync_engine is not None:
            self._sync_engine.start()
            logger.info("SyncEngine started")

        sync_status = "enabled" if self._sync_engine else "disabled"
        logger.debug(f"Created bounded contexts for project (cloud sync: {sync_status})")

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

        # Stop sync engine if running
        if self._sync_engine is not None:
            self._sync_engine.stop()
            self._sync_engine = None

        # Close Convex client if open
        if self.convex_client is not None:
            self.convex_client.close()
            self.convex_client = None

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

    # =========================================================================
    # Sync API (Public methods for MCP tools and UI)
    # =========================================================================

    def get_sync_engine(self):
        """
        Get the sync engine (public API).

        Used by command handlers and MCP tools.

        Returns:
            SyncEngine if cloud sync is enabled, None otherwise.
        """
        return self._sync_engine

    def get_sync_state(self):
        """
        Get current sync state (public API).

        Used by MCP tools to query sync status without
        accessing private attributes.

        Returns:
            SyncState if sync engine exists, None otherwise.
        """
        if self._sync_engine is None:
            return None
        return self._sync_engine.state

    def is_cloud_sync_enabled(self) -> bool:
        """
        Check if cloud sync is enabled.

        Returns:
            True if cloud sync is configured and enabled.
        """
        backend_config = self.settings_repo.get_backend_config()
        return backend_config.uses_convex

    def trigger_sync_pull(self) -> OperationResult:
        """
        Trigger a cloud sync pull operation.

        Delegates to the sync pull command handler.
        Used by UI and MCP tools to initiate sync.

        Returns:
            OperationResult from the sync pull operation.
        """
        if not self.is_cloud_sync_enabled():
            return OperationResult.failure(
                error="Cloud sync is not enabled",
                error_code="SYNC_DISABLED",
            )

        if self._sync_engine is None:
            return OperationResult.failure(
                error="Sync engine not initialized",
                error_code="SYNC_NOT_READY",
            )

        from src.shared.core.sync import SyncPullCommand
        from src.shared.infra.sync.commandHandlers import handle_sync_pull

        cmd = SyncPullCommand()
        return handle_sync_pull(cmd, self._sync_engine, self.event_bus)
