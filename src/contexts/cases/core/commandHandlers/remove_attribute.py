"""
Remove Case Attribute Use Case

Functional use case for removing an attribute from a case.
Returns OperationResult for rich error handling in UI and AI consumers.
"""

from __future__ import annotations

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

if TYPE_CHECKING:
    from src.shared.infra.event_bus import EventBus
    from src.shared.infra.state import ProjectState


def remove_case_attribute(
    command: RemoveCaseAttributeCommand,
    state: ProjectState,
    case_repo: CaseRepository | None,
    event_bus: EventBus,
) -> OperationResult:
    """Remove an attribute from a case."""
    if failure := require_project(state, "ATTRIBUTE_NOT_REMOVED/NO_PROJECT"):
        return failure

    case_id = CaseId(value=command.case_id)

    result = derive_remove_case_attribute(
        case_id=case_id,
        attr_name=command.attr_name,
        state=build_case_state(case_repo),
    )

    if isinstance(result, AttributeRemovalFailed):
        event_bus.publish(result)
        return OperationResult.from_failure(result)

    event = result

    if case_repo:
        case_repo.delete_attribute(case_id, command.attr_name)

    event_bus.publish(event)

    return OperationResult.ok(data=event)
