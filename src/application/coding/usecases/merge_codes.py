"""
Merge Codes Use Case.

Functional use case for merging source code into target code.
Returns OperationResult with error codes and suggestions.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from src.application.coding.usecases._state import build_coding_state
from src.application.protocols import MergeCodesCommand
from src.contexts.coding.core.derivers import derive_merge_codes
from src.contexts.coding.core.events import CodesMerged
from src.contexts.shared.core.failure_events import FailureEvent
from src.contexts.shared.core.operation_result import OperationResult
from src.contexts.shared.core.types import CodeId

if TYPE_CHECKING:
    from src.application.contexts import CodingContext
    from src.application.event_bus import EventBus


def merge_codes(
    command: MergeCodesCommand,
    coding_ctx: CodingContext,
    event_bus: EventBus,
) -> OperationResult:
    """
    Merge source code into target code.

    Args:
        command: Command with source and target code IDs
        coding_ctx: Coding context with repositories
        event_bus: Event bus for publishing events

    Returns:
        OperationResult with CodesMerged event on success, or error details on failure
    """
    state = build_coding_state(coding_ctx)
    source_code_id = CodeId(value=command.source_code_id)
    target_code_id = CodeId(value=command.target_code_id)

    result = derive_merge_codes(
        source_code_id=source_code_id,
        target_code_id=target_code_id,
        state=state,
    )

    # Handle failure events
    if isinstance(result, FailureEvent):
        event_bus.publish(result)
        return OperationResult.from_failure(result)

    event: CodesMerged = result

    # Reassign segments from source to target
    coding_ctx.segment_repo.reassign_code(source_code_id, target_code_id)

    # Delete the source code
    coding_ctx.code_repo.delete(source_code_id)

    event_bus.publish(event)

    # No rollback for merge - would need to recreate source code and reassign segments
    return OperationResult.ok(data=event)
