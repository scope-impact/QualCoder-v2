"""
Update Code Memo Use Case.

Functional use case for updating a code's memo.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from returns.result import Failure, Result, Success

from src.application.coding.usecases._state import build_coding_state
from src.application.protocols import UpdateCodeMemoCommand
from src.contexts.coding.core.derivers import derive_update_code_memo
from src.contexts.coding.core.events import CodeMemoUpdated
from src.contexts.shared.core.failure_events import FailureEvent
from src.contexts.shared.core.types import CodeId

if TYPE_CHECKING:
    from src.application.contexts import CodingContext
    from src.application.event_bus import EventBus


def update_code_memo(
    command: UpdateCodeMemoCommand,
    coding_ctx: CodingContext,
    event_bus: EventBus,
) -> Result[CodeMemoUpdated, str]:
    """
    Update a code's memo.

    Args:
        command: Command with code ID and new memo
        coding_ctx: Coding context with repositories
        event_bus: Event bus for publishing events

    Returns:
        Success with CodeMemoUpdated event, or Failure with error message
    """
    state = build_coding_state(coding_ctx)
    code_id = CodeId(value=command.code_id)

    result = derive_update_code_memo(
        code_id=code_id,
        new_memo=command.new_memo,
        state=state,
    )

    # Handle failure events (now returned as events, not Failure wrapper)
    if isinstance(result, FailureEvent):
        event_bus.publish(result)  # Publish failure for policies
        return Failure(result.message)

    event: CodeMemoUpdated = result

    # Update entity
    code = coding_ctx.code_repo.get_by_id(code_id)
    if code:
        updated_code = code.with_memo(event.new_memo)
        coding_ctx.code_repo.save(updated_code)

    event_bus.publish(event)
    return Success(event)
