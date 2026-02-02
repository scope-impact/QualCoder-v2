"""
Agent Context: Coding Tools Schema

Defines the CONTRACT for AI-accessible coding operations.
Used by MCP Server, REST API, and other protocol adapters.
"""

from dataclasses import dataclass

from src.contexts.shared.core import TrustLevel

# ============================================================
# Tool Input Schemas
# ============================================================


@dataclass(frozen=True)
class CreateCodeInput:
    """Input for create_code tool"""

    name: str  # Required: unique code name
    color: str | None = None  # Hex color (e.g., "#FF6B6B")
    memo: str | None = None  # Description of what the code represents
    category_id: int | None = None  # Parent category ID


@dataclass(frozen=True)
class RenameCodeInput:
    """Input for rename_code tool"""

    code_id: int
    new_name: str


@dataclass(frozen=True)
class DeleteCodeInput:
    """Input for delete_code tool"""

    code_id: int


@dataclass(frozen=True)
class MergeCodesInput:
    """Input for merge_codes tool"""

    source_code_id: int  # Code to merge from (will be deleted)
    target_code_id: int  # Code to merge into (will receive segments)


@dataclass(frozen=True)
class ApplyCodeInput:
    """Input for apply_code tool"""

    code_id: int
    source_id: int
    start_position: int
    end_position: int
    memo: str | None = None
    importance: int = 0  # 0-2


@dataclass(frozen=True)
class RemoveCodeInput:
    """Input for remove_code tool"""

    segment_id: int


@dataclass(frozen=True)
class CreateCategoryInput:
    """Input for create_category tool"""

    name: str
    parent_id: int | None = None
    memo: str | None = None


@dataclass(frozen=True)
class MoveCategoryInput:
    """Input for move_code tool"""

    code_id: int
    category_id: int | None  # None to move to root


# ============================================================
# Tool Output Schemas
# ============================================================


@dataclass(frozen=True)
class CreateCodeOutput:
    """Output from create_code tool"""

    code_id: int
    name: str
    color: str


@dataclass(frozen=True)
class ApplyCodeOutput:
    """Output from apply_code tool"""

    segment_id: int
    code_id: int
    source_id: int
    start: int
    end: int
    text: str


@dataclass(frozen=True)
class MergeCodesOutput:
    """Output from merge_codes tool"""

    target_code_id: int
    segments_moved: int


# ============================================================
# Tool Definitions (MCP-compatible)
# ============================================================

CODING_TOOLS = [
    {
        "name": "create_code",
        "description": "Create a new code in the project codebook. Use this to define a new theme, concept, or category for coding qualitative data.",
        "trust_level": TrustLevel.SUGGEST,
        "input_schema": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Name of the code (must be unique)",
                    "minLength": 1,
                    "maxLength": 100,
                },
                "color": {
                    "type": "string",
                    "description": "Hex color for the code (e.g., '#FF6B6B')",
                    "pattern": "^#[0-9A-Fa-f]{6}$",
                },
                "memo": {
                    "type": "string",
                    "description": "Description or definition of what this code represents",
                },
                "category_id": {
                    "type": "integer",
                    "description": "ID of parent category (optional)",
                },
            },
            "required": ["name"],
        },
    },
    {
        "name": "rename_code",
        "description": "Rename an existing code in the codebook.",
        "trust_level": TrustLevel.SUGGEST,
        "input_schema": {
            "type": "object",
            "properties": {
                "code_id": {
                    "type": "integer",
                    "description": "ID of the code to rename",
                },
                "new_name": {
                    "type": "string",
                    "description": "New name for the code",
                    "minLength": 1,
                    "maxLength": 100,
                },
            },
            "required": ["code_id", "new_name"],
        },
    },
    {
        "name": "delete_code",
        "description": "Delete a code from the codebook. This will also remove all segments coded with this code.",
        "trust_level": TrustLevel.REQUIRE,
        "input_schema": {
            "type": "object",
            "properties": {
                "code_id": {
                    "type": "integer",
                    "description": "ID of the code to delete",
                }
            },
            "required": ["code_id"],
        },
    },
    {
        "name": "merge_codes",
        "description": "Merge one code into another. All segments from the source code will be reassigned to the target code, then the source code will be deleted.",
        "trust_level": TrustLevel.REQUIRE,
        "input_schema": {
            "type": "object",
            "properties": {
                "source_code_id": {
                    "type": "integer",
                    "description": "ID of the code to merge from (will be deleted)",
                },
                "target_code_id": {
                    "type": "integer",
                    "description": "ID of the code to merge into",
                },
            },
            "required": ["source_code_id", "target_code_id"],
        },
    },
    {
        "name": "apply_code",
        "description": "Apply an existing code to a segment of text in a source document. This creates a coded segment that associates the selected text with the code's meaning.",
        "trust_level": TrustLevel.NOTIFY,
        "input_schema": {
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
                    "description": "Character position where the segment starts",
                    "minimum": 0,
                },
                "end_position": {
                    "type": "integer",
                    "description": "Character position where the segment ends",
                    "minimum": 0,
                },
                "memo": {
                    "type": "string",
                    "description": "Optional note about why this code was applied here",
                },
                "importance": {
                    "type": "integer",
                    "description": "Importance level (0=normal, 1=important, 2=very important)",
                    "minimum": 0,
                    "maximum": 2,
                    "default": 0,
                },
            },
            "required": ["code_id", "source_id", "start_position", "end_position"],
        },
    },
    {
        "name": "remove_code",
        "description": "Remove a code from a segment (uncode the segment).",
        "trust_level": TrustLevel.NOTIFY,
        "input_schema": {
            "type": "object",
            "properties": {
                "segment_id": {
                    "type": "integer",
                    "description": "ID of the segment to uncode",
                }
            },
            "required": ["segment_id"],
        },
    },
    {
        "name": "create_category",
        "description": "Create a new category for organizing codes.",
        "trust_level": TrustLevel.SUGGEST,
        "input_schema": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Name of the category",
                    "minLength": 1,
                    "maxLength": 100,
                },
                "parent_id": {
                    "type": "integer",
                    "description": "ID of parent category (optional, for nested categories)",
                },
                "memo": {
                    "type": "string",
                    "description": "Description of the category",
                },
            },
            "required": ["name"],
        },
    },
    {
        "name": "move_code",
        "description": "Move a code to a different category.",
        "trust_level": TrustLevel.NOTIFY,
        "input_schema": {
            "type": "object",
            "properties": {
                "code_id": {"type": "integer", "description": "ID of the code to move"},
                "category_id": {
                    "type": "integer",
                    "description": "ID of the target category (null for root level)",
                },
            },
            "required": ["code_id"],
        },
    },
]


# ============================================================
# Resource Definitions
# ============================================================

CODING_RESOURCES = [
    {
        "uri_template": "qualcoder://codes",
        "name": "All Codes",
        "description": "List of all codes in the project codebook",
        "mime_type": "application/json",
    },
    {
        "uri_template": "qualcoder://codes/{code_id}",
        "name": "Code Details",
        "description": "Detailed information about a specific code",
        "mime_type": "application/json",
    },
    {
        "uri_template": "qualcoder://codes/{code_id}/segments",
        "name": "Code Segments",
        "description": "All segments coded with a specific code",
        "mime_type": "application/json",
    },
    {
        "uri_template": "qualcoder://categories",
        "name": "All Categories",
        "description": "Hierarchical list of all code categories",
        "mime_type": "application/json",
    },
    {
        "uri_template": "qualcoder://segments",
        "name": "All Segments",
        "description": "List of all coded segments (supports filtering)",
        "mime_type": "application/json",
    },
]
