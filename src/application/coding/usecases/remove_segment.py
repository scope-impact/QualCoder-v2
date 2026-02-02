"""
Remove Segment Use Case.

Functional use case for removing coding from a segment.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from returns.result import Failure, Result, Success

from src.application.coding.usecases._state import build_coding_state
from src.application.protocols import RemoveCodeCommand
from src.contexts.coding.core.derivers import derive_remove_segment
from src.contexts.coding.core.events import SegmentUncoded
from src.contexts.shared.core.failure_events import FailureEvent
from src.contexts.shared.core.types import SegmentId

if TYPE_CHECKING:
    from src.application.contexts import CodingContext
    from src.application.event_bus import EventBus


def remove_segment(
    command: RemoveCodeCommand,
    coding_ctx: CodingContext,
    event_bus: EventBus,
) -> Result[SegmentUncoded, str]:
    """
    Remove coding from a segment.

    Args:
        command: Command with segment ID
        coding_ctx: Coding context with repositories
        event_bus: Event bus for publishing events

    Returns:
        Success with SegmentUncoded event, or Failure with error message
    """
    segment_id = SegmentId(value=command.segment_id)
    state = build_coding_state(coding_ctx)

    result = derive_remove_segment(
        segment_id=segment_id,
        state=state,
    )

    # Handle failure events (now returned as events, not Failure wrapper)
    if isinstance(result, FailureEvent):
        event_bus.publish(result)  # Publish failure for policies
        return Failure(result.message)

    event: SegmentUncoded = result

    # Delete the segment
    coding_ctx.segment_repo.delete(segment_id)

    event_bus.publish(event)
    return Success(event)
