"""
Navigate to Screen Use Case

Functional use case for navigating to a different screen.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from returns.result import Result, Success

from src.application.projects.commands import NavigateToScreenCommand
from src.application.state import ProjectState
from src.contexts.projects.core.events import ScreenChanged

if TYPE_CHECKING:
    from src.application.event_bus import EventBus


def navigate_to_screen(
    command: NavigateToScreenCommand,
    state: ProjectState,
    event_bus: EventBus,
) -> Result[ScreenChanged, str]:
    """
    Navigate to a different screen.

    Args:
        command: Command with target screen name
        state: Project state cache
        event_bus: Event bus for publishing events

    Returns:
        Success with ScreenChanged event
    """
    old_screen = state.current_screen
    new_screen = command.screen_name

    # Update state
    state.current_screen = new_screen

    # Publish event
    event = ScreenChanged.create(
        from_screen=old_screen,
        to_screen=new_screen,
    )
    event_bus.publish(event)

    return Success(event)
