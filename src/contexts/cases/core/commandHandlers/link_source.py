"""
Link Source to Case Use Case

Functional use case for linking a source to a case.
Returns OperationResult for rich error handling in UI and AI consumers.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from src.contexts.cases.core.commandHandlers._state import CaseRepository
from src.contexts.cases.core.derivers import CaseState, derive_link_source_to_case
from src.contexts.cases.core.events import SourceLinkedToCase
from src.contexts.cases.core.failure_events import SourceLinkFailed
from src.contexts.projects.core.commands import (
    LinkSourceToCaseCommand,
    UnlinkSourceFromCaseCommand,
)
from src.shared.common.operation_result import OperationResult
from src.shared.common.types import CaseId, SourceId
from src.shared.infra.state import ProjectState

if TYPE_CHECKING:
    from src.shared.infra.event_bus import EventBus


def link_source_to_case(
    command: LinkSourceToCaseCommand,
    state: ProjectState,
    case_repo: CaseRepository | None,
    event_bus: EventBus,
) -> OperationResult:
    """
    Link a source to a case.

    Args:
        command: Command with case ID and source ID
        state: Project state cache
        case_repo: Repository for cases
        event_bus: Event bus for publishing events

    Returns:
        OperationResult with SourceLinkedToCase event on success, or error details on failure
    """
    if state.project is None:
        return OperationResult.fail(
            error="No project is currently open",
            error_code="SOURCE_NOT_LINKED/NO_PROJECT",
            suggestions=("Open a project first",),
        )

    case_id = CaseId(value=command.case_id)
    source_id = SourceId(value=command.source_id)

    # Get cases from repo (source of truth)
    all_cases = case_repo.get_all() if case_repo else []

    # Build state and derive event
    case_state = CaseState(existing_cases=tuple(all_cases))

    result = derive_link_source_to_case(
        case_id=case_id,
        source_id=source_id,
        state=case_state,
    )

    # Derivers now return failure events directly (per SKILL.md)
    if isinstance(result, SourceLinkFailed):
        event_bus.publish(result)  # Publish failure for observability
        return OperationResult.from_failure(result)

    event: SourceLinkedToCase = result

    # Persist link (source name from event or empty - deriver handles validation)
    if case_repo:
        case_repo.link_source(case_id, source_id, "")

    # Publish event
    event_bus.publish(event)

    return OperationResult.ok(
        data=event,
        rollback=UnlinkSourceFromCaseCommand(
            case_id=command.case_id, source_id=command.source_id
        ),
    )
