"""
Remove Source Use Case

Functional use case for removing a source from the project.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from returns.result import Failure, Result, Success

from src.application.projects.commands import RemoveSourceCommand
from src.application.state import ProjectState
from src.contexts.projects.core.derivers import ProjectState as DomainProjectState
from src.contexts.projects.core.derivers import derive_remove_source
from src.contexts.projects.core.events import SourceRemoved
from src.contexts.projects.core.failure_events import SourceNotRemoved
from src.contexts.shared.core.types import SourceId

if TYPE_CHECKING:
    from src.application.contexts import CodingContext, SourcesContext
    from src.application.event_bus import EventBus


def remove_source(
    command: RemoveSourceCommand,
    state: ProjectState,
    sources_ctx: SourcesContext,
    coding_ctx: CodingContext | None,
    event_bus: EventBus,
) -> Result[SourceRemoved, str]:
    """
    Remove a source from the current project.

    Functional use case following 5-step pattern:
    1. Validate project is open
    2. Derive SourceRemoved event (pure)
    3. Cascade delete segments
    4. Delete from repository and update state
    5. Publish event

    Args:
        command: Command with source ID
        state: Project state cache
        sources_ctx: Sources context with repository
        coding_ctx: Coding context for segment cleanup (optional)
        event_bus: Event bus for publishing events

    Returns:
        Success with SourceRemoved event, or Failure with error message
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

    result = derive_remove_source(source_id=source_id, state=domain_state)

    if isinstance(result, SourceNotRemoved):
        return Failure(result.reason)

    event: SourceRemoved = result

    # Step 3: Cascade delete segments
    if coding_ctx and coding_ctx.segment_repo:
        coding_ctx.segment_repo.delete_by_source(source_id)

    # Step 4: Delete from repository and update state
    if sources_ctx and sources_ctx.source_repo:
        sources_ctx.source_repo.delete(source_id)

    state.remove_source(command.source_id)

    # Step 5: Publish event
    event_bus.publish(event)

    return Success(event)
