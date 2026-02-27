"""
Create Case Use Case

Functional use case for creating a new case.
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
from src.contexts.cases.core.derivers import derive_create_case
from src.contexts.cases.core.entities import Case
from src.contexts.cases.core.failure_events import CaseCreationFailed
from src.contexts.projects.core.commands import CreateCaseCommand, RemoveCaseCommand
from src.shared.common.operation_result import OperationResult
from src.shared.infra.metrics import metered_command
from src.shared.infra.state import ProjectState

if TYPE_CHECKING:
    from src.shared.infra.event_bus import EventBus


logger = logging.getLogger("qualcoder.cases.core")


@metered_command("create_case")
def create_case(
    command: CreateCaseCommand,
    state: ProjectState,
    case_repo: CaseRepository | None,
    event_bus: EventBus,
) -> OperationResult:
    """Create a new case in the current project."""
    logger.debug("create_case: name=%s", command.name)
    if failure := require_project(state, "CASE_NOT_CREATED/NO_PROJECT"):
        return failure

    result = derive_create_case(
        name=command.name,
        description=command.description,
        memo=command.memo,
        state=build_case_state(case_repo),
    )

    if isinstance(result, CaseCreationFailed):
        logger.error("create_case failed: %s", result.event_type)
        event_bus.publish(result)
        return OperationResult.from_failure(result)

    event = result
    case = Case(
        id=event.case_id,
        name=event.name,
        description=event.description,
        memo=event.memo,
    )

    if case_repo:
        case_repo.save(case)

    event_bus.publish(event)

    logger.info("Case created: id=%s", case.id.value)
    return OperationResult.ok(
        data=case,
        rollback=RemoveCaseCommand(case_id=case.id.value),
    )
