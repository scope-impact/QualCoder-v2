"""
Settings Context: Invariants

Pure validation functions for settings values.
No I/O, no side effects.
"""

from __future__ import annotations

# =============================================================================
# Valid Values
# =============================================================================

VALID_THEMES = ("light", "dark", "system")

VALID_TIMESTAMP_FORMATS = ("HH:MM:SS", "HH:MM:SS.mmm", "MM:SS")

VALID_LANGUAGES = {
    "en": "English",
    "es": "Español",
    "de": "Deutsch",
    "fr": "Français",
    "pt": "Português",
    "zh": "中文",
    "ja": "日本語",
}

VALID_FONT_FAMILIES = (
    "Inter",
    "Roboto",
    "Open Sans",
    "Source Sans Pro",
    "Noto Sans",
    "JetBrains Mono",
    "Fira Code",
    "system-ui",
)

MIN_FONT_SIZE = 10
MAX_FONT_SIZE = 24

MIN_BACKUP_INTERVAL = 5  # minutes
MAX_BACKUP_INTERVAL = 120  # minutes

MIN_MAX_BACKUPS = 1
MAX_MAX_BACKUPS = 20


# =============================================================================
# Validation Functions
# =============================================================================


def is_valid_theme(theme: str) -> bool:
    """Check if theme is valid."""
    return theme in VALID_THEMES


def is_valid_font_size(size: int) -> bool:
    """Check if font size is within valid range."""
    return MIN_FONT_SIZE <= size <= MAX_FONT_SIZE


def is_valid_font_family(family: str) -> bool:
    """Check if font family is valid."""
    return family in VALID_FONT_FAMILIES


def is_valid_language_code(code: str) -> bool:
    """Check if language code is supported."""
    return code in VALID_LANGUAGES


def is_valid_timestamp_format(format_str: str) -> bool:
    """Check if timestamp format is valid."""
    return format_str in VALID_TIMESTAMP_FORMATS


def is_valid_speaker_format(format_str: str) -> bool:
    """
    Check if speaker format is valid.

    Must contain {n} placeholder for speaker number.
    """
    return "{n}" in format_str and len(format_str.strip()) > 0


def is_valid_backup_interval(interval: int) -> bool:
    """Check if backup interval is within valid range."""
    return MIN_BACKUP_INTERVAL <= interval <= MAX_BACKUP_INTERVAL


def is_valid_max_backups(max_backups: int) -> bool:
    """Check if max backups is within valid range."""
    return MIN_MAX_BACKUPS <= max_backups <= MAX_MAX_BACKUPS
