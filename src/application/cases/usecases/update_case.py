"""
Update Case Use Case

Functional use case for updating case metadata.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from returns.result import Failure, Result, Success

from src.application.projects.commands import UpdateCaseCommand
from src.application.state import ProjectState
from src.contexts.cases.core.derivers import CaseState, derive_update_case
from src.contexts.cases.core.entities import Case
from src.contexts.cases.core.events import CaseUpdated
from src.contexts.shared.core.types import CaseId

if TYPE_CHECKING:
    from src.application.contexts import CasesContext
    from src.application.event_bus import EventBus


def update_case(
    command: UpdateCaseCommand,
    state: ProjectState,
    cases_ctx: CasesContext,
    event_bus: EventBus,
) -> Result[Case, str]:
    """
    Update an existing case.

    Args:
        command: Command with case ID and updates
        state: Project state cache
        cases_ctx: Cases context with repository
        event_bus: Event bus for publishing events

    Returns:
        Success with updated Case, or Failure with error message
    """
    if state.project is None:
        return Failure("No project is currently open")

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
        return result

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

    return Success(updated_case)
