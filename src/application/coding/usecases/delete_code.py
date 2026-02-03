"""
Delete Code Use Case.

Functional use case for deleting a code from the codebook.
Returns OperationResult with error codes and suggestions.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from src.application.coding.usecases._state import build_coding_state
from src.application.protocols import DeleteCodeCommand
from src.contexts.coding.core.derivers import derive_delete_code
from src.contexts.coding.core.events import CodeDeleted
from src.contexts.shared.core.failure_events import FailureEvent
from src.contexts.shared.core.operation_result import OperationResult
from src.contexts.shared.core.types import CodeId

if TYPE_CHECKING:
    from src.application.contexts import CodingContext
    from src.application.event_bus import EventBus


def delete_code(
    command: DeleteCodeCommand,
    coding_ctx: CodingContext,
    event_bus: EventBus,
) -> OperationResult:
    """
    Delete a code from the codebook.

    Args:
        command: Command with code ID and delete_segments flag
        coding_ctx: Coding context with repositories
        event_bus: Event bus for publishing events

    Returns:
        OperationResult with CodeDeleted event on success, or error details on failure
    """
    state = build_coding_state(coding_ctx)
    code_id = CodeId(value=command.code_id)

    result = derive_delete_code(
        code_id=code_id,
        delete_segments=command.delete_segments,
        state=state,
    )

    # Handle failure events
    if isinstance(result, FailureEvent):
        event_bus.publish(result)
        return OperationResult.from_failure(result)

    event: CodeDeleted = result

    # Delete segments if requested
    if command.delete_segments:
        coding_ctx.segment_repo.delete_by_code(code_id)

    # Delete the code
    coding_ctx.code_repo.delete(code_id)

    event_bus.publish(event)

    # No rollback for delete - would need to recreate code with all data
    return OperationResult.ok(data=event)
