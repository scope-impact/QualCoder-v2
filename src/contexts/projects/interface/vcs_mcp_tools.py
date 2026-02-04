"""
MCP Version Control Tools

Provides MCP-compatible tools for AI agent interaction with version control.

Implements QC-047 Version Control:
- AC #7: Agent can list snapshots
- AC #8: Agent can view diffs
- AC #9: Agent can restore snapshots (destructive)
- AC #10: Agent can initialize version control

These tools follow the MCP (Model Context Protocol) specification:
- Each tool has a name, description, and input schema
- Tools return structured JSON responses via OperationResult.to_dict()
- Errors are returned as failure responses with error_code and suggestions

Key tools:
- list_snapshots: Get commit history
- view_diff: Compare two snapshots
- restore_snapshot: Restore to a previous snapshot (DESTRUCTIVE)
- initialize_version_control: Initialize VCS for a project

Usage:
    from src.contexts.projects.interface import VersionControlMCPTools

    tools = VersionControlMCPTools(
        diffable=diffable_adapter,
        git=git_adapter,
        event_bus=event_bus,
        state=project_state,
    )

    # Execute tool
    result = tools.execute("list_snapshots", {"limit": 10})
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Protocol, runtime_checkable

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


@runtime_checkable
class VersionControlContext(Protocol):
    """
    Protocol defining the context requirements for VersionControlMCPTools.

    Required properties:
    - diffable: SqliteDiffableAdapter for database-to-JSON conversion
    - git: GitRepositoryAdapter for Git operations
    - event_bus: EventBus for publishing domain events
    - state: ProjectState for current project information
    """

    @property
    def diffable(self) -> SqliteDiffableAdapter:
        """Get the SQLite diffable adapter."""
        ...

    @property
    def git(self) -> GitRepositoryAdapter:
        """Get the Git repository adapter."""
        ...

    @property
    def event_bus(self) -> EventBus:
        """Get the event bus."""
        ...

    @property
    def state(self) -> ProjectState:
        """Get the project state."""
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

        # Mark destructive tools for AI awareness
        if self.is_destructive:
            schema["annotations"] = {"destructive": True}

        return schema


# Tool: list_snapshots
list_snapshots_tool = ToolDefinition(
    name="list_snapshots",
    description=(
        "List version control snapshots (commit history) for the current project. "
        "Returns commit SHA, message, author, and date for each snapshot. "
        "Use this to see what changes have been made and find refs for restore."
    ),
    parameters=(
        ToolParameter(
            name="limit",
            type="integer",
            description="Maximum number of snapshots to return. Default 20.",
            required=False,
            default=20,
        ),
    ),
)

# Tool: view_diff
view_diff_tool = ToolDefinition(
    name="view_diff",
    description=(
        "View differences between two version control snapshots. "
        "Shows what changed in the project database between the two references. "
        "References can be commit SHAs or relative refs like HEAD~1."
    ),
    parameters=(
        ToolParameter(
            name="from_ref",
            type="string",
            description="Starting commit reference (SHA, HEAD~N, etc.).",
            required=True,
        ),
        ToolParameter(
            name="to_ref",
            type="string",
            description="Ending commit reference (SHA, HEAD, etc.).",
            required=True,
        ),
    ),
)

# Tool: restore_snapshot (DESTRUCTIVE)
restore_snapshot_tool = ToolDefinition(
    name="restore_snapshot",
    description=(
        "DESTRUCTIVE: Restore the project database to a previous snapshot. "
        "This will overwrite the current database with the snapshot at the given ref. "
        "Use list_snapshots to find valid refs. Cannot be undone without another restore."
    ),
    parameters=(
        ToolParameter(
            name="ref",
            type="string",
            description="Commit reference to restore (SHA or HEAD~N).",
            required=True,
        ),
    ),
    is_destructive=True,
)

# Tool: initialize_version_control
initialize_version_control_tool = ToolDefinition(
    name="initialize_version_control",
    description=(
        "Initialize version control for the current project. "
        "Creates a Git repository and takes an initial snapshot. "
        "Must be called before other version control tools can be used. "
        "Safe to call if already initialized (will succeed with no changes)."
    ),
    parameters=(),
)


# ============================================================
# Tool Implementation
# ============================================================


class VersionControlMCPTools:
    """
    MCP-compatible version control tools for AI agent integration.

    Provides tools to:
    - List version control snapshots (commit history)
    - View differences between snapshots
    - Restore to a previous snapshot (DESTRUCTIVE)
    - Initialize version control for a project

    All tools call the SAME command handlers as the ViewModel/UI,
    ensuring consistent behavior between human and AI interactions.

    Example:
        tools = VersionControlMCPTools(
            diffable=diffable_adapter,
            git=git_adapter,
            event_bus=event_bus,
            state=project_state,
        )

        # Get available tools
        schemas = tools.get_tool_schemas()

        # List snapshots
        result = tools.execute("list_snapshots", {"limit": 10})

        # View diff between commits
        result = tools.execute("view_diff", {
            "from_ref": "HEAD~1",
            "to_ref": "HEAD"
        })
    """

    def __init__(
        self,
        diffable: SqliteDiffableAdapter,
        git: GitRepositoryAdapter,
        event_bus: EventBus,
        state: ProjectState,
    ) -> None:
        """
        Initialize version control tools with dependencies.

        Args:
            diffable: Adapter for SQLite-to-JSON conversion
            git: Adapter for Git operations
            event_bus: Event bus for publishing domain events
            state: Project state with current project information
        """
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

        handlers = {
            "list_snapshots": self.execute_list_snapshots,
            "view_diff": self.execute_view_diff,
            "restore_snapshot": self.execute_restore_snapshot,
            "initialize_version_control": self.execute_initialize_version_control,
        }

        handler = handlers.get(tool_name)
        if handler is None:
            return OperationResult.fail(
                error=f"No handler for tool: {tool_name}",
                error_code="HANDLER_NOT_FOUND",
            ).to_dict()

        try:
            return handler(arguments)
        except Exception as e:
            return OperationResult.fail(
                error=f"Tool execution error: {e!s}",
                error_code="TOOL_EXECUTION_ERROR",
            ).to_dict()

    # ============================================================
    # list_snapshots Handler
    # ============================================================

    def execute_list_snapshots(self, arguments: dict[str, Any]) -> dict[str, Any]:
        """
        Execute list_snapshots tool.

        Lists version control snapshots (commit history).

        Args:
            arguments: May contain 'limit' (default 20)

        Returns:
            Dictionary with snapshots list on success
        """
        # Get limit with default
        limit = arguments.get("limit", 20) or 20

        # Validate limit
        if not isinstance(limit, int) or limit < 1:
            return OperationResult.fail(
                error="limit must be a positive integer",
                error_code="LIST_SNAPSHOTS/INVALID_LIMIT",
                suggestions=("Provide a positive integer for limit",),
            ).to_dict()

        # Call command handler
        result = list_snapshots(
            limit=limit,
            git_adapter=self._git,
        )

        # Convert CommitInfo objects to dicts for serialization
        if result.is_success and result.data:
            commits = [
                {
                    "sha": commit.sha,
                    "message": commit.message,
                    "author": commit.author,
                    "date": commit.date.isoformat(),
                }
                for commit in result.data
            ]
            return OperationResult.ok(
                data={
                    "count": len(commits),
                    "snapshots": commits,
                }
            ).to_dict()

        return result.to_dict()

    # ============================================================
    # view_diff Handler
    # ============================================================

    def execute_view_diff(self, arguments: dict[str, Any]) -> dict[str, Any]:
        """
        Execute view_diff tool.

        Shows differences between two version control snapshots.

        Args:
            arguments: Must contain 'from_ref' and 'to_ref'

        Returns:
            Dictionary with diff text on success
        """
        # Validate required parameters
        from_ref = arguments.get("from_ref")
        to_ref = arguments.get("to_ref")

        if not from_ref:
            return OperationResult.fail(
                error="Missing required parameter: from_ref",
                error_code="VIEW_DIFF/MISSING_FROM_REF",
                suggestions=("Provide from_ref (e.g., 'HEAD~1', commit SHA)",),
            ).to_dict()

        if not to_ref:
            return OperationResult.fail(
                error="Missing required parameter: to_ref",
                error_code="VIEW_DIFF/MISSING_TO_REF",
                suggestions=("Provide to_ref (e.g., 'HEAD', commit SHA)",),
            ).to_dict()

        # Call command handler
        result = view_diff(
            from_ref=str(from_ref),
            to_ref=str(to_ref),
            git_adapter=self._git,
        )

        # Wrap diff text in structured response
        if result.is_success:
            return OperationResult.ok(
                data={
                    "from_ref": from_ref,
                    "to_ref": to_ref,
                    "diff": result.data,
                }
            ).to_dict()

        return result.to_dict()

    # ============================================================
    # restore_snapshot Handler (DESTRUCTIVE)
    # ============================================================

    def execute_restore_snapshot(self, arguments: dict[str, Any]) -> dict[str, Any]:
        """
        Execute restore_snapshot tool.

        DESTRUCTIVE: Restores the database to a previous snapshot.

        Args:
            arguments: Must contain 'ref'

        Returns:
            Dictionary with restore result
        """
        # Validate required parameter
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

        # Check if project is open
        if self._state.project is None:
            return OperationResult.fail(
                error="No project open",
                error_code="RESTORE_SNAPSHOT/NO_PROJECT",
                suggestions=("Open a project first",),
            ).to_dict()

        # Create command
        command = RestoreSnapshotCommand(
            project_path=str(self._state.project.path),
            ref=str(ref),
        )

        # Call command handler
        result = restore_snapshot(
            command=command,
            diffable_adapter=self._diffable,
            git_adapter=self._git,
            event_bus=self._event_bus,
        )

        return result.to_dict()

    # ============================================================
    # initialize_version_control Handler
    # ============================================================

    def execute_initialize_version_control(
        self, _arguments: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Execute initialize_version_control tool.

        Initializes version control for the current project.

        Args:
            _arguments: No parameters required (unused)

        Returns:
            Dictionary with initialization result
        """
        # Check if project is open
        if self._state.project is None:
            return OperationResult.fail(
                error="No project open",
                error_code="INITIALIZE_VERSION_CONTROL/NO_PROJECT",
                suggestions=("Open a project first",),
            ).to_dict()

        # Create command
        command = InitializeVersionControlCommand(
            project_path=str(self._state.project.path),
        )

        # Call command handler
        result = initialize_version_control(
            command=command,
            diffable_adapter=self._diffable,
            git_adapter=self._git,
            event_bus=self._event_bus,
        )

        return result.to_dict()
