"""
Create Project Use Case

Functional use case for creating a new project.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from returns.result import Failure, Result, Success

from src.application.lifecycle import ProjectLifecycle
from src.application.projects.commands import CreateProjectCommand
from src.application.state import ProjectState
from src.contexts.projects.core.derivers import ProjectState as DomainProjectState
from src.contexts.projects.core.derivers import derive_create_project
from src.contexts.projects.core.events import ProjectCreated

if TYPE_CHECKING:
    from src.application.event_bus import EventBus
    from src.contexts.projects.core.entities import Project


def create_project(
    command: CreateProjectCommand,
    lifecycle: ProjectLifecycle,
    state: ProjectState,
    event_bus: EventBus,
) -> Result[Project, str]:
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
        Success with Project entity, or Failure with error message
    """
    path = Path(command.path)

    # Step 1: Validate
    if not command.name or not command.name.strip():
        return Failure("Project name cannot be empty")

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
        return result

    event: ProjectCreated = result

    # Step 3: Create database file
    create_result = lifecycle.create_database(path, command.name.strip())
    if isinstance(create_result, Failure):
        return create_result

    project = create_result.unwrap()

    # Step 4: Update state cache
    state.clear()
    state.project = project
    state.add_to_recent(project)

    # Step 5: Publish event
    event_bus.publish(event)

    return Success(project)
