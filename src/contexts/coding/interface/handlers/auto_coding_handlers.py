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
from src.shared.common.operation_result import OperationResult
from src.shared.common.types import SourceId

from .base import (
    HandlerContext,
    apply_pending_suggestions,
    compute_uncoded_ranges,
    missing_param_error,
    missing_params_error,
    no_context_error,
    not_found_error,
)


def _score_code_for_text(code, text_lower: str) -> tuple[int, str]:
    """Score how well a code matches a text segment. Returns (confidence, rationale)."""
    score = 0
    reasons: list[str] = []

    # Check if code name words appear in the text (max 80 points)
    name_words = [w for w in code.name.lower().split() if len(w) > 2]
    if name_words:
        matched_words = [w for w in name_words if w in text_lower]
        if matched_words:
            match_ratio = len(matched_words) / len(name_words)
            score += 80 * match_ratio
            reasons.append(f"name matches: {', '.join(matched_words)}")

    # Check if memo keywords appear in the text (max 30 points)
    if code.memo:
        memo_words = [
            w.lower() for w in code.memo.replace(",", " ").split() if len(w) > 3
        ]
        if memo_words:
            matched_memo = [w for w in memo_words if w in text_lower]
            if matched_memo:
                score += 30 * len(matched_memo) / len(memo_words)
                reasons.append(f"memo keywords: {', '.join(matched_memo[:5])}")

    confidence = min(95, max(10, int(score)))
    rationale = (
        f"Matched on {'; '.join(reasons)}"
        if reasons
        else f"No strong match for code '{code.name}'"
    )
    return confidence, rationale


def handle_analyze_uncoded_text(
    ctx: HandlerContext,
    arguments: dict[str, Any],
) -> dict[str, Any]:
    """Analyze uncoded text in a source."""
    source_id = arguments.get("source_id")
    if source_id is None:
        return missing_param_error("ANALYZE_UNCODED", "source_id")

    # Validate source exists
    if ctx.source_repo is not None:
        source = ctx.source_repo.get_by_id(SourceId(value=str(source_id)))
        if source is None:
            return not_found_error("ANALYZE_UNCODED", "Source", str(source_id))

    segments = (
        ctx.segment_repo.get_by_source(SourceId(value=str(source_id)))
        if ctx.segment_repo
        else []
    )

    source_text = ctx.get_source_text(source_id)
    total_length = len(source_text)

    uncoded_ranges = compute_uncoded_ranges(segments, total_length)
    total_uncoded = sum(r["length"] for r in uncoded_ranges)
    uncoded_pct = int((total_uncoded / total_length) * 100) if total_length > 0 else 0

    return OperationResult.ok(
        data={
            "source_id": source_id,
            "total_length": total_length,
            "coded_length": total_length - total_uncoded,
            "uncoded_percentage": uncoded_pct,
            "segment_count": len(segments),
            "uncoded_ranges": uncoded_ranges,
        }
    ).to_dict()


def handle_suggest_codes_for_range(
    ctx: HandlerContext,
    arguments: dict[str, Any],
) -> dict[str, Any]:
    """Suggest codes for a text range based on content matching."""
    source_id = arguments.get("source_id")
    start_pos = arguments.get("start_pos")
    end_pos = arguments.get("end_pos")

    if source_id is None or start_pos is None or end_pos is None:
        return missing_params_error("SUGGEST_CODES_RANGE")

    codes = ctx.code_repo.get_all() if ctx.code_repo else []
    source_text = ctx.get_source_text(source_id)
    text_excerpt = source_text[int(start_pos) : int(end_pos)]
    text_lower = text_excerpt.lower()

    batch_id = CodingSuggestionBatchId.new()

    # Score each code and keep the top 5
    scored = []
    for code in codes:
        confidence, rationale = _score_code_for_text(code, text_lower)
        scored.append((code, confidence, rationale))

    scored.sort(key=lambda x: x[1], reverse=True)
    top = scored[:5]

    # Build cache batch and response
    coding_suggestions = []
    response_suggestions = []
    for code, confidence, rationale in top:
        csug_id = CodingSuggestionId.new()
        csug = CodingSuggestion(
            id=csug_id,
            source_id=SourceId(value=str(source_id)),
            code_id=code.id,
            start_pos=int(start_pos),
            end_pos=int(end_pos),
            rationale=rationale,
            confidence=confidence / 100.0,
        )
        coding_suggestions.append(csug)
        response_suggestions.append(
            {
                "suggestion_id": csug_id.value,
                "code_id": code.id.value,
                "code_name": code.name,
                "confidence": confidence,
                "rationale": rationale,
            }
        )

    batch = CodingSuggestionBatch(
        id=batch_id,
        source_id=SourceId(value=str(source_id)),
        suggestions=tuple(coding_suggestions),
    )
    ctx.suggestion_cache.coding_suggestions.add_batch(batch)

    return OperationResult.ok(
        data={
            "source_id": source_id,
            "start_pos": start_pos,
            "end_pos": end_pos,
            "suggestion_batch_id": batch_id.value,
            "suggestions": response_suggestions,
        }
    ).to_dict()


def handle_auto_suggest_codes(
    ctx: HandlerContext,
    arguments: dict[str, Any],
) -> dict[str, Any]:
    """Auto-suggest codes for all uncoded portions of a source."""
    source_id = arguments.get("source_id")
    min_confidence = arguments.get("min_confidence", 70)

    if source_id is None:
        return missing_param_error("AUTO_SUGGEST", "source_id")

    # Validate source exists
    if ctx.source_repo is not None:
        source = ctx.source_repo.get_by_id(SourceId(value=str(source_id)))
        if source is None:
            return not_found_error("AUTO_SUGGEST", "Source", str(source_id))

    codes = ctx.code_repo.get_all() if ctx.code_repo else []
    batch_id = CodingSuggestionBatchId.new()

    if not codes:
        return OperationResult.ok(
            data={
                "batch_id": batch_id.value,
                "source_id": source_id,
                "total_suggested": 0,
                "suggestions": [],
            }
        ).to_dict()

    source_text = ctx.get_source_text(source_id)
    segments = (
        ctx.segment_repo.get_by_source(SourceId(value=str(source_id)))
        if ctx.segment_repo
        else []
    )
    uncoded_ranges = compute_uncoded_ranges(segments, len(source_text))

    suggestions = []
    coding_suggestions = []

    for uncoded in uncoded_ranges:
        text_lower = source_text[uncoded["start_pos"] : uncoded["end_pos"]].lower()

        # Find the best matching code for this range
        best_confidence = 0
        best_code = None
        best_rationale = ""
        for code in codes:
            confidence, rationale = _score_code_for_text(code, text_lower)
            if confidence > best_confidence:
                best_confidence = confidence
                best_code = code
                best_rationale = rationale

        if best_code is None or best_confidence < min_confidence:
            continue

        csug_id = CodingSuggestionId.new()
        csug = CodingSuggestion(
            id=csug_id,
            source_id=SourceId(value=str(source_id)),
            code_id=best_code.id,
            start_pos=uncoded["start_pos"],
            end_pos=uncoded["end_pos"],
            rationale=best_rationale,
            confidence=best_confidence / 100.0,
        )
        coding_suggestions.append(csug)
        suggestions.append(
            {
                "suggestion_id": csug_id.value,
                "code_id": best_code.id.value,
                "code_name": best_code.name,
                "start_pos": csug.start_pos,
                "end_pos": csug.end_pos,
                "confidence": best_confidence,
                "rationale": best_rationale,
            }
        )

    batch = CodingSuggestionBatch(
        id=batch_id,
        source_id=SourceId(value=str(source_id)),
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
        return not_found_error("BATCH_STATUS", "Batch", batch_id)

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
    ctx: HandlerContext,
    arguments: dict[str, Any],
) -> dict[str, Any]:
    """Respond to a batch of suggestions (accept or reject)."""
    batch_id = arguments.get("suggestion_batch_id")
    response = arguments.get("response")

    if not batch_id or not response:
        return missing_params_error("RESPOND_SUGGESTION")

    batch = ctx.suggestion_cache.coding_suggestions.get_batch(
        CodingSuggestionBatchId(batch_id)
    )
    if batch is None:
        return not_found_error("RESPOND_SUGGESTION", "Batch", batch_id)

    if response == "reject":
        for suggestion in batch.suggestions:
            if suggestion.is_pending:
                updated = suggestion.with_status("rejected")
                ctx.suggestion_cache.coding_suggestions.update(updated)
        return OperationResult.ok(
            data={"status": "rejected", "reason": arguments.get("reason", "")}
        ).to_dict()

    if response != "accept":
        return OperationResult.fail(
            error=f"Invalid response type: {response}",
            error_code="RESPOND_SUGGESTION/INVALID_RESPONSE",
        ).to_dict()

    # Accept flow
    if ctx.segment_repo is None or ctx.code_repo is None:
        return no_context_error("RESPOND_SUGGESTION")

    selected_ids = {str(c) for c in arguments.get("selected_code_ids", [])}
    if selected_ids:
        eligible = [s for s in batch.suggestions if s.code_id.value in selected_ids]
    else:
        eligible = list(batch.suggestions)

    result = apply_pending_suggestions(ctx, eligible)
    return OperationResult.ok(
        data={
            "status": "accepted",
            "applied_count": result.applied_count,
            "failed_count": result.failed_count,
        }
    ).to_dict()


def handle_approve_batch_coding(
    ctx: HandlerContext,
    arguments: dict[str, Any],
) -> dict[str, Any]:
    """Approve an entire batch of coding suggestions.

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
        return not_found_error("APPROVE_BATCH", "Batch", batch_id)

    if ctx.segment_repo is None or ctx.code_repo is None:
        return no_context_error("APPROVE_BATCH")

    result = apply_pending_suggestions(ctx, batch.suggestions, track_errors=True)
    return OperationResult.ok(
        data={
            "status": "applied" if result.failed_count == 0 else "partial",
            "applied_count": result.applied_count,
            "failed_count": result.failed_count,
            "errors": result.errors if result.errors else None,
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
