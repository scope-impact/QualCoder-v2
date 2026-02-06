"""MCP Version Control Tools - AI agent integration for version control."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from src.contexts.projects.core.commandHandlers import (
    initialize_version_control,
    list_snapshots,
    restore_snapshot,
    view_diff,
)
from src.contexts.projects.core.vcs_commands import (
    InitializeVersionControlCommand,
    RestoreSnapshotCommand,
)
from src.shared.common.operation_result import OperationResult

if TYPE_CHECKING:
    from src.contexts.projects.infra.git_repository_adapter import GitRepositoryAdapter
    from src.contexts.projects.infra.sqlite_diffable_adapter import (
        SqliteDiffableAdapter,
    )
    from src.shared.infra.event_bus import EventBus
    from src.shared.infra.state import ProjectState


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
    parameters: tuple[ToolParameter, ...] = ()
    is_destructive: bool = False

    def to_schema(self) -> dict[str, Any]:
        """Convert to MCP-compatible JSON schema."""
        properties = {}
        required = []

        for param in self.parameters:
            prop: dict[str, Any] = {
                "type": param.type,
                "description": param.description,
            }
            if param.default is not None:
                prop["default"] = param.default
            if param.required:
                required.append(param.name)
            properties[param.name] = prop

        schema: dict[str, Any] = {
            "name": self.name,
            "description": self.description,
            "inputSchema": {
                "type": "object",
                "properties": properties,
                "required": required,
            },
        }
        if self.is_destructive:
            schema["annotations"] = {"destructive": True}
        return schema


# Tool definitions
list_snapshots_tool = ToolDefinition(
    name="list_snapshots",
    description="List version control snapshots (commit history). Returns SHA, message, author, date.",
    parameters=(
        ToolParameter(
            name="limit",
            type="integer",
            description="Max snapshots to return. Default 20.",
            required=False,
            default=20,
        ),
    ),
)

view_diff_tool = ToolDefinition(
    name="view_diff",
    description="View differences between two snapshots. Refs can be SHAs or HEAD~N.",
    parameters=(
        ToolParameter(
            name="from_ref", type="string", description="Starting commit reference."
        ),
        ToolParameter(
            name="to_ref", type="string", description="Ending commit reference."
        ),
    ),
)

restore_snapshot_tool = ToolDefinition(
    name="restore_snapshot",
    description="DESTRUCTIVE: Restore database to a previous snapshot. Use list_snapshots to find refs.",
    parameters=(
        ToolParameter(
            name="ref",
            type="string",
            description="Commit reference to restore (SHA or HEAD~N).",
        ),
    ),
    is_destructive=True,
)

initialize_version_control_tool = ToolDefinition(
    name="initialize_version_control",
    description="Initialize version control for the project. Creates Git repo and initial snapshot.",
    parameters=(),
)


class VersionControlMCPTools:
    """MCP-compatible version control tools for AI agent integration."""

    def __init__(
        self,
        diffable: SqliteDiffableAdapter,
        git: GitRepositoryAdapter,
        event_bus: EventBus,
        state: ProjectState,
    ) -> None:
        self._diffable = diffable
        self._git = git
        self._event_bus = event_bus
        self._state = state
        self._tools: dict[str, ToolDefinition] = {
            "list_snapshots": list_snapshots_tool,
            "view_diff": view_diff_tool,
            "restore_snapshot": restore_snapshot_tool,
            "initialize_version_control": initialize_version_control_tool,
        }

    def get_tool_schemas(self) -> list[dict[str, Any]]:
        """Get MCP-compatible tool schemas for registration."""
        return [tool.to_schema() for tool in self._tools.values()]

    def get_tool_names(self) -> list[str]:
        return list(self._tools.keys())

    def execute(self, tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        """Execute an MCP tool by name with arguments."""
        if tool_name not in self._tools:
            return OperationResult.fail(
                error=f"Unknown tool: {tool_name}",
                error_code="TOOL_NOT_FOUND",
                suggestions=(f"Available tools: {', '.join(self._tools.keys())}",),
            ).to_dict()

        handlers = {
            "list_snapshots": self._execute_list_snapshots,
            "view_diff": self._execute_view_diff,
            "restore_snapshot": self._execute_restore_snapshot,
            "initialize_version_control": self._execute_initialize_version_control,
        }

        try:
            return handlers[tool_name](arguments)
        except Exception as e:
            return OperationResult.fail(
                error=f"Tool execution error: {e!s}",
                error_code="TOOL_EXECUTION_ERROR",
            ).to_dict()

    def _execute_list_snapshots(self, arguments: dict[str, Any]) -> dict[str, Any]:
        """Execute list_snapshots tool."""
        limit = arguments.get("limit", 20) or 20
        if not isinstance(limit, int) or limit < 1:
            return OperationResult.fail(
                error="limit must be a positive integer",
                error_code="LIST_SNAPSHOTS/INVALID_LIMIT",
            ).to_dict()

        result = list_snapshots(limit=limit, git_adapter=self._git)

        if result.is_success and result.data:
            commits = [
                {
                    "sha": c.sha,
                    "message": c.message,
                    "author": c.author,
                    "date": c.date.isoformat(),
                }
                for c in result.data
            ]
            return OperationResult.ok(
                data={"count": len(commits), "snapshots": commits}
            ).to_dict()
        return result.to_dict()

    def _execute_view_diff(self, arguments: dict[str, Any]) -> dict[str, Any]:
        """Execute view_diff tool."""
        from_ref = arguments.get("from_ref")
        to_ref = arguments.get("to_ref")

        if not from_ref:
            return OperationResult.fail(
                error="Missing required parameter: from_ref",
                error_code="VIEW_DIFF/MISSING_FROM_REF",
            ).to_dict()
        if not to_ref:
            return OperationResult.fail(
                error="Missing required parameter: to_ref",
                error_code="VIEW_DIFF/MISSING_TO_REF",
            ).to_dict()

        result = view_diff(
            from_ref=str(from_ref), to_ref=str(to_ref), git_adapter=self._git
        )

        if result.is_success:
            return OperationResult.ok(
                data={"from_ref": from_ref, "to_ref": to_ref, "diff": result.data}
            ).to_dict()
        return result.to_dict()

    def _execute_restore_snapshot(self, arguments: dict[str, Any]) -> dict[str, Any]:
        """Execute restore_snapshot tool (DESTRUCTIVE)."""
        ref = arguments.get("ref")
        if not ref:
            return OperationResult.fail(
                error="Missing required parameter: ref",
                error_code="RESTORE_SNAPSHOT/MISSING_REF",
                suggestions=(
                    "Provide ref (commit SHA or HEAD~N)",
                    "Use list_snapshots to find valid refs",
                ),
            ).to_dict()

        if self._state.project is None:
            return OperationResult.fail(
                error="No project open",
                error_code="RESTORE_SNAPSHOT/NO_PROJECT",
            ).to_dict()

        command = RestoreSnapshotCommand(
            project_path=str(self._state.project.path), ref=str(ref)
        )
        result = restore_snapshot(
            command=command,
            diffable_adapter=self._diffable,
            git_adapter=self._git,
            event_bus=self._event_bus,
        )
        return result.to_dict()

    def _execute_initialize_version_control(
        self, _arguments: dict[str, Any]
    ) -> dict[str, Any]:
        """Execute initialize_version_control tool."""
        if self._state.project is None:
            return OperationResult.fail(
                error="No project open",
                error_code="INITIALIZE_VERSION_CONTROL/NO_PROJECT",
            ).to_dict()

        command = InitializeVersionControlCommand(
            project_path=str(self._state.project.path)
        )
        result = initialize_version_control(
            command=command,
            diffable_adapter=self._diffable,
            git_adapter=self._git,
            event_bus=self._event_bus,
        )
        return result.to_dict()
