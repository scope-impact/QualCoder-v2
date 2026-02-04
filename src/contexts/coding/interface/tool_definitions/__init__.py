"""
MCP Tool Definitions

Organized by feature area for maintainability.
"""

from .base import ToolDefinition, ToolParameter
from .core_tools import CORE_TOOLS
from .suggest_code_tools import SUGGEST_CODE_TOOLS
from .duplicate_tools import DUPLICATE_TOOLS
from .coding_suggestion_tools import CODING_SUGGESTION_TOOLS
from .auto_coding_tools import AUTO_CODING_TOOLS
from .batch_tools import BATCH_TOOLS

# Combine all tool definitions
ALL_TOOLS: dict[str, ToolDefinition] = {
    **CORE_TOOLS,
    **SUGGEST_CODE_TOOLS,
    **DUPLICATE_TOOLS,
    **CODING_SUGGESTION_TOOLS,
    **AUTO_CODING_TOOLS,
    **BATCH_TOOLS,
}

__all__ = [
    "ToolDefinition",
    "ToolParameter",
    "ALL_TOOLS",
    "CORE_TOOLS",
    "SUGGEST_CODE_TOOLS",
    "DUPLICATE_TOOLS",
    "CODING_SUGGESTION_TOOLS",
    "AUTO_CODING_TOOLS",
    "BATCH_TOOLS",
]
