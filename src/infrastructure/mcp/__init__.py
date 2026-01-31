"""
MCP (Model Context Protocol) Infrastructure

This module provides MCP-compatible tools for AI agent integration.
Tools are exposed to enable agents to query and navigate projects.

Implements QC-026:
- AC #5: Agent can query current project context
- AC #6: Agent can navigate to a specific source or segment
"""

from .project_tools import (
    ProjectTools,
    get_project_context_tool,
    list_sources_tool,
    navigate_to_segment_tool,
)

__all__ = [
    "ProjectTools",
    "get_project_context_tool",
    "list_sources_tool",
    "navigate_to_segment_tool",
]
