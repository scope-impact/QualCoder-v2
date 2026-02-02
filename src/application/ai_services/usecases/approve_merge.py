"""
Approve Merge Use Case

Command use case for merging duplicate codes.
Reassigns segments and deletes the source code.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from returns.result import Failure, Result, Success

from src.application.ai_services.commands import ApproveMergeCommand
from src.contexts.ai_services.core.events import MergeSuggestionApproved
from src.contexts.coding.core.entities import Code
from src.contexts.coding.core.events import CodesMerged
from src.contexts.shared.core.types import CodeId

if TYPE_CHECKING:
    from src.application.event_bus import EventBus
    from src.contexts.coding.infra.repositories import (
        SQLiteCodeRepository,
        SQLiteSegmentRepository,
    )


def approve_merge(
    command: ApproveMergeCommand,
    code_repo: SQLiteCodeRepository,
    segment_repo: SQLiteSegmentRepository,
    event_bus: EventBus,
) -> Result[Code, str]:
    """
    Approve merging duplicate codes.

    Command use case following 5-step pattern:
    1. Validate codes exist
    2. Count segments to move
    3. Reassign segments and delete source code
    4. Publish events
    5. Return target code

    Args:
        command: Command with source and target code IDs
        code_repo: Repository for code operations
        segment_repo: Repository for segment operations
        event_bus: Event bus for publishing events

    Returns:
        Success with target Code, or Failure with error message
    """
    source_code_id = CodeId(value=command.source_code_id)
    target_code_id = CodeId(value=command.target_code_id)

    # Step 1: Validate codes exist
    source_code = code_repo.get_by_id(source_code_id)
    target_code = code_repo.get_by_id(target_code_id)

    if source_code is None:
        return Failure(f"Source code {command.source_code_id} not found")

    if target_code is None:
        return Failure(f"Target code {command.target_code_id} not found")

    if source_code_id == target_code_id:
        return Failure("Cannot merge a code with itself")

    # Step 2: Count segments to move
    segments_to_move = segment_repo.count_by_code(source_code_id)

    # Step 3: Perform the merge
    segment_repo.reassign_code(source_code_id, target_code_id)
    code_repo.delete(source_code_id)

    # Step 4: Publish events
    # AI-specific event
    approved_event = MergeSuggestionApproved.create(
        source_code_id=source_code_id,
        target_code_id=target_code_id,
        segments_moved=segments_to_move,
    )
    event_bus.publish(approved_event)

    # Coding context event for other listeners
    codes_merged_event = CodesMerged.create(
        source_code_id=source_code.id,
        source_code_name=source_code.name,
        target_code_id=target_code.id,
        target_code_name=target_code.name,
        segments_moved=segments_to_move,
    )
    event_bus.publish(codes_merged_event)

    # Step 5: Return target code
    return Success(target_code)
