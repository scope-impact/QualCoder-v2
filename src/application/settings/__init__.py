"""
Application layer for the Settings bounded context.

Provides:
- Use cases for settings operations (functional 5-step pattern)
- Query functions for reading settings
- Commands for use case inputs

Use Cases:
    from src.application.settings.usecases import change_theme
    result = change_theme(command, settings_repo, event_bus)

Queries:
    from src.application.settings.queries import get_theme
    theme = get_theme(settings_repo)
"""

from src.application.settings.commands import (
    ChangeFontCommand,
    ChangeLanguageCommand,
    ChangeThemeCommand,
    ConfigureAVCodingCommand,
    ConfigureBackupCommand,
)
from src.application.settings.queries import (
    get_all_settings,
    get_av_coding_config,
    get_backup_config,
    get_font,
    get_language,
    get_theme,
)
from src.application.settings.usecases import (
    change_font,
    change_language,
    change_theme,
    configure_av_coding,
    configure_backup,
)

__all__ = [
    # Use Cases
    "change_theme",
    "change_font",
    "change_language",
    "configure_backup",
    "configure_av_coding",
    # Queries
    "get_all_settings",
    "get_theme",
    "get_font",
    "get_language",
    "get_backup_config",
    "get_av_coding_config",
    # Commands
    "ChangeFontCommand",
    "ChangeLanguageCommand",
    "ChangeThemeCommand",
    "ConfigureAVCodingCommand",
    "ConfigureBackupCommand",
]
