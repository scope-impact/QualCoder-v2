"""
Merge Codes Use Case.

Functional use case for merging source code into target code.
Returns OperationResult with error codes and suggestions.
"""

from __future__ import annotations

import logging
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
from src.shared.infra.metrics import metered_command

if TYPE_CHECKING:
    from src.shared.infra.event_bus import EventBus

logger = logging.getLogger("qualcoder.coding.core")


@metered_command("merge_codes")
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
    logger.debug("merge_codes: source_code_id=%s, target_code_id=%s", command.source_code_id, command.target_code_id)

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
        logger.error("merge_codes failed: %s", result.event_type)
        event_bus.publish(result)
        return OperationResult.from_failure(result)

    event: CodesMerged = result

    # Atomic: reassign segments + delete source code in one transaction
    from src.shared.infra.unit_of_work import UnitOfWork

    with UnitOfWork(code_repo._conn) as uow:
        segment_repo.reassign_code(source_code_id, target_code_id)
        code_repo.delete(source_code_id)
        uow.commit()

    event_bus.publish(event)

    logger.info("Codes merged: source_code_id=%s, target_code_id=%s", command.source_code_id, command.target_code_id)

    return OperationResult.ok(data=event)
