"""
Settings Context: Derivers

Pure functions that compose invariants and derive domain events.
No I/O, no side effects - returns events or SettingsNotChanged failure events.
"""

from __future__ import annotations

from src.contexts.settings.core.entities import UserSettings
from src.contexts.settings.core.events import (
    AVCodingConfigChanged,
    BackupConfigChanged,
    FontChanged,
    LanguageChanged,
    ObservabilityConfigChanged,
    ThemeChanged,
)
from src.contexts.settings.core.failure_events import (
    SettingsNotChanged,
)
from src.contexts.settings.core.invariants import (
    VALID_LANGUAGES,
    is_valid_backup_interval,
    is_valid_font_family,
    is_valid_font_size,
    is_valid_language_code,
    is_valid_log_level,
    is_valid_max_backups,
    is_valid_speaker_format,
    is_valid_theme,
    is_valid_timestamp_format,
)

# =============================================================================
# Derivers
# =============================================================================


def derive_theme_change(
    new_theme: str,
    current_settings: UserSettings,
) -> ThemeChanged | SettingsNotChanged:
    """
    Derive a theme change event from inputs and state.

    Pure function - no I/O, no side effects.

    Args:
        new_theme: The new theme name (light, dark, system)
        current_settings: Current user settings for old theme value

    Returns:
        ThemeChanged event on success, SettingsNotChanged on error
    """
    if not is_valid_theme(new_theme):
        return SettingsNotChanged.invalid_theme(new_theme)

    return ThemeChanged.create(
        old_theme=current_settings.theme.name,
        new_theme=new_theme,
    )


def derive_font_change(
    family: str,
    size: int,
    current_settings: UserSettings,
) -> FontChanged | SettingsNotChanged:
    """
    Derive a font change event from inputs and state.

    Pure function - no I/O, no side effects.

    Args:
        family: The font family name
        size: The font size in pixels
        current_settings: Current user settings for old font values

    Returns:
        FontChanged event on success, SettingsNotChanged on error
    """
    if not is_valid_font_family(family):
        return SettingsNotChanged.invalid_font_family(family)

    if not is_valid_font_size(size):
        return SettingsNotChanged.invalid_font_size(size)

    return FontChanged.create(
        old_family=current_settings.font.family,
        old_size=current_settings.font.size,
        family=family,
        size=size,
    )


def derive_language_change(
    new_language_code: str,
    current_settings: UserSettings,
) -> LanguageChanged | SettingsNotChanged:
    """
    Derive a language change event from inputs and state.

    Pure function - no I/O, no side effects.

    Args:
        new_language_code: ISO 639-1 language code
        current_settings: Current user settings for old language value

    Returns:
        LanguageChanged event on success, SettingsNotChanged on error
    """
    if not is_valid_language_code(new_language_code):
        return SettingsNotChanged.invalid_language(new_language_code)

    language_name = VALID_LANGUAGES.get(new_language_code, "Unknown")

    return LanguageChanged.create(
        old_language=current_settings.language.code,
        new_language=new_language_code,
        language_name=language_name,
    )


def derive_backup_config_change(
    enabled: bool,
    interval_minutes: int,
    max_backups: int,
    backup_path: str | None,
    current_settings: UserSettings,
) -> BackupConfigChanged | SettingsNotChanged:
    """
    Derive a backup config change event from inputs.

    Pure function - no I/O, no side effects.

    Args:
        enabled: Whether automatic backups are enabled
        interval_minutes: Backup interval in minutes
        max_backups: Maximum number of backups to keep
        backup_path: Optional custom backup path
        current_settings: Current user settings for old backup values

    Returns:
        BackupConfigChanged event on success, SettingsNotChanged on error
    """
    if not is_valid_backup_interval(interval_minutes):
        return SettingsNotChanged.invalid_backup_interval(interval_minutes)

    if not is_valid_max_backups(max_backups):
        return SettingsNotChanged.invalid_max_backups(max_backups)

    return BackupConfigChanged.create(
        old_enabled=current_settings.backup.enabled,
        old_interval_minutes=current_settings.backup.interval_minutes,
        old_max_backups=current_settings.backup.max_backups,
        old_backup_path=current_settings.backup.backup_path,
        enabled=enabled,
        interval_minutes=interval_minutes,
        max_backups=max_backups,
        backup_path=backup_path,
    )


def derive_av_coding_config_change(
    timestamp_format: str,
    speaker_format: str,
    current_settings: UserSettings,
) -> AVCodingConfigChanged | SettingsNotChanged:
    """
    Derive an AV coding config change event from inputs.

    Pure function - no I/O, no side effects.

    Args:
        timestamp_format: Timestamp display format
        speaker_format: Speaker name format template
        current_settings: Current user settings for old AV coding values

    Returns:
        AVCodingConfigChanged event on success, SettingsNotChanged on error
    """
    if not is_valid_timestamp_format(timestamp_format):
        return SettingsNotChanged.invalid_timestamp_format(timestamp_format)

    if not is_valid_speaker_format(speaker_format):
        return SettingsNotChanged.invalid_speaker_format(speaker_format)

    return AVCodingConfigChanged.create(
        old_timestamp_format=current_settings.av_coding.timestamp_format,
        old_speaker_format=current_settings.av_coding.speaker_format,
        timestamp_format=timestamp_format,
        speaker_format=speaker_format,
    )


def derive_observability_config_change(
    log_level: str,
    enable_file_logging: bool,
    enable_telemetry: bool,
    current_settings: UserSettings,
) -> ObservabilityConfigChanged | SettingsNotChanged:
    """
    Derive an observability config change event from inputs.

    Pure function - no I/O, no side effects.

    Args:
        log_level: Log level (DEBUG, INFO, WARNING, ERROR)
        enable_file_logging: Whether to write logs to file
        enable_telemetry: Whether to collect OTEL metrics
        current_settings: Current user settings for old observability values

    Returns:
        ObservabilityConfigChanged event on success, SettingsNotChanged on error
    """
    if not is_valid_log_level(log_level):
        return SettingsNotChanged.invalid_log_level(log_level)

    return ObservabilityConfigChanged.create(
        old_log_level=current_settings.observability.log_level,
        old_enable_file_logging=current_settings.observability.enable_file_logging,
        old_enable_telemetry=current_settings.observability.enable_telemetry,
        log_level=log_level.upper(),
        enable_file_logging=enable_file_logging,
        enable_telemetry=enable_telemetry,
    )


