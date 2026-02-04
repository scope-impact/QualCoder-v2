"""
Remove Case Use Case

Functional use case for removing a case.
Returns OperationResult for rich error handling in UI and AI consumers.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from src.contexts.cases.core.commandHandlers._state import CaseRepository
from src.contexts.cases.core.derivers import CaseState, derive_remove_case
from src.contexts.cases.core.events import CaseRemoved
from src.contexts.cases.core.failure_events import CaseDeletionFailed
from src.contexts.projects.core.commands import RemoveCaseCommand
from src.shared.common.operation_result import OperationResult
from src.shared.common.types import CaseId
from src.shared.infra.state import ProjectState

if TYPE_CHECKING:
    from src.shared.infra.event_bus import EventBus


def remove_case(
    command: RemoveCaseCommand,
    state: ProjectState,
    case_repo: CaseRepository | None,
    event_bus: EventBus,
) -> OperationResult:
    """
    Remove a case from the current project.

    Args:
        command: Command with case ID
        state: Project state cache
        case_repo: Repository for cases
        event_bus: Event bus for publishing events

    Returns:
        OperationResult with CaseRemoved event on success, or error details on failure
    """
    if state.project is None:
        return OperationResult.fail(
            error="No project is currently open",
            error_code="CASE_NOT_REMOVED/NO_PROJECT",
            suggestions=("Open a project first",),
        )

    case_id = CaseId(value=command.case_id)

    # Build state and derive event
    # Get existing cases from repo (source of truth) instead of state cache
    existing_cases = tuple(case_repo.get_all()) if case_repo else ()
    case_state = CaseState(existing_cases=existing_cases)

    result = derive_remove_case(case_id=case_id, state=case_state)

    # Derivers now return failure events directly (per SKILL.md)
    if isinstance(result, CaseDeletionFailed):
        event_bus.publish(result)  # Publish failure for observability
        return OperationResult.from_failure(result)

    event: CaseRemoved = result

    # Delete from repository (source of truth)
    if case_repo:
        case_repo.delete(case_id)

    # Publish event
    event_bus.publish(event)

    return OperationResult.ok(data=event)
