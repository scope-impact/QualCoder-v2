"""
MCP Coding Tools

Provides MCP-compatible tools for AI agent interaction with coding operations.

These tools follow the MCP (Model Context Protocol) specification:
- Each tool has a name, description, and input schema
- Tools return structured JSON responses via OperationResult.to_dict()
- Errors are returned as failure responses with error_code and suggestions

Key tools:
- batch_apply_codes: Apply multiple codes efficiently (AI-optimized)
- list_codes: Get all codes in the codebook
- get_code: Get details for a specific code
- apply_code: Apply a single code to a text segment
- list_segments_for_source: Get coded segments for a source

Usage:
    from src.contexts import CodingTools
    from src.shared.infra.app_context import create_app_context

    ctx = create_app_context()
    tools = CodingTools(ctx=ctx)

    # Execute batch apply (efficient for AI)
    result = tools.execute("batch_apply_codes", {
        "operations": [
            {"code_id": 1, "source_id": 1, "start_position": 0, "end_position": 50},
            {"code_id": 2, "source_id": 1, "start_position": 100, "end_position": 150},
        ]
    })
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Protocol, runtime_checkable

from src.contexts.coding.core.commandHandlers import (
    batch_apply_codes,
    get_all_codes,
    get_code,
    get_segments_for_source,
)
from src.contexts.coding.core.commandHandlers._state import (
    CategoryRepository,
    CodeRepository,
    SegmentRepository,
)
from src.contexts.coding.core.commands import ApplyCodeCommand, BatchApplyCodesCommand
from src.shared.common.operation_result import OperationResult

if TYPE_CHECKING:
    from src.shared.infra.event_bus import EventBus


@runtime_checkable
class CodingToolsContext(Protocol):
    """
    Protocol defining the context requirements for CodingTools.

    Required properties:
    - code_repo: CodeRepository for code operations
    - category_repo: CategoryRepository for category operations
    - segment_repo: SegmentRepository for segment operations
    - event_bus: EventBus for publishing events
    """

    @property
    def code_repo(self) -> CodeRepository:
        """Get the code repository."""
        ...

    @property
    def category_repo(self) -> CategoryRepository:
        """Get the category repository."""
        ...

    @property
    def segment_repo(self) -> SegmentRepository:
        """Get the segment repository."""
        ...

    @property
    def event_bus(self) -> EventBus:
        """Get the event bus."""
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
    items: dict[str, Any] | None = None  # For array types


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
            prop = {
                "type": param.type,
                "description": param.description,
            }
            if param.default is not None:
                prop["default"] = param.default
            if param.items is not None:
                prop["items"] = param.items
            if param.required:
                required.append(param.name)
            properties[param.name] = prop

        return {
            "name": self.name,
            "description": self.description,
            "inputSchema": {
                "type": "object",
                "properties": properties,
                "required": required,
            },
        }


# Tool: batch_apply_codes (AI-optimized)
batch_apply_codes_tool = ToolDefinition(
    name="batch_apply_codes",
    description=(
        "Apply multiple codes to multiple text segments in a single efficient batch. "
        "Designed for AI agents to reduce round-trips. Returns detailed results "
        "for each operation including success/failure status."
    ),
    parameters=(
        ToolParameter(
            name="operations",
            type="array",
            description=(
                "Array of code applications. Each operation requires: "
                "code_id (int), source_id (int), start_position (int), end_position (int). "
                "Optional: memo (string), importance (int 0-3)."
            ),
            required=True,
            items={
                "type": "object",
                "properties": {
                    "code_id": {
                        "type": "integer",
                        "description": "ID of the code to apply",
                    },
                    "source_id": {
                        "type": "integer",
                        "description": "ID of the source document",
                    },
                    "start_position": {
                        "type": "integer",
                        "description": "Start character position",
                    },
                    "end_position": {
                        "type": "integer",
                        "description": "End character position",
                    },
                    "memo": {
                        "type": "string",
                        "description": "Optional memo for the segment",
                    },
                    "importance": {
                        "type": "integer",
                        "description": "Importance level 0-3",
                    },
                },
                "required": ["code_id", "source_id", "start_position", "end_position"],
            },
        ),
    ),
)

# Tool: list_codes
list_codes_tool = ToolDefinition(
    name="list_codes",
    description=(
        "List all codes in the codebook. Returns code IDs, names, colors, "
        "memos, and segment counts for each code."
    ),
    parameters=(),
)

# Tool: get_code
get_code_tool = ToolDefinition(
    name="get_code",
    description=(
        "Get detailed information about a specific code including its "
        "name, color, memo, category, and usage statistics."
    ),
    parameters=(
        ToolParameter(
            name="code_id",
            type="integer",
            description="ID of the code to retrieve.",
            required=True,
        ),
    ),
)

# Tool: list_segments_for_source
list_segments_tool = ToolDefinition(
    name="list_segments_for_source",
    description=(
        "Get all coded segments for a specific source document. "
        "Returns segment positions, applied codes, and memos."
    ),
    parameters=(
        ToolParameter(
            name="source_id",
            type="integer",
            description="ID of the source to get segments for.",
            required=True,
        ),
    ),
)


# ============================================================
# Tool Implementation
# ============================================================


class CodingTools:
    """
    MCP-compatible coding tools for AI agent integration.

    Provides tools to:
    - Apply codes in batch (efficient for AI)
    - List codes and segments
    - Get code details

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
        self._ctx = ctx

        self._tools: dict[str, ToolDefinition] = {
            "batch_apply_codes": batch_apply_codes_tool,
            "list_codes": list_codes_tool,
            "get_code": get_code_tool,
            "list_segments_for_source": list_segments_tool,
        }

    @property
    def _code_repo(self) -> CodeRepository:
        """Get the code repository."""
        return self._ctx.code_repo

    @property
    def _category_repo(self) -> CategoryRepository:
        """Get the category repository."""
        return self._ctx.category_repo

    @property
    def _segment_repo(self) -> SegmentRepository:
        """Get the segment repository."""
        return self._ctx.segment_repo

    @property
    def _event_bus(self):
        """Get the event bus."""
        return self._ctx.event_bus

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
            "batch_apply_codes": self._execute_batch_apply_codes,
            "list_codes": self._execute_list_codes,
            "get_code": self._execute_get_code,
            "list_segments_for_source": self._execute_list_segments,
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
    # batch_apply_codes Handler (AI-optimized)
    # ============================================================

    def _execute_batch_apply_codes(self, arguments: dict[str, Any]) -> dict[str, Any]:
        """
        Execute batch_apply_codes tool.

        Applies multiple codes efficiently in a single batch operation.
        """
        operations_data = arguments.get("operations")
        if operations_data is None:
            return OperationResult.fail(
                error="Missing required parameter: operations",
                error_code="BATCH_APPLY_CODES/MISSING_PARAM",
                suggestions=("Provide operations array with code applications",),
            ).to_dict()

        if not operations_data:
            return OperationResult.fail(
                error="Empty operations array",
                error_code="BATCH_APPLY_CODES/EMPTY_BATCH",
                suggestions=("Provide at least one operation",),
            ).to_dict()

        if self._code_repo is None:
            return OperationResult.fail(
                error="No coding context available",
                error_code="BATCH_APPLY_CODES/NO_CONTEXT",
                suggestions=("Open a project first",),
            ).to_dict()

        # Convert operation dicts to ApplyCodeCommand objects
        operations = []
        for i, op in enumerate(operations_data):
            try:
                operations.append(
                    ApplyCodeCommand(
                        code_id=int(op["code_id"]),
                        source_id=int(op["source_id"]),
                        start_position=int(op["start_position"]),
                        end_position=int(op["end_position"]),
                        memo=op.get("memo"),
                        importance=int(op.get("importance", 0)),
                    )
                )
            except (KeyError, TypeError, ValueError) as e:
                return OperationResult.fail(
                    error=f"Invalid operation at index {i}: {e!s}",
                    error_code="BATCH_APPLY_CODES/INVALID_OPERATION",
                    suggestions=(
                        "Each operation requires: code_id, source_id, start_position, end_position",
                        f"Operation {i} is malformed",
                    ),
                ).to_dict()

        # Create batch command and execute
        command = BatchApplyCodesCommand(operations=tuple(operations))
        result = batch_apply_codes(
            command=command,
            code_repo=self._code_repo,
            category_repo=self._category_repo,
            segment_repo=self._segment_repo,
            event_bus=self._event_bus,
        )

        # Convert BatchApplyCodesResult to dict-friendly format
        if result.is_success and result.data:
            batch_result = result.data
            return OperationResult.ok(
                data={
                    "total": batch_result.total,
                    "succeeded": batch_result.succeeded,
                    "failed": batch_result.failed,
                    "all_succeeded": batch_result.all_succeeded,
                    "results": [
                        {
                            "index": r.index,
                            "success": r.success,
                            "segment_id": r.segment.id.value if r.segment else None,
                            "error": r.error,
                            "error_code": r.error_code,
                        }
                        for r in batch_result.results
                    ],
                }
            ).to_dict()

        return result.to_dict()

    # ============================================================
    # list_codes Handler
    # ============================================================

    def _execute_list_codes(self, _arguments: dict[str, Any]) -> dict[str, Any]:
        """
        Execute list_codes tool.

        Returns list of all codes with summary information.
        """
        if self._code_repo is None:
            return OperationResult.fail(
                error="No coding context available",
                error_code="CODES_NOT_LISTED/NO_CONTEXT",
                suggestions=("Open a project first",),
            ).to_dict()

        codes = get_all_codes(self._code_repo)
        return OperationResult.ok(data=codes).to_dict()

    # ============================================================
    # get_code Handler
    # ============================================================

    def _execute_get_code(self, arguments: dict[str, Any]) -> dict[str, Any]:
        """
        Execute get_code tool.

        Returns detailed code information.
        """
        code_id = arguments.get("code_id")
        if code_id is None:
            return OperationResult.fail(
                error="Missing required parameter: code_id",
                error_code="CODE_NOT_FOUND/MISSING_PARAM",
                suggestions=("Provide code_id parameter",),
            ).to_dict()

        if self._code_repo is None:
            return OperationResult.fail(
                error="No coding context available",
                error_code="CODE_NOT_FOUND/NO_CONTEXT",
                suggestions=("Open a project first",),
            ).to_dict()

        code = get_code(self._code_repo, int(code_id))
        if code is None:
            return OperationResult.fail(
                error=f"Code {code_id} not found",
                error_code="CODE_NOT_FOUND",
            ).to_dict()
        return OperationResult.ok(data=code).to_dict()

    # ============================================================
    # list_segments_for_source Handler
    # ============================================================

    def _execute_list_segments(self, arguments: dict[str, Any]) -> dict[str, Any]:
        """
        Execute list_segments_for_source tool.

        Returns all coded segments for a source document.
        """
        source_id = arguments.get("source_id")
        if source_id is None:
            return OperationResult.fail(
                error="Missing required parameter: source_id",
                error_code="SEGMENTS_NOT_LISTED/MISSING_PARAM",
                suggestions=("Provide source_id parameter",),
            ).to_dict()

        if self._segment_repo is None:
            return OperationResult.fail(
                error="No coding context available",
                error_code="SEGMENTS_NOT_LISTED/NO_CONTEXT",
                suggestions=("Open a project first",),
            ).to_dict()

        segments = get_segments_for_source(self._segment_repo, int(source_id))
        return OperationResult.ok(data=segments).to_dict()
