"""
Project Controller - Application Service

Orchestrates domain operations for project management by:
1. Loading state from repositories / file system
2. Calling pure domain derivers
3. Persisting changes on success
4. Publishing domain events

This is the "Imperative Shell" that coordinates the "Functional Core".
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any

from returns.result import Failure, Result, Success

from src.domain.cases.derivers import (
    CaseState,
    derive_create_case,
    derive_link_source_to_case,
    derive_remove_case,
    derive_set_case_attribute,
    derive_unlink_source_from_case,
    derive_update_case,
)
from src.domain.cases.entities import AttributeType, Case, CaseAttribute
from src.domain.cases.events import (
    CaseAttributeSet,
    CaseCreated,
    CaseRemoved,
    CaseUpdated,
    SourceLinkedToCase,
    SourceUnlinkedFromCase,
)
from src.domain.projects.derivers import (
    ProjectState,
    derive_add_source,
    derive_create_project,
    derive_open_project,
    derive_open_source,
    derive_remove_source,
)
from src.domain.projects.entities import (
    Project,
    ProjectId,
    ProjectSummary,
    RecentProject,
    Source,
    SourceStatus,
)
from src.domain.projects.events import (
    ProjectClosed,
    ProjectCreated,
    ProjectOpened,
    ScreenChanged,
    SourceAdded,
    SourceOpened,
    SourceRemoved,
)
from src.domain.shared.types import CaseId, SourceId

if TYPE_CHECKING:
    from src.application.event_bus import EventBus


# ============================================================
# Command DTOs
# ============================================================


@dataclass(frozen=True)
class CreateProjectCommand:
    """Command to create a new project."""

    name: str
    path: str  # String path for cross-platform compatibility
    memo: str | None = None


@dataclass(frozen=True)
class OpenProjectCommand:
    """Command to open an existing project."""

    path: str


@dataclass(frozen=True)
class AddSourceCommand:
    """Command to add a source file to the project."""

    source_path: str
    origin: str | None = None
    memo: str | None = None


@dataclass(frozen=True)
class RemoveSourceCommand:
    """Command to remove a source from the project."""

    source_id: int


@dataclass(frozen=True)
class OpenSourceCommand:
    """Command to open a source for viewing/coding."""

    source_id: int


@dataclass(frozen=True)
class NavigateToScreenCommand:
    """Command to navigate to a different screen."""

    screen_name: str


@dataclass(frozen=True)
class NavigateToSegmentCommand:
    """Command to navigate to a specific segment position in a source."""

    source_id: int
    start_pos: int
    end_pos: int
    highlight: bool = True


@dataclass(frozen=True)
class CreateCaseCommand:
    """Command to create a new case."""

    name: str
    description: str | None = None
    memo: str | None = None


@dataclass(frozen=True)
class UpdateCaseCommand:
    """Command to update an existing case."""

    case_id: int
    name: str
    description: str | None = None
    memo: str | None = None


@dataclass(frozen=True)
class RemoveCaseCommand:
    """Command to remove a case."""

    case_id: int


@dataclass(frozen=True)
class LinkSourceToCaseCommand:
    """Command to link a source to a case."""

    case_id: int
    source_id: int


@dataclass(frozen=True)
class UnlinkSourceFromCaseCommand:
    """Command to unlink a source from a case."""

    case_id: int
    source_id: int


@dataclass(frozen=True)
class SetCaseAttributeCommand:
    """Command to set an attribute on a case."""

    case_id: int
    attr_name: str
    attr_type: str  # text, number, date, boolean
    attr_value: Any


# ============================================================
# Controller Implementation
# ============================================================


class ProjectControllerImpl:
    """
    Implementation of the Project Controller.

    Coordinates between:
    - Domain derivers (pure business logic)
    - Repositories (data persistence)
    - Event bus (event publishing)
    - File system (for project/source operations)
    """

    def __init__(
        self,
        event_bus: EventBus,
        source_repo: Any | None = None,
        project_repo: Any | None = None,
        case_repo: Any | None = None,
    ) -> None:
        """
        Initialize the controller with dependencies.

        Args:
            event_bus: Event bus for publishing domain events
            source_repo: Optional repository for Source entities
            project_repo: Optional repository for Project metadata
            case_repo: Optional repository for Case entities
        """
        self._event_bus = event_bus
        self._source_repo = source_repo
        self._project_repo = project_repo
        self._case_repo = case_repo

        # Current project state
        self._current_project: Project | None = None
        self._current_screen: str | None = None
        self._current_source: Source | None = None
        self._sources: list[Source] = []
        self._cases: list[Case] = []
        self._recent_projects: list[RecentProject] = []

    # =========================================================================
    # Project Commands
    # =========================================================================

    def create_project(self, command: CreateProjectCommand) -> Result:
        """Create a new project file."""
        path = Path(command.path)

        # Build state with file system checks
        state = ProjectState(
            path_exists=lambda p: p.exists(),
            parent_writable=lambda p: p.exists() and p.is_dir(),
        )

        # Derive event or failure
        result = derive_create_project(
            name=command.name,
            path=path,
            memo=command.memo,
            owner=None,
            state=state,
        )

        if isinstance(result, Failure):
            return result

        event: ProjectCreated = result

        # Create the project entity
        project = Project(
            id=ProjectId.from_path(path),
            name=event.name,
            path=path,
            memo=event.memo,
            owner=event.owner,
        )

        # Persist project (would create .qda file via infrastructure)
        if self._project_repo:
            self._project_repo.create(project)

        # Update internal state
        self._current_project = project
        self._sources = []

        # Publish event
        self._event_bus.publish(event)

        return Success(project)

    def open_project(self, command: OpenProjectCommand) -> Result:
        """Open an existing project file."""
        path = Path(command.path)

        # Build state with file system checks
        state = ProjectState(
            path_exists=lambda p: p.exists(),
            parent_writable=lambda _p: True,
        )

        # Derive event or failure
        result = derive_open_project(
            path=path,
            state=state,
        )

        if isinstance(result, Failure):
            return result

        event: ProjectOpened = result

        # Load project from repository
        project: Project | None = None
        if self._project_repo:
            project = self._project_repo.load(path)

        if project is None:
            # Create minimal project from path
            project = Project(
                id=ProjectId.from_path(path),
                name=path.stem,
                path=path,
            )

        # Update internal state
        self._current_project = project.touch()
        self._load_sources()
        self._load_cases()

        # Add to recent projects
        self._add_to_recent(project)

        # Publish event
        self._event_bus.publish(event)

        return Success(project)

    def close_project(self) -> Result:
        """Close the current project."""
        if self._current_project is None:
            return Failure("No project is currently open")

        path = self._current_project.path

        # Clear state
        self._current_project = None
        self._sources = []
        self._cases = []

        # Publish event
        event = ProjectClosed.create(path=path)
        self._event_bus.publish(event)

        return Success(None)

    # =========================================================================
    # Source Commands
    # =========================================================================

    def add_source(self, command: AddSourceCommand) -> Result:
        """Add a source file to the current project."""
        if self._current_project is None:
            return Failure("No project is currently open")

        source_path = Path(command.source_path)

        # Build state
        state = ProjectState(
            path_exists=lambda p: p.exists(),
            parent_writable=lambda _p: True,
            existing_sources=tuple(self._sources),
        )

        # Derive event or failure
        result = derive_add_source(
            source_path=source_path,
            origin=command.origin,
            memo=command.memo,
            owner=None,
            state=state,
        )

        if isinstance(result, Failure):
            return result

        event: SourceAdded = result

        # Create source entity
        source = Source(
            id=event.source_id,
            name=event.name,
            source_type=event.source_type,
            status=SourceStatus.IMPORTED,
            file_path=event.file_path,
            file_size=event.file_size,
            origin=event.origin,
            memo=event.memo,
        )

        # Persist source
        if self._source_repo:
            self._source_repo.save(source)

        # Update internal state
        self._sources.append(source)

        # Publish event
        self._event_bus.publish(event)

        return Success(source)

    def remove_source(self, command: RemoveSourceCommand) -> Result:
        """Remove a source from the current project."""
        if self._current_project is None:
            return Failure("No project is currently open")

        source_id = SourceId(value=command.source_id)

        # Build state
        state = ProjectState(
            path_exists=lambda _p: True,
            parent_writable=lambda _p: True,
            existing_sources=tuple(self._sources),
        )

        # Derive event or failure
        result = derive_remove_source(
            source_id=source_id,
            state=state,
        )

        if isinstance(result, Failure):
            return result

        event: SourceRemoved = result

        # Delete from repository
        if self._source_repo:
            self._source_repo.delete(source_id)

        # Update internal state
        self._sources = [s for s in self._sources if s.id != source_id]

        # Publish event
        self._event_bus.publish(event)

        return Success(event)

    def open_source(self, command: OpenSourceCommand) -> Result:
        """Open a source for viewing/coding."""
        if self._current_project is None:
            return Failure("No project is currently open")

        source_id = SourceId(value=command.source_id)

        # Build state
        state = ProjectState(
            path_exists=lambda _p: True,
            parent_writable=lambda _p: True,
            existing_sources=tuple(self._sources),
        )

        # Derive event or failure
        result = derive_open_source(
            source_id=source_id,
            state=state,
        )

        if isinstance(result, Failure):
            return result

        event: SourceOpened = result

        # Update current source
        source = next((s for s in self._sources if s.id == source_id), None)
        if source:
            self._current_source = source

        # Publish source opened event
        self._event_bus.publish(event)

        # Navigate to coding screen
        old_screen = self._current_screen
        self._current_screen = "coding"

        # Publish screen changed event
        screen_event = ScreenChanged.create(
            from_screen=old_screen,
            to_screen="coding",
        )
        self._event_bus.publish(screen_event)

        return Success(event)

    # =========================================================================
    # Navigation Commands
    # =========================================================================

    def navigate_to_screen(self, command: NavigateToScreenCommand) -> Result:
        """Navigate to a different screen."""
        old_screen = self._current_screen
        new_screen = command.screen_name

        # Update state
        self._current_screen = new_screen

        # Publish event
        event = ScreenChanged.create(
            from_screen=old_screen,
            to_screen=new_screen,
        )
        self._event_bus.publish(event)

        return Success(event)

    def navigate_to_segment(self, command: NavigateToSegmentCommand) -> Result:
        """
        Navigate to a specific segment position in a source.

        This command:
        1. Opens the specified source
        2. Navigates to the coding screen
        3. Scrolls to and highlights the specified position
        """
        from src.domain.projects.events import NavigatedToSegment

        # Step 1: Validate - find the source
        source_id = SourceId(value=command.source_id)
        source = next((s for s in self._sources if s.id == source_id), None)

        if source is None:
            return Failure(f"Source {command.source_id} not found")

        # Step 2: Open the source
        self._current_source = source

        # Step 3: Navigate to coding screen
        old_screen = self._current_screen
        self._current_screen = "coding"

        # Publish screen changed event
        screen_event = ScreenChanged.create(
            from_screen=old_screen,
            to_screen="coding",
        )
        self._event_bus.publish(screen_event)

        # Step 4: Publish navigation event
        nav_event = NavigatedToSegment.create(
            source_id=source_id,
            position_start=command.start_pos,
            position_end=command.end_pos,
            highlight=command.highlight,
        )
        self._event_bus.publish(nav_event)

        return Success(nav_event)

    # =========================================================================
    # Case Commands
    # =========================================================================

    def create_case(self, command: CreateCaseCommand) -> Result:
        """Create a new case in the current project."""
        if self._current_project is None:
            return Failure("No project is currently open")

        # Build state
        state = CaseState(existing_cases=tuple(self._cases))

        # Derive event or failure
        result = derive_create_case(
            name=command.name,
            description=command.description,
            memo=command.memo,
            state=state,
        )

        if isinstance(result, Failure):
            return result

        event: CaseCreated = result

        # Create case entity
        case = Case(
            id=event.case_id,
            name=event.name,
            description=event.description,
            memo=event.memo,
        )

        # Persist case
        if self._case_repo:
            self._case_repo.save(case)

        # Update internal state
        self._cases.append(case)

        # Publish event
        self._event_bus.publish(event)

        return Success(case)

    def update_case(self, command: UpdateCaseCommand) -> Result:
        """Update an existing case."""
        if self._current_project is None:
            return Failure("No project is currently open")

        case_id = CaseId(value=command.case_id)

        # Build state
        state = CaseState(existing_cases=tuple(self._cases))

        # Derive event or failure
        result = derive_update_case(
            case_id=case_id,
            name=command.name,
            description=command.description,
            memo=command.memo,
            state=state,
        )

        if isinstance(result, Failure):
            return result

        event: CaseUpdated = result

        # Update case entity
        updated_case = Case(
            id=event.case_id,
            name=event.name,
            description=event.description,
            memo=event.memo,
        )

        # Persist case
        if self._case_repo:
            self._case_repo.save(updated_case)

        # Update internal state
        self._cases = [c if c.id != case_id else updated_case for c in self._cases]

        # Publish event
        self._event_bus.publish(event)

        return Success(updated_case)

    def remove_case(self, command: RemoveCaseCommand) -> Result:
        """Remove a case from the current project."""
        if self._current_project is None:
            return Failure("No project is currently open")

        case_id = CaseId(value=command.case_id)

        # Build state
        state = CaseState(existing_cases=tuple(self._cases))

        # Derive event or failure
        result = derive_remove_case(
            case_id=case_id,
            state=state,
        )

        if isinstance(result, Failure):
            return result

        event: CaseRemoved = result

        # Delete from repository
        if self._case_repo:
            self._case_repo.delete(case_id)

        # Update internal state
        self._cases = [c for c in self._cases if c.id != case_id]

        # Publish event
        self._event_bus.publish(event)

        return Success(event)

    def link_source_to_case(self, command: LinkSourceToCaseCommand) -> Result:
        """Link a source to a case."""
        if self._current_project is None:
            return Failure("No project is currently open")

        case_id = CaseId(value=command.case_id)
        source_id = SourceId(value=command.source_id)

        # Verify source exists
        source = next((s for s in self._sources if s.id == source_id), None)
        if source is None:
            return Failure(f"Source {command.source_id} not found")

        # Build state with fresh case data from repository
        if self._case_repo:
            self._cases = self._case_repo.get_all()
        state = CaseState(existing_cases=tuple(self._cases))

        # Derive event or failure
        result = derive_link_source_to_case(
            case_id=case_id,
            source_id=source_id,
            state=state,
        )

        if isinstance(result, Failure):
            return result

        event: SourceLinkedToCase = result

        # Persist link
        if self._case_repo:
            self._case_repo.link_source(case_id, source_id)
            # Refresh cases to get updated source_ids
            self._cases = self._case_repo.get_all()

        # Publish event
        self._event_bus.publish(event)

        return Success(event)

    def unlink_source_from_case(self, command: UnlinkSourceFromCaseCommand) -> Result:
        """Unlink a source from a case."""
        if self._current_project is None:
            return Failure("No project is currently open")

        case_id = CaseId(value=command.case_id)
        source_id = SourceId(value=command.source_id)

        # Build state with fresh case data from repository
        if self._case_repo:
            self._cases = self._case_repo.get_all()
        state = CaseState(existing_cases=tuple(self._cases))

        # Derive event or failure
        result = derive_unlink_source_from_case(
            case_id=case_id,
            source_id=source_id,
            state=state,
        )

        if isinstance(result, Failure):
            return result

        event: SourceUnlinkedFromCase = result

        # Remove link
        if self._case_repo:
            self._case_repo.unlink_source(case_id, source_id)
            # Refresh cases to get updated source_ids
            self._cases = self._case_repo.get_all()

        # Publish event
        self._event_bus.publish(event)

        return Success(event)

    def set_case_attribute(self, command: SetCaseAttributeCommand) -> Result:
        """Set an attribute on a case."""
        if self._current_project is None:
            return Failure("No project is currently open")

        case_id = CaseId(value=command.case_id)

        # Build state with fresh case data from repository
        if self._case_repo:
            self._cases = self._case_repo.get_all()
        state = CaseState(existing_cases=tuple(self._cases))

        # Derive event or failure
        result = derive_set_case_attribute(
            case_id=case_id,
            attr_name=command.attr_name,
            attr_type=command.attr_type,
            attr_value=command.attr_value,
            state=state,
        )

        if isinstance(result, Failure):
            return result

        event: CaseAttributeSet = result

        # Persist attribute
        if self._case_repo:
            attr = CaseAttribute(
                name=event.attr_name,
                attr_type=AttributeType(event.attr_type),
                value=event.attr_value,
            )
            self._case_repo.save_attribute(case_id, attr)
            # Refresh cases to get updated attributes
            self._cases = self._case_repo.get_all()

        # Publish event
        self._event_bus.publish(event)

        return Success(event)

    # =========================================================================
    # Queries
    # =========================================================================

    def get_current_project(self) -> Project | None:
        """Get the currently open project."""
        return self._current_project

    def get_current_source(self) -> Source | None:
        """Get the currently open source."""
        return self._current_source

    def get_sources(self) -> list[Source]:
        """Get all sources in the current project."""
        return list(self._sources)

    def get_source(self, source_id: int) -> Source | None:
        """Get a specific source by ID."""
        sid = SourceId(value=source_id)
        return next((s for s in self._sources if s.id == sid), None)

    def get_sources_by_type(self, source_type: str) -> list[Source]:
        """Get sources filtered by type."""
        return [s for s in self._sources if s.source_type.value == source_type]

    def get_cases(self) -> list[Case]:
        """Get all cases in the current project."""
        return list(self._cases)

    def get_case(self, case_id: int) -> Case | None:
        """Get a specific case by ID."""
        cid = CaseId(value=case_id)
        return next((c for c in self._cases if c.id == cid), None)

    def get_case_with_sources(self, case_id: int) -> tuple[Case, list[Source]] | None:
        """
        Get a case with its linked Source entities.

        Args:
            case_id: The case ID to look up

        Returns:
            Tuple of (Case, list of linked Sources) or None if not found
        """
        cid = CaseId(value=case_id)
        case = next((c for c in self._cases if c.id == cid), None)
        if case is None:
            return None

        # Get Source entities for each linked source_id
        linked_sources = []
        for sid in case.source_ids:
            source = next((s for s in self._sources if s.id.value == sid), None)
            if source:
                linked_sources.append(source)

        return (case, linked_sources)

    def get_all_cases_with_sources(self) -> list[tuple[Case, list[Source]]]:
        """
        Get all cases with their linked Source entities.

        Returns:
            List of tuples (Case, list of linked Sources)
        """
        result = []
        for case in self._cases:
            linked_sources = []
            for sid in case.source_ids:
                source = next((s for s in self._sources if s.id.value == sid), None)
                if source:
                    linked_sources.append(source)
            result.append((case, linked_sources))
        return result

    def get_project_summary(self) -> ProjectSummary | None:
        """Get summary statistics for the current project."""
        if self._current_project is None:
            return None

        from src.domain.projects.entities import SourceType

        return ProjectSummary(
            total_sources=len(self._sources),
            text_count=sum(
                1 for s in self._sources if s.source_type == SourceType.TEXT
            ),
            audio_count=sum(
                1 for s in self._sources if s.source_type == SourceType.AUDIO
            ),
            video_count=sum(
                1 for s in self._sources if s.source_type == SourceType.VIDEO
            ),
            image_count=sum(
                1 for s in self._sources if s.source_type == SourceType.IMAGE
            ),
            pdf_count=sum(1 for s in self._sources if s.source_type == SourceType.PDF),
            total_codes=0,  # Would come from coding context
            total_segments=0,
        )

    def get_recent_projects(self) -> list[RecentProject]:
        """Get list of recently opened projects."""
        return list(self._recent_projects)

    def get_current_screen(self) -> str | None:
        """Get the current screen name."""
        return self._current_screen

    # =========================================================================
    # Agent API (for AI context queries)
    # =========================================================================

    def get_project_context(self) -> dict[str, Any]:
        """
        Get the current project context for AI agent.

        Returns dict with:
        - project_name, project_path
        - source_count, sources list
        - current_screen
        """
        if self._current_project is None:
            return {"project_open": False}

        return {
            "project_open": True,
            "project_name": self._current_project.name,
            "project_path": str(self._current_project.path),
            "source_count": len(self._sources),
            "sources": [
                {
                    "id": s.id.value,
                    "name": s.name,
                    "type": s.source_type.value,
                    "status": s.status.value,
                }
                for s in self._sources
            ],
            "case_count": len(self._cases),
            "cases": [
                {
                    "id": c.id.value,
                    "name": c.name,
                    "description": c.description,
                }
                for c in self._cases
            ],
            "current_screen": self._current_screen,
        }

    # =========================================================================
    # Private Helpers
    # =========================================================================

    def _load_sources(self) -> None:
        """Load sources from repository for current project."""
        if self._source_repo:
            self._sources = self._source_repo.get_all()
        else:
            self._sources = []

    def _load_cases(self) -> None:
        """Load cases from repository for current project."""
        if self._case_repo:
            self._cases = self._case_repo.get_all()
        else:
            self._cases = []

    def _add_to_recent(self, project: Project) -> None:
        """Add project to recent projects list."""
        from datetime import UTC, datetime

        recent = RecentProject(
            path=project.path,
            name=project.name,
            last_opened=datetime.now(UTC),
        )

        # Remove if already exists
        self._recent_projects = [
            r for r in self._recent_projects if r.path != project.path
        ]

        # Add to front
        self._recent_projects.insert(0, recent)

        # Limit to 10 recent projects
        self._recent_projects = self._recent_projects[:10]
