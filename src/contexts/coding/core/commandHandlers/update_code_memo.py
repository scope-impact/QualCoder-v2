"""
Update Code Memo Use Case.

Functional use case for updating a code's memo.
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
from src.contexts.coding.core.commands import UpdateCodeMemoCommand
from src.contexts.coding.core.derivers import derive_update_code_memo
from src.contexts.coding.core.events import CodeMemoUpdated
from src.shared.common.failure_events import FailureEvent
from src.shared.common.operation_result import OperationResult
from src.shared.common.types import CodeId

if TYPE_CHECKING:
    from src.shared.infra.event_bus import EventBus


def update_code_memo(
    command: UpdateCodeMemoCommand,
    code_repo: CodeRepository,
    category_repo: CategoryRepository,
    segment_repo: SegmentRepository,
    event_bus: EventBus,
) -> OperationResult:
    """
    Update a code's memo.

    Args:
        command: Command with code ID and new memo
        code_repo: Repository for codes
        category_repo: Repository for categories
        segment_repo: Repository for segments
        event_bus: Event bus for publishing events

    Returns:
        OperationResult with CodeMemoUpdated event on success, or error details on failure
    """
    state = build_coding_state(code_repo, category_repo, segment_repo)
    code_id = CodeId(value=command.code_id)

    result = derive_update_code_memo(
        code_id=code_id,
        new_memo=command.new_memo,
        state=state,
    )

    # Handle failure events
    if isinstance(result, FailureEvent):
        event_bus.publish(result)
        return OperationResult.from_failure(result)

    event: CodeMemoUpdated = result

    # Update entity
    code = code_repo.get_by_id(code_id)
    if code:
        updated_code = code.with_memo(event.new_memo)
        code_repo.save(updated_code)

    event_bus.publish(event)

    return OperationResult.ok(
        data=event,
        rollback=UpdateCodeMemoCommand(
            code_id=command.code_id, new_memo=event.old_memo
        ),
    )
