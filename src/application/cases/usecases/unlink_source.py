"""
Unlink Source from Case Use Case

Functional use case for unlinking a source from a case.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from returns.result import Failure, Result, Success

from src.application.projects.commands import UnlinkSourceFromCaseCommand
from src.application.state import ProjectState
from src.contexts.cases.core.derivers import CaseState, derive_unlink_source_from_case
from src.contexts.cases.core.events import SourceUnlinkedFromCase
from src.contexts.shared.core.types import CaseId, SourceId

if TYPE_CHECKING:
    from src.application.contexts import CasesContext
    from src.application.event_bus import EventBus


def unlink_source_from_case(
    command: UnlinkSourceFromCaseCommand,
    state: ProjectState,
    cases_ctx: CasesContext,
    event_bus: EventBus,
) -> Result[SourceUnlinkedFromCase, str]:
    """
    Unlink a source from a case.

    Args:
        command: Command with case ID and source ID
        state: Project state cache
        cases_ctx: Cases context with repository
        event_bus: Event bus for publishing events

    Returns:
        Success with SourceUnlinkedFromCase event, or Failure with error message
    """
    if state.project is None:
        return Failure("No project is currently open")

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
        return result

    event: SourceUnlinkedFromCase = result

    # Remove link
    if cases_ctx and cases_ctx.case_repo:
        cases_ctx.case_repo.unlink_source(case_id, source_id)
        # Refresh cases to get updated source_ids
        state.cases = cases_ctx.case_repo.get_all()

    # Publish event
    event_bus.publish(event)

    return Success(event)
