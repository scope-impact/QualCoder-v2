"""
Remove Case Use Case

Functional use case for removing a case.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from returns.result import Failure, Result, Success

from src.application.projects.commands import RemoveCaseCommand
from src.application.state import ProjectState
from src.contexts.cases.core.derivers import CaseState, derive_remove_case
from src.contexts.cases.core.events import CaseRemoved
from src.contexts.shared.core.types import CaseId

if TYPE_CHECKING:
    from src.application.contexts import CasesContext
    from src.application.event_bus import EventBus


def remove_case(
    command: RemoveCaseCommand,
    state: ProjectState,
    cases_ctx: CasesContext,
    event_bus: EventBus,
) -> Result[CaseRemoved, str]:
    """
    Remove a case from the current project.

    Args:
        command: Command with case ID
        state: Project state cache
        cases_ctx: Cases context with repository
        event_bus: Event bus for publishing events

    Returns:
        Success with CaseRemoved event, or Failure with error message
    """
    if state.project is None:
        return Failure("No project is currently open")

    case_id = CaseId(value=command.case_id)

    # Build state and derive event
    case_state = CaseState(existing_cases=tuple(state.cases))

    result = derive_remove_case(case_id=case_id, state=case_state)

    if isinstance(result, Failure):
        return result

    event: CaseRemoved = result

    # Delete from repository and update state
    if cases_ctx and cases_ctx.case_repo:
        cases_ctx.case_repo.delete(case_id)

    state.remove_case(command.case_id)

    # Publish event
    event_bus.publish(event)

    return Success(event)
