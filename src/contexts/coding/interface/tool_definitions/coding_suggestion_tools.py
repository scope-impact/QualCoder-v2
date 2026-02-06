"""
QC-029.07: Apply Code to Text Range Tool Definitions

Tools for suggesting code applications to text ranges.
"""

from .base import ToolDefinition, ToolParameter

suggest_code_application_tool = ToolDefinition(
    name="suggest_code_application",
    description=(
        "Suggest applying an existing code to a text range. "
        "Requires researcher approval before the segment is created."
    ),
    parameters=(
        ToolParameter(
            name="source_id",
            type="integer",
            description="ID of the source document.",
            required=True,
        ),
        ToolParameter(
            name="code_id",
            type="integer",
            description="ID of the code to apply.",
            required=True,
        ),
        ToolParameter(
            name="start_pos",
            type="integer",
            description="Start character position in the source.",
            required=True,
        ),
        ToolParameter(
            name="end_pos",
            type="integer",
            description="End character position in the source.",
            required=True,
        ),
        ToolParameter(
            name="rationale",
            type="string",
            description="Explanation of why this code fits.",
            required=False,
            default="",
        ),
        ToolParameter(
            name="confidence",
            type="integer",
            description="Confidence level 0-100.",
            required=False,
            default=70,
        ),
        ToolParameter(
            name="include_text",
            type="boolean",
            description="Include text excerpt in response.",
            required=False,
            default=False,
        ),
    ),
)

list_pending_coding_suggestions_tool = ToolDefinition(
    name="list_pending_coding_suggestions",
    description=("List pending coding suggestions for a source."),
    parameters=(
        ToolParameter(
            name="source_id",
            type="integer",
            description="ID of the source (optional, all sources if omitted).",
            required=False,
        ),
    ),
)

approve_coding_suggestion_tool = ToolDefinition(
    name="approve_coding_suggestion",
    description=("Approve a coding suggestion, creating the segment."),
    parameters=(
        ToolParameter(
            name="suggestion_id",
            type="string",
            description="ID of the coding suggestion to approve.",
            required=True,
        ),
    ),
)

reject_coding_suggestion_tool = ToolDefinition(
    name="reject_coding_suggestion",
    description=("Reject a coding suggestion with optional feedback."),
    parameters=(
        ToolParameter(
            name="suggestion_id",
            type="string",
            description="ID of the coding suggestion to reject.",
            required=True,
        ),
        ToolParameter(
            name="reason",
            type="string",
            description="Reason for rejection.",
            required=False,
        ),
        ToolParameter(
            name="feedback",
            type="string",
            description="Feedback for the AI.",
            required=False,
        ),
    ),
)


# Export all coding suggestion tools
CODING_SUGGESTION_TOOLS = {
    "suggest_code_application": suggest_code_application_tool,
    "list_pending_coding_suggestions": list_pending_coding_suggestions_tool,
    "approve_coding_suggestion": approve_coding_suggestion_tool,
    "reject_coding_suggestion": reject_coding_suggestion_tool,
}
