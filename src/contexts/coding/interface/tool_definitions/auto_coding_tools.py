"""QC-029.08: Auto-suggest codes for uncoded text tool definitions."""

from .base import ToolDefinition, ToolParameter

AUTO_CODING_TOOLS = (
    ToolDefinition(
        name="analyze_uncoded_text",
        description="Analyze a source to find uncoded text ranges.",
        parameters=(
            ToolParameter(
                name="source_id",
                type="string",
                description="ID of the source to analyze.",
                required=True,
            ),
        ),
    ),
    ToolDefinition(
        name="suggest_codes_for_range",
        description=(
            "Suggest which existing codes fit a text range. "
            "Returns ranked suggestions with confidence scores."
        ),
        parameters=(
            ToolParameter(
                name="source_id",
                type="string",
                description="ID of the source document.",
                required=True,
            ),
            ToolParameter(
                name="start_pos",
                type="integer",
                description="Start character position.",
                required=True,
            ),
            ToolParameter(
                name="end_pos",
                type="integer",
                description="End character position.",
                required=True,
            ),
        ),
    ),
    ToolDefinition(
        name="auto_suggest_codes",
        description=(
            "Auto-suggest codes for all uncoded portions of a source. "
            "Returns a batch of suggestions for review."
        ),
        parameters=(
            ToolParameter(
                name="source_id",
                type="string",
                description="ID of the source to analyze.",
                required=True,
            ),
            ToolParameter(
                name="min_confidence",
                type="integer",
                description="Minimum confidence threshold (0-100).",
                required=False,
                default=70,
            ),
        ),
    ),
    ToolDefinition(
        name="get_suggestion_batch_status",
        description="Get status of a coding suggestion batch.",
        parameters=(
            ToolParameter(
                name="batch_id",
                type="string",
                description="ID of the batch to check.",
                required=True,
            ),
        ),
    ),
    ToolDefinition(
        name="respond_to_code_suggestion",
        description="Respond to a batch of code suggestions (accept/reject).",
        parameters=(
            ToolParameter(
                name="suggestion_batch_id",
                type="string",
                description="ID of the suggestion batch.",
                required=True,
            ),
            ToolParameter(
                name="response",
                type="string",
                description="Response type: 'accept' or 'reject'.",
                required=True,
            ),
            ToolParameter(
                name="selected_code_ids",
                type="array",
                description="Code IDs to accept (for accept response).",
                required=False,
                items={"type": "string"},
            ),
            ToolParameter(
                name="reason",
                type="string",
                description="Reason for rejection.",
                required=False,
            ),
        ),
    ),
    ToolDefinition(
        name="approve_batch_coding",
        description="Approve an entire batch of coding suggestions.",
        parameters=(
            ToolParameter(
                name="batch_id",
                type="string",
                description="ID of the batch to approve.",
                required=True,
            ),
        ),
    ),
)
