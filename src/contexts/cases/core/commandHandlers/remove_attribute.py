"""
Remove Case Attribute Use Case

Functional use case for removing an attribute from a case.
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
from src.contexts.cases.core.derivers import derive_remove_case_attribute
from src.contexts.cases.core.failure_events import AttributeRemovalFailed
from src.contexts.projects.core.commands import RemoveCaseAttributeCommand
from src.shared.common.operation_result import OperationResult
from src.shared.common.types import CaseId
from src.shared.infra.metrics import metered_command

if TYPE_CHECKING:
    from src.shared.infra.event_bus import EventBus
    from src.shared.infra.state import ProjectState


logger = logging.getLogger("qualcoder.cases.core")


@metered_command("remove_case_attribute")
def remove_case_attribute(
    command: RemoveCaseAttributeCommand,
    state: ProjectState,
    case_repo: CaseRepository | None,
    event_bus: EventBus,
) -> OperationResult:
    """Remove an attribute from a case."""
    logger.debug(
        "remove_case_attribute: case_id=%s, attribute_name=%s",
        command.case_id,
        command.attr_name,
    )
    if failure := require_project(state, "ATTRIBUTE_NOT_REMOVED/NO_PROJECT"):
        return failure

    case_id = CaseId(value=command.case_id)

    result = derive_remove_case_attribute(
        case_id=case_id,
        attr_name=command.attr_name,
        state=build_case_state(case_repo),
    )

    if isinstance(result, AttributeRemovalFailed):
        logger.error("remove_case_attribute failed: %s", result.event_type)
        event_bus.publish(result)
        return OperationResult.from_failure(result)

    event = result

    if case_repo:
        case_repo.delete_attribute(case_id, command.attr_name)

    event_bus.publish(event)

    logger.info(
        "Attribute removed: case_id=%s, attribute_name=%s",
        command.case_id,
        command.attr_name,
    )
    return OperationResult.ok(data=event)
