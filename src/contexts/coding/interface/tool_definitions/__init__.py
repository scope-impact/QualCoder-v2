"""MCP Tool Definitions organized by feature area."""

from .auto_coding_tools import AUTO_CODING_TOOLS
from .base import ToolDefinition, ToolParameter
from .batch_tools import BATCH_TOOLS
from .category_tools import CATEGORY_TOOLS
from .coding_suggestion_tools import CODING_SUGGESTION_TOOLS
from .core_tools import CORE_TOOLS
from .duplicate_tools import DUPLICATE_TOOLS
from .suggest_code_tools import SUGGEST_CODE_TOOLS


def _build_tool_dict(
    *tool_groups: tuple[ToolDefinition, ...],
) -> dict[str, ToolDefinition]:
    """Build a name-keyed dict from tuples of ToolDefinitions."""
    return {tool.name: tool for group in tool_groups for tool in group}


ALL_TOOLS: dict[str, ToolDefinition] = _build_tool_dict(
    CORE_TOOLS,
    SUGGEST_CODE_TOOLS,
    DUPLICATE_TOOLS,
    CODING_SUGGESTION_TOOLS,
    AUTO_CODING_TOOLS,
    BATCH_TOOLS,
    CATEGORY_TOOLS,
)

__all__ = [
    "ALL_TOOLS",
    "ToolDefinition",
    "ToolParameter",
]
