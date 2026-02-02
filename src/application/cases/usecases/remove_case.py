"""
Remove Case Use Case

Functional use case for removing a case.
Returns OperationResult for rich error handling in UI and AI consumers.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from returns.result import Failure

from src.application.projects.commands import RemoveCaseCommand
from src.application.state import ProjectState
from src.contexts.cases.core.derivers import CaseNotFound, CaseState, derive_remove_case
from src.contexts.cases.core.events import CaseRemoved
from src.contexts.shared.core.operation_result import OperationResult
from src.contexts.shared.core.types import CaseId

if TYPE_CHECKING:
    from src.application.contexts import CasesContext
    from src.application.event_bus import EventBus


def remove_case(
    command: RemoveCaseCommand,
    state: ProjectState,
    cases_ctx: CasesContext,
    event_bus: EventBus,
) -> OperationResult:
    """
    Remove a case from the current project.

    Args:
        command: Command with case ID
        state: Project state cache
        cases_ctx: Cases context with repository
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
    case_state = CaseState(existing_cases=tuple(state.cases))

    result = derive_remove_case(case_id=case_id, state=case_state)

    if isinstance(result, Failure):
        reason = result.failure()
        return _failure_to_result(reason)

    event: CaseRemoved = result

    # Delete from repository and update state
    if cases_ctx and cases_ctx.case_repo:
        cases_ctx.case_repo.delete(case_id)

    state.remove_case(command.case_id)

    # Publish event
    event_bus.publish(event)

    return OperationResult.ok(data=event)


def _failure_to_result(reason: object) -> OperationResult:
    """Convert deriver failure reason to OperationResult."""
    if isinstance(reason, CaseNotFound):
        return OperationResult.fail(
            error=reason.message,
            error_code="CASE_NOT_REMOVED/NOT_FOUND",
            suggestions=("Verify the case ID is correct", "Refresh the case list"),
        )
    # Fallback for unexpected reasons
    return OperationResult.fail(
        error=getattr(reason, "message", str(reason)),
        error_code="CASE_NOT_REMOVED/UNKNOWN",
    )
