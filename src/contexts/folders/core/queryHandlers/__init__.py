"""
Folders Query Handlers.

Query handlers for read-only folder operations.
"""

from src.contexts.folders.core.queryHandlers.get_folder import get_folder
from src.contexts.folders.core.queryHandlers.list_folders import list_folders

__all__ = [
    "get_folder",
    "list_folders",
]
