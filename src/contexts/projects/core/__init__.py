"""
Project Context Core - Research project lifecycle management.

This bounded context handles:
- Creating and opening QualCoder projects (.qda files)
- Managing source files within projects
- Project navigation and switching
- Recent projects list

Import from submodules directly for most types:
    from src.contexts.projects.core.entities import Project, Source, Folder
    from src.contexts.projects.core.events import ProjectCreated
    from src.contexts.projects.core.derivers import derive_create_project
"""

# Only re-export types that are actually imported from this package level
from src.contexts.projects.core.entities import RecentProject

__all__ = [
    "RecentProject",
]
