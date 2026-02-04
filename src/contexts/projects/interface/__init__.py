"""
Projects Interface Layer.

External API for the projects bounded context, including MCP tools.
"""

from src.contexts.projects.interface.vcs_mcp_tools import VersionControlMCPTools

__all__ = [
    "VersionControlMCPTools",
]
