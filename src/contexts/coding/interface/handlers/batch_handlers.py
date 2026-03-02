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

from .base import (
    HandlerContext,
    missing_param_error,
    missing_params_error,
    no_context_error,
    not_found_error,
)


def handle_find_similar_content(
    ctx: HandlerContext,
    arguments: dict[str, Any],
) -> dict[str, Any]:
    """Find similar content across sources."""
    search_text = arguments.get("search_text")
    if not search_text:
        return missing_param_error("FIND_SIMILAR", "search_text")

    source_repo = ctx.source_repo
    if source_repo is None:
        return no_context_error("FIND_SIMILAR")

    matches = []
    search_lower = search_text.lower()
    search_words = [w for w in search_lower.split() if len(w) > 2]

    for source in source_repo.get_all():
        content = source.fulltext
        if not content:
            continue

        content_lower = content.lower()
        source_matched = False

        # 1. Exact phrase match
        start = 0
        while True:
            pos = content_lower.find(search_lower, start)
            if pos == -1:
                break
            source_matched = True
            ctx_start = max(0, pos - 40)
            ctx_end = min(len(content), pos + len(search_text) + 40)
            matches.append(
                {
                    "source_id": source.id.value,
                    "source_name": source.name,
                    "start_pos": pos,
                    "end_pos": pos + len(search_text),
                    "text": content[ctx_start:ctx_end],
                }
            )
            start = pos + 1

        # 2. Word-proximity match: all search words within a sentence
        if not source_matched and len(search_words) > 1:
            sentences = content.replace("!", ".").replace("?", ".").split(".")
            char_offset = 0
            for sentence in sentences:
                sent_lower = sentence.lower()
                if all(w in sent_lower for w in search_words):
                    matches.append(
                        {
                            "source_id": source.id.value,
                            "source_name": source.name,
                            "start_pos": char_offset,
                            "end_pos": char_offset + len(sentence),
                            "text": sentence.strip(),
                        }
                    )
                char_offset += len(sentence) + 1  # +1 for the period

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
        return missing_params_error("BATCH_CODING")

    # Validate code exists
    if ctx.code_repo is not None:
        from src.contexts.coding.core.commandHandlers import get_code

        code = get_code(ctx.code_repo, str(code_id))
        if code is None:
            return not_found_error("BATCH_CODING", "Code", str(code_id))

    # Validate all referenced sources exist
    if ctx.source_repo is not None:
        from src.shared.common.types import SourceId as _SourceId

        seen_source_ids: set[str] = set()
        for seg in segments:
            sid = str(seg["source_id"])
            if sid not in seen_source_ids:
                seen_source_ids.add(sid)
                source = ctx.source_repo.get_by_id(_SourceId(value=sid))
                if source is None:
                    return not_found_error("BATCH_CODING", "Source", sid)

    batch_id = CodingSuggestionBatchId.new()
    coding_suggestions = []

    for seg in segments:
        csug_id = CodingSuggestionId.new()
        csug = CodingSuggestion(
            id=csug_id,
            source_id=SourceId(value=str(seg["source_id"])),
            code_id=CodeId(value=str(code_id)),
            start_pos=int(seg["start_pos"]),
            end_pos=int(seg["end_pos"]),
            rationale=rationale,
            confidence=0.8,
        )
        coding_suggestions.append(csug)

    batch = CodingSuggestionBatch(
        id=batch_id,
        source_id=SourceId(value=str(segments[0]["source_id"])),
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
