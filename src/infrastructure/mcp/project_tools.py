"""
MCP Project Tools

Provides MCP-compatible tools for AI agent interaction with projects.

Implements QC-026:
- AC #5: Agent can query current project context
- AC #6: Agent can navigate to a specific source or segment

These tools follow the MCP (Model Context Protocol) specification:
- Each tool has a name, description, and input schema
- Tools return structured JSON responses
- Errors are returned as failure responses

Usage:
    from src.infrastructure.mcp import ProjectTools

    # Create tools with controller dependency
    tools = ProjectTools(controller=project_controller)

    # Execute a tool
    result = tools.execute("get_project_context", {})
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from returns.result import Failure, Result, Success

if TYPE_CHECKING:
    from src.application.projects.controller import ProjectControllerImpl


# ============================================================
# Tool Definitions (MCP Schema)
# ============================================================


@dataclass(frozen=True)
class ToolParameter:
    """MCP tool parameter definition."""

    name: str
    type: str
    description: str
    required: bool = True
    default: Any = None


@dataclass(frozen=True)
class ToolDefinition:
    """MCP tool definition with schema."""

    name: str
    description: str
    parameters: tuple[ToolParameter, ...] = field(default_factory=tuple)

    def to_schema(self) -> dict[str, Any]:
        """Convert to MCP-compatible JSON schema."""
        properties = {}
        required = []

        for param in self.parameters:
            properties[param.name] = {
                "type": param.type,
                "description": param.description,
            }
            if param.default is not None:
                properties[param.name]["default"] = param.default
            if param.required:
                required.append(param.name)

        return {
            "name": self.name,
            "description": self.description,
            "inputSchema": {
                "type": "object",
                "properties": properties,
                "required": required,
            },
        }


# Tool: get_project_context
get_project_context_tool = ToolDefinition(
    name="get_project_context",
    description=(
        "Get the current project context including project name, path, "
        "source files, and current screen. Returns structured information "
        "for AI agent to understand the current state."
    ),
    parameters=(),  # No parameters needed
)

# Tool: list_sources
list_sources_tool = ToolDefinition(
    name="list_sources",
    description=(
        "List all sources (documents, media files) in the current project. "
        "Optionally filter by source type."
    ),
    parameters=(
        ToolParameter(
            name="source_type",
            type="string",
            description="Filter by source type: 'text', 'audio', 'video', 'image', 'pdf'. Leave empty for all.",
            required=False,
            default=None,
        ),
    ),
)

# Tool: read_source_content
read_source_content_tool = ToolDefinition(
    name="read_source_content",
    description=(
        "Read the text content of a source document. "
        "Supports reading full content or a specific position range. "
        "Large documents are paginated with max_length parameter."
    ),
    parameters=(
        ToolParameter(
            name="source_id",
            type="integer",
            description="The ID of the source document to read.",
            required=True,
        ),
        ToolParameter(
            name="start_pos",
            type="integer",
            description="Starting character position. Default 0.",
            required=False,
            default=0,
        ),
        ToolParameter(
            name="end_pos",
            type="integer",
            description="Ending character position. Default: end of content.",
            required=False,
            default=None,
        ),
        ToolParameter(
            name="max_length",
            type="integer",
            description="Maximum characters to return. Default 50000 for pagination.",
            required=False,
            default=50000,
        ),
    ),
)

# Tool: navigate_to_segment
navigate_to_segment_tool = ToolDefinition(
    name="navigate_to_segment",
    description=(
        "Navigate to a specific segment position within a source document. "
        "Opens the source in the coding screen and scrolls to the specified position. "
        "Optionally highlights the segment."
    ),
    parameters=(
        ToolParameter(
            name="source_id",
            type="integer",
            description="The ID of the source document to navigate to.",
            required=True,
        ),
        ToolParameter(
            name="start_pos",
            type="integer",
            description="The character position where the segment starts.",
            required=True,
        ),
        ToolParameter(
            name="end_pos",
            type="integer",
            description="The character position where the segment ends.",
            required=True,
        ),
        ToolParameter(
            name="highlight",
            type="boolean",
            description="Whether to highlight the segment. Default true.",
            required=False,
            default=True,
        ),
    ),
)


# ============================================================
# Tool Implementation
# ============================================================


class ProjectTools:
    """
    MCP-compatible project tools for AI agent integration.

    Provides tools to:
    - Query current project context (AC #5)
    - Navigate to specific sources/segments (AC #6)
    - List and filter project sources

    Example:
        controller = ProjectControllerImpl(event_bus=EventBus())
        tools = ProjectTools(controller=controller)

        # Get available tools
        schemas = tools.get_tool_schemas()

        # Execute a tool
        result = tools.execute("get_project_context", {})
    """

    def __init__(self, controller: ProjectControllerImpl) -> None:
        """
        Initialize project tools with controller dependency.

        Args:
            controller: The project controller to delegate operations to
        """
        self._controller = controller
        self._tools: dict[str, ToolDefinition] = {
            "get_project_context": get_project_context_tool,
            "list_sources": list_sources_tool,
            "read_source_content": read_source_content_tool,
            "navigate_to_segment": navigate_to_segment_tool,
        }

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

    def execute(self, tool_name: str, arguments: dict[str, Any]) -> Result:
        """
        Execute an MCP tool by name with arguments.

        Args:
            tool_name: Name of the tool to execute
            arguments: Tool arguments as dict

        Returns:
            Success with result dict, or Failure with error message
        """
        if tool_name not in self._tools:
            return Failure(f"Unknown tool: {tool_name}")

        handlers = {
            "get_project_context": self._execute_get_project_context,
            "list_sources": self._execute_list_sources,
            "read_source_content": self._execute_read_source_content,
            "navigate_to_segment": self._execute_navigate_to_segment,
        }

        handler = handlers.get(tool_name)
        if handler is None:
            return Failure(f"No handler for tool: {tool_name}")

        try:
            return handler(arguments)
        except Exception as e:
            return Failure(f"Tool execution error: {e!s}")

    def _execute_get_project_context(
        self, _arguments: dict[str, Any]
    ) -> Result[dict[str, Any], str]:
        """
        Execute get_project_context tool.

        Returns project context including:
        - project_open: bool
        - project_name: str (if open)
        - project_path: str (if open)
        - source_count: int
        - sources: list of source dicts
        - current_screen: str
        """
        context = self._controller.get_project_context()
        return Success(context)

    def _execute_list_sources(
        self, arguments: dict[str, Any]
    ) -> Result[dict[str, Any], str]:
        """
        Execute list_sources tool.

        Args:
            arguments: May contain 'source_type' filter

        Returns:
            Dict with sources list
        """
        source_type = arguments.get("source_type")

        if source_type:
            sources = self._controller.get_sources_by_type(source_type)
        else:
            sources = self._controller.get_sources()

        return Success(
            {
                "count": len(sources),
                "sources": [
                    {
                        "id": s.id.value,
                        "name": s.name,
                        "type": s.source_type.value,
                        "status": s.status.value,
                        "file_path": str(s.file_path),
                        # AC #3: Source metadata
                        "memo": s.memo,
                        "file_size": s.file_size,
                        "origin": s.origin,
                        # AC #4: Coding status
                        "code_count": s.code_count,
                    }
                    for s in sources
                ],
            }
        )

    def _execute_read_source_content(
        self, arguments: dict[str, Any]
    ) -> Result[dict[str, Any], str]:
        """
        Execute read_source_content tool.

        Args:
            arguments: Must contain source_id. Optional: start_pos, end_pos, max_length

        Returns:
            Success with content and position markers, or Failure
        """
        # Get source_id
        source_id = arguments.get("source_id")
        if source_id is None:
            return Failure("Missing required parameter: source_id")

        # Find the source
        source = self._controller.get_source(int(source_id))
        if source is None:
            return Failure(f"Source not found: {source_id}")

        # Get content
        content = source.fulltext or ""
        total_length = len(content)

        # Apply position range
        start_pos = arguments.get("start_pos", 0) or 0
        end_pos = arguments.get("end_pos")
        max_length = arguments.get("max_length", 50000) or 50000

        # If end_pos not specified, use total_length
        if end_pos is None:
            end_pos = total_length

        # Apply max_length for pagination
        actual_end = min(end_pos, start_pos + max_length)
        extracted_content = content[start_pos:actual_end]
        has_more = actual_end < total_length

        return Success(
            {
                "source_id": source_id,
                "source_name": source.name,
                "content": extracted_content,
                "start_pos": start_pos,
                "end_pos": actual_end,
                "total_length": total_length,
                "has_more": has_more,
            }
        )

    def _execute_navigate_to_segment(
        self, arguments: dict[str, Any]
    ) -> Result[dict[str, Any], str]:
        """
        Execute navigate_to_segment tool.

        Args:
            arguments: Must contain source_id, start_pos, end_pos
                      May contain highlight (default True)

        Returns:
            Success with navigation result, or Failure
        """
        from src.application.projects.controller import NavigateToSegmentCommand

        # Validate required parameters
        source_id = arguments.get("source_id")
        start_pos = arguments.get("start_pos")
        end_pos = arguments.get("end_pos")

        if source_id is None:
            return Failure("Missing required parameter: source_id")
        if start_pos is None:
            return Failure("Missing required parameter: start_pos")
        if end_pos is None:
            return Failure("Missing required parameter: end_pos")

        highlight = arguments.get("highlight", True)

        # Create command and execute
        command = NavigateToSegmentCommand(
            source_id=int(source_id),
            start_pos=int(start_pos),
            end_pos=int(end_pos),
            highlight=bool(highlight),
        )

        result = self._controller.navigate_to_segment(command)

        if isinstance(result, Failure):
            return result

        return Success(
            {
                "success": True,
                "navigated_to": {
                    "source_id": source_id,
                    "start_pos": start_pos,
                    "end_pos": end_pos,
                    "highlight": highlight,
                },
                "current_screen": self._controller.get_current_screen(),
            }
        )
