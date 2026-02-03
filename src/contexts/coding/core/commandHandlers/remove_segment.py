"""
Remove Segment Use Case.

Functional use case for removing coding from a segment.
Returns OperationResult with error codes and suggestions.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from src.contexts.coding.core.commandHandlers._state import (
    CategoryRepository,
    CodeRepository,
    SegmentRepository,
    build_coding_state,
)
from src.contexts.coding.core.commands import RemoveCodeCommand
from src.contexts.coding.core.derivers import derive_remove_segment
from src.contexts.coding.core.events import SegmentUncoded
from src.shared.common.failure_events import FailureEvent
from src.shared.common.operation_result import OperationResult
from src.shared.common.types import SegmentId

if TYPE_CHECKING:
    from src.shared.infra.event_bus import EventBus


def remove_segment(
    command: RemoveCodeCommand,
    code_repo: CodeRepository,
    category_repo: CategoryRepository,
    segment_repo: SegmentRepository,
    event_bus: EventBus,
) -> OperationResult:
    """
    Remove coding from a segment.

    Args:
        command: Command with segment ID
        code_repo: Repository for codes
        category_repo: Repository for categories
        segment_repo: Repository for segments
        event_bus: Event bus for publishing events

    Returns:
        OperationResult with SegmentUncoded event on success, or error details on failure
    """
    segment_id = SegmentId(value=command.segment_id)
    state = build_coding_state(code_repo, category_repo, segment_repo)

    result = derive_remove_segment(
        segment_id=segment_id,
        state=state,
    )

    # Handle failure events
    if isinstance(result, FailureEvent):
        event_bus.publish(result)
        return OperationResult.from_failure(result)

    event: SegmentUncoded = result

    # Delete the segment
    segment_repo.delete(segment_id)

    event_bus.publish(event)

    # No rollback for remove - would need to recreate segment with all data
    return OperationResult.ok(data=event)
