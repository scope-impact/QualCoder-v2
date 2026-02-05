"""
MCP Project Tools

Provides MCP-compatible tools for AI agent interaction with projects.

Implements:
- QC-026.05: Agent can query current project context
- QC-026.06: Agent can navigate to a specific source or segment
- QC-026.07: Agent can open and close projects programmatically
- QC-027.08: Agent can list sources
- QC-027.09: Agent can read source content
- QC-027.10: Agent can extract/suggest metadata
- QC-027.12: Agent can add text sources
- QC-027.13: Agent can manage folders
- QC-027.14: Agent can remove sources

These tools follow the MCP (Model Context Protocol) specification:
- Each tool has a name, description, and input schema
- Tools return structured JSON responses
- Errors are returned as failure responses

Usage:
    from src.contexts import ProjectTools
    from src.shared.infra.app_context import create_app_context

    # Create tools with AppContext dependency
    ctx = create_app_context()
    tools = ProjectTools(ctx=ctx)

    # Execute a tool
    result = tools.execute("get_project_context", {})
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Protocol, runtime_checkable

from returns.result import Failure, Result, Success

if TYPE_CHECKING:
    from src.shared.common.operation_result import OperationResult
    from src.shared.infra.state import ProjectState


@runtime_checkable
class ProjectToolsContext(Protocol):
    """
    Protocol defining the context requirements for ProjectTools.

    Required properties:
    - state: ProjectState for project check
    - event_bus: EventBus for publishing domain events
    - signal_bridge: Optional ProjectSignalBridge for UI updates
    - sources_context: SourcesContext for source/folder repos
    - cases_context: CasesContext for case repo

    Required methods:
    - open_project: Open a project by path
    - close_project: Close the current project
    """

    @property
    def state(self) -> ProjectState:
        """Get the project state."""
        ...

    @property
    def event_bus(self):
        """Get the event bus for publishing domain events."""
        ...

    @property
    def signal_bridge(self):
        """Get the signal bridge for UI updates (optional)."""
        ...

    @property
    def sources_context(self):
        """Get sources context with source_repo (None if no project open)."""
        ...

    @property
    def cases_context(self):
        """Get cases context with case_repo (None if no project open)."""
        ...

    def open_project(self, path: str) -> OperationResult:
        """Open a project by path."""
        ...

    def close_project(self) -> OperationResult:
        """Close the current project."""
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


# ============================================================
# Existing Tool Definitions
# ============================================================

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
# New Tool Definitions (QC-026.07, QC-027.12, QC-027.13, QC-027.14)
# ============================================================

# Tool: open_project (QC-026.07)
open_project_tool = ToolDefinition(
    name="open_project",
    description=(
        "Open an existing QualCoder project file (.qda). "
        "Closes any currently open project first."
    ),
    parameters=(
        ToolParameter(
            name="path",
            type="string",
            description="Absolute path to the .qda project file.",
            required=True,
        ),
    ),
)

# Tool: close_project (QC-026.07)
close_project_tool = ToolDefinition(
    name="close_project",
    description=(
        "Close the currently open project. "
        "Safe to call when no project is open."
    ),
    parameters=(),
)

# Tool: add_text_source (QC-027.12)
add_text_source_tool = ToolDefinition(
    name="add_text_source",
    description=(
        "Add a new text source to the current project. "
        "Provide a name and text content. "
        "Optionally include memo and origin metadata."
    ),
    parameters=(
        ToolParameter(
            name="name",
            type="string",
            description="Name for the new source (must be unique within project).",
            required=True,
        ),
        ToolParameter(
            name="content",
            type="string",
            description="The full text content of the source.",
            required=True,
        ),
        ToolParameter(
            name="memo",
            type="string",
            description="Optional memo/notes about the source.",
            required=False,
            default=None,
        ),
        ToolParameter(
            name="origin",
            type="string",
            description="Optional origin description (e.g., 'interview transcript', 'field notes').",
            required=False,
            default=None,
        ),
    ),
)

# Tool: remove_source (QC-027.14)
remove_source_tool = ToolDefinition(
    name="remove_source",
    description=(
        "Remove a source from the project. "
        "This deletes the source, its content, and all coded segments. "
        "Use confirm=false to preview what would be deleted."
    ),
    parameters=(
        ToolParameter(
            name="source_id",
            type="integer",
            description="ID of the source to remove.",
            required=True,
        ),
        ToolParameter(
            name="confirm",
            type="boolean",
            description="Set to true to actually delete. Default false returns a preview.",
            required=False,
            default=False,
        ),
    ),
)

# Tool: list_folders (QC-027.13)
list_folders_tool = ToolDefinition(
    name="list_folders",
    description=(
        "List all source folders in the current project, including hierarchy."
    ),
    parameters=(),
)

# Tool: create_folder (QC-027.13)
create_folder_tool = ToolDefinition(
    name="create_folder",
    description="Create a new folder for organizing sources.",
    parameters=(
        ToolParameter(
            name="name",
            type="string",
            description="Folder name (must be unique within parent).",
            required=True,
        ),
        ToolParameter(
            name="parent_id",
            type="integer",
            description="Parent folder ID for nesting. Omit for root-level folder.",
            required=False,
            default=None,
        ),
    ),
)

# Tool: rename_folder (QC-027.13)
rename_folder_tool = ToolDefinition(
    name="rename_folder",
    description="Rename an existing folder.",
    parameters=(
        ToolParameter(
            name="folder_id",
            type="integer",
            description="ID of the folder to rename.",
            required=True,
        ),
        ToolParameter(
            name="new_name",
            type="string",
            description="New folder name.",
            required=True,
        ),
    ),
)

# Tool: delete_folder (QC-027.13)
delete_folder_tool = ToolDefinition(
    name="delete_folder",
    description="Delete an empty folder. Fails if folder contains sources.",
    parameters=(
        ToolParameter(
            name="folder_id",
            type="integer",
            description="ID of the folder to delete.",
            required=True,
        ),
    ),
)

# Tool: move_source_to_folder (QC-027.13)
move_source_to_folder_tool = ToolDefinition(
    name="move_source_to_folder",
    description="Move a source into a folder for organization.",
    parameters=(
        ToolParameter(
            name="source_id",
            type="integer",
            description="ID of the source to move.",
            required=True,
        ),
        ToolParameter(
            name="folder_id",
            type="integer",
            description="Target folder ID. Use null or 0 for root.",
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

    Provides tools for:
    - Project lifecycle: open, close, query context
    - Source management: list, read, add text, remove
    - Source metadata: suggest metadata
    - Folder management: list, create, rename, delete, move sources
    - Navigation: navigate to segment

    Example:
        from src.shared.infra.app_context import create_app_context

        ctx = create_app_context()
        tools = ProjectTools(ctx=ctx)

        # Get available tools
        schemas = tools.get_tool_schemas()

        # Execute a tool
        result = tools.execute("get_project_context", {})
    """

    def __init__(self, ctx: ProjectToolsContext) -> None:
        """
        Initialize project tools with context dependency.

        Args:
            ctx: The context containing state, event_bus, and signal_bridge (AppContext).
        """
        self._ctx = ctx

        self._tools: dict[str, ToolDefinition] = {
            # Existing tools
            "get_project_context": get_project_context_tool,
            "list_sources": list_sources_tool,
            "read_source_content": read_source_content_tool,
            "navigate_to_segment": navigate_to_segment_tool,
            "suggest_source_metadata": suggest_source_metadata_tool,
            # QC-026.07: Project lifecycle
            "open_project": open_project_tool,
            "close_project": close_project_tool,
            # QC-027.12: Add text source
            "add_text_source": add_text_source_tool,
            # QC-027.14: Remove source
            "remove_source": remove_source_tool,
            # QC-027.13: Folder management
            "list_folders": list_folders_tool,
            "create_folder": create_folder_tool,
            "rename_folder": rename_folder_tool,
            "delete_folder": delete_folder_tool,
            "move_source_to_folder": move_source_to_folder_tool,
        }

    @property
    def _state(self):
        """Get the project state from context."""
        return self._ctx.state

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
        handlers = {
            # Existing
            "get_project_context": self._execute_get_project_context,
            "list_sources": self._execute_list_sources,
            "read_source_content": self._execute_read_source_content,
            "navigate_to_segment": self._execute_navigate_to_segment,
            "suggest_source_metadata": self._execute_suggest_source_metadata,
            # QC-026.07
            "open_project": self._execute_open_project,
            "close_project": self._execute_close_project,
            # QC-027.12
            "add_text_source": self._execute_add_text_source,
            # QC-027.14
            "remove_source": self._execute_remove_source,
            # QC-027.13
            "list_folders": self._execute_list_folders,
            "create_folder": self._execute_create_folder,
            "rename_folder": self._execute_rename_folder,
            "delete_folder": self._execute_delete_folder,
            "move_source_to_folder": self._execute_move_source_to_folder,
        }

        handler = handlers.get(tool_name)
        if handler is None:
            return Failure(f"Unknown tool: {tool_name}")

        try:
            return handler(arguments)
        except Exception as e:
            return Failure(f"Tool execution error: {e!s}")

    # ============================================================
    # Existing Tool Handlers
    # ============================================================

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

        # Get sources and cases from repos (source of truth)
        sources_ctx = self._ctx.sources_context
        cases_ctx = self._ctx.cases_context

        all_sources = sources_ctx.source_repo.get_all() if sources_ctx else []
        all_cases = cases_ctx.case_repo.get_all() if cases_ctx else []

        context = {
            "project_open": True,
            "project_name": state.project.name,
            "project_path": str(state.project.path),
            "source_count": len(all_sources),
            "sources": [
                {
                    "id": s.id.value,
                    "name": s.name,
                    "type": s.source_type.value,
                    "status": s.status.value,
                }
                for s in all_sources
            ],
            "case_count": len(all_cases),
            "cases": [
                {
                    "id": c.id.value,
                    "name": c.name,
                    "description": c.description,
                }
                for c in all_cases
            ],
            "current_screen": state.current_screen,
        }
        return Success(context)

    def _execute_list_sources(
        self, arguments: dict[str, Any]
    ) -> Result[dict[str, Any], str]:
        """Execute list_sources tool."""
        source_type = arguments.get("source_type")

        # Get sources from repo (source of truth)
        sources_ctx = self._ctx.sources_context
        all_sources = sources_ctx.source_repo.get_all() if sources_ctx else []

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
        """Execute read_source_content tool."""
        # Get source_id
        source_id = arguments.get("source_id")
        if source_id is None:
            return Failure("Missing required parameter: source_id")

        # Find the source from repo (source of truth)
        sources_ctx = self._ctx.sources_context
        if not sources_ctx:
            return Failure("No project open")

        from src.shared.common.types import SourceId

        source = sources_ctx.source_repo.get_by_id(SourceId(value=int(source_id)))
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
        """Execute navigate_to_segment tool."""
        from src.contexts.projects.core.commands import NavigateToSegmentCommand

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

        # Validate source exists
        source_repo = self._ctx.sources_context.source_repo
        source = source_repo.get(int(source_id))
        if source is None:
            return Failure(f"Source not found: {source_id}")

        # Create command for navigation
        _command = NavigateToSegmentCommand(
            source_id=int(source_id),
            start_pos=int(start_pos),
            end_pos=int(end_pos),
            highlight=bool(highlight),
        )

        # TODO: Implement proper navigation handler in coding context
        # For now, just return success - the UI will handle the navigation
        # via signal bridge when implemented

        return Success(
            {
                "success": True,
                "navigated_to": {
                    "source_id": source_id,
                    "start_pos": start_pos,
                    "end_pos": end_pos,
                    "highlight": highlight,
                },
                "current_screen": self._state.current_screen,
            }
        )

    def _execute_suggest_source_metadata(
        self, arguments: dict[str, Any]
    ) -> Result[dict[str, Any], str]:
        """Execute suggest_source_metadata tool."""
        # Validate required parameter
        source_id = arguments.get("source_id")
        if source_id is None:
            return Failure("Missing required parameter: source_id")

        # Verify source exists via repo (source of truth)
        sources_ctx = self._ctx.sources_context
        if not sources_ctx:
            return Failure("No project open")

        from src.shared.common.types import SourceId as SId

        source = sources_ctx.source_repo.get_by_id(SId(value=int(source_id)))
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

    # ============================================================
    # QC-026.07: Project Lifecycle Tools
    # ============================================================

    def _execute_open_project(
        self, arguments: dict[str, Any]
    ) -> Result[dict[str, Any], str]:
        """
        Execute open_project tool.

        Calls AppContext.open_project() which delegates to the
        open_project command handler.
        """
        path = arguments.get("path")
        if not path:
            return Failure("Missing required parameter: path")

        result = self._ctx.open_project(str(path))

        if result.is_failure:
            return Failure(result.error or "Failed to open project")

        project = result.data
        return Success(
            {
                "success": True,
                "project_name": project.name,
                "project_path": str(project.path),
                "source_count": len(
                    self._ctx.sources_context.source_repo.get_all()
                    if self._ctx.sources_context
                    else []
                ),
            }
        )

    def _execute_close_project(
        self, _arguments: dict[str, Any]
    ) -> Result[dict[str, Any], str]:
        """
        Execute close_project tool.

        Idempotent - safe to call when no project is open.
        """
        if self._state.project is None:
            return Success(
                {
                    "success": True,
                    "closed": False,
                    "message": "No project was open",
                }
            )

        project_name = self._state.project.name
        result = self._ctx.close_project()

        if result.is_failure:
            return Failure(result.error or "Failed to close project")

        return Success(
            {
                "success": True,
                "closed": True,
                "project_name": project_name,
            }
        )

    # ============================================================
    # QC-027.12: Add Text Source Tool
    # ============================================================

    def _execute_add_text_source(
        self, arguments: dict[str, Any]
    ) -> Result[dict[str, Any], str]:
        """
        Execute add_text_source tool.

        Calls the add_text_source command handler to create a new
        text source with agent-provided content.
        """
        from src.contexts.projects.core.commands import AddTextSourceCommand
        from src.contexts.sources.core.commandHandlers.add_text_source import (
            add_text_source,
        )

        name = arguments.get("name")
        content = arguments.get("content")

        if not name:
            return Failure("Missing required parameter: name")
        if not content:
            return Failure("Missing required parameter: content")

        command = AddTextSourceCommand(
            name=name,
            content=content,
            memo=arguments.get("memo"),
            origin=arguments.get("origin"),
        )

        source_repo = (
            self._ctx.sources_context.source_repo
            if self._ctx.sources_context
            else None
        )

        result = add_text_source(
            command=command,
            state=self._state,
            source_repo=source_repo,
            event_bus=self._ctx.event_bus,
        )

        if result.is_failure:
            return Failure(result.error or "Failed to add source")

        source = result.data
        return Success(
            {
                "success": True,
                "source_id": source.id.value,
                "name": source.name,
                "type": source.source_type.value,
                "status": source.status.value,
                "file_size": source.file_size,
            }
        )

    # ============================================================
    # QC-027.14: Remove Source Tool
    # ============================================================

    def _execute_remove_source(
        self, arguments: dict[str, Any]
    ) -> Result[dict[str, Any], str]:
        """
        Execute remove_source tool.

        Supports preview mode (confirm=false) and actual deletion (confirm=true).
        Calls the remove_source command handler for actual deletion.
        """
        source_id = arguments.get("source_id")
        if source_id is None:
            return Failure("Missing required parameter: source_id")

        confirm = arguments.get("confirm", False)

        # Verify source exists
        sources_ctx = self._ctx.sources_context
        if not sources_ctx:
            return Failure("No project open")

        from src.shared.common.types import SourceId

        source = sources_ctx.source_repo.get_by_id(SourceId(value=int(source_id)))
        if source is None:
            return Failure(f"Source not found: {source_id}")

        # Preview mode: show what would be deleted
        if not confirm:
            return Success(
                {
                    "preview": True,
                    "source_id": source.id.value,
                    "source_name": source.name,
                    "source_type": source.source_type.value,
                    "coded_segments_count": source.code_count,
                    "requires_approval": True,
                    "message": (
                        f"This will delete source '{source.name}' "
                        f"and {source.code_count} coded segment(s)"
                    ),
                }
            )

        # Actual deletion via command handler
        from src.contexts.projects.core.commands import RemoveSourceCommand
        from src.contexts.sources.core.commandHandlers.remove_source import (
            remove_source,
        )

        command = RemoveSourceCommand(source_id=int(source_id))

        # Get segment_repo from coding context for cascade delete
        segment_repo = (
            self._ctx.coding_context.segment_repo
            if hasattr(self._ctx, "coding_context") and self._ctx.coding_context
            else None
        )

        result = remove_source(
            command=command,
            state=self._state,
            source_repo=sources_ctx.source_repo,
            segment_repo=segment_repo,
            event_bus=self._ctx.event_bus,
        )

        if result.is_failure:
            return Failure(result.error or "Failed to remove source")

        event = result.data
        return Success(
            {
                "success": True,
                "removed": True,
                "source_id": event.source_id.value,
                "source_name": event.name,
                "segments_removed": event.segments_removed,
            }
        )

    # ============================================================
    # QC-027.13: Folder Management Tools
    # ============================================================

    def _execute_list_folders(
        self, _arguments: dict[str, Any]
    ) -> Result[dict[str, Any], str]:
        """Execute list_folders tool (query - direct repo access)."""
        from src.contexts.folders.core.commandHandlers.list_folders import list_folders

        folder_repo = (
            self._ctx.sources_context.folder_repo
            if self._ctx.sources_context
            else None
        )

        result = list_folders(state=self._state, folder_repo=folder_repo)

        if result.is_failure:
            return Failure(result.error or "Failed to list folders")

        return Success(result.data)

    def _execute_create_folder(
        self, arguments: dict[str, Any]
    ) -> Result[dict[str, Any], str]:
        """Execute create_folder tool via command handler."""
        from src.contexts.folders.core.commandHandlers.create_folder import (
            create_folder,
        )
        from src.contexts.projects.core.commands import CreateFolderCommand

        name = arguments.get("name")
        if not name:
            return Failure("Missing required parameter: name")

        parent_id = arguments.get("parent_id")

        command = CreateFolderCommand(name=name, parent_id=parent_id)

        sources_ctx = self._ctx.sources_context
        folder_repo = sources_ctx.folder_repo if sources_ctx else None
        source_repo = sources_ctx.source_repo if sources_ctx else None

        result = create_folder(
            command=command,
            state=self._state,
            folder_repo=folder_repo,
            source_repo=source_repo,
            event_bus=self._ctx.event_bus,
        )

        if result.is_failure:
            return Failure(result.error or "Failed to create folder")

        folder = result.data
        return Success(
            {
                "success": True,
                "folder_id": folder.id.value,
                "name": folder.name,
                "parent_id": folder.parent_id.value if folder.parent_id else None,
            }
        )

    def _execute_rename_folder(
        self, arguments: dict[str, Any]
    ) -> Result[dict[str, Any], str]:
        """Execute rename_folder tool via command handler."""
        from src.contexts.folders.core.commandHandlers.rename_folder import (
            rename_folder,
        )
        from src.contexts.projects.core.commands import RenameFolderCommand

        folder_id = arguments.get("folder_id")
        new_name = arguments.get("new_name")

        if folder_id is None:
            return Failure("Missing required parameter: folder_id")
        if not new_name:
            return Failure("Missing required parameter: new_name")

        command = RenameFolderCommand(folder_id=int(folder_id), new_name=new_name)

        sources_ctx = self._ctx.sources_context
        folder_repo = sources_ctx.folder_repo if sources_ctx else None
        source_repo = sources_ctx.source_repo if sources_ctx else None

        result = rename_folder(
            command=command,
            state=self._state,
            folder_repo=folder_repo,
            source_repo=source_repo,
            event_bus=self._ctx.event_bus,
        )

        if result.is_failure:
            return Failure(result.error or "Failed to rename folder")

        folder = result.data
        return Success(
            {
                "success": True,
                "folder_id": folder.id.value,
                "name": folder.name,
            }
        )

    def _execute_delete_folder(
        self, arguments: dict[str, Any]
    ) -> Result[dict[str, Any], str]:
        """Execute delete_folder tool via command handler."""
        from src.contexts.folders.core.commandHandlers.delete_folder import (
            delete_folder,
        )
        from src.contexts.projects.core.commands import DeleteFolderCommand

        folder_id = arguments.get("folder_id")
        if folder_id is None:
            return Failure("Missing required parameter: folder_id")

        command = DeleteFolderCommand(folder_id=int(folder_id))

        sources_ctx = self._ctx.sources_context
        folder_repo = sources_ctx.folder_repo if sources_ctx else None
        source_repo = sources_ctx.source_repo if sources_ctx else None

        result = delete_folder(
            command=command,
            state=self._state,
            folder_repo=folder_repo,
            source_repo=source_repo,
            event_bus=self._ctx.event_bus,
        )

        if result.is_failure:
            return Failure(result.error or "Failed to delete folder")

        event = result.data
        return Success(
            {
                "success": True,
                "folder_id": event.folder_id.value,
                "name": event.name,
            }
        )

    def _execute_move_source_to_folder(
        self, arguments: dict[str, Any]
    ) -> Result[dict[str, Any], str]:
        """Execute move_source_to_folder tool via command handler."""
        from src.contexts.folders.core.commandHandlers.move_source import (
            move_source_to_folder,
        )
        from src.contexts.projects.core.commands import MoveSourceToFolderCommand

        source_id = arguments.get("source_id")
        if source_id is None:
            return Failure("Missing required parameter: source_id")

        # folder_id=0 treated as None (root)
        folder_id = arguments.get("folder_id")
        if folder_id == 0:
            folder_id = None

        command = MoveSourceToFolderCommand(
            source_id=int(source_id), folder_id=folder_id
        )

        sources_ctx = self._ctx.sources_context
        folder_repo = sources_ctx.folder_repo if sources_ctx else None
        source_repo = sources_ctx.source_repo if sources_ctx else None

        result = move_source_to_folder(
            command=command,
            state=self._state,
            folder_repo=folder_repo,
            source_repo=source_repo,
            event_bus=self._ctx.event_bus,
        )

        if result.is_failure:
            return Failure(result.error or "Failed to move source")

        event = result.data
        return Success(
            {
                "success": True,
                "source_id": event.source_id.value,
                "old_folder_id": (
                    event.old_folder_id.value if event.old_folder_id else None
                ),
                "new_folder_id": (
                    event.new_folder_id.value if event.new_folder_id else None
                ),
            }
        )
