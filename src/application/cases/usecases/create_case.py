"""
Create Case Use Case

Functional use case for creating a new case.
Returns OperationResult for rich error handling in UI and AI consumers.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from returns.result import Failure

from src.application.projects.commands import CreateCaseCommand, RemoveCaseCommand
from src.application.state import ProjectState
from src.contexts.cases.core.derivers import (
    CaseNameTooLong,
    CaseState,
    DuplicateCaseName,
    EmptyCaseName,
    derive_create_case,
)
from src.contexts.cases.core.entities import Case
from src.contexts.cases.core.events import CaseCreated
from src.contexts.shared.core.operation_result import OperationResult

if TYPE_CHECKING:
    from src.application.contexts import CasesContext
    from src.application.event_bus import EventBus


def create_case(
    command: CreateCaseCommand,
    state: ProjectState,
    cases_ctx: CasesContext,
    event_bus: EventBus,
) -> OperationResult:
    """
    Create a new case in the current project.

    Args:
        command: Command with case name and description
        state: Project state cache
        cases_ctx: Cases context with repository
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
    case_state = CaseState(existing_cases=tuple(state.cases))

    result = derive_create_case(
        name=command.name,
        description=command.description,
        memo=command.memo,
        state=case_state,
    )

    if isinstance(result, Failure):
        reason = result.failure()
        return _failure_to_result(reason)

    event: CaseCreated = result

    # Create case entity
    case = Case(
        id=event.case_id,
        name=event.name,
        description=event.description,
        memo=event.memo,
    )

    # Persist and update state
    if cases_ctx and cases_ctx.case_repo:
        cases_ctx.case_repo.save(case)

    state.add_case(case)

    # Publish event
    event_bus.publish(event)

    # Return success with rollback command
    return OperationResult.ok(
        data=case,
        rollback=RemoveCaseCommand(case_id=case.id.value),
    )


def _failure_to_result(reason: object) -> OperationResult:
    """Convert deriver failure reason to OperationResult."""
    if isinstance(reason, EmptyCaseName):
        return OperationResult.fail(
            error=reason.message,
            error_code="CASE_NOT_CREATED/EMPTY_NAME",
            suggestions=("Provide a non-empty case name",),
        )
    if isinstance(reason, CaseNameTooLong):
        return OperationResult.fail(
            error=reason.message,
            error_code="CASE_NOT_CREATED/NAME_TOO_LONG",
            suggestions=(
                "Use a shorter name (max 100 characters)",
                "Abbreviate or use an acronym",
            ),
        )
    if isinstance(reason, DuplicateCaseName):
        return OperationResult.fail(
            error=reason.message,
            error_code="CASE_NOT_CREATED/DUPLICATE_NAME",
            suggestions=(
                "Use a different name",
                "Add a suffix to distinguish (e.g., 'Case A-2')",
            ),
        )
    # Fallback for unexpected reasons
    return OperationResult.fail(
        error=getattr(reason, "message", str(reason)),
        error_code="CASE_NOT_CREATED/UNKNOWN",
    )
