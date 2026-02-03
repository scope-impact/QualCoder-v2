"""
Rename Code Use Case.

Functional use case for renaming an existing code.
Returns OperationResult with error codes, suggestions, and rollback support.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from src.application.coding.usecases._state import build_coding_state
from src.application.protocols import RenameCodeCommand
from src.contexts.coding.core.derivers import derive_rename_code
from src.contexts.coding.core.events import CodeRenamed
from src.contexts.shared.core.failure_events import FailureEvent
from src.contexts.shared.core.operation_result import OperationResult
from src.contexts.shared.core.types import CodeId

if TYPE_CHECKING:
    from src.application.contexts import CodingContext
    from src.application.event_bus import EventBus


def rename_code(
    command: RenameCodeCommand,
    coding_ctx: CodingContext,
    event_bus: EventBus,
) -> OperationResult:
    """
    Rename an existing code.

    Args:
        command: Command with code ID and new name
        coding_ctx: Coding context with repositories
        event_bus: Event bus for publishing events

    Returns:
        OperationResult with CodeRenamed event on success, or error details on failure
    """
    state = build_coding_state(coding_ctx)
    code_id = CodeId(value=command.code_id)

    result = derive_rename_code(
        code_id=code_id,
        new_name=command.new_name,
        state=state,
    )

    # Handle failure events
    if isinstance(result, FailureEvent):
        event_bus.publish(result)
        return OperationResult.from_failure(result)

    event: CodeRenamed = result

    # Update entity
    code = coding_ctx.code_repo.get_by_id(code_id)
    if code:
        updated_code = code.with_name(event.new_name)
        coding_ctx.code_repo.save(updated_code)

    event_bus.publish(event)

    return OperationResult.ok(
        data=event,
        rollback=RenameCodeCommand(code_id=command.code_id, new_name=event.old_name),
    )
