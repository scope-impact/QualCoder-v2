"""
Approve Merge Use Case

Command use case for merging duplicate codes.
Reassigns segments and deletes the source code.

Uses MergePolicy for cross-context validation.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from returns.result import Failure, Result, Success

from src.application.ai_services.commands import ApproveMergeCommand
from src.application.ai_services.policies import MergePolicy
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


class _SegmentCounterAdapter:
    """Adapter to make segment repo compatible with policy protocol."""

    def __init__(self, segment_repo: SQLiteSegmentRepository):
        self._repo = segment_repo

    def count_by_code_id(self, code_id: int) -> int:
        return self._repo.count_by_code(CodeId(value=code_id))


class _CodeRepoAdapter:
    """Adapter to make code repo compatible with policy protocol."""

    def __init__(self, code_repo: SQLiteCodeRepository):
        self._repo = code_repo

    def get_by_id(self, code_id: int) -> Code | None:
        return self._repo.get_by_id(CodeId(value=code_id))


def approve_merge(
    command: ApproveMergeCommand,
    code_repo: SQLiteCodeRepository,
    segment_repo: SQLiteSegmentRepository,
    event_bus: EventBus,
    min_similarity: float = 0.0,
) -> Result[Code, str]:
    """
    Approve merging duplicate codes.

    Command use case following 5-step pattern:
    1. Validate with policy
    2. Reassign segments
    3. Delete source code
    4. Publish events
    5. Return target code

    Args:
        command: Command with source and target code IDs
        code_repo: Repository for code operations
        segment_repo: Repository for segment operations
        event_bus: Event bus for publishing events
        min_similarity: Optional minimum similarity threshold

    Returns:
        Success with target Code, or Failure with error message
    """
    # Step 1: Validate with policy
    policy = MergePolicy(
        code_repo=_CodeRepoAdapter(code_repo),
        segment_counter=_SegmentCounterAdapter(segment_repo),
        min_similarity=min_similarity,
        require_smaller_to_larger=False,  # User chose direction
    )
    decision = policy.can_merge(
        source_code_id=command.source_code_id,
        target_code_id=command.target_code_id,
    )

    if not decision.allowed:
        return Failure(decision.reason)

    # Use validated codes from policy decision
    source_code = decision.source_code
    target_code = decision.target_code
    segments_to_move = decision.segments_to_reassign

    source_code_id = CodeId(value=command.source_code_id)
    target_code_id = CodeId(value=command.target_code_id)

    # Step 2 & 3: Perform the merge
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
