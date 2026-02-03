"""
Create Code Use Case.

Functional use case for creating a new code in the codebook.
Returns OperationResult with error codes, suggestions, and rollback support.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from src.application.coding.usecases._state import build_coding_state
from src.application.protocols import CreateCodeCommand, DeleteCodeCommand
from src.contexts.coding.core.derivers import derive_create_code
from src.contexts.coding.core.entities import Code, Color
from src.contexts.coding.core.events import CodeCreated
from src.contexts.shared.core.failure_events import FailureEvent
from src.contexts.shared.core.operation_result import OperationResult
from src.contexts.shared.core.types import CategoryId

if TYPE_CHECKING:
    from src.application.contexts import CodingContext
    from src.application.event_bus import EventBus


def create_code(
    command: CreateCodeCommand,
    coding_ctx: CodingContext,
    event_bus: EventBus,
) -> OperationResult:
    """
    Create a new code in the codebook.

    Args:
        command: Command with code name, color, memo, and category
        coding_ctx: Coding context with repositories
        event_bus: Event bus for publishing events

    Returns:
        OperationResult with Code on success, or error details on failure
    """
    # Parse color
    try:
        color = Color.from_hex(command.color)
    except ValueError as e:
        return OperationResult.fail(
            error=str(e),
            error_code="CODE_NOT_CREATED/INVALID_COLOR",
            suggestions=("Use a valid hex color like #FF0000",),
        )

    # Build current state
    state = build_coding_state(coding_ctx)

    # Parse category ID
    category_id = CategoryId(value=command.category_id) if command.category_id else None

    # Derive event or failure
    result = derive_create_code(
        name=command.name,
        color=color,
        memo=command.memo,
        category_id=category_id,
        owner=None,
        state=state,
    )

    # Handle failure events
    if isinstance(result, FailureEvent):
        event_bus.publish(result)
        return OperationResult.from_failure(result)

    event: CodeCreated = result

    # Create and persist the entity
    code = Code(
        id=event.code_id,
        name=event.name,
        color=event.color,
        memo=event.memo,
        category_id=event.category_id,
        owner=event.owner,
    )
    coding_ctx.code_repo.save(code)

    # Publish event
    event_bus.publish(event)

    return OperationResult.ok(
        data=code,
        rollback=DeleteCodeCommand(code_id=code.id.value, delete_segments=False),
    )
