"""
Update Source Use Case

Functional use case for updating source metadata.
Returns OperationResult with error codes and suggestions.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from src.contexts.projects.core.commands import UpdateSourceCommand
from src.contexts.projects.core.derivers import ProjectState as DomainProjectState
from src.contexts.projects.core.derivers import derive_update_source
from src.contexts.projects.core.entities import SourceStatus
from src.contexts.projects.core.events import SourceUpdated
from src.contexts.projects.core.failure_events import SourceNotUpdated
from src.contexts.sources.core.commandHandlers._state import SourceRepository
from src.shared.common.operation_result import OperationResult
from src.shared.common.types import SourceId
from src.shared.infra.state import ProjectState

if TYPE_CHECKING:
    from src.shared.infra.event_bus import EventBus


def update_source(
    command: UpdateSourceCommand,
    state: ProjectState,
    source_repo: SourceRepository | None,
    event_bus: EventBus,
) -> OperationResult:
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
        source_repo: Repository for source operations
        event_bus: Event bus for publishing events

    Returns:
        OperationResult with updated Source on success, or error details on failure
    """
    # Step 1: Validate
    if state.project is None:
        return OperationResult.fail(
            error="No project is currently open",
            error_code="SOURCE_NOT_UPDATED/NO_PROJECT",
            suggestions=("Open a project first",),
        )

    source_id = SourceId(value=command.source_id)

    # Step 2: Build domain state and derive event
    # Get existing sources from repo (source of truth) instead of state cache
    existing_sources = tuple(source_repo.get_all()) if source_repo else ()
    domain_state = DomainProjectState(
        path_exists=lambda _p: True,
        parent_writable=lambda _p: True,
        existing_sources=existing_sources,
    )

    result = derive_update_source(
        source_id=source_id,
        memo=command.memo,
        origin=command.origin,
        status=command.status,
        state=domain_state,
    )

    if isinstance(result, SourceNotUpdated):
        return OperationResult.fail(
            error=result.reason,
            error_code=f"SOURCE_NOT_UPDATED/{result.event_type.upper()}",
        )

    event: SourceUpdated = result

    # Step 3: Find and update the source entity
    source = source_repo.get_by_id(source_id) if source_repo else None
    if source is None:
        return OperationResult.fail(
            error=f"Source {command.source_id} not found",
            error_code="SOURCE_NOT_UPDATED/NOT_FOUND",
        )

    # Apply updates
    updated_source = source
    if event.memo is not None:
        updated_source = updated_source.with_memo(event.memo)
    if event.origin is not None:
        updated_source = updated_source.with_origin(event.origin)
    if event.status is not None:
        updated_source = updated_source.with_status(SourceStatus(event.status))

    # Step 4: Persist to repository (source of truth)
    if source_repo:
        source_repo.save(updated_source)

    # Step 5: Publish event
    event_bus.publish(event)

    return OperationResult.ok(data=updated_source)
