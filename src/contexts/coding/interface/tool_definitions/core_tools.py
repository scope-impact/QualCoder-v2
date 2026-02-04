"""
Core MCP Tool Definitions

Basic coding tools: batch_apply_codes, list_codes, get_code, list_segments_for_source.
"""

from .base import ToolDefinition, ToolParameter

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


# Export all core tools
CORE_TOOLS = {
    "batch_apply_codes": batch_apply_codes_tool,
    "list_codes": list_codes_tool,
    "get_code": get_code_tool,
    "list_segments_for_source": list_segments_tool,
}
