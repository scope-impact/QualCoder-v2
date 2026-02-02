"""
DEPRECATED: Use src.contexts.projects.core.entities instead.

This module re-exports from the new bounded context location for backwards compatibility.
"""

from src.contexts.projects.core.entities import (
    Folder,
    Project,
    ProjectId,
    ProjectSummary,
    RecentProject,
    Source,
    SourceStatus,
    SourceType,
)

__all__ = [
    "Folder",
    "Project",
    "ProjectId",
    "ProjectSummary",
    "RecentProject",
    "Source",
    "SourceStatus",
    "SourceType",
]
