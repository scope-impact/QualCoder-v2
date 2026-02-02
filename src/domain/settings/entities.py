"""
DEPRECATED: Use src.contexts.settings.core.entities instead.

This module re-exports from the new bounded context location for backwards compatibility.
"""

from src.contexts.settings.core.entities import (
    AVCodingConfig,
    BackupConfig,
    FontPreference,
    LanguagePreference,
    ThemePreference,
    UserSettings,
)

__all__ = [
    "AVCodingConfig",
    "BackupConfig",
    "FontPreference",
    "LanguagePreference",
    "ThemePreference",
    "UserSettings",
]
