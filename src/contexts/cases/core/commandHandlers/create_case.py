"""
Create Case Use Case

Functional use case for creating a new case.
Returns OperationResult for rich error handling in UI and AI consumers.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from src.contexts.cases.core.commandHandlers._state import CaseRepository
from src.contexts.cases.core.derivers import CaseState, derive_create_case
from src.contexts.cases.core.entities import Case
from src.contexts.cases.core.events import CaseCreated
from src.contexts.cases.core.failure_events import CaseCreationFailed
from src.contexts.projects.core.commands import CreateCaseCommand, RemoveCaseCommand
from src.shared.common.operation_result import OperationResult
from src.shared.infra.state import ProjectState

if TYPE_CHECKING:
    from src.shared.infra.event_bus import EventBus


def create_case(
    command: CreateCaseCommand,
    state: ProjectState,
    case_repo: CaseRepository | None,
    event_bus: EventBus,
) -> OperationResult:
    """
    Create a new case in the current project.

    Args:
        command: Command with case name and description
        state: Project state cache
        case_repo: Repository for cases
        event_bus: Event bus for publishing events

    Returns:
        OperationResult with Case entity on success, or error details on failure
    """
    if state.project is None:
        return OperationResult.fail(
            error="No project is currently open",
            error_code="CASE_NOT_CREATED/NO_PROJECT",
            suggestions=("Open a project first",),
        )

    # Build state and derive event
    # Get existing cases from repo (source of truth) instead of state cache
    existing_cases = tuple(case_repo.get_all()) if case_repo else ()
    case_state = CaseState(existing_cases=existing_cases)

    result = derive_create_case(
        name=command.name,
        description=command.description,
        memo=command.memo,
        state=case_state,
    )

    # Derivers now return failure events directly (per SKILL.md)
    if isinstance(result, CaseCreationFailed):
        event_bus.publish(result)  # Publish failure for observability
        return OperationResult.from_failure(result)

    event: CaseCreated = result

    # Create case entity
    case = Case(
        id=event.case_id,
        name=event.name,
        description=event.description,
        memo=event.memo,
    )

    # Persist to repository (source of truth)
    if case_repo:
        case_repo.save(case)

    # Publish event
    event_bus.publish(event)

    # Return success with rollback command
    return OperationResult.ok(
        data=case,
        rollback=RemoveCaseCommand(case_id=case.id.value),
    )
