"""
Link Source to Case Use Case

Functional use case for linking a source to a case.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from returns.result import Failure, Result, Success

from src.application.projects.commands import LinkSourceToCaseCommand
from src.application.state import ProjectState
from src.contexts.cases.core.derivers import CaseState, derive_link_source_to_case
from src.contexts.cases.core.events import SourceLinkedToCase
from src.contexts.shared.core.types import CaseId, SourceId

if TYPE_CHECKING:
    from src.application.contexts import CasesContext
    from src.application.event_bus import EventBus


def link_source_to_case(
    command: LinkSourceToCaseCommand,
    state: ProjectState,
    cases_ctx: CasesContext,
    event_bus: EventBus,
) -> Result[SourceLinkedToCase, str]:
    """
    Link a source to a case.

    Args:
        command: Command with case ID and source ID
        state: Project state cache
        cases_ctx: Cases context with repository
        event_bus: Event bus for publishing events

    Returns:
        Success with SourceLinkedToCase event, or Failure with error message
    """
    if state.project is None:
        return Failure("No project is currently open")

    case_id = CaseId(value=command.case_id)
    source_id = SourceId(value=command.source_id)

    # Verify source exists
    source = state.get_source(command.source_id)
    if source is None:
        return Failure(f"Source {command.source_id} not found")

    # Refresh cases from repo for fresh source_ids
    if cases_ctx and cases_ctx.case_repo:
        state.cases = cases_ctx.case_repo.get_all()

    # Build state and derive event
    case_state = CaseState(existing_cases=tuple(state.cases))

    result = derive_link_source_to_case(
        case_id=case_id,
        source_id=source_id,
        state=case_state,
    )

    if isinstance(result, Failure):
        return result

    event: SourceLinkedToCase = result

    # Persist link
    if cases_ctx and cases_ctx.case_repo:
        cases_ctx.case_repo.link_source(case_id, source_id, source.name)
        # Refresh cases to get updated source_ids
        state.cases = cases_ctx.case_repo.get_all()

    # Publish event
    event_bus.publish(event)

    return Success(event)
