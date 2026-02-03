"""
Change Code Color Use Case.

Functional use case for changing a code's color.
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
from src.contexts.coding.core.commands import ChangeCodeColorCommand
from src.contexts.coding.core.derivers import derive_change_code_color
from src.contexts.coding.core.entities import Color
from src.contexts.coding.core.events import CodeColorChanged
from src.shared.common.failure_events import FailureEvent
from src.shared.common.operation_result import OperationResult
from src.shared.common.types import CodeId

if TYPE_CHECKING:
    from src.shared.infra.event_bus import EventBus


def change_code_color(
    command: ChangeCodeColorCommand,
    code_repo: CodeRepository,
    category_repo: CategoryRepository,
    segment_repo: SegmentRepository,
    event_bus: EventBus,
) -> OperationResult:
    """
    Change a code's color.

    Args:
        command: Command with code ID and new color
        code_repo: Repository for codes
        category_repo: Repository for categories
        segment_repo: Repository for segments
        event_bus: Event bus for publishing events

    Returns:
        OperationResult with CodeColorChanged event on success, or error details on failure
    """
    state = build_coding_state(code_repo, category_repo, segment_repo)
    code_id = CodeId(value=command.code_id)

    try:
        new_color = Color.from_hex(command.new_color)
    except ValueError as e:
        return OperationResult.fail(
            error=str(e),
            error_code="CODE_COLOR_NOT_CHANGED/INVALID_COLOR",
            suggestions=("Use a valid hex color like #FF0000",),
        )

    result = derive_change_code_color(
        code_id=code_id,
        new_color=new_color,
        state=state,
    )

    # Handle failure events
    if isinstance(result, FailureEvent):
        event_bus.publish(result)
        return OperationResult.from_failure(result)

    event: CodeColorChanged = result

    # Update entity
    code = code_repo.get_by_id(code_id)
    if code:
        updated_code = code.with_color(event.new_color)
        code_repo.save(updated_code)

    event_bus.publish(event)

    return OperationResult.ok(
        data=event,
        rollback=ChangeCodeColorCommand(
            code_id=command.code_id, new_color=event.old_color.to_hex()
        ),
    )
