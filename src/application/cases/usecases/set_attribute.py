"""
Set Case Attribute Use Case

Functional use case for setting an attribute on a case.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from returns.result import Failure, Result, Success

from src.application.projects.commands import SetCaseAttributeCommand
from src.application.state import ProjectState
from src.contexts.cases.core.derivers import CaseState, derive_set_case_attribute
from src.contexts.cases.core.entities import AttributeType, CaseAttribute
from src.contexts.cases.core.events import CaseAttributeSet
from src.contexts.shared.core.types import CaseId

if TYPE_CHECKING:
    from src.application.contexts import CasesContext
    from src.application.event_bus import EventBus


def set_case_attribute(
    command: SetCaseAttributeCommand,
    state: ProjectState,
    cases_ctx: CasesContext,
    event_bus: EventBus,
) -> Result[CaseAttributeSet, str]:
    """
    Set an attribute on a case.

    Args:
        command: Command with case ID and attribute details
        state: Project state cache
        cases_ctx: Cases context with repository
        event_bus: Event bus for publishing events

    Returns:
        Success with CaseAttributeSet event, or Failure with error message
    """
    if state.project is None:
        return Failure("No project is currently open")

    case_id = CaseId(value=command.case_id)

    # Refresh cases from repo
    if cases_ctx and cases_ctx.case_repo:
        state.cases = cases_ctx.case_repo.get_all()

    # Build state and derive event
    case_state = CaseState(existing_cases=tuple(state.cases))

    result = derive_set_case_attribute(
        case_id=case_id,
        attr_name=command.attr_name,
        attr_type=command.attr_type,
        attr_value=command.attr_value,
        state=case_state,
    )

    if isinstance(result, Failure):
        return result

    event: CaseAttributeSet = result

    # Persist attribute
    if cases_ctx and cases_ctx.case_repo:
        attr = CaseAttribute(
            name=event.attr_name,
            attr_type=AttributeType(event.attr_type),
            value=event.attr_value,
        )
        cases_ctx.case_repo.save_attribute(case_id, attr)
        # Refresh cases to get updated attributes
        state.cases = cases_ctx.case_repo.get_all()

    # Publish event
    event_bus.publish(event)

    return Success(event)
