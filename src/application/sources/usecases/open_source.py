"""
Open Source Use Case

Functional use case for opening a source for viewing/coding.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from returns.result import Failure, Result, Success

from src.application.projects.commands import OpenSourceCommand
from src.application.state import ProjectState
from src.contexts.projects.core.derivers import ProjectState as DomainProjectState
from src.contexts.projects.core.derivers import derive_open_source
from src.contexts.projects.core.events import ScreenChanged, SourceOpened
from src.contexts.projects.core.failure_events import SourceNotOpened
from src.contexts.shared.core.types import SourceId

if TYPE_CHECKING:
    from src.application.event_bus import EventBus


def open_source(
    command: OpenSourceCommand,
    state: ProjectState,
    event_bus: EventBus,
) -> Result[SourceOpened, str]:
    """
    Open a source for viewing/coding.

    Functional use case following 5-step pattern:
    1. Validate project is open
    2. Derive SourceOpened event (pure)
    3. Update current source in state
    4. Navigate to coding screen
    5. Publish events

    Args:
        command: Command with source ID
        state: Project state cache
        event_bus: Event bus for publishing events

    Returns:
        Success with SourceOpened event, or Failure with error message
    """
    # Step 1: Validate
    if state.project is None:
        return Failure("No project is currently open")

    source_id = SourceId(value=command.source_id)

    # Step 2: Build domain state and derive event
    domain_state = DomainProjectState(
        path_exists=lambda _p: True,
        parent_writable=lambda _p: True,
        existing_sources=tuple(state.sources),
    )

    result = derive_open_source(source_id=source_id, state=domain_state)

    if isinstance(result, SourceNotOpened):
        return Failure(result.reason)

    event: SourceOpened = result

    # Step 3: Update current source in state
    source = state.get_source(command.source_id)
    if source:
        state.current_source = source

    # Publish source opened event
    event_bus.publish(event)

    # Step 4: Navigate to coding screen
    old_screen = state.current_screen
    state.current_screen = "coding"

    # Step 5: Publish screen changed event
    screen_event = ScreenChanged.create(
        from_screen=old_screen,
        to_screen="coding",
    )
    event_bus.publish(screen_event)

    return Success(event)
