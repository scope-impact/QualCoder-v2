"""
Sources Context: Entities and Value Objects

Immutable data types representing domain concepts for source management.

Note: For backward compatibility, the actual entity definitions are in
projects/core/entities.py. This module re-exports them for use in the
Sources bounded context. A future migration will move the definitions here.
"""

from __future__ import annotations

# Re-export from projects for backward compatibility
# These entities conceptually belong to Sources but are currently defined in Projects
from src.contexts.projects.core.entities import (
    Folder,
    Source,
    SourceStatus,
    SourceType,
)

__all__ = [
    "Source",
    "SourceType",
    "SourceStatus",
    "Folder",
]
