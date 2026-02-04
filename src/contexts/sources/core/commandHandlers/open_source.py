"""
Open Source Use Case

Functional use case for opening a source for viewing/coding.
Returns OperationResult with error codes and suggestions.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from src.contexts.projects.core.commands import OpenSourceCommand
from src.contexts.projects.core.derivers import ProjectState as DomainProjectState
from src.contexts.projects.core.derivers import derive_open_source
from src.contexts.projects.core.events import ScreenChanged, SourceOpened
from src.contexts.projects.core.failure_events import SourceNotOpened
from src.contexts.sources.core.commandHandlers._state import SourceRepository
from src.shared.common.operation_result import OperationResult
from src.shared.common.types import SourceId
from src.shared.infra.state import ProjectState

if TYPE_CHECKING:
    from src.shared.infra.event_bus import EventBus


def open_source(
    command: OpenSourceCommand,
    state: ProjectState,
    event_bus: EventBus,
    source_repo: SourceRepository,
) -> OperationResult:
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
        state: Project state (for project check and screen tracking)
        event_bus: Event bus for publishing events
        source_repo: Repository for source queries (source of truth)

    Returns:
        OperationResult with SourceOpened event on success, or error details on failure
    """
    # Step 1: Validate
    if state.project is None:
        return OperationResult.fail(
            error="No project is currently open",
            error_code="SOURCE_NOT_OPENED/NO_PROJECT",
            suggestions=("Open a project first",),
        )

    source_id = SourceId(value=command.source_id)

    # Step 2: Build domain state and derive event
    # Get existing sources from repo (source of truth)
    existing_sources = tuple(source_repo.get_all())
    domain_state = DomainProjectState(
        path_exists=lambda _p: True,
        parent_writable=lambda _p: True,
        existing_sources=existing_sources,
    )

    result = derive_open_source(source_id=source_id, state=domain_state)

    if isinstance(result, SourceNotOpened):
        return OperationResult.fail(
            error=result.reason,
            error_code=f"SOURCE_NOT_OPENED/{result.event_type.upper()}",
        )

    event: SourceOpened = result

    # Step 3: Update current source ID in state (ID only, repos have full entity)
    state.current_source_id = source_id

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

    return OperationResult.ok(data=event)
