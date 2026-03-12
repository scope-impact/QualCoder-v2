"""
Move Code to Category Use Case.

Functional use case for moving a code to a different category.
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
from src.contexts.coding.core.commands import MoveCodeToCategoryCommand
from src.contexts.coding.core.derivers import derive_move_code_to_category
from src.contexts.coding.core.events import CodeMovedToCategory
from src.shared.common.failure_events import FailureEvent
from src.shared.common.operation_result import OperationResult
from src.shared.common.types import CategoryId, CodeId
from src.shared.infra.metrics import metered_command

if TYPE_CHECKING:
    from src.shared.infra.event_bus import EventBus
    from src.shared.infra.session import Session

logger = logging.getLogger("qualcoder.coding.core")


@metered_command("move_code_to_category")
def move_code_to_category(
    command: MoveCodeToCategoryCommand,
    code_repo: CodeRepository,
    category_repo: CategoryRepository,
    segment_repo: SegmentRepository,
    event_bus: EventBus,
    session: Session | None = None,
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
    logger.debug(
        "move_code_to_category: code_id=%s, category_id=%s",
        command.code_id,
        command.category_id,
    )

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
        logger.error("move_code_to_category failed: %s", result.event_type)
        event_bus.publish(result)
        return OperationResult.from_failure(result)

    event: CodeMovedToCategory = result

    # Update entity
    code = code_repo.get_by_id(code_id)
    if code:
        updated_code = code.with_category(event.new_category_id)
        code_repo.save(updated_code)

    event_bus.publish(event)

    logger.info(
        "Code moved to category: code_id=%s, category_id=%s",
        command.code_id,
        command.category_id,
    )

    # Get old category ID for rollback
    old_category_id = event.old_category_id.value if event.old_category_id else None
    return OperationResult.ok(
        data=event,
        rollback=MoveCodeToCategoryCommand(
            code_id=command.code_id, category_id=old_category_id
        ),
    )
