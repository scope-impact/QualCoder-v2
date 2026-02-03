"""
Delete Category Use Case.

Functional use case for deleting a code category.
Returns OperationResult with error codes and suggestions.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from src.application.coding.usecases._state import build_coding_state
from src.application.protocols import DeleteCategoryCommand
from src.contexts.coding.core.derivers import derive_delete_category
from src.contexts.coding.core.events import CategoryDeleted
from src.contexts.shared.core.failure_events import FailureEvent
from src.contexts.shared.core.operation_result import OperationResult
from src.contexts.shared.core.types import CategoryId

if TYPE_CHECKING:
    from src.application.contexts import CodingContext
    from src.application.event_bus import EventBus


def delete_category(
    command: DeleteCategoryCommand,
    coding_ctx: CodingContext,
    event_bus: EventBus,
) -> OperationResult:
    """
    Delete a code category.

    Args:
        command: Command with category ID and orphan strategy
        coding_ctx: Coding context with repositories
        event_bus: Event bus for publishing events

    Returns:
        OperationResult with CategoryDeleted event on success, or error details on failure
    """
    state = build_coding_state(coding_ctx)
    category_id = CategoryId(value=command.category_id)

    result = derive_delete_category(
        category_id=category_id,
        orphan_strategy=command.orphan_strategy,
        state=state,
    )

    # Handle failure events
    if isinstance(result, FailureEvent):
        event_bus.publish(result)
        return OperationResult.from_failure(result)

    event: CategoryDeleted = result

    # Handle orphaned codes based on strategy
    if command.orphan_strategy == "move_to_parent":
        category = coding_ctx.category_repo.get_by_id(category_id)
        parent_id = category.parent_id if category else None
        # Update codes to point to parent (or None)
        for code in coding_ctx.code_repo.get_by_category(category_id):
            updated_code = code.with_category(parent_id)
            coding_ctx.code_repo.save(updated_code)

    # Delete the category
    coding_ctx.category_repo.delete(category_id)

    event_bus.publish(event)

    # No rollback for delete - would need to recreate category and reassign codes
    return OperationResult.ok(data=event)
