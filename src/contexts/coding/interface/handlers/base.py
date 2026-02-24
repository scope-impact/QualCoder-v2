"""
Handler Base Classes and Context

Provides the shared context and protocol for all MCP tool handlers.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Protocol, runtime_checkable

from src.contexts.coding.core.commandHandlers import apply_code
from src.contexts.coding.core.commandHandlers._state import (
    CategoryRepository,
    CodeRepository,
    SegmentRepository,
)
from src.contexts.coding.core.commands import ApplyCodeCommand
from src.shared.common.operation_result import OperationResult
from src.shared.common.types import SourceId

if TYPE_CHECKING:
    from src.contexts.coding.core.ai_entities import CodingSuggestion
    from src.contexts.coding.infra.suggestion_cache import SuggestionCache
    from src.shared.infra.event_bus import EventBus


@runtime_checkable
class CodingToolsContext(Protocol):
    """
    Protocol defining the context requirements for CodingTools.

    Required properties:
    - coding_context: CodingContext with repositories
    - event_bus: EventBus for publishing events
    """

    @property
    def event_bus(self) -> EventBus: ...


class HandlerContext:
    """
    Shared context for all tool handlers.

    Provides access to repositories, event bus, and suggestion cache.
    """

    def __init__(
        self,
        ctx: CodingToolsContext,
        suggestion_cache: SuggestionCache,
    ) -> None:
        self._ctx = ctx
        self._suggestion_cache = suggestion_cache

    @property
    def _coding_context(self):
        """Get the coding context if available."""
        return getattr(self._ctx, "coding_context", None)

    @property
    def code_repo(self) -> CodeRepository | None:
        return self._coding_context.code_repo if self._coding_context else None

    @property
    def category_repo(self) -> CategoryRepository | None:
        return self._coding_context.category_repo if self._coding_context else None

    @property
    def segment_repo(self) -> SegmentRepository | None:
        return self._coding_context.segment_repo if self._coding_context else None

    @property
    def event_bus(self) -> EventBus:
        return self._ctx.event_bus

    @property
    def source_repo(self):
        sources_ctx = getattr(self._ctx, "sources_context", None)
        return sources_ctx.source_repo if sources_ctx else None

    @property
    def suggestion_cache(self) -> SuggestionCache:
        return self._suggestion_cache

    def get_source_text(self, source_id: int) -> str:
        """Retrieve the full text of a source, or empty string if unavailable."""
        if self.source_repo is None:
            return ""
        source = self.source_repo.get_by_id(SourceId(source_id))
        return source.fulltext if source and source.fulltext else ""

    def apply_suggestion(self, suggestion: CodingSuggestion) -> OperationResult:
        """Apply a coding suggestion via the apply_code command handler.

        Creates the segment and publishes the SegmentCoded event.
        Returns the OperationResult from apply_code.
        """
        command = ApplyCodeCommand(
            code_id=suggestion.code_id.value,
            source_id=suggestion.source_id.value,
            start_position=suggestion.start_pos,
            end_position=suggestion.end_pos,
            memo=suggestion.rationale,
        )
        return apply_code(
            command=command,
            code_repo=self.code_repo,
            category_repo=self.category_repo,
            segment_repo=self.segment_repo,
            event_bus=self.event_bus,
        )


@dataclass
class ApplyResult:
    """Result of applying a batch of pending suggestions."""

    applied_count: int
    failed_count: int
    errors: list[dict[str, Any]]


def apply_pending_suggestions(
    ctx: HandlerContext,
    suggestions: tuple | list,
    *,
    track_errors: bool = False,
) -> ApplyResult:
    """Apply all pending suggestions from a batch via the command handler.

    Iterates over suggestions, skips non-pending ones, applies each via
    ctx.apply_suggestion(), and updates the cache status.

    Args:
        ctx: Handler context with repos and event bus.
        suggestions: Iterable of CodingSuggestion entities.
        track_errors: If True, collect per-suggestion error details.

    Returns:
        ApplyResult with counts and optional error details.
    """
    applied_count = 0
    failed_count = 0
    errors: list[dict[str, Any]] = []

    for suggestion in suggestions:
        if not suggestion.is_pending:
            continue

        result = ctx.apply_suggestion(suggestion)
        if result.is_success:
            updated = suggestion.with_status("approved")
            ctx.suggestion_cache.coding_suggestions.update(updated)
            applied_count += 1
        else:
            failed_count += 1
            if track_errors:
                errors.append(
                    {
                        "suggestion_id": suggestion.id.value,
                        "error": result.error,
                        "error_code": result.error_code,
                    }
                )

    return ApplyResult(
        applied_count=applied_count,
        failed_count=failed_count,
        errors=errors,
    )


def no_context_error(error_code_prefix: str) -> dict[str, Any]:
    """Return a standardized 'no context' error response."""
    return OperationResult.fail(
        error="No coding context available",
        error_code=f"{error_code_prefix}/NO_CONTEXT",
        suggestions=("Open a project first",),
    ).to_dict()


def missing_param_error(
    error_code_prefix: str,
    param_name: str,
    suggestion: str | None = None,
) -> dict[str, Any]:
    """Return a standardized 'missing parameter' error response."""
    suggestions = (suggestion,) if suggestion else (f"Provide {param_name} parameter",)
    return OperationResult.fail(
        error=f"Missing required parameter: {param_name}",
        error_code=f"{error_code_prefix}/MISSING_PARAM",
        suggestions=suggestions,
    ).to_dict()


def missing_params_error(error_code_prefix: str) -> dict[str, Any]:
    """Return a standardized 'missing parameters' error for multi-param handlers."""
    return OperationResult.fail(
        error="Missing required parameters",
        error_code=f"{error_code_prefix}/MISSING_PARAMS",
    ).to_dict()


def not_found_error(
    error_code_prefix: str, entity: str, entity_id: str
) -> dict[str, Any]:
    """Return a standardized 'not found' error response."""
    return OperationResult.fail(
        error=f"{entity} {entity_id} not found",
        error_code=f"{error_code_prefix}/NOT_FOUND",
    ).to_dict()


def compute_uncoded_ranges(segments: list, total_length: int) -> list[dict[str, int]]:
    """Compute uncoded character ranges from coded segments.

    Merges overlapping coded ranges and returns the gaps as uncoded regions.
    Each returned dict has keys: start_pos, end_pos, length.
    """
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
    uncoded: list[dict[str, int]] = []
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
