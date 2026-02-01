"""
Settings Context: Domain Layer

Entities, events, and derivers for user settings and preferences.
"""

from src.domain.settings.entities import (
    AVCodingConfig,
    BackupConfig,
    FontPreference,
    LanguagePreference,
    ThemePreference,
    UserSettings,
)
from src.domain.settings.events import (
    AVCodingConfigChanged,
    BackupConfigChanged,
    FontChanged,
    LanguageChanged,
    ThemeChanged,
)

__all__ = [
    # Entities / Value Objects
    "AVCodingConfig",
    "BackupConfig",
    "FontPreference",
    "LanguagePreference",
    "ThemePreference",
    "UserSettings",
    # Events
    "AVCodingConfigChanged",
    "BackupConfigChanged",
    "FontChanged",
    "LanguageChanged",
    "ThemeChanged",
]
