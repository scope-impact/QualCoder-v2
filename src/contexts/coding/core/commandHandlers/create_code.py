"""
Create Code Use Case.

Functional use case for creating a new code in the codebook.
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
from src.contexts.coding.core.commands import CreateCodeCommand, DeleteCodeCommand
from src.contexts.coding.core.derivers import derive_create_code
from src.contexts.coding.core.entities import Code, Color
from src.contexts.coding.core.events import CodeCreated
from src.shared.common.failure_events import FailureEvent
from src.shared.common.operation_result import OperationResult
from src.shared.common.types import CategoryId

if TYPE_CHECKING:
    from src.shared.infra.event_bus import EventBus


def create_code(
    command: CreateCodeCommand,
    code_repo: CodeRepository,
    category_repo: CategoryRepository,
    segment_repo: SegmentRepository,
    event_bus: EventBus,
) -> OperationResult:
    """
    Create a new code in the codebook.

    Args:
        command: Command with code name, color, memo, and category
        code_repo: Repository for codes
        category_repo: Repository for categories
        segment_repo: Repository for segments
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
    state = build_coding_state(code_repo, category_repo, segment_repo)

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
    code_repo.save(code)

    # Publish event
    event_bus.publish(event)

    return OperationResult.ok(
        data=code,
        rollback=DeleteCodeCommand(code_id=code.id.value, delete_segments=False),
    )
