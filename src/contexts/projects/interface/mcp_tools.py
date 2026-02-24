"""
MCP Project Tools

Provides MCP-compatible tools for AI agent interaction with projects.

Implements:
- QC-026.05: Agent can query current project context
- QC-026.07: Agent can open and close projects programmatically

Source and folder tools live in their own bounded contexts:
- src/contexts/sources/interface/mcp_tools.py (SourceTools)
- src/contexts/folders/interface/mcp_tools.py (FolderTools)
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Protocol, runtime_checkable

from returns.result import Failure, Result, Success

from src.shared.common.mcp_types import ToolDefinition, ToolParameter

if TYPE_CHECKING:
    from src.shared.common.operation_result import OperationResult
    from src.shared.infra.state import ProjectState


@runtime_checkable
class ProjectToolsContext(Protocol):
    """Protocol defining the context requirements for ProjectTools."""

    @property
    def state(self) -> ProjectState: ...

    @property
    def sources_context(self): ...

    @property
    def cases_context(self): ...

    def open_project(self, path: str) -> OperationResult: ...

    def close_project(self) -> OperationResult: ...


# ============================================================
# Tool Definitions
# ============================================================

get_project_context_tool = ToolDefinition(
    name="get_project_context",
    description=(
        "Get the current project context including project name, path, "
        "source files, and current screen. Returns structured information "
        "for AI agent to understand the current state."
    ),
    parameters=(),
)

open_project_tool = ToolDefinition(
    name="open_project",
    description=(
        "Open an existing QualCoder project file (.qda). "
        "NOTE: Projects must be opened from the QualCoder UI "
        "(File > Open Project) to ensure proper database initialization. "
        "This tool returns guidance to the user."
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

close_project_tool = ToolDefinition(
    name="close_project",
    description=(
        "Close the currently open project. "
        "NOTE: Projects must be closed from the QualCoder UI "
        "(File > Close Project) to ensure proper cleanup. "
        "This tool returns guidance to the user."
    ),
    parameters=(),
)

ALL_PROJECT_TOOLS = {
    "get_project_context": get_project_context_tool,
    "open_project": open_project_tool,
    "close_project": close_project_tool,
}


# Tool: get_sync_status
get_sync_status_tool = ToolDefinition(
    name="get_sync_status",
    description=(
        "Get the current cloud sync status. Returns whether cloud sync is enabled, "
        "connection status, pending changes count, and last sync time. "
        "Use this to check if the project is syncing with other devices."
    ),
    parameters=(),  # No parameters needed
)


# Tool: sync_pull
sync_pull_tool = ToolDefinition(
    name="sync_pull",
    description=(
        "Pull remote changes from cloud (like 'git pull'). "
        "Fetches latest data from Convex and applies to local SQLite. "
        "Use this to sync changes made on other devices."
    ),
    parameters=(
        ToolParameter(
            name="entity_types",
            type="array",
            description=(
                "Entity types to pull. Options: code, category, segment, source, folder, case. "
                "Default: all types."
            ),
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

    Provides tools for project lifecycle: open, close, query context.
    Source and folder tools are in SourceTools and FolderTools respectively.
    """

    def __init__(self, ctx: ProjectToolsContext) -> None:
        self._ctx = ctx
        self._tools: dict[str, ToolDefinition] = {
            **ALL_PROJECT_TOOLS,
            "get_sync_status": get_sync_status_tool,
            "sync_pull": sync_pull_tool,
        }
        self._handlers = {
            "get_project_context": self._execute_get_project_context,
            "open_project": self._execute_open_project,
            "close_project": self._execute_close_project,
            "get_sync_status": self._execute_get_sync_status,
            "sync_pull": self._execute_sync_pull,
        }

    @property
    def _state(self):
        return self._ctx.state

    def get_tool_schemas(self) -> list[dict[str, Any]]:
        return [tool.to_schema() for tool in self._tools.values()]

    def get_tool_names(self) -> list[str]:
        return list(self._tools.keys())

    def execute(self, tool_name: str, arguments: dict[str, Any]) -> Result:
        handler = self._handlers.get(tool_name)
        if handler is not None:
            try:
                return handler(arguments)
            except Exception as e:
                return Failure(f"Tool execution error: {e!s}")

        return Failure(f"Unknown tool: {tool_name}")

    # ── Project Lifecycle Handlers ────────────────────────────

    def _execute_get_project_context(
        self, _arguments: dict[str, Any]
    ) -> Result[dict[str, Any], str]:
        state = self._state

        if state.project is None:
            return Success({"project_open": False})

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

    def _execute_open_project(
        self, arguments: dict[str, Any]
    ) -> Result[dict[str, Any], str]:
        path = arguments.get("path", "")
        return Success(
            {
                "success": False,
                "message": (
                    "Please open the project from the QualCoder UI "
                    "(File > Open Project) to ensure database connections "
                    "are properly initialized. "
                    f"Requested path: {path}"
                ),
            }
        )

    def _execute_close_project(
        self, _arguments: dict[str, Any]
    ) -> Result[dict[str, Any], str]:
        return Success(
            {
                "success": False,
                "message": (
                    "Please close the project from the QualCoder UI "
                    "(File > Close Project) to ensure database connections "
                    "are properly cleaned up."
                ),
            }
        )

    def _execute_get_sync_status(
        self, _arguments: dict[str, Any]
    ) -> Result[dict[str, Any], str]:
        """
        Execute get_sync_status tool using command handler.

        Returns sync status including:
        - cloud_sync_enabled: bool - whether cloud sync is enabled in settings
        - connected: bool - whether currently connected to cloud
        - status: string - current sync status (offline, connecting, syncing, synced, error)
        - pending_changes: int - number of changes waiting to sync
        - last_sync: string or null - ISO timestamp of last successful sync
        - error: string or null - error message if status is 'error'
        """
        from src.shared.core.sync.commands import SyncStatusCommand
        from src.shared.infra.sync.commandHandlers import handle_sync_status

        # Use public API methods instead of private attribute access
        sync_engine = self._ctx.get_sync_engine()
        cloud_sync_enabled = self._ctx.is_cloud_sync_enabled()

        # Call command handler (same pattern as ViewModel)
        result = handle_sync_status(
            cmd=SyncStatusCommand(),
            sync_engine=sync_engine,
            cloud_sync_enabled=cloud_sync_enabled,
        )

        if result.success:
            return Success(result.data)
        return Failure(result.error or "Failed to get sync status")

    def _execute_sync_pull(
        self, arguments: dict[str, Any]
    ) -> Result[dict[str, Any], str]:
        """
        Execute sync_pull tool using command handler.

        Pulls remote changes from Convex (like 'git pull').
        Calls the same command handler that ViewModel would use.

        Args:
            arguments: May contain 'entity_types' array

        Returns:
            Success with pull results, or Failure with error
        """
        from src.shared.core.sync.commands import SyncPullCommand
        from src.shared.infra.sync.commandHandlers import handle_sync_pull

        # Use public API
        sync_engine = self._ctx.get_sync_engine()
        if sync_engine is None:
            return Failure("Cloud sync not enabled")

        # Build command
        entity_types = arguments.get("entity_types")
        if entity_types:
            cmd = SyncPullCommand(entity_types=tuple(entity_types))
        else:
            cmd = SyncPullCommand()  # Default: all types

        # Call command handler (same as ViewModel would)
        result = handle_sync_pull(
            cmd=cmd,
            sync_engine=sync_engine,
            event_bus=self._ctx.event_bus,
        )

        if result.success:
            return Success(result.data)
        return Failure(result.error or "Sync pull failed")
