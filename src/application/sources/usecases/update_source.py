"""
Update Source Use Case

Functional use case for updating source metadata.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from returns.result import Failure, Result, Success

from src.application.projects.commands import UpdateSourceCommand
from src.application.state import ProjectState
from src.contexts.projects.core.derivers import ProjectState as DomainProjectState
from src.contexts.projects.core.derivers import derive_update_source
from src.contexts.projects.core.entities import Source, SourceStatus
from src.contexts.projects.core.events import SourceUpdated
from src.contexts.shared.core.types import SourceId

if TYPE_CHECKING:
    from src.application.contexts import SourcesContext
    from src.application.event_bus import EventBus


def update_source(
    command: UpdateSourceCommand,
    state: ProjectState,
    sources_ctx: SourcesContext,
    event_bus: EventBus,
) -> Result[Source, str]:
    """
    Update source metadata (memo, origin, status).

    Functional use case following 5-step pattern:
    1. Validate project is open and source exists
    2. Derive SourceUpdated event (pure)
    3. Apply updates to source entity
    4. Persist and update state
    5. Publish event

    Args:
        command: Command with source ID and updates
        state: Project state cache
        sources_ctx: Sources context with repository
        event_bus: Event bus for publishing events

    Returns:
        Success with updated Source, or Failure with error message
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

    result = derive_update_source(
        source_id=source_id,
        memo=command.memo,
        origin=command.origin,
        status=command.status,
        state=domain_state,
    )

    if isinstance(result, Failure):
        return result

    event: SourceUpdated = result

    # Step 3: Find and update the source entity
    source = state.get_source(command.source_id)
    if source is None:
        return Failure(f"Source {command.source_id} not found")

    # Apply updates
    updated_source = source
    if event.memo is not None:
        updated_source = updated_source.with_memo(event.memo)
    if event.origin is not None:
        updated_source = updated_source.with_origin(event.origin)
    if event.status is not None:
        updated_source = updated_source.with_status(SourceStatus(event.status))

    # Step 4: Persist and update state
    if sources_ctx and sources_ctx.source_repo:
        sources_ctx.source_repo.save(updated_source)

    state.update_source(updated_source)

    # Step 5: Publish event
    event_bus.publish(event)

    return Success(updated_source)
