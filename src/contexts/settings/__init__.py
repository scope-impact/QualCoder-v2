"""
Settings Context: User preferences and configuration.

This bounded context manages user-level settings including theme, font,
language, backup configuration, and AV coding preferences.
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
from src.contexts.settings.core.entities import (
    AVCodingConfig,
    BackupConfig,
    FontPreference,
    LanguagePreference,
    ThemePreference,
    UserSettings,
)
from src.contexts.settings.core.events import (
    AVCodingConfigChanged,
    BackupConfigChanged,
    FontChanged,
    LanguageChanged,
    ThemeChanged,
)
from src.contexts.settings.core.invariants import (
    MAX_BACKUP_INTERVAL,
    MAX_FONT_SIZE,
    MAX_MAX_BACKUPS,
    MIN_BACKUP_INTERVAL,
    MIN_FONT_SIZE,
    MIN_MAX_BACKUPS,
    VALID_FONT_FAMILIES,
    VALID_LANGUAGES,
    VALID_THEMES,
    VALID_TIMESTAMP_FORMATS,
    is_valid_backup_interval,
    is_valid_font_family,
    is_valid_font_size,
    is_valid_language_code,
    is_valid_max_backups,
    is_valid_speaker_format,
    is_valid_theme,
    is_valid_timestamp_format,
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
    # Derivers
    "derive_av_coding_config_change",
    "derive_backup_config_change",
    "derive_font_change",
    "derive_language_change",
    "derive_theme_change",
    # Failure types
    "InvalidBackupInterval",
    "InvalidFontFamily",
    "InvalidFontSize",
    "InvalidLanguage",
    "InvalidMaxBackups",
    "InvalidSpeakerFormat",
    "InvalidTheme",
    "InvalidTimestampFormat",
    # Invariants
    "VALID_THEMES",
    "VALID_TIMESTAMP_FORMATS",
    "VALID_LANGUAGES",
    "VALID_FONT_FAMILIES",
    "MIN_FONT_SIZE",
    "MAX_FONT_SIZE",
    "MIN_BACKUP_INTERVAL",
    "MAX_BACKUP_INTERVAL",
    "MIN_MAX_BACKUPS",
    "MAX_MAX_BACKUPS",
    "is_valid_theme",
    "is_valid_font_size",
    "is_valid_font_family",
    "is_valid_language_code",
    "is_valid_timestamp_format",
    "is_valid_speaker_format",
    "is_valid_backup_interval",
    "is_valid_max_backups",
]
