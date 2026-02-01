"""
Application layer for the Settings bounded context.

Provides the SettingsController for handling commands and queries.
"""

from src.application.settings.commands import (
    ChangeFontCommand,
    ChangeLanguageCommand,
    ChangeThemeCommand,
    ConfigureAVCodingCommand,
    ConfigureBackupCommand,
)
from src.application.settings.controller import SettingsControllerImpl

__all__ = [
    # Controller
    "SettingsControllerImpl",
    # Commands
    "ChangeFontCommand",
    "ChangeLanguageCommand",
    "ChangeThemeCommand",
    "ConfigureAVCodingCommand",
    "ConfigureBackupCommand",
]
