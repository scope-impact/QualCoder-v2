"""
Open Project Use Case

Functional use case for opening an existing project.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from returns.result import Failure, Result, Success

from src.application.lifecycle import ProjectLifecycle
from src.application.projects.commands import OpenProjectCommand
from src.application.state import ProjectState
from src.contexts.projects.core.derivers import ProjectState as DomainProjectState
from src.contexts.projects.core.derivers import derive_open_project
from src.contexts.projects.core.entities import Project, ProjectId
from src.contexts.projects.core.events import ProjectOpened

if TYPE_CHECKING:
    from src.application.event_bus import EventBus


def open_project(
    command: OpenProjectCommand,
    lifecycle: ProjectLifecycle,
    state: ProjectState,
    event_bus: EventBus,
    get_contexts: callable,
) -> Result[Project, str]:
    """
    Open an existing project file.

    Functional use case following 5-step pattern:
    1. Validate path exists
    2. Derive event using domain deriver (pure)
    3. Open database connection
    4. Load data into state cache
    5. Publish event

    Args:
        command: Command with project path
        lifecycle: Project lifecycle for database operations
        state: Project state cache
        event_bus: Event bus for publishing events
        get_contexts: Callback to get bounded contexts after connection is established

    Returns:
        Success with Project entity, or Failure with error message
    """
    path = Path(command.path)

    # Step 1 & 2: Build domain state and derive event
    domain_state = DomainProjectState(
        path_exists=lambda p: p.exists(),
        parent_writable=lambda _p: True,
    )

    result = derive_open_project(path=path, state=domain_state)

    if isinstance(result, Failure):
        return result

    event: ProjectOpened = result

    # Step 3: Open database
    open_result = lifecycle.open_database(path)
    if isinstance(open_result, Failure):
        return open_result

    connection = open_result.unwrap()

    # Get contexts for loading data
    contexts = get_contexts(connection)
    sources_ctx = contexts.get("sources")
    cases_ctx = contexts.get("cases")
    folders_ctx = contexts.get("folders")
    projects_ctx = contexts.get("projects")

    # Load project metadata
    project: Project | None = None
    if projects_ctx and projects_ctx.project_repo:
        project = projects_ctx.project_repo.load(path)

    if project is None:
        project = Project(
            id=ProjectId.from_path(path),
            name=path.stem,
            path=path,
        )

    # Step 4: Update state cache
    state.clear()
    state.project = project.touch() if hasattr(project, "touch") else project

    # Load sources
    if sources_ctx and sources_ctx.source_repo:
        state.sources = sources_ctx.source_repo.get_all()

    # Load folders
    if folders_ctx and folders_ctx.folder_repo:
        state.folders = folders_ctx.folder_repo.get_all()

    # Load cases
    if cases_ctx and cases_ctx.case_repo:
        state.cases = cases_ctx.case_repo.get_all()

    state.add_to_recent(project)

    # Step 5: Publish event
    event_bus.publish(event)

    return Success(project)
