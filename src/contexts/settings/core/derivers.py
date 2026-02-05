"""
Settings Context: Derivers

Pure functions that compose invariants and derive domain events.
No I/O, no side effects - returns events or Failure.
"""

from __future__ import annotations

from dataclasses import dataclass

from returns.result import Failure

from src.contexts.settings.core.entities import UserSettings
from src.contexts.settings.core.events import (
    AVCodingConfigChanged,
    BackupConfigChanged,
    CloudSyncConfigChanged,
    FontChanged,
    LanguageChanged,
    ThemeChanged,
)
from src.contexts.settings.core.invariants import (
    VALID_LANGUAGES,
    can_enable_cloud_sync,
    is_valid_backup_interval,
    is_valid_convex_url,
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


@dataclass(frozen=True)
class CloudSyncSettingsFailed:
    """Cloud sync settings change failed."""

    reason: str = ""
    error_code: str = ""
    suggestions: tuple[str, ...] = ()

    @classmethod
    def invalid_url(cls, url: str) -> CloudSyncSettingsFailed:
        """Create failure for invalid Convex URL."""
        return cls(
            reason=f"Invalid Convex URL: '{url}'",
            error_code="INVALID_CONVEX_URL",
            suggestions=(
                "URL must start with https://",
                "URL must end with .convex.cloud",
                "Example: https://your-project.convex.cloud",
            ),
        )

    @classmethod
    def url_required(cls) -> CloudSyncSettingsFailed:
        """Create failure when trying to enable without URL."""
        return cls(
            reason="Convex URL is required to enable cloud sync",
            error_code="URL_REQUIRED",
            suggestions=(
                "Configure the Convex URL first",
                "Get your URL from convex.dev dashboard",
            ),
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

    return ThemeChanged.create(
        old_theme=current_settings.theme.name,
        new_theme=new_theme,
    )


def derive_font_change(
    family: str,
    size: int,
    current_settings: UserSettings,
) -> FontChanged | Failure:
    """
    Derive a font change event from inputs and state.

    Pure function - no I/O, no side effects.

    Args:
        family: The font family name
        size: The font size in pixels
        current_settings: Current user settings for old font values

    Returns:
        FontChanged event on success, Failure with reason on error
    """
    if not is_valid_font_family(family):
        return Failure(InvalidFontFamily(family=family))

    if not is_valid_font_size(size):
        return Failure(InvalidFontSize(size=size))

    return FontChanged.create(
        old_family=current_settings.font.family,
        old_size=current_settings.font.size,
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
) -> BackupConfigChanged | Failure:
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
        BackupConfigChanged event on success, Failure with reason on error
    """
    if not is_valid_backup_interval(interval_minutes):
        return Failure(InvalidBackupInterval(interval=interval_minutes))

    if not is_valid_max_backups(max_backups):
        return Failure(InvalidMaxBackups(max_backups=max_backups))

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
) -> AVCodingConfigChanged | Failure:
    """
    Derive an AV coding config change event from inputs.

    Pure function - no I/O, no side effects.

    Args:
        timestamp_format: Timestamp display format
        speaker_format: Speaker name format template
        current_settings: Current user settings for old AV coding values

    Returns:
        AVCodingConfigChanged event on success, Failure with reason on error
    """
    if not is_valid_timestamp_format(timestamp_format):
        return Failure(InvalidTimestampFormat(format_str=timestamp_format))

    if not is_valid_speaker_format(speaker_format):
        return Failure(InvalidSpeakerFormat(format_str=speaker_format))

    return AVCodingConfigChanged.create(
        old_timestamp_format=current_settings.av_coding.timestamp_format,
        old_speaker_format=current_settings.av_coding.speaker_format,
        timestamp_format=timestamp_format,
        speaker_format=speaker_format,
    )


def derive_cloud_sync_config_change(
    enabled: bool,
    convex_url: str | None,
    current_settings: UserSettings,
) -> CloudSyncConfigChanged | Failure:
    """
    Derive a cloud sync config change event from inputs.

    Pure function - no I/O, no side effects.

    Args:
        enabled: Whether cloud sync is enabled
        convex_url: Convex deployment URL (required if enabled)
        current_settings: Current user settings for old cloud sync values

    Returns:
        CloudSyncConfigChanged event on success, Failure with reason on error
    """
    # Validate URL format if provided
    if convex_url and not is_valid_convex_url(convex_url):
        return Failure(CloudSyncSettingsFailed.invalid_url(convex_url))

    # Cannot enable without valid URL
    if enabled and not can_enable_cloud_sync(convex_url):
        return Failure(CloudSyncSettingsFailed.url_required())

    return CloudSyncConfigChanged.create(
        old_enabled=current_settings.backend.cloud_sync_enabled,
        old_convex_url=current_settings.backend.convex_url,
        enabled=enabled,
        convex_url=convex_url,
    )
