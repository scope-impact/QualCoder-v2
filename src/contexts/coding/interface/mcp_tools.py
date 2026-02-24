"""MCP-compatible coding tools for AI agent integration."""

from __future__ import annotations

from typing import Any

from src.contexts.coding.infra.suggestion_cache import SuggestionCache
from src.shared.common.operation_result import OperationResult

from .handlers import ALL_HANDLERS, CodingToolsContext, HandlerContext
from .tool_definitions import ALL_TOOLS


class CodingTools:
    """Dispatches MCP tool calls to the appropriate coding handler.

    All tools delegate to command handlers (not direct repo access)
    and return OperationResult.to_dict() for consistent responses.
    """

    def __init__(self, ctx: CodingToolsContext) -> None:
        if ctx is None:
            raise ValueError("ctx is required")

        self._suggestion_cache = SuggestionCache()
        self._handler_ctx = HandlerContext(ctx, self._suggestion_cache)
        self._tools = ALL_TOOLS
        self._handlers = ALL_HANDLERS

    def get_tool_schemas(self) -> list[dict[str, Any]]:
        """Return MCP-compatible tool schemas for registration."""
        return [tool.to_schema() for tool in self._tools.values()]

    def get_tool_names(self) -> list[str]:
        """Return list of available tool names."""
        return list(self._tools.keys())

    def execute(self, tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        """Execute an MCP tool by name with arguments."""
        if tool_name not in self._tools:
            return OperationResult.fail(
                error=f"Unknown tool: {tool_name}",
                error_code="TOOL_NOT_FOUND",
                suggestions=(f"Available tools: {', '.join(self._tools.keys())}",),
            ).to_dict()

        handler = self._handlers.get(tool_name)
        if handler is None:
            return OperationResult.fail(
                error=f"No handler for tool: {tool_name}",
                error_code="HANDLER_NOT_FOUND",
            ).to_dict()

        try:
            return handler(self._handler_ctx, arguments)
        except Exception as e:
            return OperationResult.fail(
                error=f"Tool execution error: {e!s}",
                error_code="TOOL_EXECUTION_ERROR",
            ).to_dict()
