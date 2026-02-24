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


def _compute_uncoded_ranges(segments: list, total_length: int) -> list[dict[str, int]]:
    """Compute uncoded character ranges from a list of coded segments."""
    if total_length == 0:
        return []

    # Merge overlapping coded ranges
    coded = sorted(
        [(s.position.start, s.position.end) for s in segments], key=lambda x: x[0]
    )
    merged: list[tuple[int, int]] = []
    for start, end in coded:
        if merged and start <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], end))
        else:
            merged.append((start, end))

    # Find gaps
    uncoded = []
    prev_end = 0
    for start, end in merged:
        if start > prev_end:
            uncoded.append(
                {"start_pos": prev_end, "end_pos": start, "length": start - prev_end}
            )
        prev_end = max(prev_end, end)
    if prev_end < total_length:
        uncoded.append(
            {
                "start_pos": prev_end,
                "end_pos": total_length,
                "length": total_length - prev_end,
            }
        )

    return uncoded


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

    # Get actual source length
    total_length = 0
    source_repo = ctx.source_repo
    if source_repo is not None:
        source = source_repo.get_by_id(SourceId(int(source_id)))
        if source and source.fulltext:
            total_length = len(source.fulltext)

    uncoded_ranges = _compute_uncoded_ranges(segments, total_length)
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


def _score_code_for_text(code, text_lower: str) -> tuple[int, str]:
    """Score how well a code matches a text segment. Returns (confidence, rationale)."""
    score = 0
    reasons = []

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
    if reasons:
        rationale = f"Matched on {'; '.join(reasons)}"
    else:
        rationale = f"No strong match for code '{code.name}'"

    return confidence, rationale


def handle_suggest_codes_for_range(
    ctx: HandlerContext,
    arguments: dict[str, Any],
) -> dict[str, Any]:
    """Suggest codes for a text range based on content matching."""
    source_id = arguments.get("source_id")
    start_pos = arguments.get("start_pos")
    end_pos = arguments.get("end_pos")

    if source_id is None or start_pos is None or end_pos is None:
        return OperationResult.fail(
            error="Missing required parameters",
            error_code="SUGGEST_CODES_RANGE/MISSING_PARAMS",
        ).to_dict()

    codes = ctx.code_repo.get_all() if ctx.code_repo else []

    # Get the actual text from the source
    text_excerpt = ""
    source_repo = ctx.source_repo
    if source_repo is not None:
        source = source_repo.get_by_id(SourceId(int(source_id)))
        if source and source.fulltext:
            text_excerpt = source.fulltext[int(start_pos) : int(end_pos)]

    text_lower = text_excerpt.lower()
    batch_id = CodingSuggestionBatchId.new()

    # Score each code against the actual text
    scored = []
    for code in codes:
        confidence, rationale = _score_code_for_text(code, text_lower)
        scored.append(
            {
                "code_id": code.id.value,
                "code_name": code.name,
                "confidence": confidence,
                "rationale": rationale,
                "_code_id_obj": code.id,
            }
        )

    # Sort by confidence descending, return top 5
    scored.sort(key=lambda x: x["confidence"], reverse=True)
    top_suggestions = scored[:5]

    # Store suggestions as a batch in the cache so respond_to_code_suggestion can find them
    coding_suggestions = []
    for s in top_suggestions:
        csug_id = CodingSuggestionId.new()
        csug = CodingSuggestion(
            id=csug_id,
            source_id=SourceId(int(source_id)),
            code_id=s["_code_id_obj"],
            start_pos=int(start_pos),
            end_pos=int(end_pos),
            rationale=s["rationale"],
            confidence=s["confidence"] / 100.0,
        )
        coding_suggestions.append(csug)
        s["suggestion_id"] = csug_id.value

    batch = CodingSuggestionBatch(
        id=batch_id,
        source_id=SourceId(int(source_id)),
        suggestions=tuple(coding_suggestions),
    )
    ctx.suggestion_cache.coding_suggestions.add_batch(batch)

    # Remove internal keys before returning
    suggestions = [
        {k: v for k, v in s.items() if k != "_code_id_obj"} for s in top_suggestions
    ]

    return OperationResult.ok(
        data={
            "source_id": source_id,
            "start_pos": start_pos,
            "end_pos": end_pos,
            "suggestion_batch_id": batch_id.value,
            "suggestions": suggestions,
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

    codes = ctx.code_repo.get_all() if ctx.code_repo else []
    if not codes:
        return OperationResult.ok(
            data={
                "batch_id": CodingSuggestionBatchId.new().value,
                "source_id": source_id,
                "total_suggested": 0,
                "suggestions": [],
            }
        ).to_dict()

    # Get source text and uncoded ranges
    source_text = ""
    total_length = 0
    source_repo = ctx.source_repo
    if source_repo is not None:
        source = source_repo.get_by_id(SourceId(int(source_id)))
        if source and source.fulltext:
            source_text = source.fulltext
            total_length = len(source_text)

    segments = (
        ctx.segment_repo.get_by_source(SourceId(int(source_id)))
        if ctx.segment_repo
        else []
    )
    uncoded_ranges = _compute_uncoded_ranges(segments, total_length)

    batch_id = CodingSuggestionBatchId.new()
    suggestions = []
    coding_suggestions = []

    # For each uncoded range, find the best matching code
    for uncoded in uncoded_ranges:
        text_excerpt = source_text[uncoded["start_pos"] : uncoded["end_pos"]]
        text_lower = text_excerpt.lower()

        # Score all codes against this range
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
            source_id=SourceId(int(source_id)),
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
    ctx: HandlerContext,
    arguments: dict[str, Any],
) -> dict[str, Any]:
    """Respond to a batch of suggestions (accept or reject)."""
    batch_id = arguments.get("suggestion_batch_id")
    response = arguments.get("response")

    if not batch_id or not response:
        return OperationResult.fail(
            error="Missing required parameters",
            error_code="RESPOND_SUGGESTION/MISSING_PARAMS",
        ).to_dict()

    batch = ctx.suggestion_cache.coding_suggestions.get_batch(
        CodingSuggestionBatchId(batch_id)
    )
    if batch is None:
        return OperationResult.fail(
            error=f"Batch {batch_id} not found",
            error_code="RESPOND_SUGGESTION/NOT_FOUND",
        ).to_dict()

    if response == "accept":
        if ctx.segment_repo is None or ctx.code_repo is None:
            return no_context_error("RESPOND_SUGGESTION")

        selected_ids = set(arguments.get("selected_code_ids", []))
        applied_count = 0
        failed_count = 0

        for suggestion in batch.suggestions:
            if not suggestion.is_pending:
                continue
            # If selected_ids provided, only apply those; otherwise apply all
            if selected_ids and suggestion.code_id.value not in selected_ids:
                continue

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
                updated = suggestion.with_status("approved")
                ctx.suggestion_cache.coding_suggestions.update(updated)
                applied_count += 1
            else:
                failed_count += 1

        return OperationResult.ok(
            data={
                "status": "accepted",
                "applied_count": applied_count,
                "failed_count": failed_count,
            }
        ).to_dict()
    elif response == "reject":
        # Mark all pending suggestions as rejected
        for suggestion in batch.suggestions:
            if suggestion.is_pending:
                updated = suggestion.with_status("rejected")
                ctx.suggestion_cache.coding_suggestions.update(updated)

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
