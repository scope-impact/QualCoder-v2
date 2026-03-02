"""QC-028.08: Duplicate code detection and merging tool definitions."""

from .base import ToolDefinition, ToolParameter

DUPLICATE_TOOLS = (
    ToolDefinition(
        name="detect_duplicate_codes",
        description=(
            "Detect semantically similar codes that may be duplicates. "
            "Returns candidate pairs with similarity scores."
        ),
        parameters=(
            ToolParameter(
                name="threshold",
                type="number",
                description="Similarity threshold (0.0-1.0). Default 0.8.",
                required=False,
                default=0.8,
            ),
            ToolParameter(
                name="include_usage_analysis",
                type="boolean",
                description="Include analysis of how codes are used.",
                required=False,
                default=False,
            ),
        ),
    ),
    ToolDefinition(
        name="suggest_merge_codes",
        description="Suggest merging one code into another. Requires approval.",
        parameters=(
            ToolParameter(
                name="source_code_id",
                type="string",
                description="ID of the code to merge FROM (will be deleted).",
                required=True,
            ),
            ToolParameter(
                name="target_code_id",
                type="string",
                description="ID of the code to merge INTO (will be kept).",
                required=True,
            ),
            ToolParameter(
                name="rationale",
                type="string",
                description="Explanation of why these codes should be merged.",
                required=True,
            ),
        ),
    ),
    ToolDefinition(
        name="approve_merge",
        description="Approve a pending merge suggestion, executing the merge.",
        parameters=(
            ToolParameter(
                name="merge_suggestion_id",
                type="string",
                description="ID of the merge suggestion to approve.",
                required=True,
            ),
        ),
    ),
)
