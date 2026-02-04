"""
QC-028.08: Detect Duplicate Codes Handlers

Handlers for detecting and merging semantically similar codes.
"""

from __future__ import annotations

from difflib import SequenceMatcher
from typing import Any

from src.contexts.coding.core.ai_entities import (
    DetectionId,
    DuplicateCandidate,
    DuplicateDetectionResult,
    MergeSuggestion,
    MergeSuggestionId,
    SimilarityScore,
)
from src.contexts.coding.core.entities import TextSegment
from src.shared.common.operation_result import OperationResult
from src.shared.common.types import CodeId

from .base import HandlerContext, missing_param_error, no_context_error


def _calculate_similarity(a: str, b: str) -> float:
    """Calculate similarity between two strings."""
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()


def handle_detect_duplicate_codes(
    ctx: HandlerContext,
    arguments: dict[str, Any],
) -> dict[str, Any]:
    """Detect semantically similar codes."""
    threshold = arguments.get("threshold", 0.8)
    include_usage = arguments.get("include_usage_analysis", False)

    if ctx.code_repo is None:
        return no_context_error("DETECT_DUPLICATES")

    codes = ctx.code_repo.get_all()
    candidates = []

    # Simple name-based similarity detection
    for i, code_a in enumerate(codes):
        for code_b in codes[i + 1 :]:
            similarity = _calculate_similarity(code_a.name, code_b.name)
            if similarity >= threshold:
                # Get segment counts
                a_segments = (
                    len(ctx.segment_repo.get_by_code(code_a.id))
                    if ctx.segment_repo
                    else 0
                )
                b_segments = (
                    len(ctx.segment_repo.get_by_code(code_b.id))
                    if ctx.segment_repo
                    else 0
                )

                candidate = DuplicateCandidate(
                    code_a_id=code_a.id,
                    code_a_name=code_a.name,
                    code_b_id=code_b.id,
                    code_b_name=code_b.name,
                    similarity=SimilarityScore(similarity),
                    rationale=f"Names are similar: '{code_a.name}' vs '{code_b.name}'",
                    code_a_segment_count=a_segments,
                    code_b_segment_count=b_segments,
                )
                candidates.append(candidate)

    # Sort by similarity (highest first)
    candidates.sort(key=lambda c: c.similarity.value, reverse=True)

    # Store detection result
    detection = DuplicateDetectionResult(
        id=DetectionId.new(),
        candidates=tuple(candidates),
        threshold=threshold,
        codes_analyzed=len(codes),
    )
    ctx.suggestion_cache.duplicate_detections.add(detection)

    return OperationResult.ok(
        data={
            "requires_approval": True,
            "codes_analyzed": len(codes),
            "candidates": [
                {
                    "code_a_id": c.code_a_id.value,
                    "code_a_name": c.code_a_name,
                    "code_b_id": c.code_b_id.value,
                    "code_b_name": c.code_b_name,
                    "similarity": c.similarity.percentage,
                    "rationale": c.rationale,
                    "code_a_segments": c.code_a_segment_count,
                    "code_b_segments": c.code_b_segment_count,
                }
                for c in candidates
            ],
        }
    ).to_dict()


def handle_suggest_merge_codes(
    ctx: HandlerContext,
    arguments: dict[str, Any],
) -> dict[str, Any]:
    """Suggest merging codes."""
    source_code_id = arguments.get("source_code_id")
    target_code_id = arguments.get("target_code_id")
    rationale = arguments.get("rationale")

    if source_code_id is None or target_code_id is None:
        return OperationResult.fail(
            error="Missing required parameters: source_code_id and target_code_id",
            error_code="SUGGEST_MERGE/MISSING_PARAMS",
        ).to_dict()

    if not rationale:
        return missing_param_error("SUGGEST_MERGE", "rationale")

    merge_id = MergeSuggestionId.new()
    suggestion = MergeSuggestion(
        id=merge_id,
        source_code_id=CodeId(int(source_code_id)),
        target_code_id=CodeId(int(target_code_id)),
        rationale=rationale,
    )

    ctx.suggestion_cache.merge_suggestions.add(suggestion)

    return OperationResult.ok(
        data={
            "status": "pending_approval",
            "requires_approval": True,
            "merge_suggestion_id": merge_id.value,
            "merge_source_id": source_code_id,
            "merge_target_id": target_code_id,
        }
    ).to_dict()


def handle_approve_merge(
    ctx: HandlerContext,
    arguments: dict[str, Any],
) -> dict[str, Any]:
    """Approve a merge suggestion."""
    merge_id = arguments.get("merge_suggestion_id")
    if not merge_id:
        return missing_param_error("APPROVE_MERGE", "merge_suggestion_id")

    suggestion = ctx.suggestion_cache.merge_suggestions.get_by_id(
        MergeSuggestionId(merge_id)
    )
    if suggestion is None:
        return OperationResult.fail(
            error=f"Merge suggestion {merge_id} not found",
            error_code="APPROVE_MERGE/NOT_FOUND",
        ).to_dict()

    # Execute merge: Update all segments from source to target, then delete source
    if ctx.segment_repo:
        segments = ctx.segment_repo.get_by_code(suggestion.source_code_id)
        for segment in segments:
            updated = TextSegment(
                id=segment.id,
                source_id=segment.source_id,
                code_id=suggestion.target_code_id,
                position=segment.position,
                selected_text=segment.selected_text,
                memo=segment.memo,
                importance=segment.importance,
                owner=segment.owner,
                created_at=segment.created_at,
            )
            ctx.segment_repo.save(updated)

    # Delete source code
    if ctx.code_repo:
        ctx.code_repo.delete(suggestion.source_code_id)

    # Update suggestion status
    updated = suggestion.with_status("approved")
    ctx.suggestion_cache.merge_suggestions.update(updated)

    return OperationResult.ok(
        data={
            "status": "merged",
            "merged_from": suggestion.source_code_id.value,
            "merged_into": suggestion.target_code_id.value,
        }
    ).to_dict()


# Handler registry for duplicate detection tools
DUPLICATE_HANDLERS = {
    "detect_duplicate_codes": handle_detect_duplicate_codes,
    "suggest_merge_codes": handle_suggest_merge_codes,
    "approve_merge": handle_approve_merge,
}
