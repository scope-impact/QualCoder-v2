"""
Batch Apply Codes Use Case.

Functional use case for applying multiple codes to multiple text segments
in a single batch operation. Designed for AI agent efficiency.

Returns OperationResult with detailed success/failure information for each
operation in the batch.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from src.application.coding.usecases._state import build_coding_state
from src.application.protocols import ApplyCodeCommand, BatchApplyCodesCommand
from src.contexts.coding.core.derivers import derive_apply_code_to_text
from src.contexts.coding.core.entities import TextSegment
from src.contexts.coding.core.events import SegmentCoded
from src.contexts.shared.core.failure_events import FailureEvent
from src.contexts.shared.core.operation_result import OperationResult
from src.contexts.shared.core.types import CodeId, SourceId

if TYPE_CHECKING:
    from src.application.contexts import CodingContext
    from src.application.event_bus import EventBus


@dataclass(frozen=True)
class BatchOperationResult:
    """Result of a single operation within a batch."""

    index: int
    success: bool
    segment: TextSegment | None = None
    error: str | None = None
    error_code: str | None = None


@dataclass(frozen=True)
class BatchApplyCodesResult:
    """Aggregated result of a batch apply codes operation."""

    total: int
    succeeded: int
    failed: int
    results: tuple[BatchOperationResult, ...] = field(default_factory=tuple)

    @property
    def all_succeeded(self) -> bool:
        """Check if all operations succeeded."""
        return self.failed == 0


def batch_apply_codes(
    command: BatchApplyCodesCommand,
    coding_ctx: CodingContext,
    event_bus: EventBus,
    source_content_provider: Any | None = None,
) -> OperationResult:
    """
    Apply multiple codes to multiple text segments in a single batch.

    This use case is optimized for AI agents that need to apply multiple
    codes efficiently without making multiple individual API calls.

    Args:
        command: Command with list of ApplyCodeCommand operations
        coding_ctx: Coding context with repositories
        event_bus: Event bus for publishing events
        source_content_provider: Optional provider for source content

    Returns:
        OperationResult with BatchApplyCodesResult on success.
        Success is returned even if some operations fail (partial success).
        The result contains detailed information about each operation.

    Example:
        result = batch_apply_codes(
            BatchApplyCodesCommand(operations=(
                ApplyCodeCommand(code_id=1, source_id=1, start_position=0, end_position=10),
                ApplyCodeCommand(code_id=2, source_id=1, start_position=20, end_position=30),
            )),
            coding_ctx,
            event_bus,
        )
        if result.is_success:
            batch_result = result.data
            print(f"Applied {batch_result.succeeded}/{batch_result.total} codes")
    """
    if not command.operations:
        return OperationResult.fail(
            error="No operations provided",
            error_code="BATCH_APPLY_CODES/EMPTY_BATCH",
            suggestions=("Provide at least one operation in the batch",),
        )

    results: list[BatchOperationResult] = []
    succeeded = 0
    failed = 0

    # Process each operation
    for index, op in enumerate(command.operations):
        op_result = _apply_single_code(
            op=op,
            index=index,
            coding_ctx=coding_ctx,
            event_bus=event_bus,
            source_content_provider=source_content_provider,
        )
        results.append(op_result)

        if op_result.success:
            succeeded += 1
        else:
            failed += 1

    # Build aggregated result
    batch_result = BatchApplyCodesResult(
        total=len(command.operations),
        succeeded=succeeded,
        failed=failed,
        results=tuple(results),
    )

    # Return success even with partial failures (caller can inspect results)
    if succeeded == 0:
        return OperationResult.fail(
            error=f"All {failed} operations failed",
            error_code="BATCH_APPLY_CODES/ALL_FAILED",
            suggestions=("Check individual operation errors in result data",),
        )

    return OperationResult.ok(data=batch_result)


def _apply_single_code(
    op: ApplyCodeCommand,
    index: int,
    coding_ctx: CodingContext,
    event_bus: EventBus,
    source_content_provider: Any | None,
) -> BatchOperationResult:
    """Apply a single code operation within the batch."""
    code_id = CodeId(value=op.code_id)
    source_id = SourceId(value=op.source_id)

    # Get source content for the selected text
    selected_text = _get_selected_text(
        source_content_provider,
        source_id,
        op.start_position,
        op.end_position,
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
        start=op.start_position,
        end=op.end_position,
        selected_text=selected_text,
        memo=op.memo,
        importance=op.importance,
        owner=None,
        state=state,
    )

    # Handle failure events
    if isinstance(result, FailureEvent):
        event_bus.publish(result)  # Publish failure for policies
        return BatchOperationResult(
            index=index,
            success=False,
            error=result.message,
            error_code=f"BATCH_APPLY_CODES/{result.event_type.upper()}",
        )

    event: SegmentCoded = result

    # Create and persist segment
    segment = TextSegment(
        id=event.segment_id,
        source_id=source_id,
        code_id=code_id,
        position=event.position,
        selected_text=event.selected_text,
        memo=event.memo,
        importance=op.importance,
        owner=event.owner,
    )
    coding_ctx.segment_repo.save(segment)

    event_bus.publish(event)

    return BatchOperationResult(
        index=index,
        success=True,
        segment=segment,
    )


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
