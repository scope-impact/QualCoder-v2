"""
Delete Code Use Case.

Functional use case for deleting a code from the codebook.
Returns OperationResult with error codes and suggestions.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from src.contexts.coding.core.commandHandlers._state import (
    CategoryRepository,
    CodeRepository,
    SegmentRepository,
    build_coding_state,
)
from src.contexts.coding.core.commands import DeleteCodeCommand
from src.contexts.coding.core.derivers import derive_delete_code
from src.contexts.coding.core.events import CodeDeleted
from src.shared.common.failure_events import FailureEvent
from src.shared.common.operation_result import OperationResult
from src.shared.common.types import CodeId

if TYPE_CHECKING:
    from src.shared.infra.event_bus import EventBus


def delete_code(
    command: DeleteCodeCommand,
    code_repo: CodeRepository,
    category_repo: CategoryRepository,
    segment_repo: SegmentRepository,
    event_bus: EventBus,
) -> OperationResult:
    """
    Delete a code from the codebook.

    Args:
        command: Command with code ID and delete_segments flag
        code_repo: Repository for codes
        category_repo: Repository for categories
        segment_repo: Repository for segments
        event_bus: Event bus for publishing events

    Returns:
        OperationResult with CodeDeleted event on success, or error details on failure
    """
    state = build_coding_state(code_repo, category_repo, segment_repo)
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
        segment_repo.delete_by_code(code_id)

    # Delete the code
    code_repo.delete(code_id)

    event_bus.publish(event)

    # No rollback for delete - would need to recreate code with all data
    return OperationResult.ok(data=event)
