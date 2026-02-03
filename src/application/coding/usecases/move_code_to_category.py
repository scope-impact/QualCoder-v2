"""
Move Code to Category Use Case.

Functional use case for moving a code to a different category.
Returns OperationResult with error codes, suggestions, and rollback support.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from src.application.coding.usecases._state import build_coding_state
from src.application.protocols import MoveCodeToCategoryCommand
from src.contexts.coding.core.derivers import derive_move_code_to_category
from src.contexts.coding.core.events import CodeMovedToCategory
from src.contexts.shared.core.failure_events import FailureEvent
from src.contexts.shared.core.operation_result import OperationResult
from src.contexts.shared.core.types import CategoryId, CodeId

if TYPE_CHECKING:
    from src.application.contexts import CodingContext
    from src.application.event_bus import EventBus


def move_code_to_category(
    command: MoveCodeToCategoryCommand,
    coding_ctx: CodingContext,
    event_bus: EventBus,
) -> OperationResult:
    """
    Move a code to a different category.

    Args:
        command: Command with code ID and new category ID
        coding_ctx: Coding context with repositories
        event_bus: Event bus for publishing events

    Returns:
        OperationResult with CodeMovedToCategory event on success, or error details on failure
    """
    state = build_coding_state(coding_ctx)
    code_id = CodeId(value=command.code_id)
    new_category_id = (
        CategoryId(value=command.category_id) if command.category_id else None
    )

    result = derive_move_code_to_category(
        code_id=code_id,
        new_category_id=new_category_id,
        state=state,
    )

    # Handle failure events
    if isinstance(result, FailureEvent):
        event_bus.publish(result)
        return OperationResult.from_failure(result)

    event: CodeMovedToCategory = result

    # Update entity
    code = coding_ctx.code_repo.get_by_id(code_id)
    if code:
        updated_code = code.with_category(event.new_category_id)
        coding_ctx.code_repo.save(updated_code)

    event_bus.publish(event)

    # Get old category ID for rollback
    old_category_id = event.old_category_id.value if event.old_category_id else None
    return OperationResult.ok(
        data=event,
        rollback=MoveCodeToCategoryCommand(
            code_id=command.code_id, category_id=old_category_id
        ),
    )
