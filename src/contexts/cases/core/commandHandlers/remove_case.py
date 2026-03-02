"""
Remove Case Use Case

Functional use case for removing a case.
Returns OperationResult for rich error handling in UI and AI consumers.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from src.contexts.cases.core.commandHandlers._state import (
    CaseRepository,
    build_case_state,
    require_project,
)
from src.contexts.cases.core.derivers import derive_remove_case
from src.contexts.cases.core.failure_events import CaseDeletionFailed
from src.contexts.projects.core.commands import RemoveCaseCommand
from src.shared.common.operation_result import OperationResult
from src.shared.common.types import CaseId
from src.shared.infra.metrics import metered_command

if TYPE_CHECKING:
    from src.shared.infra.event_bus import EventBus
    from src.shared.infra.state import ProjectState


logger = logging.getLogger("qualcoder.cases.core")


@metered_command("remove_case")
def remove_case(
    command: RemoveCaseCommand,
    state: ProjectState,
    case_repo: CaseRepository | None,
    event_bus: EventBus,
) -> OperationResult:
    """Remove a case from the current project."""
    logger.debug("remove_case: case_id=%s", command.case_id)
    if failure := require_project(state, "CASE_NOT_REMOVED/NO_PROJECT"):
        return failure

    case_id = CaseId(value=command.case_id)
    result = derive_remove_case(case_id=case_id, state=build_case_state(case_repo))

    if isinstance(result, CaseDeletionFailed):
        logger.error("remove_case failed: %s", result.event_type)
        event_bus.publish(result)
        return OperationResult.from_failure(result)

    event = result

    if case_repo:
        case_repo.delete(case_id)

    event_bus.publish(event)

    logger.info("Case removed: id=%s", command.case_id)
    return OperationResult.ok(data=event)
