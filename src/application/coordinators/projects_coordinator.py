"""
Projects Coordinator - Project Lifecycle Management.

Handles project open/create/close operations and manages
bounded context lifecycle.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from returns.result import Result

from src.application.coordinators.base import BaseCoordinator

if TYPE_CHECKING:
    from src.contexts.projects.core.entities import (
        Project,
        ProjectSummary,
        RecentProject,
    )


class ProjectsCoordinator(BaseCoordinator):
    """
    Coordinator for project lifecycle operations.

    Manages:
    - Opening existing projects
    - Creating new projects
    - Closing projects
    - Project queries (summary, context, recent)

    Also responsible for creating/clearing bounded contexts
    when projects are opened/closed.
    """

    # =========================================================================
    # Project Commands
    # =========================================================================

    def open_project(self, path: str) -> Result:
        """
        Open an existing project.

        Args:
            path: Path to the project file (.qda)

        Returns:
            Success with project, or Failure with error
        """
        from src.application.projects.commands import OpenProjectCommand
        from src.application.projects.usecases import open_project

        command = OpenProjectCommand(path=path)
        return open_project(
            command=command,
            lifecycle=self.lifecycle,
            state=self.state,
            event_bus=self.event_bus,
            get_contexts=self._get_contexts,
        )

    def create_project(self, name: str, path: str) -> Result:
        """
        Create a new project.

        Args:
            name: Project name
            path: Path for the new project file

        Returns:
            Success with project, or Failure with error
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

    def close_project(self) -> Result:
        """Close the current project."""
        from src.application.projects.usecases import close_project

        result = close_project(
            lifecycle=self.lifecycle,
            state=self.state,
            event_bus=self.event_bus,
        )
        self._infra.clear_contexts()
        return result

    # =========================================================================
    # Project Queries
    # =========================================================================

    def get_current_project(self) -> Project | None:
        """Get the currently open project."""
        return self.state.project

    def get_recent_projects(self) -> list[RecentProject]:
        """Get list of recently opened projects."""
        return list(self.state.recent_projects)

    def get_project_summary(self) -> ProjectSummary | None:
        """Get summary statistics for the current project."""
        from src.contexts.projects.core.entities import ProjectSummary, SourceType

        if self.state.project is None:
            return None

        return ProjectSummary(
            total_sources=len(self.state.sources),
            text_count=sum(
                1 for s in self.state.sources if s.source_type == SourceType.TEXT
            ),
            audio_count=sum(
                1 for s in self.state.sources if s.source_type == SourceType.AUDIO
            ),
            video_count=sum(
                1 for s in self.state.sources if s.source_type == SourceType.VIDEO
            ),
            image_count=sum(
                1 for s in self.state.sources if s.source_type == SourceType.IMAGE
            ),
            pdf_count=sum(
                1 for s in self.state.sources if s.source_type == SourceType.PDF
            ),
            total_codes=0,  # Would come from coding context
            total_segments=0,
        )

    def get_project_context(self) -> dict[str, Any]:
        """
        Get current project context for AI agent.

        Returns dict with:
        - project_name, project_path
        - source_count, sources list
        - current_screen
        """
        if self.state.project is None:
            return {"project_open": False}

        return {
            "project_open": True,
            "project_name": self.state.project.name,
            "project_path": str(self.state.project.path),
            "source_count": len(self.state.sources),
            "sources": [
                {
                    "id": s.id.value,
                    "name": s.name,
                    "type": s.source_type.value,
                    "status": s.status.value,
                }
                for s in self.state.sources
            ],
            "case_count": len(self.state.cases),
            "cases": [
                {
                    "id": c.id.value,
                    "name": c.name,
                    "description": c.description,
                }
                for c in self.state.cases
            ],
            "current_screen": self.state.current_screen,
        }

    # =========================================================================
    # Context Management
    # =========================================================================

    def _create_contexts(self, connection) -> None:
        """
        Create bounded context objects for the open project.

        Called after a project is successfully opened.
        """
        from src.application.contexts import (
            CasesContext,
            CodingContext,
            ProjectsContext,
            SourcesContext,
        )

        self._infra.sources_context = SourcesContext.create(connection)
        self._infra.coding_context = CodingContext.create(connection)
        self._infra.cases_context = CasesContext.create(connection)
        self._infra.projects_context = ProjectsContext.create(connection)

    def _get_contexts(self, connection) -> dict:
        """
        Get context dict for use cases.

        Called by use cases to get contexts after connection is established.
        """
        self._create_contexts(connection)
        return {
            "sources": self._infra.sources_context,
            "cases": self._infra.cases_context,
            "coding": self._infra.coding_context,
            "folders": self._infra.sources_context,  # Folders are in sources context
            "projects": self._infra.projects_context,
        }
