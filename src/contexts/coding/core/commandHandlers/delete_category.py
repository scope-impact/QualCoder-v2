"""
Delete Category Use Case.

Functional use case for deleting a code category.
Returns OperationResult with error codes and suggestions.
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
from src.contexts.coding.core.commands import DeleteCategoryCommand
from src.contexts.coding.core.derivers import derive_delete_category
from src.contexts.coding.core.events import CategoryDeleted
from src.shared.common.failure_events import FailureEvent
from src.shared.common.operation_result import OperationResult
from src.shared.common.types import CategoryId
from src.shared.infra.metrics import metered_command

if TYPE_CHECKING:
    from src.shared.infra.event_bus import EventBus
    from src.shared.infra.session import Session

logger = logging.getLogger("qualcoder.coding.core")


@metered_command("delete_category")
def delete_category(
    command: DeleteCategoryCommand,
    code_repo: CodeRepository,
    category_repo: CategoryRepository,
    segment_repo: SegmentRepository,
    event_bus: EventBus,
    session: Session | None = None,
) -> OperationResult:
    """
    Delete a code category.

    Args:
        command: Command with category ID and orphan strategy
        code_repo: Repository for codes
        category_repo: Repository for categories
        segment_repo: Repository for segments
        event_bus: Event bus for publishing events

    Returns:
        OperationResult with CategoryDeleted event on success, or error details on failure
    """
    logger.debug("delete_category: category_id=%s", command.category_id)

    state = build_coding_state(code_repo, category_repo, segment_repo)
    category_id = CategoryId(value=command.category_id)

    result = derive_delete_category(
        category_id=category_id,
        orphan_strategy=command.orphan_strategy,
        state=state,
    )

    # Handle failure events
    if isinstance(result, FailureEvent):
        logger.error("delete_category failed: %s", result.event_type)
        event_bus.publish(result)
        return OperationResult.from_failure(result)

    event: CategoryDeleted = result

    # Atomic: handle orphaned codes + delete category in one transaction
    from src.shared.infra.unit_of_work import UnitOfWork

    with UnitOfWork(category_repo._conn) as uow:
        if command.orphan_strategy == "move_to_parent":
            category = category_repo.get_by_id(category_id)
            parent_id = category.parent_id if category else None
            for code in code_repo.get_by_category(category_id):
                updated_code = code.with_category(parent_id)
                code_repo.save(updated_code)
        category_repo.delete(category_id)
        uow.commit()
    if session:
        session.commit()

    event_bus.publish(event)

    logger.info("Category deleted: category_id=%s", command.category_id)

    return OperationResult.ok(data=event)
