"""
MCP Folder Tools

Provides MCP-compatible tools for AI agent interaction with folders.

Implements QC-027.13: Agent can manage folders.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Protocol, runtime_checkable

from returns.result import Failure, Result, Success

from src.shared.common.mcp_types import ToolDefinition, ToolParameter

if TYPE_CHECKING:
    from src.shared.infra.state import ProjectState


@runtime_checkable
class FolderToolsContext(Protocol):
    """Protocol defining context requirements for FolderTools."""

    @property
    def state(self) -> ProjectState: ...

    @property
    def event_bus(self): ...

    @property
    def folders_context(self): ...

    @property
    def sources_context(self): ...


# ============================================================
# Tool Definitions
# ============================================================

list_folders_tool = ToolDefinition(
    name="list_folders",
    description="List all source folders in the current project, including hierarchy.",
    parameters=(),
)

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
            type="string",
            description="Parent folder ID for nesting. Omit for root-level folder.",
            required=False,
            default=None,
        ),
    ),
)

rename_folder_tool = ToolDefinition(
    name="rename_folder",
    description="Rename an existing folder.",
    parameters=(
        ToolParameter(
            name="folder_id",
            type="string",
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

delete_folder_tool = ToolDefinition(
    name="delete_folder",
    description="Delete an empty folder. Fails if folder contains sources.",
    parameters=(
        ToolParameter(
            name="folder_id",
            type="string",
            description="ID of the folder to delete.",
            required=True,
        ),
    ),
)

move_source_to_folder_tool = ToolDefinition(
    name="move_source_to_folder",
    description="Move a source into a folder for organization.",
    parameters=(
        ToolParameter(
            name="source_id",
            type="string",
            description="ID of the source to move.",
            required=True,
        ),
        ToolParameter(
            name="folder_id",
            type="string",
            description="Target folder ID. Use null or 0 for root.",
            required=False,
            default=None,
        ),
    ),
)

ALL_FOLDER_TOOLS = {
    "list_folders": list_folders_tool,
    "create_folder": create_folder_tool,
    "rename_folder": rename_folder_tool,
    "delete_folder": delete_folder_tool,
    "move_source_to_folder": move_source_to_folder_tool,
}


# ============================================================
# Tool Implementation
# ============================================================


class FolderTools:
    """MCP-compatible folder tools for AI agent integration."""

    def __init__(self, ctx: FolderToolsContext) -> None:
        self._ctx = ctx
        self._tools = ALL_FOLDER_TOOLS
        self._handlers = {
            "list_folders": self._execute_list_folders,
            "create_folder": self._execute_create_folder,
            "rename_folder": self._execute_rename_folder,
            "delete_folder": self._execute_delete_folder,
            "move_source_to_folder": self._execute_move_source_to_folder,
        }

    @property
    def _state(self):
        return self._ctx.state

    @property
    def _folder_repo(self):
        ctx = self._ctx.folders_context
        return ctx.folder_repo if ctx else None

    @property
    def _source_repo(self):
        ctx = self._ctx.sources_context
        return ctx.source_repo if ctx else None

    def get_tool_schemas(self) -> list[dict[str, Any]]:
        return [tool.to_schema() for tool in self._tools.values()]

    def get_tool_names(self) -> list[str]:
        return list(self._tools.keys())

    def execute(self, tool_name: str, arguments: dict[str, Any]) -> Result:
        handler = self._handlers.get(tool_name)
        if handler is None:
            return Failure(f"Unknown tool: {tool_name}")
        try:
            return handler(arguments)
        except Exception as e:
            return Failure(f"Tool execution error: {e!s}")

    # ── Handlers ──────────────────────────────────────────────

    def _execute_list_folders(
        self, _arguments: dict[str, Any]
    ) -> Result[dict[str, Any], str]:
        from src.contexts.folders.core.queryHandlers.list_folders import list_folders

        result = list_folders(state=self._state, folder_repo=self._folder_repo)

        if result.is_failure:
            return Failure(result.error or "Failed to list folders")

        return Success(result.data)

    def _execute_create_folder(
        self, arguments: dict[str, Any]
    ) -> Result[dict[str, Any], str]:
        from src.contexts.folders.core.commandHandlers.create_folder import (
            create_folder,
        )
        from src.contexts.folders.core.commands import CreateFolderCommand

        name = arguments.get("name")
        if name is None:
            return Failure("Missing required parameter: name")

        parent_id = arguments.get("parent_id")
        command = CreateFolderCommand(name=name, parent_id=parent_id)

        result = create_folder(
            command=command,
            state=self._state,
            folder_repo=self._folder_repo,
            source_repo=self._source_repo,
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
        from src.contexts.folders.core.commandHandlers.rename_folder import (
            rename_folder,
        )
        from src.contexts.folders.core.commands import RenameFolderCommand

        folder_id = arguments.get("folder_id")
        new_name = arguments.get("new_name")

        if folder_id is None:
            return Failure("Missing required parameter: folder_id")
        if new_name is None:
            return Failure("Missing required parameter: new_name")

        command = RenameFolderCommand(folder_id=str(folder_id), new_name=new_name)

        result = rename_folder(
            command=command,
            state=self._state,
            folder_repo=self._folder_repo,
            source_repo=self._source_repo,
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
        from src.contexts.folders.core.commandHandlers.delete_folder import (
            delete_folder,
        )
        from src.contexts.folders.core.commands import DeleteFolderCommand

        folder_id = arguments.get("folder_id")
        if folder_id is None:
            return Failure("Missing required parameter: folder_id")

        command = DeleteFolderCommand(folder_id=str(folder_id))

        result = delete_folder(
            command=command,
            state=self._state,
            folder_repo=self._folder_repo,
            source_repo=self._source_repo,
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
        from src.contexts.folders.core.commandHandlers.move_source import (
            move_source_to_folder,
        )
        from src.contexts.folders.core.commands import MoveSourceToFolderCommand

        source_id = arguments.get("source_id")
        if source_id is None:
            return Failure("Missing required parameter: source_id")

        folder_id = arguments.get("folder_id")
        if folder_id == 0:
            folder_id = None

        command = MoveSourceToFolderCommand(
            source_id=str(source_id),
            folder_id=str(folder_id) if folder_id is not None else None,
        )

        result = move_source_to_folder(
            command=command,
            state=self._state,
            folder_repo=self._folder_repo,
            source_repo=self._source_repo,
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
