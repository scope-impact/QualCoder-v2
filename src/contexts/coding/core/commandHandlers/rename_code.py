"""
Rename Code Use Case.

Functional use case for renaming an existing code.
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
from src.contexts.coding.core.commands import RenameCodeCommand
from src.contexts.coding.core.derivers import derive_rename_code
from src.contexts.coding.core.events import CodeRenamed
from src.shared.common.failure_events import FailureEvent
from src.shared.common.operation_result import OperationResult
from src.shared.common.types import CodeId
from src.shared.infra.metrics import metered_command

if TYPE_CHECKING:
    from src.shared.infra.event_bus import EventBus
    from src.shared.infra.session import Session

logger = logging.getLogger("qualcoder.coding.core")


@metered_command("rename_code")
def rename_code(
    command: RenameCodeCommand,
    code_repo: CodeRepository,
    category_repo: CategoryRepository,
    segment_repo: SegmentRepository,
    event_bus: EventBus,
    session: Session | None = None,
) -> OperationResult:
    """
    Rename an existing code.

    Args:
        command: Command with code ID and new name
        code_repo: Repository for codes
        category_repo: Repository for categories
        segment_repo: Repository for segments
        event_bus: Event bus for publishing events

    Returns:
        OperationResult with CodeRenamed event on success, or error details on failure
    """
    logger.debug(
        "rename_code: code_id=%s, new_name=%s", command.code_id, command.new_name
    )

    state = build_coding_state(code_repo, category_repo, segment_repo)
    code_id = CodeId(value=command.code_id)

    result = derive_rename_code(
        code_id=code_id,
        new_name=command.new_name,
        state=state,
    )

    # Handle failure events
    if isinstance(result, FailureEvent):
        logger.error("rename_code failed: %s", result.event_type)
        event_bus.publish(result)
        return OperationResult.from_failure(result)

    event: CodeRenamed = result

    # Update entity
    code = code_repo.get_by_id(code_id)
    if code:
        updated_code = code.with_name(event.new_name)
        code_repo.save(updated_code)

    event_bus.publish(event)

    logger.info(
        "Code renamed: code_id=%s, new_name=%s", command.code_id, command.new_name
    )

    return OperationResult.ok(
        data=event,
        rollback=RenameCodeCommand(code_id=command.code_id, new_name=event.old_name),
    )
