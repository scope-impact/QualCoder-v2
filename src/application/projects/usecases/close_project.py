"""
Close Project Use Case

Functional use case for closing the current project.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from returns.result import Failure, Result, Success

from src.application.lifecycle import ProjectLifecycle
from src.application.state import ProjectState
from src.contexts.projects.core.events import ProjectClosed

if TYPE_CHECKING:
    from src.application.event_bus import EventBus


def close_project(
    lifecycle: ProjectLifecycle,
    state: ProjectState,
    event_bus: EventBus,
) -> Result[None, str]:
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
        Success with None, or Failure with error message
    """
    # Step 1: Validate
    if state.project is None:
        return Failure("No project is currently open")

    # Step 2: Get path for event
    path = state.project.path

    # Step 3: Close database
    lifecycle.close_database()

    # Step 4: Clear state cache
    state.clear()

    # Step 5: Publish event
    event = ProjectClosed.create(path=path)
    event_bus.publish(event)

    return Success(None)
