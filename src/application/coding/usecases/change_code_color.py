"""
Change Code Color Use Case.

Functional use case for changing a code's color.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from returns.result import Failure, Result, Success

from src.application.coding.usecases._state import build_coding_state
from src.application.protocols import ChangeCodeColorCommand
from src.contexts.coding.core.derivers import derive_change_code_color
from src.contexts.coding.core.entities import Color
from src.contexts.coding.core.events import CodeColorChanged
from src.contexts.shared.core.failure_events import FailureEvent
from src.contexts.shared.core.types import CodeId

if TYPE_CHECKING:
    from src.application.contexts import CodingContext
    from src.application.event_bus import EventBus


def change_code_color(
    command: ChangeCodeColorCommand,
    coding_ctx: CodingContext,
    event_bus: EventBus,
) -> Result[CodeColorChanged, str]:
    """
    Change a code's color.

    Args:
        command: Command with code ID and new color
        coding_ctx: Coding context with repositories
        event_bus: Event bus for publishing events

    Returns:
        Success with CodeColorChanged event, or Failure with error message
    """
    state = build_coding_state(coding_ctx)
    code_id = CodeId(value=command.code_id)

    try:
        new_color = Color.from_hex(command.new_color)
    except ValueError as e:
        return Failure(str(e))

    result = derive_change_code_color(
        code_id=code_id,
        new_color=new_color,
        state=state,
    )

    # Handle failure events (now returned as events, not Failure wrapper)
    if isinstance(result, FailureEvent):
        event_bus.publish(result)  # Publish failure for policies
        return Failure(result.message)

    event: CodeColorChanged = result

    # Update entity
    code = coding_ctx.code_repo.get_by_id(code_id)
    if code:
        updated_code = code.with_color(event.new_color)
        coding_ctx.code_repo.save(updated_code)

    event_bus.publish(event)
    return Success(event)
