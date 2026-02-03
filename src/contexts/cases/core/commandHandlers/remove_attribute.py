"""
Remove Case Attribute Use Case

Functional use case for removing an attribute from a case.
Returns OperationResult for rich error handling in UI and AI consumers.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from src.contexts.cases.core.commandHandlers._state import CaseRepository
from src.contexts.cases.core.derivers import CaseState, derive_remove_case_attribute
from src.contexts.cases.core.events import CaseAttributeRemoved
from src.contexts.cases.core.failure_events import AttributeRemovalFailed
from src.contexts.projects.core.commands import RemoveCaseAttributeCommand
from src.shared.common.operation_result import OperationResult
from src.shared.common.types import CaseId
from src.shared.infra.state import ProjectState

if TYPE_CHECKING:
    from src.shared.infra.event_bus import EventBus


def remove_case_attribute(
    command: RemoveCaseAttributeCommand,
    state: ProjectState,
    case_repo: CaseRepository | None,
    event_bus: EventBus,
) -> OperationResult:
    """
    Remove an attribute from a case.

    Args:
        command: Command with case ID and attribute name
        state: Project state cache
        case_repo: Repository for cases
        event_bus: Event bus for publishing events

    Returns:
        OperationResult with CaseAttributeRemoved event on success, or error details on failure
    """
    if state.project is None:
        return OperationResult.fail(
            error="No project is currently open",
            error_code="ATTRIBUTE_NOT_REMOVED/NO_PROJECT",
            suggestions=("Open a project first",),
        )

    case_id = CaseId(value=command.case_id)

    # Get cases from repo (source of truth)
    all_cases = case_repo.get_all() if case_repo else []

    # Build state and derive event
    case_state = CaseState(existing_cases=tuple(all_cases))

    result = derive_remove_case_attribute(
        case_id=case_id,
        attr_name=command.attr_name,
        state=case_state,
    )

    # Derivers now return failure events directly (per SKILL.md)
    if isinstance(result, AttributeRemovalFailed):
        event_bus.publish(result)  # Publish failure for observability
        return OperationResult.from_failure(result)

    event: CaseAttributeRemoved = result

    # Delete attribute from repository
    if case_repo:
        case_repo.delete_attribute(case_id, command.attr_name)

    # Publish event
    event_bus.publish(event)

    return OperationResult.ok(data=event)
