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
    from src.application.app_context import get_app_context

    # Create tools with AppContext dependency
    ctx = get_app_context()
    tools = ProjectTools(ctx=ctx)

    # Execute a tool
    result = tools.execute("get_project_context", {})
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Protocol, runtime_checkable

from returns.result import Failure, Result, Success

if TYPE_CHECKING:
    from src.application.navigation.service import NavigationService
    from src.application.state import ProjectState


@runtime_checkable
class ProjectToolsContext(Protocol):
    """
    Protocol defining the context requirements for ProjectTools.

    This protocol allows ProjectTools to work with both AppContext
    (the target architecture) and CoordinatorInfrastructure (legacy).

    Required properties:
    - state: ProjectState for accessing sources, cases, project info
    - event_bus: EventBus for publishing domain events
    - signal_bridge: Optional ProjectSignalBridge for UI updates
    """

    @property
    def state(self) -> ProjectState:
        """Get the project state cache."""
        ...

    @property
    def event_bus(self):
        """Get the event bus for publishing domain events."""
        ...

    @property
    def signal_bridge(self):
        """Get the signal bridge for UI updates (optional)."""
        ...


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


# Tool: suggest_source_metadata
suggest_source_metadata_tool = ToolDefinition(
    name="suggest_source_metadata",
    description=(
        "Submit metadata suggestions for a source document. "
        "Agent provides extracted/suggested language, topics, and organization hints. "
        "Suggestions are stored with pending status for researcher approval."
    ),
    parameters=(
        ToolParameter(
            name="source_id",
            type="integer",
            description="The ID of the source document.",
            required=True,
        ),
        ToolParameter(
            name="language",
            type="string",
            description="Detected language code (e.g., 'en', 'es', 'fr').",
            required=False,
            default=None,
        ),
        ToolParameter(
            name="topics",
            type="array",
            description="List of extracted key topics/themes.",
            required=False,
            default=None,
        ),
        ToolParameter(
            name="organization_suggestion",
            type="string",
            description="Suggestion for organizing/grouping this source.",
            required=False,
            default=None,
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
        from src.application.app_context import get_app_context

        ctx = get_app_context()
        tools = ProjectTools(ctx=ctx)

        # Get available tools
        schemas = tools.get_tool_schemas()

        # Execute a tool
        result = tools.execute("get_project_context", {})
    """

    def __init__(
        self,
        ctx: ProjectToolsContext | None = None,
        *,
        navigation_service: NavigationService | None = None,
        # Legacy parameter for backward compatibility
        coordinator=None,
    ) -> None:
        """
        Initialize project tools with context dependency.

        Args:
            ctx: The context containing state, event_bus, and signal_bridge.
                 Can be either AppContext or CoordinatorInfrastructure.
            navigation_service: Optional pre-configured NavigationService. If not
                provided, one will be created from ctx when needed.
            coordinator: DEPRECATED. Use ctx instead. Accepts ApplicationCoordinator
                for backward compatibility (will use its internal infrastructure).
        """
        # Handle backward compatibility with old coordinator parameter
        if ctx is None and coordinator is not None:
            # ApplicationCoordinator has _infra which satisfies ProjectToolsContext
            ctx = coordinator._infra

        if ctx is None:
            raise ValueError(
                "ctx (AppContext or CoordinatorInfrastructure) is required"
            )

        self._ctx = ctx
        self._navigation_service = navigation_service

        self._tools: dict[str, ToolDefinition] = {
            "get_project_context": get_project_context_tool,
            "list_sources": list_sources_tool,
            "read_source_content": read_source_content_tool,
            "navigate_to_segment": navigate_to_segment_tool,
            "suggest_source_metadata": suggest_source_metadata_tool,
        }

    @property
    def _state(self):
        """Get the project state from context."""
        return self._ctx.state

    def _get_navigation_service(self) -> NavigationService:
        """
        Get or create the navigation service.

        Lazily creates NavigationService to avoid import issues during init.
        """
        if self._navigation_service is None:
            from src.application.navigation.service import NavigationService

            self._navigation_service = NavigationService(self._ctx)
        return self._navigation_service

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
            "suggest_source_metadata": self._execute_suggest_source_metadata,
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
        state = self._state

        if state.project is None:
            return Success({"project_open": False})

        context = {
            "project_open": True,
            "project_name": state.project.name,
            "project_path": str(state.project.path),
            "source_count": len(state.sources),
            "sources": [
                {
                    "id": s.id.value,
                    "name": s.name,
                    "type": s.source_type.value,
                    "status": s.status.value,
                }
                for s in state.sources
            ],
            "case_count": len(state.cases),
            "cases": [
                {
                    "id": c.id.value,
                    "name": c.name,
                    "description": c.description,
                }
                for c in state.cases
            ],
            "current_screen": state.current_screen,
        }
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
        all_sources = list(self._state.sources)

        if source_type:
            sources = [s for s in all_sources if s.source_type.value == source_type]
        else:
            sources = all_sources

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

        # Find the source from state
        source = self._state.get_source(int(source_id))
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
        from src.application.projects.commands import NavigateToSegmentCommand

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

        # Create command and execute via NavigationService
        command = NavigateToSegmentCommand(
            source_id=int(source_id),
            start_pos=int(start_pos),
            end_pos=int(end_pos),
            highlight=bool(highlight),
        )

        nav_service = self._get_navigation_service()
        result = nav_service.navigate_to_segment(command)

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
                "current_screen": nav_service.get_current_screen(),
            }
        )

    def _execute_suggest_source_metadata(
        self, arguments: dict[str, Any]
    ) -> Result[dict[str, Any], str]:
        """
        Execute suggest_source_metadata tool.

        Args:
            arguments: Must contain source_id. Optional: language, topics, organization_suggestion

        Returns:
            Success with suggestion stored (pending approval), or Failure
        """
        # Validate required parameter
        source_id = arguments.get("source_id")
        if source_id is None:
            return Failure("Missing required parameter: source_id")

        # Verify source exists
        source = self._state.get_source(int(source_id))
        if source is None:
            return Failure(f"Source not found: {source_id}")

        # Extract suggested metadata
        language = arguments.get("language")
        topics = arguments.get("topics", []) or []
        organization_suggestion = arguments.get("organization_suggestion")

        # Build suggestion record
        suggested = {}
        if language:
            suggested["language"] = language
        if topics:
            suggested["topics"] = topics
        if organization_suggestion:
            suggested["organization_suggestion"] = organization_suggestion

        # Return suggestion with pending status for researcher approval (AC #4)
        return Success(
            {
                "source_id": source_id,
                "source_name": source.name,
                "suggested": suggested,
                "status": "pending_approval",
                "requires_approval": True,
            }
        )
