"""
Move Code to Category Use Case.

Functional use case for moving a code to a different category.
Returns OperationResult with error codes, suggestions, and rollback support.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from src.contexts.coding.core.commandHandlers._state import (
    CategoryRepository,
    CodeRepository,
    SegmentRepository,
    build_coding_state,
)
from src.contexts.coding.core.commands import MoveCodeToCategoryCommand
from src.contexts.coding.core.derivers import derive_move_code_to_category
from src.contexts.coding.core.events import CodeMovedToCategory
from src.shared.common.failure_events import FailureEvent
from src.shared.common.operation_result import OperationResult
from src.shared.common.types import CategoryId, CodeId

if TYPE_CHECKING:
    from src.shared.infra.event_bus import EventBus


def move_code_to_category(
    command: MoveCodeToCategoryCommand,
    code_repo: CodeRepository,
    category_repo: CategoryRepository,
    segment_repo: SegmentRepository,
    event_bus: EventBus,
) -> OperationResult:
    """
    Move a code to a different category.

    Args:
        command: Command with code ID and new category ID
        code_repo: Repository for codes
        category_repo: Repository for categories
        segment_repo: Repository for segments
        event_bus: Event bus for publishing events

    Returns:
        OperationResult with CodeMovedToCategory event on success, or error details on failure
    """
    state = build_coding_state(code_repo, category_repo, segment_repo)
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
    code = code_repo.get_by_id(code_id)
    if code:
        updated_code = code.with_category(event.new_category_id)
        code_repo.save(updated_code)

    event_bus.publish(event)

    # Get old category ID for rollback
    old_category_id = event.old_category_id.value if event.old_category_id else None
    return OperationResult.ok(
        data=event,
        rollback=MoveCodeToCategoryCommand(
            code_id=command.code_id, category_id=old_category_id
        ),
    )
