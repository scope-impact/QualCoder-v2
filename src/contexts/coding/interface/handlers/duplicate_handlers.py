"""
QC-028.08: Detect Duplicate Codes Handlers

Handlers for detecting and merging semantically similar codes.

All mutation handlers delegate to command handlers to ensure proper event publishing.
"""

from __future__ import annotations

from typing import Any

from rapidfuzz import fuzz

from src.contexts.coding.core.ai_entities import (
    DetectionId,
    DuplicateCandidate,
    DuplicateDetectionResult,
    MergeSuggestion,
    MergeSuggestionId,
    SimilarityScore,
)
from src.contexts.coding.core.commandHandlers import merge_codes
from src.contexts.coding.core.commands import MergeCodesCommand
from src.shared.common.operation_result import OperationResult
from src.shared.common.types import CodeId

from .base import (
    HandlerContext,
    missing_param_error,
    missing_params_error,
    no_context_error,
    not_found_error,
)


def _calculate_similarity(
    name_a: str,
    name_b: str,
    memo_a: str | None = None,
    memo_b: str | None = None,
) -> float:
    """Calculate similarity using token-level matching.

    Uses rapidfuzz token_set_ratio which compares unique word sets,
    handling reordering and duplicates. When both codes have memos,
    blends name similarity (60%) with memo similarity (40%).
    """
    name_score = fuzz.token_set_ratio(name_a, name_b) / 100.0

    if memo_a and memo_b:
        memo_score = fuzz.token_set_ratio(memo_a, memo_b) / 100.0
        return 0.6 * name_score + 0.4 * memo_score

    return name_score


def handle_detect_duplicate_codes(
    ctx: HandlerContext,
    arguments: dict[str, Any],
) -> dict[str, Any]:
    """Detect semantically similar codes."""
    threshold = arguments.get("threshold", 0.8)

    if ctx.code_repo is None:
        return no_context_error("DETECT_DUPLICATES")

    codes = ctx.code_repo.get_all()
    candidates = []

    for i, code_a in enumerate(codes):
        for code_b in codes[i + 1 :]:
            similarity = _calculate_similarity(
                code_a.name,
                code_b.name,
                memo_a=code_a.memo,
                memo_b=code_b.memo,
            )
            if similarity < threshold:
                continue

            a_segments = (
                len(ctx.segment_repo.get_by_code(code_a.id)) if ctx.segment_repo else 0
            )
            b_segments = (
                len(ctx.segment_repo.get_by_code(code_b.id)) if ctx.segment_repo else 0
            )

            rationale = f"Names are similar: '{code_a.name}' vs '{code_b.name}'"
            if code_a.memo and code_b.memo:
                rationale += " (name + memo similarity)"

            candidates.append(
                DuplicateCandidate(
                    code_a_id=code_a.id,
                    code_a_name=code_a.name,
                    code_b_id=code_b.id,
                    code_b_name=code_b.name,
                    similarity=SimilarityScore(similarity),
                    rationale=rationale,
                    code_a_segment_count=a_segments,
                    code_b_segment_count=b_segments,
                )
            )

    candidates.sort(key=lambda c: c.similarity.value, reverse=True)

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
        return missing_params_error("SUGGEST_MERGE")

    if not rationale:
        return missing_param_error("SUGGEST_MERGE", "rationale")

    # Validate both codes exist
    if ctx.code_repo is not None:
        from src.contexts.coding.core.commandHandlers import get_code

        if get_code(ctx.code_repo, str(source_code_id)) is None:
            return not_found_error("SUGGEST_MERGE", "Source code", str(source_code_id))
        if get_code(ctx.code_repo, str(target_code_id)) is None:
            return not_found_error("SUGGEST_MERGE", "Target code", str(target_code_id))

    merge_id = MergeSuggestionId.new()
    suggestion = MergeSuggestion(
        id=merge_id,
        source_code_id=CodeId(value=str(source_code_id)),
        target_code_id=CodeId(value=str(target_code_id)),
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
    """Approve a merge suggestion.

    Delegates to merge_codes command handler for proper event publishing
    (CodesMerged) for UI refresh.
    """
    merge_id = arguments.get("merge_suggestion_id")
    if not merge_id:
        return missing_param_error("APPROVE_MERGE", "merge_suggestion_id")

    suggestion = ctx.suggestion_cache.merge_suggestions.get_by_id(
        MergeSuggestionId(merge_id)
    )
    if suggestion is None:
        return not_found_error("APPROVE_MERGE", "Merge suggestion", merge_id)

    if ctx.code_repo is None or ctx.segment_repo is None:
        return no_context_error("APPROVE_MERGE")

    command = MergeCodesCommand(
        source_code_id=suggestion.source_code_id.value,
        target_code_id=suggestion.target_code_id.value,
    )
    result = merge_codes(
        command=command,
        code_repo=ctx.code_repo,
        category_repo=ctx.category_repo,
        segment_repo=ctx.segment_repo,
        event_bus=ctx.event_bus,
        session=ctx.session,
    )

    if result.is_success:
        updated = suggestion.with_status("approved")
        ctx.suggestion_cache.merge_suggestions.update(updated)
        return OperationResult.ok(
            data={
                "status": "merged",
                "merged_from": suggestion.source_code_id.value,
                "merged_into": suggestion.target_code_id.value,
            }
        ).to_dict()

    return result.to_dict()


# Handler registry for duplicate detection tools
DUPLICATE_HANDLERS = {
    "detect_duplicate_codes": handle_detect_duplicate_codes,
    "suggest_merge_codes": handle_suggest_merge_codes,
    "approve_merge": handle_approve_merge,
}
