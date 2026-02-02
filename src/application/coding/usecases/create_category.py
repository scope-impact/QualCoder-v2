"""
Create Category Use Case.

Functional use case for creating a new code category.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from returns.result import Failure, Result, Success

from src.application.coding.usecases._state import build_coding_state
from src.application.protocols import CreateCategoryCommand
from src.contexts.coding.core.derivers import derive_create_category
from src.contexts.coding.core.entities import Category
from src.contexts.coding.core.events import CategoryCreated
from src.contexts.shared.core.failure_events import FailureEvent
from src.contexts.shared.core.types import CategoryId

if TYPE_CHECKING:
    from src.application.contexts import CodingContext
    from src.application.event_bus import EventBus


def create_category(
    command: CreateCategoryCommand,
    coding_ctx: CodingContext,
    event_bus: EventBus,
) -> Result[Category, str]:
    """
    Create a new code category.

    Args:
        command: Command with category name, parent ID, and memo
        coding_ctx: Coding context with repositories
        event_bus: Event bus for publishing events

    Returns:
        Success with created Category, or Failure with error message
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

    # Handle failure events (now returned as events, not Failure wrapper)
    if isinstance(result, FailureEvent):
        event_bus.publish(result)  # Publish failure for policies
        return Failure(result.message)

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
    return Success(category)
