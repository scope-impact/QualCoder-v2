"""
Settings Command Handlers.

Command handlers for user settings management.
"""

from src.contexts.settings.core.commandHandlers.change_font import change_font
from src.contexts.settings.core.commandHandlers.change_language import change_language
from src.contexts.settings.core.commandHandlers.change_theme import change_theme
from src.contexts.settings.core.commandHandlers.configure_av_coding import (
    configure_av_coding,
)
from src.contexts.settings.core.commandHandlers.configure_backup import configure_backup

__all__ = [
    "change_font",
    "change_language",
    "change_theme",
    "configure_av_coding",
    "configure_backup",
]
