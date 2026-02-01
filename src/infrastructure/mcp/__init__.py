"""
MCP (Model Context Protocol) Infrastructure

This module provides MCP-compatible tools for AI agent integration.
Tools are exposed to enable agents to query and navigate projects.

Implements QC-026:
- AC #5: Agent can query current project context
- AC #6: Agent can navigate to a specific source or segment

Implements QC-034:
- AC #5: Agent can list all cases
- AC #6: Agent can suggest case groupings
- AC #7: Agent can compare across cases
"""

from .case_tools import (
    CaseTools,
    compare_cases_tool,
    get_case_tool,
    list_cases_tool,
    suggest_case_groupings_tool,
)
from .project_tools import (
    ProjectTools,
    get_project_context_tool,
    list_sources_tool,
    navigate_to_segment_tool,
)

__all__ = [
    # Project tools
    "ProjectTools",
    "get_project_context_tool",
    "list_sources_tool",
    "navigate_to_segment_tool",
    # Case tools
    "CaseTools",
    "list_cases_tool",
    "get_case_tool",
    "suggest_case_groupings_tool",
    "compare_cases_tool",
]
