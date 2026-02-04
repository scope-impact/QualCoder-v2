"""
Remove Source Use Case

Functional use case for removing a source from the project.
Returns OperationResult with error codes and suggestions.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from src.contexts.projects.core.commands import RemoveSourceCommand
from src.contexts.projects.core.derivers import ProjectState as DomainProjectState
from src.contexts.projects.core.derivers import derive_remove_source
from src.contexts.projects.core.events import SourceRemoved
from src.contexts.projects.core.failure_events import SourceNotRemoved
from src.contexts.sources.core.commandHandlers._state import (
    SegmentRepository,
    SourceRepository,
)
from src.shared.common.operation_result import OperationResult
from src.shared.common.types import SourceId
from src.shared.infra.state import ProjectState

if TYPE_CHECKING:
    from src.shared.infra.event_bus import EventBus


def remove_source(
    command: RemoveSourceCommand,
    state: ProjectState,
    source_repo: SourceRepository | None,
    segment_repo: SegmentRepository | None,
    event_bus: EventBus,
) -> OperationResult:
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
        source_repo: Repository for source operations
        segment_repo: Repository for segment cleanup (cascade delete)
        event_bus: Event bus for publishing events

    Returns:
        OperationResult with SourceRemoved event on success, or error details on failure
    """
    # Step 1: Validate
    if state.project is None:
        return OperationResult.fail(
            error="No project is currently open",
            error_code="SOURCE_NOT_REMOVED/NO_PROJECT",
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

    result = derive_remove_source(source_id=source_id, state=domain_state)

    if isinstance(result, SourceNotRemoved):
        return OperationResult.fail(
            error=result.reason,
            error_code=f"SOURCE_NOT_REMOVED/{result.event_type.upper()}",
        )

    event: SourceRemoved = result

    # Step 3: Cascade delete segments
    if segment_repo:
        segment_repo.delete_by_source(source_id)

    # Step 4: Delete from repository (source of truth)
    if source_repo:
        source_repo.delete(source_id)

    # Step 5: Publish event
    event_bus.publish(event)

    # No rollback - would need to recreate source with all data
    return OperationResult.ok(data=event)
