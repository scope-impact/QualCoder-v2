"""
Settings Context: Derivers

Pure functions that compose invariants and derive domain events.
No I/O, no side effects - returns events or Failure.
"""

from __future__ import annotations

from dataclasses import dataclass

from returns.result import Failure

from src.domain.settings.entities import UserSettings
from src.domain.settings.events import (
    AVCodingConfigChanged,
    BackupConfigChanged,
    FontChanged,
    LanguageChanged,
    ThemeChanged,
)
from src.domain.settings.invariants import (
    VALID_LANGUAGES,
    is_valid_backup_interval,
    is_valid_font_family,
    is_valid_font_size,
    is_valid_language_code,
    is_valid_max_backups,
    is_valid_speaker_format,
    is_valid_theme,
    is_valid_timestamp_format,
)

# =============================================================================
# Failure Reasons
# =============================================================================


@dataclass(frozen=True)
class InvalidTheme:
    """Theme is not valid."""

    theme: str = ""
    message: str = ""

    def __post_init__(self) -> None:
        if not self.message:
            object.__setattr__(
                self,
                "message",
                f"Invalid theme '{self.theme}'. Must be: light, dark, or system",
            )


@dataclass(frozen=True)
class InvalidFontSize:
    """Font size is outside valid range."""

    size: int = 0
    message: str = ""

    def __post_init__(self) -> None:
        if not self.message:
            object.__setattr__(
                self,
                "message",
                f"Font size {self.size} is invalid. Must be between 10 and 24",
            )


@dataclass(frozen=True)
class InvalidFontFamily:
    """Font family is not supported."""

    family: str = ""
    message: str = ""

    def __post_init__(self) -> None:
        if not self.message:
            object.__setattr__(
                self,
                "message",
                f"Font family '{self.family}' is not supported",
            )


@dataclass(frozen=True)
class InvalidLanguage:
    """Language code is not supported."""

    code: str = ""
    message: str = ""

    def __post_init__(self) -> None:
        if not self.message:
            object.__setattr__(
                self,
                "message",
                f"Language code '{self.code}' is not supported",
            )


@dataclass(frozen=True)
class InvalidBackupInterval:
    """Backup interval is outside valid range."""

    interval: int = 0
    message: str = ""

    def __post_init__(self) -> None:
        if not self.message:
            object.__setattr__(
                self,
                "message",
                f"Backup interval {self.interval} minutes is invalid. Must be between 5 and 120",
            )


@dataclass(frozen=True)
class InvalidMaxBackups:
    """Max backups is outside valid range."""

    max_backups: int = 0
    message: str = ""

    def __post_init__(self) -> None:
        if not self.message:
            object.__setattr__(
                self,
                "message",
                f"Max backups {self.max_backups} is invalid. Must be between 1 and 20",
            )


@dataclass(frozen=True)
class InvalidTimestampFormat:
    """Timestamp format is not valid."""

    format_str: str = ""
    message: str = ""

    def __post_init__(self) -> None:
        if not self.message:
            object.__setattr__(
                self,
                "message",
                f"Timestamp format '{self.format_str}' is invalid. Use HH:MM:SS, HH:MM:SS.mmm, or MM:SS",
            )


@dataclass(frozen=True)
class InvalidSpeakerFormat:
    """Speaker format is not valid."""

    format_str: str = ""
    message: str = ""

    def __post_init__(self) -> None:
        if not self.message:
            object.__setattr__(
                self,
                "message",
                f"Speaker format '{self.format_str}' must contain {{n}} placeholder",
            )


# =============================================================================
# Derivers
# =============================================================================


def derive_theme_change(
    new_theme: str,
    current_settings: UserSettings,
) -> ThemeChanged | Failure:
    """
    Derive a theme change event from inputs and state.

    Pure function - no I/O, no side effects.

    Args:
        new_theme: The new theme name (light, dark, system)
        current_settings: Current user settings for old theme value

    Returns:
        ThemeChanged event on success, Failure with reason on error
    """
    if not is_valid_theme(new_theme):
        return Failure(InvalidTheme(theme=new_theme))

    return ThemeChanged(
        old_theme=current_settings.theme.name,
        new_theme=new_theme,
    )


def derive_font_change(
    family: str,
    size: int,
    current_settings: UserSettings,  # noqa: ARG001 - kept for API consistency
) -> FontChanged | Failure:
    """
    Derive a font change event from inputs and state.

    Pure function - no I/O, no side effects.

    Args:
        family: The font family name
        size: The font size in pixels
        current_settings: Current user settings (for API consistency)

    Returns:
        FontChanged event on success, Failure with reason on error
    """
    if not is_valid_font_family(family):
        return Failure(InvalidFontFamily(family=family))

    if not is_valid_font_size(size):
        return Failure(InvalidFontSize(size=size))

    return FontChanged(
        family=family,
        size=size,
    )


def derive_language_change(
    new_language_code: str,
    current_settings: UserSettings,
) -> LanguageChanged | Failure:
    """
    Derive a language change event from inputs and state.

    Pure function - no I/O, no side effects.

    Args:
        new_language_code: ISO 639-1 language code
        current_settings: Current user settings for old language value

    Returns:
        LanguageChanged event on success, Failure with reason on error
    """
    if not is_valid_language_code(new_language_code):
        return Failure(InvalidLanguage(code=new_language_code))

    language_name = VALID_LANGUAGES.get(new_language_code, "Unknown")

    return LanguageChanged(
        old_language=current_settings.language.code,
        new_language=new_language_code,
        language_name=language_name,
    )


def derive_backup_config_change(
    enabled: bool,
    interval_minutes: int,
    max_backups: int,
    backup_path: str | None,
) -> BackupConfigChanged | Failure:
    """
    Derive a backup config change event from inputs.

    Pure function - no I/O, no side effects.

    Args:
        enabled: Whether automatic backups are enabled
        interval_minutes: Backup interval in minutes
        max_backups: Maximum number of backups to keep
        backup_path: Optional custom backup path

    Returns:
        BackupConfigChanged event on success, Failure with reason on error
    """
    if not is_valid_backup_interval(interval_minutes):
        return Failure(InvalidBackupInterval(interval=interval_minutes))

    if not is_valid_max_backups(max_backups):
        return Failure(InvalidMaxBackups(max_backups=max_backups))

    return BackupConfigChanged(
        enabled=enabled,
        interval_minutes=interval_minutes,
        max_backups=max_backups,
        backup_path=backup_path,
    )


def derive_av_coding_config_change(
    timestamp_format: str,
    speaker_format: str,
) -> AVCodingConfigChanged | Failure:
    """
    Derive an AV coding config change event from inputs.

    Pure function - no I/O, no side effects.

    Args:
        timestamp_format: Timestamp display format
        speaker_format: Speaker name format template

    Returns:
        AVCodingConfigChanged event on success, Failure with reason on error
    """
    if not is_valid_timestamp_format(timestamp_format):
        return Failure(InvalidTimestampFormat(format_str=timestamp_format))

    if not is_valid_speaker_format(speaker_format):
        return Failure(InvalidSpeakerFormat(format_str=speaker_format))

    return AVCodingConfigChanged(
        timestamp_format=timestamp_format,
        speaker_format=speaker_format,
    )
