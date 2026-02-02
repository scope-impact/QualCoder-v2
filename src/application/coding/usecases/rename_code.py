"""
Rename Code Use Case.

Functional use case for renaming an existing code.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from returns.result import Failure, Result, Success

from src.application.coding.usecases._state import build_coding_state
from src.application.protocols import RenameCodeCommand
from src.contexts.coding.core.derivers import derive_rename_code
from src.contexts.coding.core.events import CodeRenamed
from src.contexts.shared.core.failure_events import FailureEvent
from src.contexts.shared.core.types import CodeId

if TYPE_CHECKING:
    from src.application.contexts import CodingContext
    from src.application.event_bus import EventBus


def rename_code(
    command: RenameCodeCommand,
    coding_ctx: CodingContext,
    event_bus: EventBus,
) -> Result[CodeRenamed, str]:
    """
    Rename an existing code.

    Args:
        command: Command with code ID and new name
        coding_ctx: Coding context with repositories
        event_bus: Event bus for publishing events

    Returns:
        Success with CodeRenamed event, or Failure with error message
    """
    state = build_coding_state(coding_ctx)
    code_id = CodeId(value=command.code_id)

    result = derive_rename_code(
        code_id=code_id,
        new_name=command.new_name,
        state=state,
    )

    # Handle failure events (now returned as events, not Failure wrapper)
    if isinstance(result, FailureEvent):
        event_bus.publish(result)  # Publish failure for policies
        return Failure(result.message)

    event: CodeRenamed = result

    # Update entity
    code = coding_ctx.code_repo.get_by_id(code_id)
    if code:
        updated_code = code.with_name(event.new_name)
        coding_ctx.code_repo.save(updated_code)

    event_bus.publish(event)
    return Success(event)
