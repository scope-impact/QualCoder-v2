"""
Update Case Use Case

Functional use case for updating case metadata.
Returns OperationResult for rich error handling in UI and AI consumers.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from src.contexts.cases.core.commandHandlers._state import CaseRepository
from src.contexts.cases.core.derivers import CaseState, derive_update_case
from src.contexts.cases.core.entities import Case
from src.contexts.cases.core.events import CaseUpdated
from src.contexts.cases.core.failure_events import CaseUpdateFailed
from src.contexts.projects.core.commands import UpdateCaseCommand
from src.shared.common.operation_result import OperationResult
from src.shared.common.types import CaseId
from src.shared.infra.state import ProjectState

if TYPE_CHECKING:
    from src.shared.infra.event_bus import EventBus


def update_case(
    command: UpdateCaseCommand,
    state: ProjectState,
    case_repo: CaseRepository | None,
    event_bus: EventBus,
) -> OperationResult:
    """
    Update an existing case.

    Args:
        command: Command with case ID and updates
        state: Project state cache
        case_repo: Repository for cases
        event_bus: Event bus for publishing events

    Returns:
        OperationResult with updated Case on success, or error details on failure
    """
    if state.project is None:
        return OperationResult.fail(
            error="No project is currently open",
            error_code="CASE_NOT_UPDATED/NO_PROJECT",
            suggestions=("Open a project first",),
        )

    case_id = CaseId(value=command.case_id)

    # Build state and derive event
    # Get existing cases from repo (source of truth) instead of state cache
    existing_cases = tuple(case_repo.get_all()) if case_repo else ()
    case_state = CaseState(existing_cases=existing_cases)

    result = derive_update_case(
        case_id=case_id,
        name=command.name,
        description=command.description,
        memo=command.memo,
        state=case_state,
    )

    # Derivers now return failure events directly (per SKILL.md)
    if isinstance(result, CaseUpdateFailed):
        event_bus.publish(result)  # Publish failure for observability
        return OperationResult.from_failure(result)

    event: CaseUpdated = result

    # Create updated case entity
    updated_case = Case(
        id=event.case_id,
        name=event.name,
        description=event.description,
        memo=event.memo,
    )

    # Persist to repository (source of truth)
    if case_repo:
        case_repo.save(updated_case)

    # Publish event
    event_bus.publish(event)

    return OperationResult.ok(data=updated_case)
