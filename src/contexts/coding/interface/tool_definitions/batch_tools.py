"""Batch operations tool definitions for multi-source coding."""

from .base import ToolDefinition, ToolParameter

BATCH_TOOLS = (
    ToolDefinition(
        name="find_similar_content",
        description="Find similar content across sources that matches a pattern.",
        parameters=(
            ToolParameter(
                name="search_text",
                type="string",
                description="Text pattern to search for.",
                required=True,
            ),
            ToolParameter(
                name="code_id",
                type="string",
                description="Optional code ID for context.",
                required=False,
            ),
        ),
    ),
    ToolDefinition(
        name="suggest_batch_coding",
        description="Suggest applying a code to multiple segments at once.",
        parameters=(
            ToolParameter(
                name="code_id",
                type="string",
                description="ID of the code to apply.",
                required=True,
            ),
            ToolParameter(
                name="segments",
                type="array",
                description="Array of segment definitions.",
                required=True,
                items={
                    "type": "object",
                    "properties": {
                        "source_id": {"type": "string"},
                        "start_pos": {"type": "integer"},
                        "end_pos": {"type": "integer"},
                    },
                    "required": ["source_id", "start_pos", "end_pos"],
                },
            ),
            ToolParameter(
                name="rationale",
                type="string",
                description="Explanation for the batch coding.",
                required=True,
            ),
        ),
    ),
)
