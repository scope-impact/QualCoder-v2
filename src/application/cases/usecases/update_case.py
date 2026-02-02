"""
Update Case Use Case

Functional use case for updating case metadata.
Returns OperationResult for rich error handling in UI and AI consumers.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from returns.result import Failure

from src.application.projects.commands import UpdateCaseCommand
from src.application.state import ProjectState
from src.contexts.cases.core.derivers import (
    CaseNameTooLong,
    CaseNotFound,
    CaseState,
    DuplicateCaseName,
    EmptyCaseName,
    derive_update_case,
)
from src.contexts.cases.core.entities import Case
from src.contexts.cases.core.events import CaseUpdated
from src.contexts.shared.core.operation_result import OperationResult
from src.contexts.shared.core.types import CaseId

if TYPE_CHECKING:
    from src.application.contexts import CasesContext
    from src.application.event_bus import EventBus


def update_case(
    command: UpdateCaseCommand,
    state: ProjectState,
    cases_ctx: CasesContext,
    event_bus: EventBus,
) -> OperationResult:
    """
    Update an existing case.

    Args:
        command: Command with case ID and updates
        state: Project state cache
        cases_ctx: Cases context with repository
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
    case_state = CaseState(existing_cases=tuple(state.cases))

    result = derive_update_case(
        case_id=case_id,
        name=command.name,
        description=command.description,
        memo=command.memo,
        state=case_state,
    )

    if isinstance(result, Failure):
        reason = result.failure()
        return _failure_to_result(reason)

    event: CaseUpdated = result

    # Create updated case entity
    updated_case = Case(
        id=event.case_id,
        name=event.name,
        description=event.description,
        memo=event.memo,
    )

    # Persist and update state
    if cases_ctx and cases_ctx.case_repo:
        cases_ctx.case_repo.save(updated_case)

    state.update_case(updated_case)

    # Publish event
    event_bus.publish(event)

    return OperationResult.ok(data=updated_case)


def _failure_to_result(reason: object) -> OperationResult:
    """Convert deriver failure reason to OperationResult."""
    if isinstance(reason, CaseNotFound):
        return OperationResult.fail(
            error=reason.message,
            error_code="CASE_NOT_UPDATED/NOT_FOUND",
            suggestions=("Verify the case ID is correct", "Refresh the case list"),
        )
    if isinstance(reason, EmptyCaseName):
        return OperationResult.fail(
            error=reason.message,
            error_code="CASE_NOT_UPDATED/EMPTY_NAME",
            suggestions=("Provide a non-empty case name",),
        )
    if isinstance(reason, CaseNameTooLong):
        return OperationResult.fail(
            error=reason.message,
            error_code="CASE_NOT_UPDATED/NAME_TOO_LONG",
            suggestions=("Use a shorter name (max 100 characters)",),
        )
    if isinstance(reason, DuplicateCaseName):
        return OperationResult.fail(
            error=reason.message,
            error_code="CASE_NOT_UPDATED/DUPLICATE_NAME",
            suggestions=("Use a different name",),
        )
    # Fallback for unexpected reasons
    return OperationResult.fail(
        error=getattr(reason, "message", str(reason)),
        error_code="CASE_NOT_UPDATED/UNKNOWN",
    )
