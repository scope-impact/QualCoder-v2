"""
Set Case Attribute Use Case

Functional use case for setting an attribute on a case.
Returns OperationResult for rich error handling in UI and AI consumers.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from src.contexts.cases.core.commandHandlers._state import CaseRepository
from src.contexts.cases.core.derivers import CaseState, derive_set_case_attribute
from src.contexts.cases.core.entities import AttributeType, CaseAttribute
from src.contexts.cases.core.events import CaseAttributeSet
from src.contexts.cases.core.failure_events import AttributeSetFailed
from src.contexts.projects.core.commands import SetCaseAttributeCommand
from src.shared.common.operation_result import OperationResult
from src.shared.common.types import CaseId
from src.shared.infra.state import ProjectState

if TYPE_CHECKING:
    from src.shared.infra.event_bus import EventBus


def set_case_attribute(
    command: SetCaseAttributeCommand,
    state: ProjectState,
    case_repo: CaseRepository | None,
    event_bus: EventBus,
) -> OperationResult:
    """
    Set an attribute on a case.

    Args:
        command: Command with case ID and attribute details
        state: Project state cache
        case_repo: Repository for cases
        event_bus: Event bus for publishing events

    Returns:
        OperationResult with CaseAttributeSet event on success, or error details on failure
    """
    if state.project is None:
        return OperationResult.fail(
            error="No project is currently open",
            error_code="ATTRIBUTE_NOT_SET/NO_PROJECT",
            suggestions=("Open a project first",),
        )

    case_id = CaseId(value=command.case_id)

    # Get cases from repo (source of truth)
    all_cases = case_repo.get_all() if case_repo else []

    # Build state and derive event
    case_state = CaseState(existing_cases=tuple(all_cases))

    result = derive_set_case_attribute(
        case_id=case_id,
        attr_name=command.attr_name,
        attr_type=command.attr_type,
        attr_value=command.attr_value,
        state=case_state,
    )

    # Derivers now return failure events directly (per SKILL.md)
    if isinstance(result, AttributeSetFailed):
        event_bus.publish(result)  # Publish failure for observability
        return OperationResult.from_failure(result)

    event: CaseAttributeSet = result

    # Persist attribute
    if case_repo:
        attr = CaseAttribute(
            name=event.attr_name,
            attr_type=AttributeType(event.attr_type),
            value=event.attr_value,
        )
        case_repo.save_attribute(case_id, attr)

    # Publish event
    event_bus.publish(event)

    return OperationResult.ok(data=event)
