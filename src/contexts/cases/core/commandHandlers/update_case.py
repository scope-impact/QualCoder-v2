"""
Update Case Use Case

Functional use case for updating case metadata.
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
from src.contexts.cases.core.derivers import derive_update_case
from src.contexts.cases.core.entities import Case
from src.contexts.cases.core.failure_events import CaseUpdateFailed
from src.contexts.projects.core.commands import UpdateCaseCommand
from src.shared.common.operation_result import OperationResult
from src.shared.common.types import CaseId
from src.shared.infra.metrics import metered_command

if TYPE_CHECKING:
    from src.shared.infra.event_bus import EventBus
    from src.shared.infra.session import Session
    from src.shared.infra.state import ProjectState


logger = logging.getLogger("qualcoder.cases.core")


@metered_command("update_case")
def update_case(
    command: UpdateCaseCommand,
    state: ProjectState,
    case_repo: CaseRepository | None,
    event_bus: EventBus,
    session: Session | None = None,
) -> OperationResult:
    """Update an existing case."""
    logger.debug("update_case: case_id=%s", command.case_id)
    if failure := require_project(state, "CASE_NOT_UPDATED/NO_PROJECT"):
        return failure

    case_id = CaseId(value=command.case_id)

    result = derive_update_case(
        case_id=case_id,
        name=command.name,
        description=command.description,
        memo=command.memo,
        state=build_case_state(case_repo),
    )

    if isinstance(result, CaseUpdateFailed):
        logger.error("update_case failed: %s", result.event_type)
        event_bus.publish(result)
        return OperationResult.from_failure(result)

    event = result
    updated_case = Case(
        id=event.case_id,
        name=event.name,
        description=event.description,
        memo=event.memo,
    )

    if case_repo:
        case_repo.save(updated_case)

    event_bus.publish(event)

    logger.info("Case updated: id=%s", command.case_id)
    return OperationResult.ok(data=updated_case)
