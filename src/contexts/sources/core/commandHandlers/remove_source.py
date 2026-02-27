"""
Remove Source Use Case

Functional use case for removing a source from the project.
Returns OperationResult with error codes and suggestions.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from src.contexts.projects.core.commands import RemoveSourceCommand
from src.contexts.projects.core.derivers import derive_remove_source
from src.contexts.projects.core.events import SourceRemoved
from src.contexts.projects.core.failure_events import SourceNotRemoved
from src.contexts.sources.core.commandHandlers._state import (
    SegmentRepository,
    SourceRepository,
    build_domain_state,
)
from src.shared.common.operation_result import OperationResult
from src.shared.common.types import SourceId
from src.shared.infra.metrics import metered_command
from src.shared.infra.state import ProjectState

if TYPE_CHECKING:
    from src.shared.infra.event_bus import EventBus

logger = logging.getLogger("qualcoder.sources.core")


@metered_command("remove_source")
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
    logger.debug("remove_source: source_id=%s", command.source_id)
    # Step 1: Validate
    if state.project is None:
        logger.error("remove_source: no project is currently open")
        return OperationResult.fail(
            error="No project is currently open",
            error_code="SOURCE_NOT_REMOVED/NO_PROJECT",
            suggestions=("Open a project first",),
        )

    source_id = SourceId(value=command.source_id)

    # Step 2: Build domain state and derive event
    domain_state = build_domain_state(source_repo)

    result = derive_remove_source(source_id=source_id, state=domain_state)

    if isinstance(result, SourceNotRemoved):
        logger.error("remove_source: derivation failed, reason=%s", result.message)
        return OperationResult.fail(
            error=result.message,
            error_code=result.event_type,
        )

    event: SourceRemoved = result

    # Atomic: cascade delete segments + delete source in one transaction
    from src.shared.infra.unit_of_work import UnitOfWork

    with UnitOfWork(source_repo._conn) as uow:
        if segment_repo:
            segment_repo.delete_by_source(source_id)
        source_repo.delete(source_id)
        uow.commit()

    event_bus.publish(event)
    logger.info("remove_source: removed source_id=%s", source_id)
    return OperationResult.ok(data=event)
