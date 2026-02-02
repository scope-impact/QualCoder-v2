"""
Base Coordinator Infrastructure.

Provides shared infrastructure for all per-context coordinators.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.application.contexts import (
        CasesContext,
        CodingContext,
        ProjectsContext,
        SourcesContext,
    )
    from src.application.event_bus import EventBus
    from src.application.lifecycle import ProjectLifecycle
    from src.application.projects.signal_bridge import ProjectSignalBridge
    from src.application.state import ProjectState
    from src.contexts.settings.infra import UserSettingsRepository


@dataclass
class CoordinatorInfrastructure:
    """
    Shared infrastructure passed to all coordinators.

    This dataclass holds the core dependencies that all coordinators need:
    - event_bus: For publishing domain events
    - state: In-memory cache of project data
    - lifecycle: Database connection management
    - settings_repo: User settings persistence
    - signal_bridge: Qt signal bridge for UI updates (optional)

    Contexts are populated when a project is opened and cleared when closed.
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

    def clear_contexts(self) -> None:
        """Clear bounded context objects when project closes."""
        self.sources_context = None
        self.cases_context = None
        self.coding_context = None
        self.projects_context = None


class BaseCoordinator:
    """
    Base class for all per-context coordinators.

    Provides access to shared infrastructure via the _infra property.
    Sub-coordinators should inherit from this and implement their
    context-specific methods.
    """

    def __init__(self, infra: CoordinatorInfrastructure) -> None:
        """
        Initialize with shared infrastructure.

        Args:
            infra: CoordinatorInfrastructure instance shared across all coordinators
        """
        self._infra = infra

    @property
    def state(self) -> ProjectState:
        """Get the project state cache."""
        return self._infra.state

    @property
    def event_bus(self) -> EventBus:
        """Get the event bus."""
        return self._infra.event_bus

    @property
    def lifecycle(self) -> ProjectLifecycle:
        """Get the project lifecycle manager."""
        return self._infra.lifecycle

    @property
    def settings_repo(self) -> UserSettingsRepository:
        """Get the settings repository."""
        return self._infra.settings_repo

    @property
    def signal_bridge(self) -> ProjectSignalBridge | None:
        """Get the signal bridge (None if Qt not available)."""
        return self._infra.signal_bridge

    @property
    def sources_context(self) -> SourcesContext | None:
        """Get the Sources context (None if no project open)."""
        return self._infra.sources_context

    @property
    def cases_context(self) -> CasesContext | None:
        """Get the Cases context (None if no project open)."""
        return self._infra.cases_context

    @property
    def coding_context(self) -> CodingContext | None:
        """Get the Coding context (None if no project open)."""
        return self._infra.coding_context

    @property
    def projects_context(self) -> ProjectsContext | None:
        """Get the Projects context (None if no project open)."""
        return self._infra.projects_context
