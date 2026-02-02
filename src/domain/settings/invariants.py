"""
DEPRECATED: Use src.contexts.settings.core.invariants instead.

This module re-exports from the new bounded context location for backwards compatibility.
"""

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
