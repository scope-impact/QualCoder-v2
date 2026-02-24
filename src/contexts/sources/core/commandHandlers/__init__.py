"""
Sources Command Handlers.

Command handlers for source file management operations.
"""

from src.contexts.sources.core.commandHandlers.add_source import add_source
from src.contexts.sources.core.commandHandlers.open_source import open_source
from src.contexts.sources.core.commandHandlers.remove_source import remove_source
from src.contexts.sources.core.commandHandlers.update_source import update_source
from src.contexts.sources.core.queryHandlers.get_source import get_source
from src.contexts.sources.core.queryHandlers.list_sources import list_sources

__all__ = [
    "add_source",
    "get_source",
    "list_sources",
    "open_source",
    "remove_source",
    "update_source",
]
