"""
Handler Base Classes and Context

Provides the shared context and protocol for all MCP tool handlers.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Protocol, runtime_checkable

from src.contexts.coding.core.commandHandlers._state import (
    CategoryRepository,
    CodeRepository,
    SegmentRepository,
)
from src.shared.common.operation_result import OperationResult

if TYPE_CHECKING:
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
    def event_bus(self) -> EventBus:
        """Get the event bus."""
        ...


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
    def code_repo(self) -> CodeRepository | None:
        """Get the code repository from coding context."""
        if hasattr(self._ctx, "coding_context") and self._ctx.coding_context is not None:
            return self._ctx.coding_context.code_repo
        return None

    @property
    def category_repo(self) -> CategoryRepository | None:
        """Get the category repository from coding context."""
        if hasattr(self._ctx, "coding_context") and self._ctx.coding_context is not None:
            return self._ctx.coding_context.category_repo
        return None

    @property
    def segment_repo(self) -> SegmentRepository | None:
        """Get the segment repository from coding context."""
        if hasattr(self._ctx, "coding_context") and self._ctx.coding_context is not None:
            return self._ctx.coding_context.segment_repo
        return None

    @property
    def event_bus(self) -> EventBus:
        """Get the event bus."""
        return self._ctx.event_bus

    @property
    def suggestion_cache(self) -> SuggestionCache:
        """Get the suggestion cache."""
        return self._suggestion_cache


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
