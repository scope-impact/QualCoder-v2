"""
Navigate to Segment Use Case

Functional use case for navigating to a specific segment in a source.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from returns.result import Failure, Result, Success

from src.application.projects.commands import NavigateToSegmentCommand
from src.application.state import ProjectState
from src.contexts.projects.core.events import NavigatedToSegment, ScreenChanged
from src.contexts.shared.core.types import SourceId

if TYPE_CHECKING:
    from src.application.event_bus import EventBus


def navigate_to_segment(
    command: NavigateToSegmentCommand,
    state: ProjectState,
    event_bus: EventBus,
) -> Result[NavigatedToSegment, str]:
    """
    Navigate to a specific segment position in a source.

    This will:
    1. Open the specified source
    2. Navigate to the coding screen
    3. Scroll to and highlight the specified position

    Args:
        command: Command with source ID and position
        state: Project state cache
        event_bus: Event bus for publishing events

    Returns:
        Success with NavigatedToSegment event, or Failure with error message
    """
    # Validate project is open
    if state.project is None:
        return Failure("No project is currently open")

    source_id = SourceId(value=command.source_id)

    # Find the source
    source = state.get_source(command.source_id)
    if source is None:
        return Failure(f"Source {command.source_id} not found")

    # Open the source
    state.current_source = source

    # Navigate to coding screen
    old_screen = state.current_screen
    state.current_screen = "coding"

    # Publish screen changed event
    screen_event = ScreenChanged.create(
        from_screen=old_screen,
        to_screen="coding",
    )
    event_bus.publish(screen_event)

    # Publish navigation event
    nav_event = NavigatedToSegment.create(
        source_id=source_id,
        position_start=command.start_pos,
        position_end=command.end_pos,
        highlight=command.highlight,
    )
    event_bus.publish(nav_event)

    return Success(nav_event)
