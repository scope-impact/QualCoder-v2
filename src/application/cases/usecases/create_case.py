"""
Create Case Use Case

Functional use case for creating a new case.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from returns.result import Failure, Result, Success

from src.application.projects.commands import CreateCaseCommand
from src.application.state import ProjectState
from src.contexts.cases.core.derivers import CaseState, derive_create_case
from src.contexts.cases.core.entities import Case
from src.contexts.cases.core.events import CaseCreated

if TYPE_CHECKING:
    from src.application.contexts import CasesContext
    from src.application.event_bus import EventBus


def create_case(
    command: CreateCaseCommand,
    state: ProjectState,
    cases_ctx: CasesContext,
    event_bus: EventBus,
) -> Result[Case, str]:
    """
    Create a new case in the current project.

    Args:
        command: Command with case name and description
        state: Project state cache
        cases_ctx: Cases context with repository
        event_bus: Event bus for publishing events

    Returns:
        Success with Case entity, or Failure with error message
    """
    if state.project is None:
        return Failure("No project is currently open")

    # Build state and derive event
    case_state = CaseState(existing_cases=tuple(state.cases))

    result = derive_create_case(
        name=command.name,
        description=command.description,
        memo=command.memo,
        state=case_state,
    )

    if isinstance(result, Failure):
        return result

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

    return Success(case)
