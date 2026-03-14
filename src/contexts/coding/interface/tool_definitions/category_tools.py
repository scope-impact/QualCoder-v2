"""Category and Code Management MCP Tool Definitions."""

from .base import ToolDefinition, ToolParameter

CATEGORY_TOOLS = (
    ToolDefinition(
        name="rename_code",
        description=(
            "Rename an existing code in the codebook. "
            "Returns the old and new name for confirmation."
        ),
        parameters=(
            ToolParameter(
                name="code_id",
                type="string",
                description="ID of the code to rename.",
                required=True,
            ),
            ToolParameter(
                name="new_name",
                type="string",
                description="New name for the code.",
                required=True,
            ),
        ),
    ),
    ToolDefinition(
        name="update_code_memo",
        description=(
            "Update or set a code's memo (description/definition). "
            "Use for codebook definitions, inclusion/exclusion criteria, "
            "or analytical notes. Omit the memo parameter to clear it."
        ),
        parameters=(
            ToolParameter(
                name="code_id",
                type="string",
                description="ID of the code to update.",
                required=True,
            ),
            ToolParameter(
                name="memo",
                type="string",
                description="New memo text for the code. Omit to clear.",
                required=False,
            ),
        ),
    ),
    ToolDefinition(
        name="create_category",
        description=(
            "Create a new category for organizing codes into themes. "
            "Categories form a hierarchy via parent_id. "
            "Use for Phase 3 (Searching for Themes) in thematic analysis."
        ),
        parameters=(
            ToolParameter(
                name="name",
                type="string",
                description="Name of the new category.",
                required=True,
            ),
            ToolParameter(
                name="parent_id",
                type="string",
                description="Optional parent category ID for nested hierarchy.",
                required=False,
            ),
            ToolParameter(
                name="memo",
                type="string",
                description="Optional description/memo for the category.",
                required=False,
            ),
        ),
    ),
    ToolDefinition(
        name="move_code_to_category",
        description=(
            "Move a code into a category (or uncategorize it). "
            "Omit category_id to remove from current category. "
            "Use for organizing codes under themes."
        ),
        parameters=(
            ToolParameter(
                name="code_id",
                type="string",
                description="ID of the code to move.",
                required=True,
            ),
            ToolParameter(
                name="category_id",
                type="string",
                description="ID of target category. Omit to uncategorize.",
                required=False,
            ),
        ),
    ),
    ToolDefinition(
        name="merge_codes",
        description=(
            "Merge source code into target code. All segments from the source "
            "are reassigned to the target, and the source code is deleted. "
            "Use for Phase 4 (Reviewing Themes) to consolidate overlapping codes."
        ),
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
                description="ID of the code to merge INTO (will receive segments).",
                required=True,
            ),
        ),
    ),
    ToolDefinition(
        name="delete_code",
        description=(
            "Delete a code from the codebook. Optionally deletes all "
            "associated segments. Use for Phase 4 to remove irrelevant codes."
        ),
        parameters=(
            ToolParameter(
                name="code_id",
                type="string",
                description="ID of the code to delete.",
                required=True,
            ),
            ToolParameter(
                name="delete_segments",
                type="boolean",
                description="If true, also delete all segments for this code. Default: false.",
                required=False,
            ),
        ),
    ),
    ToolDefinition(
        name="list_categories",
        description=(
            "List all categories with hierarchy information and code counts. "
            "Returns category IDs, names, parent relationships, and "
            "the number of codes in each category."
        ),
        parameters=(),
    ),
)
