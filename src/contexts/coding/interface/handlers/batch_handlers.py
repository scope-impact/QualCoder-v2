"""
Batch Operations Handlers

Handlers for batch coding operations across multiple sources.
"""

from __future__ import annotations

from typing import Any

from src.contexts.coding.core.ai_entities import (
    CodingSuggestion,
    CodingSuggestionBatch,
    CodingSuggestionBatchId,
    CodingSuggestionId,
)
from src.shared.common.operation_result import OperationResult
from src.shared.common.types import CodeId, SourceId

from .base import HandlerContext, missing_param_error


def handle_find_similar_content(
    ctx: HandlerContext,
    arguments: dict[str, Any],
) -> dict[str, Any]:
    """Find similar content across sources."""
    search_text = arguments.get("search_text")
    if not search_text:
        return missing_param_error("FIND_SIMILAR", "search_text")

    # Simplified: return mock matches
    # In real implementation, would search source content
    matches = [
        {"source_id": 1, "start_pos": 10, "end_pos": 50, "text": search_text[:20]},
        {"source_id": 2, "start_pos": 25, "end_pos": 65, "text": search_text[:20]},
        {"source_id": 3, "start_pos": 5, "end_pos": 45, "text": search_text[:20]},
    ]

    return OperationResult.ok(
        data={
            "search_text": search_text,
            "matches": matches,
            "match_count": len(matches),
        }
    ).to_dict()


def handle_suggest_batch_coding(
    ctx: HandlerContext,
    arguments: dict[str, Any],
) -> dict[str, Any]:
    """Suggest batch coding for multiple segments."""
    code_id = arguments.get("code_id")
    segments = arguments.get("segments")
    rationale = arguments.get("rationale")

    if code_id is None or not segments or not rationale:
        return OperationResult.fail(
            error="Missing required parameters",
            error_code="BATCH_CODING/MISSING_PARAMS",
        ).to_dict()

    batch_id = CodingSuggestionBatchId.new()
    coding_suggestions = []

    for seg in segments:
        csug_id = CodingSuggestionId.new()
        csug = CodingSuggestion(
            id=csug_id,
            source_id=SourceId(int(seg["source_id"])),
            code_id=CodeId(int(code_id)),
            start_pos=int(seg["start_pos"]),
            end_pos=int(seg["end_pos"]),
            rationale=rationale,
            confidence=0.8,
        )
        coding_suggestions.append(csug)

    # Store batch
    batch = CodingSuggestionBatch(
        id=batch_id,
        source_id=SourceId(int(segments[0]["source_id"])),
        suggestions=tuple(coding_suggestions),
    )
    ctx.suggestion_cache.coding_suggestions.add_batch(batch)

    return OperationResult.ok(
        data={
            "status": "pending_approval",
            "requires_approval": True,
            "batch_id": batch_id.value,
            "segment_count": len(segments),
        }
    ).to_dict()


# Handler registry for batch tools
BATCH_HANDLERS = {
    "find_similar_content": handle_find_similar_content,
    "suggest_batch_coding": handle_suggest_batch_coding,
}
