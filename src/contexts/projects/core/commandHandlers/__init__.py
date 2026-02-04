"""
Projects Command Handlers.

Command handlers for project lifecycle management.
"""

from src.contexts.projects.core.commandHandlers.close_project import close_project
from src.contexts.projects.core.commandHandlers.create_project import create_project
from src.contexts.projects.core.commandHandlers.open_project import open_project

__all__ = [
    "close_project",
    "create_project",
    "open_project",
]
