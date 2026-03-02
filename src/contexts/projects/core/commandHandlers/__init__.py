"""
Projects Command Handlers.

Command handlers for project lifecycle management and version control.
"""

from src.contexts.projects.core.commandHandlers.auto_commit import auto_commit
from src.contexts.projects.core.commandHandlers.close_project import close_project
from src.contexts.projects.core.commandHandlers.create_project import create_project
from src.contexts.projects.core.commandHandlers.initialize_version_control import (
    initialize_version_control,
)
from src.contexts.projects.core.commandHandlers.list_snapshots import list_snapshots
from src.contexts.projects.core.commandHandlers.open_project import open_project
from src.contexts.projects.core.commandHandlers.restore_snapshot import restore_snapshot
from src.contexts.projects.core.commandHandlers.view_diff import view_diff

__all__ = [
    # Project lifecycle
    "close_project",
    "create_project",
    "open_project",
    # Version control
    "auto_commit",
    "initialize_version_control",
    "list_snapshots",
    "restore_snapshot",
    "view_diff",
]
