"""
Session State - Minimal Session Tracking

Following DDD workshop pattern: repositories are the source of truth for data,
state only tracks session-level information (what's open, what screen we're on).

Architecture:
    - Repos are source of truth (via bounded contexts)
    - SessionState tracks current session (project, screen, source being viewed)
    - ViewModels query repos directly (CQRS pattern)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from src.shared.common.types import SourceId

if TYPE_CHECKING:
    from src.contexts.projects.core.entities import (
        Project,
        RecentProject,
    )


@dataclass
class ProjectState:
    """
    Session state for the currently open project.

    This class tracks minimal session information:
    - project: Currently open project
    - current_screen: Active screen name
    - current_source_id: ID of source being viewed (repos have full entity)
    - recent_projects: Recently opened projects

    IMPORTANT: Repositories are the source of truth for entity data.
    Query repos directly instead of accessing cached lists.

    Attributes:
        project: Currently open project, or None if no project is open
        current_screen: Name of the currently active screen
        current_source_id: ID of source currently open for viewing/coding
        recent_projects: List of recently opened projects
    """

    project: Project | None = None
    current_screen: str | None = None
    current_source_id: SourceId | None = None
    recent_projects: list[RecentProject] = field(default_factory=list)

    @property
    def is_project_open(self) -> bool:
        """Check if a project is currently open."""
        return self.project is not None

    def clear(self) -> None:
        """Clear all project-specific state."""
        self.project = None
        self.current_screen = None
        self.current_source_id = None

    # =========================================================================
    # Recent Projects
    # =========================================================================

    def add_to_recent(self, project: Project) -> None:
        """Add a project to the recent projects list."""
        from datetime import UTC, datetime

        from src.contexts.projects.core.entities import RecentProject

        recent = RecentProject(
            path=project.path,
            name=project.name,
            last_opened=datetime.now(UTC),
        )

        # Remove if already exists
        self.recent_projects = [
            r for r in self.recent_projects if r.path != project.path
        ]

        # Add to front
        self.recent_projects.insert(0, recent)

        # Limit to 10 recent projects
        self.recent_projects = self.recent_projects[:10]
