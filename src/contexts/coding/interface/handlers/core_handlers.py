"""
Core Tool Handlers

Handlers for: batch_apply_codes, list_codes, get_code, list_segments_for_source,
delete_segment, create_code.

All mutation handlers delegate to command handlers to ensure proper event publishing.
"""

from __future__ import annotations

from typing import Any

from src.contexts.coding.core.commandHandlers import (
    batch_apply_codes,
    create_code,
    get_all_codes,
    get_code,
    get_segments_for_source,
    remove_segment,
)
from src.contexts.coding.core.commands import (
    ApplyCodeCommand,
    BatchApplyCodesCommand,
    CreateCodeCommand,
    RemoveCodeCommand,
)
from src.contexts.coding.core.entities import Code, TextSegment
from src.shared.common.operation_result import OperationResult

from .base import HandlerContext, missing_param_error, no_context_error, not_found_error


def _serialize_code(code: Code) -> dict[str, Any]:
    """Serialize Code entity to JSON-compatible dict."""
    return {
        "id": code.id.value,
        "name": code.name,
        "color": code.color.to_hex(),
        "memo": code.memo,
        "category_id": code.category_id.value if code.category_id else None,
        "owner": code.owner,
        "created_at": code.created_at.isoformat() if code.created_at else None,
    }


def _serialize_segment(segment: TextSegment) -> dict[str, Any]:
    """Serialize TextSegment entity to JSON-compatible dict."""
    return {
        "id": segment.id.value,
        "source_id": segment.source_id.value,
        "code_id": segment.code_id.value,
        "start_position": segment.position.start,
        "end_position": segment.position.end,
        "selected_text": segment.selected_text,
        "memo": segment.memo,
        "importance": segment.importance,
    }


def handle_batch_apply_codes(
    ctx: HandlerContext,
    arguments: dict[str, Any],
) -> dict[str, Any]:
    """Apply multiple codes efficiently in a single batch operation."""
    operations_data = arguments.get("operations")
    if operations_data is None:
        return missing_param_error(
            "BATCH_APPLY_CODES",
            "operations",
            "Provide operations array with code applications",
        )

    if not operations_data:
        return OperationResult.fail(
            error="Empty operations array",
            error_code="BATCH_APPLY_CODES/EMPTY_BATCH",
            suggestions=("Provide at least one operation",),
        ).to_dict()

    if ctx.code_repo is None:
        return no_context_error("BATCH_APPLY_CODES")

    operations = []
    for i, op in enumerate(operations_data):
        try:
            operations.append(
                ApplyCodeCommand(
                    code_id=str(op["code_id"]),
                    source_id=str(op["source_id"]),
                    start_position=int(op["start_position"]),
                    end_position=int(op["end_position"]),
                    memo=op.get("memo"),
                    importance=int(op.get("importance", 0)),
                )
            )
        except (KeyError, TypeError, ValueError) as e:
            return OperationResult.fail(
                error=f"Invalid operation at index {i}: {e!s}",
                error_code="BATCH_APPLY_CODES/INVALID_OPERATION",
                suggestions=(
                    "Each operation requires: code_id, source_id, start_position, end_position",
                    f"Operation {i} is malformed",
                ),
            ).to_dict()

    command = BatchApplyCodesCommand(operations=tuple(operations))
    result = batch_apply_codes(
        command=command,
        code_repo=ctx.code_repo,
        category_repo=ctx.category_repo,
        segment_repo=ctx.segment_repo,
        event_bus=ctx.event_bus,
    )

    if result.is_success and result.data:
        batch_result = result.data
        return OperationResult.ok(
            data={
                "total": batch_result.total,
                "succeeded": batch_result.succeeded,
                "failed": batch_result.failed,
                "all_succeeded": batch_result.all_succeeded,
                "results": [
                    {
                        "index": r.index,
                        "success": r.success,
                        "segment_id": r.segment.id.value if r.segment else None,
                        "error": r.error,
                        "error_code": r.error_code,
                    }
                    for r in batch_result.results
                ],
            }
        ).to_dict()

    return result.to_dict()


def handle_list_codes(
    ctx: HandlerContext,
    _arguments: dict[str, Any],
) -> dict[str, Any]:
    """Return all codes with summary information."""
    if ctx.code_repo is None:
        return no_context_error("CODES_NOT_LISTED")

    codes = get_all_codes(ctx.code_repo)
    return OperationResult.ok(data=[_serialize_code(c) for c in codes]).to_dict()


def handle_get_code(
    ctx: HandlerContext,
    arguments: dict[str, Any],
) -> dict[str, Any]:
    """Return detailed information for a single code."""
    code_id = arguments.get("code_id")
    if code_id is None:
        return missing_param_error("CODE_NOT_FOUND", "code_id")

    if ctx.code_repo is None:
        return no_context_error("CODE_NOT_FOUND")

    code = get_code(ctx.code_repo, str(code_id))
    if code is None:
        return not_found_error("CODE_NOT_FOUND", "Code", str(code_id))

    return OperationResult.ok(data=_serialize_code(code)).to_dict()


def handle_list_segments(
    ctx: HandlerContext,
    arguments: dict[str, Any],
) -> dict[str, Any]:
    """Return all coded segments for a source document."""
    source_id = arguments.get("source_id")
    if source_id is None:
        return missing_param_error("SEGMENTS_NOT_LISTED", "source_id")

    if ctx.segment_repo is None:
        return no_context_error("SEGMENTS_NOT_LISTED")

    # Validate source exists
    if ctx.source_repo is not None:
        from src.shared.common.types import SourceId

        source = ctx.source_repo.get_by_id(SourceId(value=str(source_id)))
        if source is None:
            return not_found_error("SEGMENTS_NOT_LISTED", "Source", str(source_id))

    segments = get_segments_for_source(ctx.segment_repo, str(source_id))
    return OperationResult.ok(data=[_serialize_segment(s) for s in segments]).to_dict()


def handle_delete_segment(
    ctx: HandlerContext,
    arguments: dict[str, Any],
) -> dict[str, Any]:
    """Remove a coded segment by ID via the remove_segment command handler."""
    segment_id = arguments.get("segment_id")
    if segment_id is None:
        return missing_param_error("DELETE_SEGMENT", "segment_id")

    if ctx.segment_repo is None or ctx.code_repo is None:
        return no_context_error("DELETE_SEGMENT")

    command = RemoveCodeCommand(segment_id=segment_id)
    result = remove_segment(
        command=command,
        code_repo=ctx.code_repo,
        category_repo=ctx.category_repo,
        segment_repo=ctx.segment_repo,
        event_bus=ctx.event_bus,
    )

    if result.is_success:
        return OperationResult.ok(
            data={"deleted": True, "segment_id": segment_id}
        ).to_dict()

    return result.to_dict()


def handle_create_code(
    ctx: HandlerContext,
    arguments: dict[str, Any],
) -> dict[str, Any]:
    """Create a new code in the codebook via the create_code command handler."""
    name = arguments.get("name")
    if name is None:
        return missing_param_error("CREATE_CODE", "name")

    color = arguments.get("color")
    if color is None:
        return missing_param_error("CREATE_CODE", "color")

    if ctx.code_repo is None:
        return no_context_error("CREATE_CODE")

    category_id_raw = arguments.get("category_id")
    command = CreateCodeCommand(
        name=str(name),
        color=str(color),
        memo=arguments.get("memo"),
        category_id=str(category_id_raw) if category_id_raw is not None else None,
    )

    result = create_code(
        command=command,
        code_repo=ctx.code_repo,
        category_repo=ctx.category_repo,
        segment_repo=ctx.segment_repo,
        event_bus=ctx.event_bus,
    )

    if result.is_success and result.data:
        code = result.data
        return OperationResult.ok(
            data={
                "code_id": code.id.value,
                "name": code.name,
                "color": code.color.to_hex(),
                "memo": code.memo,
                "category_id": code.category_id.value if code.category_id else None,
            }
        ).to_dict()

    return result.to_dict()


# Handler registry for core tools
CORE_HANDLERS = {
    "batch_apply_codes": handle_batch_apply_codes,
    "list_codes": handle_list_codes,
    "get_code": handle_get_code,
    "list_segments_for_source": handle_list_segments,
    "delete_segment": handle_delete_segment,
    "create_code": handle_create_code,
}
