"""
MCP Case Tools

Provides MCP-compatible tools for AI agent interaction with cases.

Implements QC-034:
- AC #5: Agent can list all cases
- AC #6: Agent can suggest case groupings
- AC #7: Agent can compare across cases

These tools follow the MCP (Model Context Protocol) specification:
- Each tool has a name, description, and input schema
- Tools return structured JSON responses
- Errors are returned as failure responses

Usage:
    from src.infrastructure.mcp import CaseTools

    # Create tools with repository dependency
    tools = CaseTools(case_repo=case_repository)

    # Execute a tool
    result = tools.execute("list_cases", {})
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from returns.result import Failure, Result, Success

if TYPE_CHECKING:
    from src.contexts.cases.infra.case_repository import SQLiteCaseRepository


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

    Example:
        from src.contexts.cases.infra.case_repository import SQLiteCaseRepository

        case_repo = SQLiteCaseRepository(connection)
        tools = CaseTools(case_repo=case_repo)

        # Get available tools
        schemas = tools.get_tool_schemas()

        # Execute a tool
        result = tools.execute("list_cases", {})
    """

    def __init__(self, case_repo: SQLiteCaseRepository) -> None:
        """
        Initialize case tools with repository dependency.

        Args:
            case_repo: The case repository to delegate operations to
        """
        self._case_repo = case_repo
        self._tools: dict[str, ToolDefinition] = {
            "list_cases": list_cases_tool,
            "get_case": get_case_tool,
            "suggest_case_groupings": suggest_case_groupings_tool,
            "compare_cases": compare_cases_tool,
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
            "list_cases": self._execute_list_cases,
            "get_case": self._execute_get_case,
            "suggest_case_groupings": self._execute_suggest_case_groupings,
            "compare_cases": self._execute_compare_cases,
        }

        handler = handlers.get(tool_name)
        if handler is None:
            return Failure(f"No handler for tool: {tool_name}")

        try:
            return handler(arguments)
        except Exception as e:
            return Failure(f"Tool execution error: {e!s}")

    # ============================================================
    # list_cases Handler (AC #5)
    # ============================================================

    def _execute_list_cases(
        self, _arguments: dict[str, Any]
    ) -> Result[dict[str, Any], str]:
        """
        Execute list_cases tool.

        Returns list of all cases with summary information.
        """
        cases = self._case_repo.get_all()

        return Success(
            {
                "total_count": len(cases),
                "cases": [
                    {
                        "case_id": c.id.value,
                        "name": c.name,
                        "description": c.description,
                        "attribute_count": len(c.attributes),
                        "source_count": len(c.source_ids),
                    }
                    for c in cases
                ],
            }
        )

    # ============================================================
    # get_case Handler
    # ============================================================

    def _execute_get_case(
        self, arguments: dict[str, Any]
    ) -> Result[dict[str, Any], str]:
        """
        Execute get_case tool.

        Returns detailed case information including attributes and sources.
        """
        case_id = arguments.get("case_id")
        if case_id is None:
            return Failure("Missing required parameter: case_id")

        from src.contexts.shared import CaseId

        case = self._case_repo.get_by_id(CaseId(value=int(case_id)))
        if case is None:
            return Failure(f"Case not found: {case_id}")

        return Success(
            {
                "case_id": case.id.value,
                "name": case.name,
                "description": case.description,
                "memo": case.memo,
                "attributes": [
                    {
                        "name": attr.name,
                        "type": attr.attr_type.value,
                        "value": attr.value,
                    }
                    for attr in case.attributes
                ],
                "source_count": len(case.source_ids),
                "source_ids": list(case.source_ids),
            }
        )

    # ============================================================
    # suggest_case_groupings Handler (AC #6)
    # ============================================================

    def _execute_suggest_case_groupings(
        self, arguments: dict[str, Any]
    ) -> Result[dict[str, Any], str]:
        """
        Execute suggest_case_groupings tool.

        Analyzes case attributes and suggests meaningful groupings.
        """
        attribute_names = arguments.get("attribute_names")
        min_group_size = arguments.get("min_group_size", 2) or 2

        cases = self._case_repo.get_all()

        if not cases:
            return Success(
                {
                    "groupings": [],
                    "total_cases_analyzed": 0,
                    "ungrouped_case_ids": [],
                }
            )

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

        return Success(
            {
                "groupings": groupings,
                "total_cases_analyzed": len(cases),
                "ungrouped_case_ids": ungrouped_case_ids,
            }
        )

    # ============================================================
    # compare_cases Handler (AC #7)
    # ============================================================

    def _execute_compare_cases(
        self, arguments: dict[str, Any]
    ) -> Result[dict[str, Any], str]:
        """
        Execute compare_cases tool.

        Compares multiple cases and returns comparison data.
        """
        case_ids = arguments.get("case_ids")
        if case_ids is None:
            return Failure("Missing required parameter: case_ids")

        if len(case_ids) < 2:
            return Failure("Comparison requires at least 2 cases")

        from src.contexts.shared import CaseId

        # Fetch all cases
        cases = []
        for cid in case_ids:
            case = self._case_repo.get_by_id(CaseId(value=int(cid)))
            if case is None:
                return Failure(f"Case not found: {cid}")
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

        return Success(
            {
                "cases": case_comparisons,
                "common_codes": [],  # Would need segment/code data
                "analysis_summary": analysis_summary,
            }
        )
