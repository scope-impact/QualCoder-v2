"""
Agent Context: Cases Tools Schema

Defines the CONTRACT for AI-accessible case operations.
Used by MCP Server, REST API, and other protocol adapters.

Cases organize qualitative data by participant, site, or other groupings.
"""

from dataclasses import dataclass

from src.contexts.shared.core import TrustLevel

# ============================================================
# Tool Input Schemas
# ============================================================


@dataclass(frozen=True)
class CreateCaseInput:
    """Input for create_case tool"""

    name: str  # Required: case name (e.g., participant ID)
    description: str | None = None  # What this case represents
    memo: str | None = None  # Additional notes


@dataclass(frozen=True)
class UpdateCaseInput:
    """Input for update_case tool"""

    case_id: int
    name: str | None = None  # New name
    description: str | None = None  # New description
    memo: str | None = None  # New memo


@dataclass(frozen=True)
class DeleteCaseInput:
    """Input for delete_case tool"""

    case_id: int


@dataclass(frozen=True)
class LinkSourceToCaseInput:
    """Input for link_source_to_case tool"""

    case_id: int
    source_id: int


@dataclass(frozen=True)
class UnlinkSourceFromCaseInput:
    """Input for unlink_source_from_case tool"""

    case_id: int
    source_id: int


@dataclass(frozen=True)
class SetCaseAttributeInput:
    """Input for set_case_attribute tool"""

    case_id: int
    attr_name: str  # Attribute name (e.g., "age", "gender")
    attr_type: str  # One of: text, number, date, boolean
    attr_value: str | int | float | bool  # Value matching the type


@dataclass(frozen=True)
class SuggestCaseGroupingsInput:
    """Input for suggest_case_groupings tool"""

    attribute_names: list[str] | None = None  # Focus on specific attributes (optional)
    min_group_size: int = 2  # Minimum cases per group


@dataclass(frozen=True)
class CompareCasesInput:
    """Input for compare_cases tool"""

    case_ids: list[int]  # Cases to compare (at least 2)
    code_ids: list[int] | None = None  # Filter to specific codes (optional)


# ============================================================
# Tool Output Schemas
# ============================================================


@dataclass(frozen=True)
class CreateCaseOutput:
    """Output from create_case tool"""

    case_id: int
    name: str


@dataclass(frozen=True)
class CaseAttributeOutput:
    """Attribute in case data"""

    name: str
    type: str  # text, number, date, boolean
    value: str | int | float | bool


@dataclass(frozen=True)
class CaseWithSourcesOutput:
    """Output for get_case tool"""

    case_id: int
    name: str
    description: str | None
    memo: str | None
    attributes: list[CaseAttributeOutput]
    source_count: int
    source_ids: list[int]


@dataclass(frozen=True)
class CaseSummaryOutput:
    """Summary of a case for list_cases"""

    case_id: int
    name: str
    description: str | None
    attribute_count: int
    source_count: int


@dataclass(frozen=True)
class ListCasesOutput:
    """Output from list_cases tool"""

    cases: list[CaseSummaryOutput]
    total_count: int


@dataclass(frozen=True)
class CaseGroupMemberOutput:
    """A case within a suggested group"""

    case_id: int
    name: str


@dataclass(frozen=True)
class SuggestedGroupOutput:
    """A suggested case grouping"""

    group_name: str  # Suggested group name (e.g., "Age 25-34", "Urban Sites")
    attribute_basis: str  # Which attribute(s) this grouping is based on
    rationale: str  # Why this grouping is meaningful
    cases: list[CaseGroupMemberOutput]  # Cases in this group


@dataclass(frozen=True)
class SuggestCaseGroupingsOutput:
    """Output from suggest_case_groupings tool"""

    groupings: list[SuggestedGroupOutput]
    total_cases_analyzed: int
    ungrouped_case_ids: list[int]  # Cases that didn't fit any group


@dataclass(frozen=True)
class CaseCodeSummaryOutput:
    """Code summary for a case in comparison"""

    code_id: int
    code_name: str
    segment_count: int


@dataclass(frozen=True)
class CaseComparisonOutput:
    """Comparison data for a single case"""

    case_id: int
    case_name: str
    unique_codes: list[CaseCodeSummaryOutput]  # Codes only in this case
    total_segments: int


@dataclass(frozen=True)
class CompareCasesOutput:
    """Output from compare_cases tool"""

    cases: list[CaseComparisonOutput]  # Comparison data per case
    common_codes: list[CaseCodeSummaryOutput]  # Codes present in all cases
    analysis_summary: str  # Natural language summary of comparison


# ============================================================
# Tool Definitions (MCP-compatible)
# ============================================================

CASES_TOOLS = [
    {
        "name": "list_cases",
        "description": "List all cases in the project. Cases organize data by participant, site, or other groupings. Returns case IDs, names, and summary information.",
        "trust_level": TrustLevel.AUTONOMOUS,
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "get_case",
        "description": "Get detailed information about a specific case, including its attributes and linked sources.",
        "trust_level": TrustLevel.AUTONOMOUS,
        "input_schema": {
            "type": "object",
            "properties": {
                "case_id": {
                    "type": "integer",
                    "description": "ID of the case to retrieve",
                }
            },
            "required": ["case_id"],
        },
    },
    {
        "name": "create_case",
        "description": "Create a new case in the project. Cases represent research units like participants, sites, or organizations.",
        "trust_level": TrustLevel.SUGGEST,
        "input_schema": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Name or identifier for the case (e.g., 'P01', 'Site A')",
                    "minLength": 1,
                    "maxLength": 255,
                },
                "description": {
                    "type": "string",
                    "description": "Description of what this case represents",
                },
                "memo": {
                    "type": "string",
                    "description": "Additional notes about the case",
                },
            },
            "required": ["name"],
        },
    },
    {
        "name": "update_case",
        "description": "Update an existing case's name, description, or memo.",
        "trust_level": TrustLevel.SUGGEST,
        "input_schema": {
            "type": "object",
            "properties": {
                "case_id": {
                    "type": "integer",
                    "description": "ID of the case to update",
                },
                "name": {
                    "type": "string",
                    "description": "New name for the case",
                    "minLength": 1,
                    "maxLength": 255,
                },
                "description": {
                    "type": "string",
                    "description": "New description for the case",
                },
                "memo": {
                    "type": "string",
                    "description": "New memo for the case",
                },
            },
            "required": ["case_id"],
        },
    },
    {
        "name": "delete_case",
        "description": "Delete a case from the project. This will also remove all source links and attributes.",
        "trust_level": TrustLevel.REQUIRE,
        "input_schema": {
            "type": "object",
            "properties": {
                "case_id": {
                    "type": "integer",
                    "description": "ID of the case to delete",
                }
            },
            "required": ["case_id"],
        },
    },
    {
        "name": "link_source_to_case",
        "description": "Link a source document to a case. This associates the source with the case for analysis.",
        "trust_level": TrustLevel.NOTIFY,
        "input_schema": {
            "type": "object",
            "properties": {
                "case_id": {
                    "type": "integer",
                    "description": "ID of the case",
                },
                "source_id": {
                    "type": "integer",
                    "description": "ID of the source to link",
                },
            },
            "required": ["case_id", "source_id"],
        },
    },
    {
        "name": "unlink_source_from_case",
        "description": "Remove a source document from a case.",
        "trust_level": TrustLevel.NOTIFY,
        "input_schema": {
            "type": "object",
            "properties": {
                "case_id": {
                    "type": "integer",
                    "description": "ID of the case",
                },
                "source_id": {
                    "type": "integer",
                    "description": "ID of the source to unlink",
                },
            },
            "required": ["case_id", "source_id"],
        },
    },
    {
        "name": "set_case_attribute",
        "description": "Set or update an attribute on a case. Attributes store demographic or categorical data.",
        "trust_level": TrustLevel.NOTIFY,
        "input_schema": {
            "type": "object",
            "properties": {
                "case_id": {
                    "type": "integer",
                    "description": "ID of the case",
                },
                "attr_name": {
                    "type": "string",
                    "description": "Name of the attribute (e.g., 'age', 'gender', 'education')",
                    "minLength": 1,
                    "maxLength": 100,
                },
                "attr_type": {
                    "type": "string",
                    "description": "Type of the attribute value",
                    "enum": ["text", "number", "date", "boolean"],
                },
                "attr_value": {
                    "description": "Value of the attribute (must match attr_type)",
                },
            },
            "required": ["case_id", "attr_name", "attr_type", "attr_value"],
        },
    },
    {
        "name": "suggest_case_groupings",
        "description": "Analyze case attributes and suggest meaningful groupings. Identifies patterns in demographic or categorical data to help organize cases for analysis.",
        "trust_level": TrustLevel.AUTONOMOUS,
        "input_schema": {
            "type": "object",
            "properties": {
                "attribute_names": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Focus analysis on specific attributes (optional, analyzes all if not provided)",
                },
                "min_group_size": {
                    "type": "integer",
                    "description": "Minimum number of cases required for a group",
                    "minimum": 2,
                    "default": 2,
                },
            },
            "required": [],
        },
    },
    {
        "name": "compare_cases",
        "description": "Compare coding patterns across multiple cases. Identifies unique themes per case and common themes across all cases to support cross-case analysis.",
        "trust_level": TrustLevel.AUTONOMOUS,
        "input_schema": {
            "type": "object",
            "properties": {
                "case_ids": {
                    "type": "array",
                    "items": {"type": "integer"},
                    "description": "IDs of cases to compare (minimum 2)",
                    "minItems": 2,
                },
                "code_ids": {
                    "type": "array",
                    "items": {"type": "integer"},
                    "description": "Filter comparison to specific codes (optional)",
                },
            },
            "required": ["case_ids"],
        },
    },
]

# ============================================================
# Resource Definitions
# ============================================================

CASES_RESOURCES = [
    {
        "uri_template": "qualcoder://cases",
        "name": "All Cases",
        "description": "List of all cases in the project",
        "mime_type": "application/json",
    },
    {
        "uri_template": "qualcoder://cases/{case_id}",
        "name": "Case Details",
        "description": "Detailed information about a specific case including attributes and linked sources",
        "mime_type": "application/json",
    },
    {
        "uri_template": "qualcoder://cases/{case_id}/sources",
        "name": "Case Sources",
        "description": "List of sources linked to a specific case",
        "mime_type": "application/json",
    },
    {
        "uri_template": "qualcoder://cases/{case_id}/attributes",
        "name": "Case Attributes",
        "description": "List of attributes for a specific case",
        "mime_type": "application/json",
    },
]
