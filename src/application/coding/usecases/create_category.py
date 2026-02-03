"""
Create Category Use Case.

Functional use case for creating a new code category.
Returns OperationResult with error codes, suggestions, and rollback support.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from src.application.coding.usecases._state import build_coding_state
from src.application.protocols import CreateCategoryCommand, DeleteCategoryCommand
from src.contexts.coding.core.derivers import derive_create_category
from src.contexts.coding.core.entities import Category
from src.contexts.coding.core.events import CategoryCreated
from src.contexts.shared.core.failure_events import FailureEvent
from src.contexts.shared.core.operation_result import OperationResult
from src.contexts.shared.core.types import CategoryId

if TYPE_CHECKING:
    from src.application.contexts import CodingContext
    from src.application.event_bus import EventBus


def create_category(
    command: CreateCategoryCommand,
    coding_ctx: CodingContext,
    event_bus: EventBus,
) -> OperationResult:
    """
    Create a new code category.

    Args:
        command: Command with category name, parent ID, and memo
        coding_ctx: Coding context with repositories
        event_bus: Event bus for publishing events

    Returns:
        OperationResult with Category on success, or error details on failure
    """
    state = build_coding_state(coding_ctx)
    parent_id = CategoryId(value=command.parent_id) if command.parent_id else None

    result = derive_create_category(
        name=command.name,
        parent_id=parent_id,
        memo=command.memo,
        owner=None,
        state=state,
    )

    # Handle failure events
    if isinstance(result, FailureEvent):
        event_bus.publish(result)
        return OperationResult.from_failure(result)

    event: CategoryCreated = result

    # Create and persist category
    category = Category(
        id=event.category_id,
        name=event.name,
        parent_id=event.parent_id,
        memo=event.memo,
    )
    coding_ctx.category_repo.save(category)

    event_bus.publish(event)

    return OperationResult.ok(
        data=category,
        rollback=DeleteCategoryCommand(
            category_id=category.id.value, orphan_strategy="move_to_parent"
        ),
    )
