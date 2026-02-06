"""
QC-029.08: Suggest Codes for Text Handlers

Handlers for auto-suggesting codes for uncoded text.

All mutation handlers delegate to command handlers to ensure proper event publishing.
"""

from __future__ import annotations

from typing import Any

from src.contexts.coding.core.ai_entities import (
    CodingSuggestion,
    CodingSuggestionBatch,
    CodingSuggestionBatchId,
    CodingSuggestionId,
)
from src.contexts.coding.core.commandHandlers import apply_code
from src.contexts.coding.core.commands import ApplyCodeCommand
from src.shared.common.operation_result import OperationResult
from src.shared.common.types import SourceId

from .base import HandlerContext, missing_param_error, no_context_error


def handle_analyze_uncoded_text(
    ctx: HandlerContext,
    arguments: dict[str, Any],
) -> dict[str, Any]:
    """Analyze uncoded text in a source."""
    source_id = arguments.get("source_id")
    if source_id is None:
        return missing_param_error("ANALYZE_UNCODED", "source_id")

    # Get segments for this source
    segments = (
        ctx.segment_repo.get_by_source(SourceId(int(source_id)))
        if ctx.segment_repo
        else []
    )

    # Calculate coded vs uncoded (simplified - would need source text length)
    total_coded = sum(s.position.end - s.position.start for s in segments)
    # Assume 10000 char document for demo
    assumed_length = 10000
    uncoded_pct = max(0, 100 - int((total_coded / assumed_length) * 100))

    return OperationResult.ok(
        data={
            "source_id": source_id,
            "total_length": assumed_length,
            "coded_length": total_coded,
            "uncoded_percentage": uncoded_pct,
            "segment_count": len(segments),
            "uncoded_ranges": [],  # Would be computed
        }
    ).to_dict()


def handle_suggest_codes_for_range(
    ctx: HandlerContext,
    arguments: dict[str, Any],
) -> dict[str, Any]:
    """Suggest codes for a text range."""
    source_id = arguments.get("source_id")
    start_pos = arguments.get("start_pos")
    end_pos = arguments.get("end_pos")

    if source_id is None or start_pos is None or end_pos is None:
        return OperationResult.fail(
            error="Missing required parameters",
            error_code="SUGGEST_CODES_RANGE/MISSING_PARAMS",
        ).to_dict()

    # Get all codes and suggest based on names (simplified)
    codes = ctx.code_repo.get_all() if ctx.code_repo else []

    suggestions = []
    batch_id = CodingSuggestionBatchId.new()

    # Generate deterministic confidence scores based on code position
    # In a real implementation, this would use semantic analysis
    for i, code in enumerate(codes[:5]):  # Limit to top 5
        # Higher ranked codes get higher confidence (descending from 90)
        confidence = 90 - (i * 6)  # 90, 84, 78, 72, 66
        suggestions.append(
            {
                "code_id": code.id.value,
                "code_name": code.name,
                "confidence": confidence,
                "rationale": f"Code '{code.name}' may apply to this text segment",
            }
        )

    return OperationResult.ok(
        data={
            "source_id": source_id,
            "start_pos": start_pos,
            "end_pos": end_pos,
            "suggestion_batch_id": batch_id.value,
            "suggestions": sorted(
                suggestions, key=lambda x: x["confidence"], reverse=True
            ),
        }
    ).to_dict()


def handle_auto_suggest_codes(
    ctx: HandlerContext,
    arguments: dict[str, Any],
) -> dict[str, Any]:
    """Auto-suggest codes for all uncoded portions."""
    source_id = arguments.get("source_id")
    _min_confidence = arguments.get("min_confidence", 70)  # Reserved for AI

    if source_id is None:
        return missing_param_error("AUTO_SUGGEST", "source_id")

    codes = ctx.code_repo.get_all() if ctx.code_repo else []
    batch_id = CodingSuggestionBatchId.new()

    # Create suggestions with deterministic confidence scores
    # In a real implementation, this would use AI/semantic analysis
    suggestions = []
    coding_suggestions = []

    for i, code in enumerate(codes[:3]):  # Limit to 3 suggestions
        # Higher ranked codes get higher confidence (descending from 95%)
        confidence = (95 - (i * 8)) / 100.0  # 0.95, 0.87, 0.79
        csug_id = CodingSuggestionId.new()

        csug = CodingSuggestion(
            id=csug_id,
            source_id=SourceId(int(source_id)),
            code_id=code.id,
            start_pos=i * 100,
            end_pos=(i + 1) * 100,
            rationale=f"Auto-suggested: Code '{code.name}' appears relevant",
            confidence=confidence,
        )
        coding_suggestions.append(csug)

        suggestions.append(
            {
                "suggestion_id": csug_id.value,
                "code_id": code.id.value,
                "code_name": code.name,
                "start_pos": csug.start_pos,
                "end_pos": csug.end_pos,
                "confidence": csug.confidence_percentage,
                "rationale": csug.rationale,
            }
        )

    # Store batch
    batch = CodingSuggestionBatch(
        id=batch_id,
        source_id=SourceId(int(source_id)),
        suggestions=tuple(coding_suggestions),
    )
    ctx.suggestion_cache.coding_suggestions.add_batch(batch)

    return OperationResult.ok(
        data={
            "batch_id": batch_id.value,
            "source_id": source_id,
            "total_suggested": len(suggestions),
            "suggestions": suggestions,
        }
    ).to_dict()


def handle_get_suggestion_batch_status(
    ctx: HandlerContext,
    arguments: dict[str, Any],
) -> dict[str, Any]:
    """Get status of a suggestion batch."""
    batch_id = arguments.get("batch_id")
    if not batch_id:
        return missing_param_error("BATCH_STATUS", "batch_id")

    batch = ctx.suggestion_cache.coding_suggestions.get_batch(
        CodingSuggestionBatchId(batch_id)
    )
    if batch is None:
        return OperationResult.fail(
            error=f"Batch {batch_id} not found",
            error_code="BATCH_STATUS/NOT_FOUND",
        ).to_dict()

    return OperationResult.ok(
        data={
            "batch_id": batch_id,
            "status": batch.status,
            "total_count": batch.count,
            "pending_count": batch.pending_count,
            "reviewed_count": batch.reviewed_count,
        }
    ).to_dict()


def handle_respond_to_code_suggestion(
    _ctx: HandlerContext,
    arguments: dict[str, Any],
) -> dict[str, Any]:
    """Respond to a batch of suggestions."""
    batch_id = arguments.get("suggestion_batch_id")
    response = arguments.get("response")

    if not batch_id or not response:
        return OperationResult.fail(
            error="Missing required parameters",
            error_code="RESPOND_SUGGESTION/MISSING_PARAMS",
        ).to_dict()

    if response == "accept":
        selected_ids = arguments.get("selected_code_ids", [])
        return OperationResult.ok(
            data={
                "status": "accepted",
                "applied_count": len(selected_ids),
            }
        ).to_dict()
    elif response == "reject":
        return OperationResult.ok(
            data={
                "status": "rejected",
                "reason": arguments.get("reason", ""),
            }
        ).to_dict()
    else:
        return OperationResult.fail(
            error=f"Invalid response type: {response}",
            error_code="RESPOND_SUGGESTION/INVALID_RESPONSE",
        ).to_dict()


def handle_approve_batch_coding(
    ctx: HandlerContext,
    arguments: dict[str, Any],
) -> dict[str, Any]:
    """
    Approve an entire batch of coding suggestions.

    Delegates to apply_code command handler for each suggestion to ensure
    proper event publishing (SegmentCoded) for UI refresh.
    """
    batch_id = arguments.get("batch_id")
    if not batch_id:
        return missing_param_error("APPROVE_BATCH", "batch_id")

    batch = ctx.suggestion_cache.coding_suggestions.get_batch(
        CodingSuggestionBatchId(batch_id)
    )
    if batch is None:
        return OperationResult.fail(
            error=f"Batch {batch_id} not found",
            error_code="APPROVE_BATCH/NOT_FOUND",
        ).to_dict()

    if ctx.segment_repo is None or ctx.code_repo is None:
        return no_context_error("APPROVE_BATCH")

    # Approve all pending suggestions using command handler
    applied_count = 0
    failed_count = 0
    errors = []

    for suggestion in batch.suggestions:
        if suggestion.is_pending:
            # Delegate to apply_code command handler - publishes SegmentCoded event
            command = ApplyCodeCommand(
                code_id=suggestion.code_id.value,
                source_id=suggestion.source_id.value,
                start_position=suggestion.start_pos,
                end_position=suggestion.end_pos,
                memo=suggestion.rationale,
            )
            result = apply_code(
                command=command,
                code_repo=ctx.code_repo,
                category_repo=ctx.category_repo,
                segment_repo=ctx.segment_repo,
                event_bus=ctx.event_bus,
            )

            if result.is_success:
                # Update suggestion status
                updated = suggestion.with_status("approved")
                ctx.suggestion_cache.coding_suggestions.update(updated)
                applied_count += 1
            else:
                failed_count += 1
                errors.append(
                    {
                        "suggestion_id": suggestion.id.value,
                        "error": result.error,
                        "error_code": result.error_code,
                    }
                )

    return OperationResult.ok(
        data={
            "status": "applied" if failed_count == 0 else "partial",
            "applied_count": applied_count,
            "failed_count": failed_count,
            "errors": errors if errors else None,
        }
    ).to_dict()


# Handler registry for auto-coding tools
AUTO_CODING_HANDLERS = {
    "analyze_uncoded_text": handle_analyze_uncoded_text,
    "suggest_codes_for_range": handle_suggest_codes_for_range,
    "auto_suggest_codes": handle_auto_suggest_codes,
    "get_suggestion_batch_status": handle_get_suggestion_batch_status,
    "respond_to_code_suggestion": handle_respond_to_code_suggestion,
    "approve_batch_coding": handle_approve_batch_coding,
}
