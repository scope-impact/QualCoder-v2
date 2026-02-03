"""
Open Project Use Case

Functional use case for opening an existing project.
Returns OperationResult with error codes and suggestions.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from returns.result import Failure

from src.contexts.projects.core.commands import OpenProjectCommand
from src.contexts.projects.core.derivers import ProjectState as DomainProjectState
from src.contexts.projects.core.derivers import derive_open_project
from src.contexts.projects.core.entities import Project, ProjectId
from src.contexts.projects.core.events import ProjectOpened
from src.shared.common.operation_result import OperationResult
from src.shared.infra.lifecycle import ProjectLifecycle
from src.shared.infra.state import ProjectState

if TYPE_CHECKING:
    from src.shared.infra.event_bus import EventBus


def open_project(
    command: OpenProjectCommand,
    lifecycle: ProjectLifecycle,
    state: ProjectState,
    event_bus: EventBus,
    get_contexts: callable,
) -> OperationResult:
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
        OperationResult with Project entity on success, or error details on failure
    """
    path = Path(command.path)

    # Step 1 & 2: Build domain state and derive event
    domain_state = DomainProjectState(
        path_exists=lambda p: p.exists(),
        parent_writable=lambda _p: True,
    )

    result = derive_open_project(path=path, state=domain_state)

    if isinstance(result, Failure):
        return OperationResult.fail(
            error=result.failure(),
            error_code="PROJECT_NOT_OPENED/DERIVER_FAILED",
        )

    event: ProjectOpened = result

    # Step 3: Open database
    open_result = lifecycle.open_database(path)
    if isinstance(open_result, Failure):
        return OperationResult.fail(
            error=open_result.failure(),
            error_code="PROJECT_NOT_OPENED/DB_OPEN_FAILED",
        )

    connection = open_result.unwrap()

    # Get contexts for loading data
    contexts = get_contexts(connection)
    _sources_ctx = contexts.get("sources")  # Reserved for future use
    _cases_ctx = contexts.get("cases")  # Reserved for future use
    _folders_ctx = contexts.get("folders")  # Reserved for future use
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

    # Step 4: Update state (minimal session tracking only)
    state.clear()
    state.project = project.touch() if hasattr(project, "touch") else project
    state.add_to_recent(project)

    # Step 5: Publish event
    event_bus.publish(event)

    return OperationResult.ok(data=project)
