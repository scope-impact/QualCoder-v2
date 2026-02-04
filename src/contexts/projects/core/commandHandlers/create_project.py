"""
Create Project Use Case

Functional use case for creating a new project.
Returns OperationResult with error codes and suggestions.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from returns.result import Failure

from src.contexts.projects.core.commands import CreateProjectCommand
from src.contexts.projects.core.derivers import ProjectState as DomainProjectState
from src.contexts.projects.core.derivers import derive_create_project
from src.contexts.projects.core.events import ProjectCreated
from src.shared.common.operation_result import OperationResult
from src.shared.infra.lifecycle import ProjectLifecycle
from src.shared.infra.state import ProjectState

if TYPE_CHECKING:
    from src.shared.infra.event_bus import EventBus


def create_project(
    command: CreateProjectCommand,
    lifecycle: ProjectLifecycle,
    state: ProjectState,
    event_bus: EventBus,
) -> OperationResult:
    """
    Create a new project file.

    Functional use case following 5-step pattern:
    1. Validate input
    2. Derive event using domain deriver (pure)
    3. Create database file
    4. Update state cache
    5. Publish event

    Args:
        command: Command with project name and path
        lifecycle: Project lifecycle for database operations
        state: Project state cache
        event_bus: Event bus for publishing events

    Returns:
        OperationResult with Project entity on success, or error details on failure
    """
    path = Path(command.path)

    # Step 1: Validate
    if not command.name or not command.name.strip():
        return OperationResult.fail(
            error="Project name cannot be empty",
            error_code="PROJECT_NOT_CREATED/EMPTY_NAME",
        )

    # Step 2: Build domain state and derive event
    domain_state = DomainProjectState(
        path_exists=lambda p: p.exists(),
        parent_writable=lambda p: p.exists() and p.is_dir(),
    )

    result = derive_create_project(
        name=command.name.strip(),
        path=path,
        memo=command.memo,
        owner=None,
        state=domain_state,
    )

    if isinstance(result, Failure):
        return OperationResult.fail(
            error=result.failure(),
            error_code="PROJECT_NOT_CREATED/DERIVER_FAILED",
        )

    event: ProjectCreated = result

    # Step 3: Create database file
    create_result = lifecycle.create_database(path, command.name.strip())
    if isinstance(create_result, Failure):
        return OperationResult.fail(
            error=create_result.failure(),
            error_code="PROJECT_NOT_CREATED/DB_CREATION_FAILED",
        )

    project = create_result.unwrap()

    # Step 4: Update state cache
    state.clear()
    state.project = project
    state.add_to_recent(project)

    # Step 5: Publish event
    event_bus.publish(event)

    return OperationResult.ok(data=project)
