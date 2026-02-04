"""
Close Project Use Case

Functional use case for closing the current project.
Returns OperationResult with error codes and suggestions.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from src.contexts.projects.core.events import ProjectClosed
from src.shared.common.operation_result import OperationResult
from src.shared.infra.lifecycle import ProjectLifecycle
from src.shared.infra.state import ProjectState

if TYPE_CHECKING:
    from src.shared.infra.event_bus import EventBus


def close_project(
    lifecycle: ProjectLifecycle,
    state: ProjectState,
    event_bus: EventBus,
) -> OperationResult:
    """
    Close the current project.

    Functional use case following 5-step pattern:
    1. Validate a project is open
    2. Get path for event
    3. Close database connection
    4. Clear state cache
    5. Publish event

    Args:
        lifecycle: Project lifecycle for database operations
        state: Project state cache
        event_bus: Event bus for publishing events

    Returns:
        OperationResult with None on success, or error details on failure
    """
    # Step 1: Validate
    if state.project is None:
        return OperationResult.fail(
            error="No project is currently open",
            error_code="PROJECT_NOT_CLOSED/NO_PROJECT",
        )

    # Step 2: Get path for event
    path = state.project.path

    # Step 3: Close database
    lifecycle.close_database()

    # Step 4: Clear state cache
    state.clear()

    # Step 5: Publish event
    event = ProjectClosed.create(path=path)
    event_bus.publish(event)

    return OperationResult.ok()
