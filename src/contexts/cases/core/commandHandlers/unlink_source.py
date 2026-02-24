"""
Unlink Source from Case Use Case

Functional use case for unlinking a source from a case.
Returns OperationResult for rich error handling in UI and AI consumers.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from src.contexts.cases.core.commandHandlers._state import (
    CaseRepository,
    build_case_state,
    require_project,
)
from src.contexts.cases.core.derivers import derive_unlink_source_from_case
from src.contexts.cases.core.failure_events import SourceUnlinkFailed
from src.contexts.projects.core.commands import UnlinkSourceFromCaseCommand
from src.shared.common.operation_result import OperationResult
from src.shared.common.types import CaseId, SourceId

if TYPE_CHECKING:
    from src.shared.infra.event_bus import EventBus
    from src.shared.infra.state import ProjectState


def unlink_source_from_case(
    command: UnlinkSourceFromCaseCommand,
    state: ProjectState,
    case_repo: CaseRepository | None,
    event_bus: EventBus,
) -> OperationResult:
    """Unlink a source from a case."""
    if failure := require_project(state, "SOURCE_NOT_UNLINKED/NO_PROJECT"):
        return failure

    case_id = CaseId(value=command.case_id)
    source_id = SourceId(value=command.source_id)

    result = derive_unlink_source_from_case(
        case_id=case_id,
        source_id=source_id,
        state=build_case_state(case_repo),
    )

    if isinstance(result, SourceUnlinkFailed):
        event_bus.publish(result)
        return OperationResult.from_failure(result)

    event = result

    if case_repo:
        case_repo.unlink_source(case_id, source_id)

    event_bus.publish(event)

    return OperationResult.ok(data=event)
