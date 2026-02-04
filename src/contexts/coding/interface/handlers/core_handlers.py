"""
Core Tool Handlers

Handlers for: batch_apply_codes, list_codes, get_code, list_segments_for_source.
"""

from __future__ import annotations

from typing import Any

from src.contexts.coding.core.commandHandlers import (
    batch_apply_codes,
    get_all_codes,
    get_code,
    get_segments_for_source,
)
from src.contexts.coding.core.commands import ApplyCodeCommand, BatchApplyCodesCommand
from src.shared.common.operation_result import OperationResult

from .base import HandlerContext, missing_param_error, no_context_error


def handle_batch_apply_codes(
    ctx: HandlerContext,
    arguments: dict[str, Any],
) -> dict[str, Any]:
    """
    Execute batch_apply_codes tool.

    Applies multiple codes efficiently in a single batch operation.
    """
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

    # Convert operation dicts to ApplyCodeCommand objects
    operations = []
    for i, op in enumerate(operations_data):
        try:
            operations.append(
                ApplyCodeCommand(
                    code_id=int(op["code_id"]),
                    source_id=int(op["source_id"]),
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

    # Create batch command and execute
    command = BatchApplyCodesCommand(operations=tuple(operations))
    result = batch_apply_codes(
        command=command,
        code_repo=ctx.code_repo,
        category_repo=ctx.category_repo,
        segment_repo=ctx.segment_repo,
        event_bus=ctx.event_bus,
    )

    # Convert BatchApplyCodesResult to dict-friendly format
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
    """
    Execute list_codes tool.

    Returns list of all codes with summary information.
    """
    if ctx.code_repo is None:
        return no_context_error("CODES_NOT_LISTED")

    codes = get_all_codes(ctx.code_repo)
    return OperationResult.ok(data=codes).to_dict()


def handle_get_code(
    ctx: HandlerContext,
    arguments: dict[str, Any],
) -> dict[str, Any]:
    """
    Execute get_code tool.

    Returns detailed code information.
    """
    code_id = arguments.get("code_id")
    if code_id is None:
        return missing_param_error("CODE_NOT_FOUND", "code_id")

    if ctx.code_repo is None:
        return no_context_error("CODE_NOT_FOUND")

    code = get_code(ctx.code_repo, int(code_id))
    if code is None:
        return OperationResult.fail(
            error=f"Code {code_id} not found",
            error_code="CODE_NOT_FOUND",
        ).to_dict()
    return OperationResult.ok(data=code).to_dict()


def handle_list_segments(
    ctx: HandlerContext,
    arguments: dict[str, Any],
) -> dict[str, Any]:
    """
    Execute list_segments_for_source tool.

    Returns all coded segments for a source document.
    """
    source_id = arguments.get("source_id")
    if source_id is None:
        return missing_param_error("SEGMENTS_NOT_LISTED", "source_id")

    if ctx.segment_repo is None:
        return no_context_error("SEGMENTS_NOT_LISTED")

    segments = get_segments_for_source(ctx.segment_repo, int(source_id))
    return OperationResult.ok(data=segments).to_dict()


# Handler registry for core tools
CORE_HANDLERS = {
    "batch_apply_codes": handle_batch_apply_codes,
    "list_codes": handle_list_codes,
    "get_code": handle_get_code,
    "list_segments_for_source": handle_list_segments,
}
