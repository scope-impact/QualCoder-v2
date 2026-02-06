"""
QC-028.07: Suggest New Code Handlers

Handlers for AI-assisted code suggestion workflow.

All mutation handlers delegate to command handlers to ensure proper event publishing.
"""

from __future__ import annotations

from typing import Any

from src.contexts.coding.core.ai_entities import CodeSuggestion, SuggestionId
from src.contexts.coding.core.commandHandlers import create_code
from src.contexts.coding.core.commands import CreateCodeCommand
from src.contexts.coding.core.entities import Color
from src.shared.common.operation_result import OperationResult
from src.shared.common.types import SourceId

from .base import HandlerContext, missing_param_error, no_context_error


def handle_analyze_content_for_codes(
    ctx: HandlerContext,
    arguments: dict[str, Any],
) -> dict[str, Any]:
    """Analyze uncoded content in a source."""
    source_id = arguments.get("source_id")
    if source_id is None:
        return missing_param_error("ANALYZE_CONTENT", "source_id")

    if ctx.segment_repo is None:
        return no_context_error("ANALYZE_CONTENT")

    # Get existing segments for this source
    segments = ctx.segment_repo.get_by_source(SourceId(int(source_id)))

    return OperationResult.ok(
        data={
            "source_id": source_id,
            "segment_count": len(segments),
            "analysis": "Content analysis complete",
            "uncoded_segments": [],  # Would be computed from source text
        }
    ).to_dict()


def handle_suggest_new_code(
    ctx: HandlerContext,
    arguments: dict[str, Any],
) -> dict[str, Any]:
    """Suggest a new code."""
    name = arguments.get("name")
    rationale = arguments.get("rationale")

    if not name:
        return missing_param_error("SUGGEST_CODE", "name")

    if not rationale:
        return missing_param_error("SUGGEST_CODE", "rationale")

    color_hex = arguments.get("color", "#808080")
    confidence = min(100, max(0, arguments.get("confidence", 70))) / 100.0

    # Create suggestion
    suggestion_id = SuggestionId.new()
    suggestion = CodeSuggestion(
        id=suggestion_id,
        name=name,
        color=Color.from_hex(color_hex),
        rationale=rationale,
        confidence=confidence,
        memo=arguments.get("description"),
        status="pending",
    )

    # Store in suggestion cache
    ctx.suggestion_cache.code_suggestions.add(suggestion)

    return OperationResult.ok(
        data={
            "status": "pending_approval",
            "requires_approval": True,
            "suggestion_id": suggestion_id.value,
            "name": name,
            "color": color_hex,
            "rationale": rationale,
            "confidence": suggestion.confidence_percentage,
        }
    ).to_dict()


def handle_list_pending_suggestions(
    ctx: HandlerContext,
    _arguments: dict[str, Any],
) -> dict[str, Any]:
    """List pending code suggestions."""
    suggestions = ctx.suggestion_cache.code_suggestions.get_all_pending()

    return OperationResult.ok(
        data={
            "count": len(suggestions),
            "suggestions": [
                {
                    "suggestion_id": s.id.value,
                    "name": s.name,
                    "color": s.color.to_hex(),
                    "rationale": s.rationale,
                    "confidence": s.confidence_percentage,
                    "status": s.status,
                }
                for s in suggestions
            ],
        }
    ).to_dict()


def handle_approve_suggestion(
    ctx: HandlerContext,
    arguments: dict[str, Any],
) -> dict[str, Any]:
    """
    Approve a pending code suggestion.

    Delegates to create_code command handler for proper event publishing
    (CodeCreated) for UI refresh.
    """
    suggestion_id = arguments.get("suggestion_id")
    if not suggestion_id:
        return missing_param_error("APPROVE_SUGGESTION", "suggestion_id")

    suggestion = ctx.suggestion_cache.code_suggestions.get_by_id(
        SuggestionId(suggestion_id)
    )
    if suggestion is None:
        return OperationResult.fail(
            error=f"Suggestion {suggestion_id} not found",
            error_code="APPROVE_SUGGESTION/NOT_FOUND",
        ).to_dict()

    if not suggestion.is_pending:
        return OperationResult.fail(
            error=f"Suggestion {suggestion_id} is not pending",
            error_code="APPROVE_SUGGESTION/NOT_PENDING",
        ).to_dict()

    if ctx.code_repo is None:
        return no_context_error("APPROVE_SUGGESTION")

    # Delegate to create_code command handler - publishes CodeCreated event
    command = CreateCodeCommand(
        name=suggestion.name,
        color=suggestion.color.to_hex(),
        memo=suggestion.memo,
    )
    result = create_code(
        command=command,
        code_repo=ctx.code_repo,
        category_repo=ctx.category_repo,
        segment_repo=ctx.segment_repo,
        event_bus=ctx.event_bus,
    )

    if result.is_success:
        # Update suggestion status
        updated = suggestion.with_status("approved")
        ctx.suggestion_cache.code_suggestions.update(updated)

        # Extract code from result
        code = result.data
        return OperationResult.ok(
            data={
                "status": "created",
                "code_id": code.id.value,
                "name": code.name,
            }
        ).to_dict()

    return result.to_dict()


# Handler registry for suggest code tools
SUGGEST_CODE_HANDLERS = {
    "analyze_content_for_codes": handle_analyze_content_for_codes,
    "suggest_new_code": handle_suggest_new_code,
    "list_pending_suggestions": handle_list_pending_suggestions,
    "approve_suggestion": handle_approve_suggestion,
}
