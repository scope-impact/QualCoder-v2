"""QC-028.07: AI-assisted code suggestion tool definitions."""

from .base import ToolDefinition, ToolParameter

SUGGEST_CODE_TOOLS = (
    ToolDefinition(
        name="analyze_content_for_codes",
        description=(
            "Analyze uncoded content in a source to identify patterns and themes. "
            "Returns information about uncoded segments that may need new codes."
        ),
        parameters=(
            ToolParameter(
                name="source_id",
                type="integer",
                description="ID of the source to analyze.",
                required=True,
            ),
        ),
    ),
    ToolDefinition(
        name="suggest_new_code",
        description=(
            "Suggest a new code based on analysis of uncoded content. "
            "The suggestion requires researcher approval before creation."
        ),
        parameters=(
            ToolParameter(
                name="name",
                type="string",
                description="Suggested name for the new code.",
                required=True,
            ),
            ToolParameter(
                name="rationale",
                type="string",
                description="Explanation of why this code is needed.",
                required=True,
            ),
            ToolParameter(
                name="color",
                type="string",
                description="Hex color for the code (e.g., '#FF5722').",
                required=False,
                default="#808080",
            ),
            ToolParameter(
                name="description",
                type="string",
                description="Description/memo for the code.",
                required=False,
            ),
            ToolParameter(
                name="confidence",
                type="integer",
                description="Confidence level 0-100 in this suggestion.",
                required=False,
                default=70,
            ),
            ToolParameter(
                name="sample_contexts",
                type="array",
                description="Sample text excerpts supporting this suggestion.",
                required=False,
                items={"type": "string"},
            ),
        ),
    ),
    ToolDefinition(
        name="list_pending_suggestions",
        description="List all pending code suggestions awaiting researcher approval.",
        parameters=(),
    ),
    ToolDefinition(
        name="approve_suggestion",
        description="Approve a pending code suggestion, creating the code.",
        parameters=(
            ToolParameter(
                name="suggestion_id",
                type="string",
                description="ID of the suggestion to approve.",
                required=True,
            ),
        ),
    ),
)
