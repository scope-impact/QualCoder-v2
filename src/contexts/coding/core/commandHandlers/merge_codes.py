"""
Merge Codes Use Case.

Functional use case for merging source code into target code.
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
from src.contexts.coding.core.commands import MergeCodesCommand
from src.contexts.coding.core.derivers import derive_merge_codes
from src.contexts.coding.core.events import CodesMerged
from src.shared.common.failure_events import FailureEvent
from src.shared.common.operation_result import OperationResult
from src.shared.common.types import CodeId

if TYPE_CHECKING:
    from src.shared.infra.event_bus import EventBus


def merge_codes(
    command: MergeCodesCommand,
    code_repo: CodeRepository,
    category_repo: CategoryRepository,
    segment_repo: SegmentRepository,
    event_bus: EventBus,
) -> OperationResult:
    """
    Merge source code into target code.

    Args:
        command: Command with source and target code IDs
        code_repo: Repository for codes
        category_repo: Repository for categories
        segment_repo: Repository for segments
        event_bus: Event bus for publishing events

    Returns:
        OperationResult with CodesMerged event on success, or error details on failure
    """
    state = build_coding_state(code_repo, category_repo, segment_repo)
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
    segment_repo.reassign_code(source_code_id, target_code_id)

    # Delete the source code
    code_repo.delete(source_code_id)

    event_bus.publish(event)

    # No rollback for merge - would need to recreate source code and reassign segments
    return OperationResult.ok(data=event)
