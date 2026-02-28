"""
QC-029.07: Apply Code to Text Range Handlers

Handlers for suggesting code applications to text ranges.

All mutation handlers delegate to command handlers to ensure proper event publishing.
"""

from __future__ import annotations

from typing import Any

from src.contexts.coding.core.ai_entities import CodingSuggestion, CodingSuggestionId
from src.shared.common.operation_result import OperationResult
from src.shared.common.types import CodeId, SourceId

from .base import (
    HandlerContext,
    missing_param_error,
    missing_params_error,
    no_context_error,
    not_found_error,
)


def handle_suggest_code_application(
    ctx: HandlerContext,
    arguments: dict[str, Any],
) -> dict[str, Any]:
    """Suggest applying a code to a text range."""
    source_id = arguments.get("source_id")
    code_id = arguments.get("code_id")
    start_pos = arguments.get("start_pos")
    end_pos = arguments.get("end_pos")

    if source_id is None or code_id is None or start_pos is None or end_pos is None:
        return missing_params_error("SUGGEST_APPLICATION")

    rationale = arguments.get("rationale", "")
    confidence = min(100, max(0, arguments.get("confidence", 70))) / 100.0
    include_text = arguments.get("include_text", False)

    suggestion_id = CodingSuggestionId.new()
    suggestion = CodingSuggestion(
        id=suggestion_id,
        source_id=SourceId(value=str(source_id)),
        code_id=CodeId(value=str(code_id)),
        start_pos=int(start_pos),
        end_pos=int(end_pos),
        rationale=rationale,
        confidence=confidence,
    )

    ctx.suggestion_cache.coding_suggestions.add(suggestion)

    data: dict[str, Any] = {
        "status": "pending_approval",
        "requires_approval": True,
        "suggestion_id": suggestion_id.value,
        "source_id": source_id,
        "code_id": code_id,
        "start_pos": start_pos,
        "end_pos": end_pos,
        "rationale": rationale,
        "confidence": suggestion.confidence_percentage,
    }

    if include_text:
        source_text = ctx.get_source_text(source_id)
        data["text_excerpt"] = source_text[int(start_pos) : int(end_pos)]

    return OperationResult.ok(data=data).to_dict()


def handle_list_pending_coding_suggestions(
    ctx: HandlerContext,
    arguments: dict[str, Any],
) -> dict[str, Any]:
    """List pending coding suggestions."""
    source_id = arguments.get("source_id")

    if source_id:
        suggestions = ctx.suggestion_cache.coding_suggestions.get_by_source(
            SourceId(value=str(source_id))
        )
    else:
        suggestions = ctx.suggestion_cache.coding_suggestions.get_all_pending()

    return OperationResult.ok(
        data={
            "count": len(suggestions),
            "suggestions": [
                {
                    "suggestion_id": s.id.value,
                    "source_id": s.source_id.value,
                    "code_id": s.code_id.value,
                    "start_pos": s.start_pos,
                    "end_pos": s.end_pos,
                    "rationale": s.rationale,
                    "confidence": s.confidence_percentage,
                    "status": s.status,
                }
                for s in suggestions
            ],
        }
    ).to_dict()


def handle_approve_coding_suggestion(
    ctx: HandlerContext,
    arguments: dict[str, Any],
) -> dict[str, Any]:
    """Approve a coding suggestion.

    Delegates to apply_code command handler for proper event publishing
    (SegmentCoded) for UI refresh.
    """
    suggestion_id = arguments.get("suggestion_id")
    if not suggestion_id:
        return missing_param_error("APPROVE_CODING", "suggestion_id")

    suggestion = ctx.suggestion_cache.coding_suggestions.get_by_id(
        CodingSuggestionId(suggestion_id)
    )
    if suggestion is None:
        return not_found_error("APPROVE_CODING", "Suggestion", suggestion_id)

    if suggestion.status != "pending":
        return OperationResult.fail(
            error=f"Suggestion already {suggestion.status}",
            error_code="APPROVE_CODING/ALREADY_PROCESSED",
        ).to_dict()

    if ctx.segment_repo is None or ctx.code_repo is None:
        return no_context_error("APPROVE_CODING")

    result = ctx.apply_suggestion(suggestion)
    if result.is_success:
        updated = suggestion.with_status("approved")
        ctx.suggestion_cache.coding_suggestions.update(updated)
        segment = result.data
        return OperationResult.ok(
            data={"status": "applied", "segment_id": segment.id.value}
        ).to_dict()

    return result.to_dict()


def handle_reject_coding_suggestion(
    ctx: HandlerContext,
    arguments: dict[str, Any],
) -> dict[str, Any]:
    """Reject a coding suggestion."""
    suggestion_id = arguments.get("suggestion_id")
    if not suggestion_id:
        return missing_param_error("REJECT_CODING", "suggestion_id")

    suggestion = ctx.suggestion_cache.coding_suggestions.get_by_id(
        CodingSuggestionId(suggestion_id)
    )
    if suggestion is None:
        return not_found_error("REJECT_CODING", "Suggestion", suggestion_id)

    updated = suggestion.with_status("rejected")
    ctx.suggestion_cache.coding_suggestions.update(updated)

    return OperationResult.ok(
        data={"status": "rejected", "suggestion_id": suggestion_id}
    ).to_dict()


# Handler registry for coding suggestion tools
CODING_SUGGESTION_HANDLERS = {
    "suggest_code_application": handle_suggest_code_application,
    "list_pending_coding_suggestions": handle_list_pending_coding_suggestions,
    "approve_coding_suggestion": handle_approve_coding_suggestion,
    "reject_coding_suggestion": handle_reject_coding_suggestion,
}
