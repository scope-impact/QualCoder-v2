"""
QC-029.08: Suggest Codes for Text Tool Definitions

Tools for auto-suggesting codes for uncoded text.
"""

from .base import ToolDefinition, ToolParameter

analyze_uncoded_text_tool = ToolDefinition(
    name="analyze_uncoded_text",
    description=(
        "Analyze a source to find uncoded text ranges."
    ),
    parameters=(
        ToolParameter(
            name="source_id",
            type="integer",
            description="ID of the source to analyze.",
            required=True,
        ),
    ),
)

suggest_codes_for_range_tool = ToolDefinition(
    name="suggest_codes_for_range",
    description=(
        "Suggest which existing codes fit a text range. "
        "Returns ranked suggestions with confidence scores."
    ),
    parameters=(
        ToolParameter(
            name="source_id",
            type="integer",
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
)

auto_suggest_codes_tool = ToolDefinition(
    name="auto_suggest_codes",
    description=(
        "Auto-suggest codes for all uncoded portions of a source. "
        "Returns a batch of suggestions for review."
    ),
    parameters=(
        ToolParameter(
            name="source_id",
            type="integer",
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
)

get_suggestion_batch_status_tool = ToolDefinition(
    name="get_suggestion_batch_status",
    description=(
        "Get status of a coding suggestion batch."
    ),
    parameters=(
        ToolParameter(
            name="batch_id",
            type="string",
            description="ID of the batch to check.",
            required=True,
        ),
    ),
)

respond_to_code_suggestion_tool = ToolDefinition(
    name="respond_to_code_suggestion",
    description=(
        "Respond to a batch of code suggestions (accept/reject)."
    ),
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
            items={"type": "integer"},
        ),
        ToolParameter(
            name="reason",
            type="string",
            description="Reason for rejection.",
            required=False,
        ),
    ),
)

approve_batch_coding_tool = ToolDefinition(
    name="approve_batch_coding",
    description=(
        "Approve an entire batch of coding suggestions."
    ),
    parameters=(
        ToolParameter(
            name="batch_id",
            type="string",
            description="ID of the batch to approve.",
            required=True,
        ),
    ),
)


# Export all auto-coding tools
AUTO_CODING_TOOLS = {
    "analyze_uncoded_text": analyze_uncoded_text_tool,
    "suggest_codes_for_range": suggest_codes_for_range_tool,
    "auto_suggest_codes": auto_suggest_codes_tool,
    "get_suggestion_batch_status": get_suggestion_batch_status_tool,
    "respond_to_code_suggestion": respond_to_code_suggestion_tool,
    "approve_batch_coding": approve_batch_coding_tool,
}
