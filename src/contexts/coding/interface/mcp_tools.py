"""
MCP Coding Tools

Provides MCP-compatible tools for AI agent interaction with coding operations.

These tools follow the MCP (Model Context Protocol) specification:
- Each tool has a name, description, and input schema
- Tools return structured JSON responses via OperationResult.to_dict()
- Errors are returned as failure responses with error_code and suggestions

Tool categories:
- Core: batch_apply_codes, list_codes, get_code, list_segments_for_source
- QC-028.07: Suggest new codes (analyze_content_for_codes, suggest_new_code, etc.)
- QC-028.08: Detect duplicate codes (detect_duplicate_codes, suggest_merge_codes, etc.)
- QC-029.07: Apply code to text (suggest_code_application, approve_coding_suggestion, etc.)
- QC-029.08: Auto-suggest codes (auto_suggest_codes, suggest_codes_for_range, etc.)
- Batch: Multi-source operations (find_similar_content, suggest_batch_coding)

Usage:
    from src.contexts.coding.interface import CodingTools
    from src.shared.infra.app_context import create_app_context

    ctx = create_app_context()
    tools = CodingTools(ctx=ctx)

    # Get available tools
    schemas = tools.get_tool_schemas()

    # Execute batch apply
    result = tools.execute("batch_apply_codes", {
        "operations": [
            {"code_id": 1, "source_id": 1, "start_position": 0, "end_position": 50},
        ]
    })
"""

from __future__ import annotations

from typing import Any

from src.contexts.coding.infra.suggestion_cache import SuggestionCache
from src.shared.common.operation_result import OperationResult

from .handlers import ALL_HANDLERS, CodingToolsContext, HandlerContext
from .tool_definitions import ALL_TOOLS


class CodingTools:
    """
    MCP-compatible coding tools for AI agent integration.

    Provides tools organized by feature:
    - Core coding operations (batch_apply, list, get)
    - AI-assisted code suggestions (QC-028.07)
    - Duplicate code detection (QC-028.08)
    - AI-assisted text coding (QC-029.07, QC-029.08)
    - Batch operations

    All tools call use cases instead of direct repository access,
    and return OperationResult.to_dict() for consistent responses.

    Example:
        from src.shared.infra.app_context import create_app_context

        ctx = create_app_context()
        tools = CodingTools(ctx=ctx)

        # Get available tools
        schemas = tools.get_tool_schemas()

        # Execute batch apply
        result = tools.execute("batch_apply_codes", {
            "operations": [
                {"code_id": 1, "source_id": 1, "start_position": 0, "end_position": 50},
            ]
        })
    """

    def __init__(self, ctx: CodingToolsContext) -> None:
        """
        Initialize coding tools with context dependency.

        Args:
            ctx: The context containing repositories and event_bus.
                 Should be AppContext or any object implementing CodingToolsContext.
        """
        if ctx is None:
            raise ValueError("ctx is required")

        self._suggestion_cache = SuggestionCache()
        self._handler_ctx = HandlerContext(ctx, self._suggestion_cache)
        self._tools = ALL_TOOLS
        self._handlers = ALL_HANDLERS

    def get_tool_schemas(self) -> list[dict[str, Any]]:
        """
        Get MCP-compatible tool schemas for registration.

        Returns:
            List of tool schema dicts for MCP registration
        """
        return [tool.to_schema() for tool in self._tools.values()]

    def get_tool_names(self) -> list[str]:
        """Get list of available tool names."""
        return list(self._tools.keys())

    def execute(self, tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        """
        Execute an MCP tool by name with arguments.

        Args:
            tool_name: Name of the tool to execute
            arguments: Tool arguments as dict

        Returns:
            Dictionary with success/failure and data/error fields
        """
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
