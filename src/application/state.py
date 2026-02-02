"""
Application State - In-Memory Cache for Project Data

Separates caching concerns from controllers and persistence.
ProjectState holds the current session state including:
- Current project and screen
- Loaded entities (sources, cases, folders)
- Current source being viewed

This is a pure data structure with no behavior - just state management.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.contexts.cases.core.entities import Case
    from src.contexts.projects.core.entities import (
        Folder,
        Project,
        RecentProject,
        Source,
    )


@dataclass
class ProjectState:
    """
    In-memory state for the currently open project.

    This dataclass holds all the loaded data for the current session.
    It is managed by the Coordinator and passed to use cases.

    Attributes:
        project: Currently open project, or None if no project is open
        sources: All sources loaded from the project
        cases: All cases loaded from the project
        folders: All folders loaded from the project
        current_screen: Name of the currently active screen
        current_source: Source currently open for viewing/coding
        recent_projects: List of recently opened projects
    """

    project: Project | None = None
    sources: list[Source] = field(default_factory=list)
    cases: list[Case] = field(default_factory=list)
    folders: list[Folder] = field(default_factory=list)
    current_screen: str | None = None
    current_source: Source | None = None
    recent_projects: list[RecentProject] = field(default_factory=list)

    @property
    def is_project_open(self) -> bool:
        """Check if a project is currently open."""
        return self.project is not None

    def clear(self) -> None:
        """Clear all project-specific state."""
        self.project = None
        self.sources = []
        self.cases = []
        self.folders = []
        self.current_screen = None
        self.current_source = None

    def add_source(self, source: Source) -> None:
        """Add a source to the state."""
        self.sources.append(source)

    def remove_source(self, source_id: int) -> None:
        """Remove a source from the state by ID."""
        from src.contexts.shared.core.types import SourceId

        sid = SourceId(value=source_id)
        self.sources = [s for s in self.sources if s.id != sid]

    def update_source(self, source: Source) -> None:
        """Update a source in the state."""
        self.sources = [s if s.id != source.id else source for s in self.sources]

    def get_source(self, source_id: int) -> Source | None:
        """Get a source by ID."""
        from src.contexts.shared.core.types import SourceId

        sid = SourceId(value=source_id)
        return next((s for s in self.sources if s.id == sid), None)

    def add_case(self, case: Case) -> None:
        """Add a case to the state."""
        self.cases.append(case)

    def remove_case(self, case_id: int) -> None:
        """Remove a case from the state by ID."""
        from src.contexts.shared.core.types import CaseId

        cid = CaseId(value=case_id)
        self.cases = [c for c in self.cases if c.id != cid]

    def update_case(self, case: Case) -> None:
        """Update a case in the state."""
        self.cases = [c if c.id != case.id else case for c in self.cases]

    def get_case(self, case_id: int) -> Case | None:
        """Get a case by ID."""
        from src.contexts.shared.core.types import CaseId

        cid = CaseId(value=case_id)
        return next((c for c in self.cases if c.id == cid), None)

    def add_folder(self, folder: Folder) -> None:
        """Add a folder to the state."""
        self.folders.append(folder)

    def remove_folder(self, folder_id: int) -> None:
        """Remove a folder from the state by ID."""
        from src.contexts.shared.core.types import FolderId

        fid = FolderId(value=folder_id)
        self.folders = [f for f in self.folders if f.id != fid]

    def update_folder(self, folder: Folder) -> None:
        """Update a folder in the state."""
        self.folders = [f if f.id != folder.id else folder for f in self.folders]

    def get_folder(self, folder_id: int) -> Folder | None:
        """Get a folder by ID."""
        from src.contexts.shared.core.types import FolderId

        fid = FolderId(value=folder_id)
        return next((f for f in self.folders if f.id == fid), None)

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
