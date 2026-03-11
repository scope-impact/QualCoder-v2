"""
Create Category Use Case.

Functional use case for creating a new code category.
Returns OperationResult with error codes, suggestions, and rollback support.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from src.contexts.coding.core.commandHandlers._state import (
    CategoryRepository,
    CodeRepository,
    SegmentRepository,
    build_coding_state,
)
from src.contexts.coding.core.commands import (
    CreateCategoryCommand,
    DeleteCategoryCommand,
)
from src.contexts.coding.core.derivers import derive_create_category
from src.contexts.coding.core.entities import Category
from src.contexts.coding.core.events import CategoryCreated
from src.shared.common.failure_events import FailureEvent
from src.shared.common.operation_result import OperationResult
from src.shared.common.types import CategoryId
from src.shared.infra.metrics import metered_command

if TYPE_CHECKING:
    from src.shared.infra.event_bus import EventBus
    from src.shared.infra.session import Session

logger = logging.getLogger("qualcoder.coding.core")


@metered_command("create_category")
def create_category(
    command: CreateCategoryCommand,
    code_repo: CodeRepository,
    category_repo: CategoryRepository,
    segment_repo: SegmentRepository,
    event_bus: EventBus,
    session: Session | None = None,
) -> OperationResult:
    """
    Create a new code category.

    Args:
        command: Command with category name, parent ID, and memo
        code_repo: Repository for codes
        category_repo: Repository for categories
        segment_repo: Repository for segments
        event_bus: Event bus for publishing events

    Returns:
        OperationResult with Category on success, or error details on failure
    """
    logger.debug("create_category: name=%s", command.name)

    state = build_coding_state(code_repo, category_repo, segment_repo)
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
        logger.error("create_category failed: %s", result.event_type)
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
    category_repo.save(category)
    if session:
        session.commit()

    event_bus.publish(event)

    logger.info("Category created: id=%s, name=%s", category.id.value, category.name)

    return OperationResult.ok(
        data=category,
        rollback=DeleteCategoryCommand(
            category_id=category.id.value, orphan_strategy="move_to_parent"
        ),
    )
