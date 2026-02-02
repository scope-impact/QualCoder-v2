"""
Apply Code Use Case.

Functional use case for applying a code to a text segment.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from returns.result import Failure, Result, Success

from src.application.coding.usecases._state import build_coding_state
from src.application.protocols import ApplyCodeCommand
from src.contexts.coding.core.derivers import derive_apply_code_to_text
from src.contexts.coding.core.entities import TextSegment
from src.contexts.coding.core.events import SegmentCoded
from src.contexts.shared.core.failure_events import FailureEvent
from src.contexts.shared.core.types import CodeId, SourceId

if TYPE_CHECKING:
    from src.application.contexts import CodingContext
    from src.application.event_bus import EventBus


def apply_code(
    command: ApplyCodeCommand,
    coding_ctx: CodingContext,
    event_bus: EventBus,
    source_content_provider: Any | None = None,
) -> Result[TextSegment, str]:
    """
    Apply a code to a text segment.

    Args:
        command: Command with code ID, source ID, and position
        coding_ctx: Coding context with repositories
        event_bus: Event bus for publishing events
        source_content_provider: Optional provider for source content

    Returns:
        Success with created TextSegment, or Failure with error message
    """
    code_id = CodeId(value=command.code_id)
    source_id = SourceId(value=command.source_id)

    # Get source content for the selected text
    selected_text = _get_selected_text(
        source_content_provider,
        source_id,
        command.start_position,
        command.end_position,
    )

    # Build state with source info
    state = build_coding_state(
        coding_ctx,
        source_id=source_id,
        source_exists=True,
        source_content_provider=source_content_provider,
    )

    result = derive_apply_code_to_text(
        code_id=code_id,
        source_id=source_id,
        start=command.start_position,
        end=command.end_position,
        selected_text=selected_text,
        memo=command.memo,
        importance=command.importance,
        owner=None,
        state=state,
    )

    # Handle failure events (now returned as events, not Failure wrapper)
    if isinstance(result, FailureEvent):
        event_bus.publish(result)  # Publish failure for policies
        return Failure(result.message)

    event: SegmentCoded = result

    # Create and persist segment
    segment = TextSegment(
        id=event.segment_id,
        source_id=source_id,
        code_id=code_id,
        position=event.position,
        selected_text=event.selected_text,
        memo=event.memo,
        importance=command.importance,
        owner=event.owner,
    )
    coding_ctx.segment_repo.save(segment)

    event_bus.publish(event)
    return Success(segment)


def _get_selected_text(
    source_provider: Any | None,
    source_id: SourceId,
    start: int,
    end: int,
) -> str:
    """Get the selected text from a source."""
    if source_provider:
        content = source_provider.get_content(source_id)
        if content:
            return content[start:end]
    # Fallback: return placeholder
    return f"[text from {start} to {end}]"
