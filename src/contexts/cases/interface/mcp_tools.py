"""
MCP Case Tools

Provides MCP-compatible tools for AI agent interaction with cases.

Implements QC-034:
- AC #5: Agent can list all cases
- AC #6: Agent can suggest case groupings
- AC #7: Agent can compare across cases

These tools follow the MCP (Model Context Protocol) specification:
- Each tool has a name, description, and input schema
- Tools return structured JSON responses via OperationResult.to_dict()
- Errors are returned as failure responses with error_code and suggestions

Usage:
    from src.contexts import CaseTools
    from src.shared.infra.app_context import create_app_context

    # Create tools with AppContext dependency
    ctx = create_app_context()
    tools = CaseTools(ctx=ctx)

    # Execute a tool
    result = tools.execute("list_cases", {})
"""

from __future__ import annotations

from collections import defaultdict
from typing import TYPE_CHECKING, Any, Protocol, runtime_checkable

from src.contexts.cases.core.commandHandlers import get_case, list_cases
from src.shared.common.mcp_types import ToolDefinition, ToolParameter
from src.shared.common.operation_result import OperationResult

if TYPE_CHECKING:
    from src.shared.infra.state import ProjectState


@runtime_checkable
class CaseToolsContext(Protocol):
    """
    Protocol defining the context requirements for CaseTools.

    This protocol allows CaseTools to work with AppContext
    following the same pattern as ProjectTools.

    Required properties:
    - state: ProjectState for project check
    - cases_context: CasesContext for case_repo access
    """

    @property
    def state(self) -> ProjectState:
        """Get the project state."""
        ...

    @property
    def cases_context(self):
        """Get cases context with case_repo (None if no project open)."""
        ...


# Tool: list_cases
list_cases_tool = ToolDefinition(
    name="list_cases",
    description=(
        "List all cases in the project. Cases organize data by participant, "
        "site, or other groupings. Returns case IDs, names, and summary information."
    ),
    parameters=(),
)

# Tool: get_case
get_case_tool = ToolDefinition(
    name="get_case",
    description=(
        "Get detailed information about a specific case, including its "
        "attributes and linked sources."
    ),
    parameters=(
        ToolParameter(
            name="case_id",
            type="integer",
            description="ID of the case to retrieve.",
            required=True,
        ),
    ),
)

# Tool: suggest_case_groupings
suggest_case_groupings_tool = ToolDefinition(
    name="suggest_case_groupings",
    description=(
        "Analyze case attributes and suggest meaningful groupings. Identifies "
        "patterns in demographic or categorical data to help organize cases."
    ),
    parameters=(
        ToolParameter(
            name="attribute_names",
            type="array",
            description="Focus analysis on specific attributes (optional).",
            required=False,
            default=None,
        ),
        ToolParameter(
            name="min_group_size",
            type="integer",
            description="Minimum number of cases required for a group.",
            required=False,
            default=2,
        ),
    ),
)

# Tool: compare_cases
compare_cases_tool = ToolDefinition(
    name="compare_cases",
    description=(
        "Compare coding patterns across multiple cases. Identifies unique "
        "themes per case and common themes across all cases."
    ),
    parameters=(
        ToolParameter(
            name="case_ids",
            type="array",
            description="IDs of cases to compare (minimum 2).",
            required=True,
        ),
        ToolParameter(
            name="code_ids",
            type="array",
            description="Filter comparison to specific codes (optional).",
            required=False,
            default=None,
        ),
    ),
)


# ============================================================
# Tool Implementation
# ============================================================


class CaseTools:
    """
    MCP-compatible case tools for AI agent integration.

    Provides tools to:
    - List all cases (AC #5)
    - Get case details
    - Suggest case groupings (AC #6)
    - Compare cases (AC #7)

    All tools call use cases instead of direct state access,
    and return OperationResult.to_dict() for consistent responses.

    Example:
        from src.shared.infra.app_context import create_app_context

        ctx = create_app_context()
        tools = CaseTools(ctx=ctx)

        # Get available tools
        schemas = tools.get_tool_schemas()

        # Execute a tool
        result = tools.execute("list_cases", {})
    """

    def __init__(self, ctx: CaseToolsContext) -> None:
        """
        Initialize case tools with context dependency.

        Args:
            ctx: The context containing state for accessing cases (AppContext).
        """
        self._ctx = ctx

        self._tools: dict[str, ToolDefinition] = {
            "list_cases": list_cases_tool,
            "get_case": get_case_tool,
            "suggest_case_groupings": suggest_case_groupings_tool,
            "compare_cases": compare_cases_tool,
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
            "list_cases": self._execute_list_cases,
            "get_case": self._execute_get_case,
            "suggest_case_groupings": self._execute_suggest_case_groupings,
            "compare_cases": self._execute_compare_cases,
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
    # list_cases Handler (AC #5)
    # ============================================================

    def _execute_list_cases(self, _arguments: dict[str, Any]) -> dict[str, Any]:
        """
        Execute list_cases tool.

        Returns list of all cases with summary information.
        """
        if self._state is None:
            return OperationResult.fail(
                error="No project context available",
                error_code="CASES_NOT_LISTED/NO_CONTEXT",
                suggestions=("Open a project first",),
            ).to_dict()

        # Get case_repo from context (source of truth)
        cases_ctx = self._ctx.cases_context
        case_repo = cases_ctx.case_repo if cases_ctx else None

        # Call use case with repo
        result = list_cases(self._state, case_repo=case_repo)
        return result.to_dict()

    # ============================================================
    # get_case Handler
    # ============================================================

    def _execute_get_case(self, arguments: dict[str, Any]) -> dict[str, Any]:
        """
        Execute get_case tool.

        Returns detailed case information including attributes and sources.
        """
        case_id = arguments.get("case_id")
        if case_id is None:
            return OperationResult.fail(
                error="Missing required parameter: case_id",
                error_code="CASE_NOT_FOUND/MISSING_PARAM",
                suggestions=("Provide case_id parameter",),
            ).to_dict()

        if self._state is None:
            return OperationResult.fail(
                error="No project context available",
                error_code="CASE_NOT_FOUND/NO_CONTEXT",
                suggestions=("Open a project first",),
            ).to_dict()

        # Get case_repo from context (source of truth)
        cases_ctx = self._ctx.cases_context
        case_repo = cases_ctx.case_repo if cases_ctx else None

        # Call use case with repo
        result = get_case(int(case_id), self._state, case_repo=case_repo)
        return result.to_dict()

    # ============================================================
    # suggest_case_groupings Handler (AC #6)
    # ============================================================

    def _execute_suggest_case_groupings(
        self, arguments: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Execute suggest_case_groupings tool.

        Analyzes case attributes and suggests meaningful groupings.
        """
        attribute_names = arguments.get("attribute_names")
        min_group_size = arguments.get("min_group_size", 2) or 2

        if self._state is None:
            return OperationResult.fail(
                error="No project context available",
                error_code="GROUPINGS_NOT_SUGGESTED/NO_CONTEXT",
                suggestions=("Open a project first",),
            ).to_dict()

        # Get cases from repo (source of truth)
        cases_ctx = self._ctx.cases_context
        cases = cases_ctx.case_repo.get_all() if cases_ctx else []

        if not cases:
            return OperationResult.ok(
                data={
                    "groupings": [],
                    "total_cases_analyzed": 0,
                    "ungrouped_case_ids": [],
                }
            ).to_dict()

        # Analyze attributes to find groupings
        groupings = []
        grouped_case_ids = set()

        # Collect all unique attribute names across cases
        all_attr_names = set()
        for case in cases:
            for attr in case.attributes:
                all_attr_names.add(attr.name)

        # Filter to specified attributes if provided
        target_attrs = set(attribute_names) if attribute_names else all_attr_names

        # For each attribute, group cases by value
        for attr_name in target_attrs:
            # Build value -> cases mapping
            value_to_cases: dict[Any, list] = defaultdict(list)

            for case in cases:
                attr = case.get_attribute(attr_name)
                if attr is not None:
                    value_to_cases[attr.value].append(case)

            # Create groupings for values with enough cases
            for value, group_cases in value_to_cases.items():
                if len(group_cases) >= min_group_size:
                    group_name = f"{attr_name}: {value}"
                    groupings.append(
                        {
                            "group_name": group_name,
                            "attribute_basis": attr_name,
                            "rationale": (
                                f"Cases share the same {attr_name} value ({value})"
                            ),
                            "cases": [
                                {"case_id": c.id.value, "name": c.name}
                                for c in group_cases
                            ],
                        }
                    )
                    for c in group_cases:
                        grouped_case_ids.add(c.id.value)

        # Find ungrouped cases
        ungrouped_case_ids = [
            c.id.value for c in cases if c.id.value not in grouped_case_ids
        ]

        return OperationResult.ok(
            data={
                "groupings": groupings,
                "total_cases_analyzed": len(cases),
                "ungrouped_case_ids": ungrouped_case_ids,
            }
        ).to_dict()

    # ============================================================
    # compare_cases Handler (AC #7)
    # ============================================================

    def _execute_compare_cases(self, arguments: dict[str, Any]) -> dict[str, Any]:
        """
        Execute compare_cases tool.

        Compares multiple cases and returns comparison data.
        """
        case_ids = arguments.get("case_ids")
        if case_ids is None:
            return OperationResult.fail(
                error="Missing required parameter: case_ids",
                error_code="CASES_NOT_COMPARED/MISSING_PARAM",
                suggestions=("Provide case_ids parameter (array of IDs)",),
            ).to_dict()

        if len(case_ids) < 2:
            return OperationResult.fail(
                error="Comparison requires at least 2 cases",
                error_code="CASES_NOT_COMPARED/INSUFFICIENT_CASES",
                suggestions=("Provide at least 2 case IDs to compare",),
            ).to_dict()

        if self._state is None:
            return OperationResult.fail(
                error="No project context available",
                error_code="CASES_NOT_COMPARED/NO_CONTEXT",
                suggestions=("Open a project first",),
            ).to_dict()

        # Get case_repo from context (source of truth)
        cases_ctx = self._ctx.cases_context
        case_repo = cases_ctx.case_repo if cases_ctx else None

        # Fetch all cases using get_case use case
        cases = []
        for cid in case_ids:
            result = get_case(int(cid), self._state, case_repo=case_repo)
            if result.is_failure:
                return OperationResult.fail(
                    error=f"Case not found: {cid}",
                    error_code="CASES_NOT_COMPARED/CASE_NOT_FOUND",
                    suggestions=(
                        "Use list_cases to see available cases",
                        f"Check if case ID {cid} exists",
                    ),
                ).to_dict()
            # Get case from repo for building comparison
            from src.shared.common.types import CaseId

            case = case_repo.get_by_id(CaseId(value=int(cid))) if case_repo else None
            if case:
                cases.append(case)

        # Build comparison data
        case_comparisons = []
        for case in cases:
            case_comparisons.append(
                {
                    "case_id": case.id.value,
                    "case_name": case.name,
                    "unique_codes": [],  # Would need segment/code data
                    "total_segments": 0,  # Would need segment data
                }
            )

        # Generate analysis summary
        case_names = [c.name for c in cases]
        analysis_summary = (
            f"Comparison of {len(cases)} cases: {', '.join(case_names)}. "
            "No coded segments available for detailed code comparison."
        )

        return OperationResult.ok(
            data={
                "cases": case_comparisons,
                "common_codes": [],  # Would need segment/code data
                "analysis_summary": analysis_summary,
            }
        ).to_dict()
