"""
DEPRECATED: Use src.contexts.settings.core.derivers instead.

This module re-exports from the new bounded context location for backwards compatibility.
"""

from src.contexts.settings.core.derivers import (
    InvalidBackupInterval,
    InvalidFontFamily,
    InvalidFontSize,
    InvalidLanguage,
    InvalidMaxBackups,
    InvalidSpeakerFormat,
    InvalidTheme,
    InvalidTimestampFormat,
    derive_av_coding_config_change,
    derive_backup_config_change,
    derive_font_change,
    derive_language_change,
    derive_theme_change,
)

__all__ = [
    "InvalidBackupInterval",
    "InvalidFontFamily",
    "InvalidFontSize",
    "InvalidLanguage",
    "InvalidMaxBackups",
    "InvalidSpeakerFormat",
    "InvalidTheme",
    "InvalidTimestampFormat",
    "derive_av_coding_config_change",
    "derive_backup_config_change",
    "derive_font_change",
    "derive_language_change",
    "derive_theme_change",
]
