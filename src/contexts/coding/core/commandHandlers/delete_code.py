"""
Delete Code Use Case.

Functional use case for deleting a code from the codebook.
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
from src.contexts.coding.core.commands import DeleteCodeCommand
from src.contexts.coding.core.derivers import derive_delete_code
from src.contexts.coding.core.events import CodeDeleted
from src.shared.common.failure_events import FailureEvent
from src.shared.common.operation_result import OperationResult
from src.shared.common.types import CodeId
from src.shared.infra.metrics import metered_command

if TYPE_CHECKING:
    from src.shared.infra.event_bus import EventBus
    from src.shared.infra.session import Session

logger = logging.getLogger("qualcoder.coding.core")


@metered_command("delete_code")
def delete_code(
    command: DeleteCodeCommand,
    code_repo: CodeRepository,
    category_repo: CategoryRepository,
    segment_repo: SegmentRepository,
    event_bus: EventBus,
    session: Session | None = None,
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
    logger.debug("delete_code: code_id=%s", command.code_id)

    state = build_coding_state(code_repo, category_repo, segment_repo)
    code_id = CodeId(value=command.code_id)

    result = derive_delete_code(
        code_id=code_id,
        delete_segments=command.delete_segments,
        state=state,
    )

    # Handle failure events
    if isinstance(result, FailureEvent):
        logger.error("delete_code failed: %s", result.event_type)
        event_bus.publish(result)
        return OperationResult.from_failure(result)

    event: CodeDeleted = result

    # Delete segments + code, then commit via session
    if command.delete_segments:
        segment_repo.delete_by_code(code_id)
    code_repo.delete(code_id)
    if session:
        session.commit()

    event_bus.publish(event)

    logger.info("Code deleted: code_id=%s", command.code_id)

    return OperationResult.ok(data=event)
