"""
Unlink Source from Case Use Case

Functional use case for unlinking a source from a case.
Returns OperationResult for rich error handling in UI and AI consumers.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from returns.result import Failure

from src.application.projects.commands import UnlinkSourceFromCaseCommand
from src.application.state import ProjectState
from src.contexts.cases.core.derivers import (
    CaseNotFound,
    CaseState,
    SourceNotLinked,
    derive_unlink_source_from_case,
)
from src.contexts.cases.core.events import SourceUnlinkedFromCase
from src.contexts.shared.core.operation_result import OperationResult
from src.contexts.shared.core.types import CaseId, SourceId

if TYPE_CHECKING:
    from src.application.contexts import CasesContext
    from src.application.event_bus import EventBus


def unlink_source_from_case(
    command: UnlinkSourceFromCaseCommand,
    state: ProjectState,
    cases_ctx: CasesContext,
    event_bus: EventBus,
) -> OperationResult:
    """
    Unlink a source from a case.

    Args:
        command: Command with case ID and source ID
        state: Project state cache
        cases_ctx: Cases context with repository
        event_bus: Event bus for publishing events

    Returns:
        OperationResult with SourceUnlinkedFromCase event on success, or error details on failure
    """
    if state.project is None:
        return OperationResult.fail(
            error="No project is currently open",
            error_code="SOURCE_NOT_UNLINKED/NO_PROJECT",
            suggestions=("Open a project first",),
        )

    case_id = CaseId(value=command.case_id)
    source_id = SourceId(value=command.source_id)

    # Refresh cases from repo for fresh source_ids
    if cases_ctx and cases_ctx.case_repo:
        state.cases = cases_ctx.case_repo.get_all()

    # Build state and derive event
    case_state = CaseState(existing_cases=tuple(state.cases))

    result = derive_unlink_source_from_case(
        case_id=case_id,
        source_id=source_id,
        state=case_state,
    )

    if isinstance(result, Failure):
        reason = result.failure()
        return _failure_to_result(reason)

    event: SourceUnlinkedFromCase = result

    # Remove link
    if cases_ctx and cases_ctx.case_repo:
        cases_ctx.case_repo.unlink_source(case_id, source_id)
        # Refresh cases to get updated source_ids
        state.cases = cases_ctx.case_repo.get_all()

    # Publish event
    event_bus.publish(event)

    return OperationResult.ok(data=event)


def _failure_to_result(reason: object) -> OperationResult:
    """Convert deriver failure reason to OperationResult."""
    if isinstance(reason, CaseNotFound):
        return OperationResult.fail(
            error=reason.message,
            error_code="SOURCE_NOT_UNLINKED/CASE_NOT_FOUND",
            suggestions=("Verify the case ID is correct",),
        )
    if isinstance(reason, SourceNotLinked):
        return OperationResult.fail(
            error=reason.message,
            error_code="SOURCE_NOT_UNLINKED/NOT_LINKED",
            suggestions=("Source is not linked to this case",),
        )
    # Fallback for unexpected reasons
    return OperationResult.fail(
        error=getattr(reason, "message", str(reason)),
        error_code="SOURCE_NOT_UNLINKED/UNKNOWN",
    )
