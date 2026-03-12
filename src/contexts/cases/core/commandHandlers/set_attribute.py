"""
Set Case Attribute Use Case

Functional use case for setting an attribute on a case.
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
from src.contexts.cases.core.derivers import derive_set_case_attribute
from src.contexts.cases.core.entities import AttributeType, CaseAttribute
from src.contexts.cases.core.failure_events import AttributeSetFailed
from src.contexts.projects.core.commands import SetCaseAttributeCommand
from src.shared.common.operation_result import OperationResult
from src.shared.common.types import CaseId
from src.shared.infra.metrics import metered_command

if TYPE_CHECKING:
    from src.shared.infra.event_bus import EventBus
    from src.shared.infra.session import Session
    from src.shared.infra.state import ProjectState


logger = logging.getLogger("qualcoder.cases.core")


@metered_command("set_case_attribute")
def set_case_attribute(
    command: SetCaseAttributeCommand,
    state: ProjectState,
    case_repo: CaseRepository | None,
    event_bus: EventBus,
    session: Session | None = None,
) -> OperationResult:
    """Set an attribute on a case."""
    logger.debug(
        "set_case_attribute: case_id=%s, attribute_name=%s",
        command.case_id,
        command.attr_name,
    )
    if failure := require_project(state, "ATTRIBUTE_NOT_SET/NO_PROJECT"):
        return failure

    case_id = CaseId(value=command.case_id)

    result = derive_set_case_attribute(
        case_id=case_id,
        attr_name=command.attr_name,
        attr_type=command.attr_type,
        attr_value=command.attr_value,
        state=build_case_state(case_repo),
    )

    if isinstance(result, AttributeSetFailed):
        logger.error("set_case_attribute failed: %s", result.event_type)
        event_bus.publish(result)
        return OperationResult.from_failure(result)

    event = result

    if case_repo:
        attr = CaseAttribute(
            name=event.attr_name,
            attr_type=AttributeType(event.attr_type),
            value=event.attr_value,
        )
        case_repo.save_attribute(case_id, attr)

    event_bus.publish(event)

    logger.info(
        "Attribute set: case_id=%s, attribute_name=%s",
        command.case_id,
        command.attr_name,
    )
    return OperationResult.ok(data=event)
