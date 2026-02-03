"""
Remove Segment Use Case.

Functional use case for removing coding from a segment.
Returns OperationResult with error codes and suggestions.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from src.application.coding.usecases._state import build_coding_state
from src.application.protocols import RemoveCodeCommand
from src.contexts.coding.core.derivers import derive_remove_segment
from src.contexts.coding.core.events import SegmentUncoded
from src.contexts.shared.core.failure_events import FailureEvent
from src.contexts.shared.core.operation_result import OperationResult
from src.contexts.shared.core.types import SegmentId

if TYPE_CHECKING:
    from src.application.contexts import CodingContext
    from src.application.event_bus import EventBus


def remove_segment(
    command: RemoveCodeCommand,
    coding_ctx: CodingContext,
    event_bus: EventBus,
) -> OperationResult:
    """
    Remove coding from a segment.

    Args:
        command: Command with segment ID
        coding_ctx: Coding context with repositories
        event_bus: Event bus for publishing events

    Returns:
        OperationResult with SegmentUncoded event on success, or error details on failure
    """
    segment_id = SegmentId(value=command.segment_id)
    state = build_coding_state(coding_ctx)

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
    coding_ctx.segment_repo.delete(segment_id)

    event_bus.publish(event)

    # No rollback for remove - would need to recreate segment with all data
    return OperationResult.ok(data=event)
