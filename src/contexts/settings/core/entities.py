"""
Settings Context: Domain Entities

Immutable entities and value objects representing user settings and preferences.
"""

from __future__ import annotations

from dataclasses import dataclass, field

# =============================================================================
# Value Objects
# =============================================================================


@dataclass(frozen=True)
class ThemePreference:
    """
    Theme selection value object.

    Represents the user's preferred visual theme.
    """

    name: str = "light"  # "light", "dark", "system"

    def with_name(self, new_name: str) -> ThemePreference:
        """Return new ThemePreference with updated name."""
        return ThemePreference(name=new_name)


@dataclass(frozen=True)
class FontPreference:
    """
    Font configuration value object.

    Controls the application's typography settings.
    """

    family: str = "Inter"
    size: int = 14  # base size in pixels

    def with_family(self, new_family: str) -> FontPreference:
        """Return new FontPreference with updated family."""
        return FontPreference(family=new_family, size=self.size)

    def with_size(self, new_size: int) -> FontPreference:
        """Return new FontPreference with updated size."""
        return FontPreference(family=self.family, size=new_size)


@dataclass(frozen=True)
class LanguagePreference:
    """
    Language selection value object.

    Controls the application's display language.
    """

    code: str = "en"  # ISO 639-1 language code
    name: str = "English"

    def with_language(self, code: str, name: str) -> LanguagePreference:
        """Return new LanguagePreference with updated language."""
        return LanguagePreference(code=code, name=name)


@dataclass(frozen=True)
class BackupConfig:
    """
    Backup configuration value object.

    Controls automatic project backup settings.
    """

    enabled: bool = False
    interval_minutes: int = 30
    max_backups: int = 5
    backup_path: str | None = None

    def with_enabled(self, enabled: bool) -> BackupConfig:
        """Return new BackupConfig with updated enabled state."""
        return BackupConfig(
            enabled=enabled,
            interval_minutes=self.interval_minutes,
            max_backups=self.max_backups,
            backup_path=self.backup_path,
        )

    def with_interval(self, interval_minutes: int) -> BackupConfig:
        """Return new BackupConfig with updated interval."""
        return BackupConfig(
            enabled=self.enabled,
            interval_minutes=interval_minutes,
            max_backups=self.max_backups,
            backup_path=self.backup_path,
        )

    def with_max_backups(self, max_backups: int) -> BackupConfig:
        """Return new BackupConfig with updated max backups."""
        return BackupConfig(
            enabled=self.enabled,
            interval_minutes=self.interval_minutes,
            max_backups=max_backups,
            backup_path=self.backup_path,
        )

    def with_backup_path(self, backup_path: str | None) -> BackupConfig:
        """Return new BackupConfig with updated backup path."""
        return BackupConfig(
            enabled=self.enabled,
            interval_minutes=self.interval_minutes,
            max_backups=self.max_backups,
            backup_path=backup_path,
        )


@dataclass(frozen=True)
class AVCodingConfig:
    """
    Audio/Video coding configuration value object.

    Controls timestamp and speaker formatting for AV coding.
    """

    timestamp_format: str = "HH:MM:SS"  # or "HH:MM:SS.mmm", "MM:SS"
    speaker_format: str = "Speaker {n}"  # template for speaker names

    def with_timestamp_format(self, timestamp_format: str) -> AVCodingConfig:
        """Return new AVCodingConfig with updated timestamp format."""
        return AVCodingConfig(
            timestamp_format=timestamp_format,
            speaker_format=self.speaker_format,
        )

    def with_speaker_format(self, speaker_format: str) -> AVCodingConfig:
        """Return new AVCodingConfig with updated speaker format."""
        return AVCodingConfig(
            timestamp_format=self.timestamp_format,
            speaker_format=speaker_format,
        )


# =============================================================================
# Aggregate Root
# =============================================================================


@dataclass(frozen=True)
class UserSettings:
    """
    User Settings entity - Aggregate root for the Settings context.

    Represents all user-configurable preferences. Immutable with copy methods.
    """

    theme: ThemePreference = field(default_factory=ThemePreference)
    font: FontPreference = field(default_factory=FontPreference)
    language: LanguagePreference = field(default_factory=LanguagePreference)
    backup: BackupConfig = field(default_factory=BackupConfig)
    av_coding: AVCodingConfig = field(default_factory=AVCodingConfig)

    @classmethod
    def default(cls) -> UserSettings:
        """Create default user settings."""
        return cls()

    def with_theme(self, theme: ThemePreference) -> UserSettings:
        """Return new UserSettings with updated theme."""
        return UserSettings(
            theme=theme,
            font=self.font,
            language=self.language,
            backup=self.backup,
            av_coding=self.av_coding,
        )

    def with_font(self, font: FontPreference) -> UserSettings:
        """Return new UserSettings with updated font."""
        return UserSettings(
            theme=self.theme,
            font=font,
            language=self.language,
            backup=self.backup,
            av_coding=self.av_coding,
        )

    def with_language(self, language: LanguagePreference) -> UserSettings:
        """Return new UserSettings with updated language."""
        return UserSettings(
            theme=self.theme,
            font=self.font,
            language=language,
            backup=self.backup,
            av_coding=self.av_coding,
        )

    def with_backup(self, backup: BackupConfig) -> UserSettings:
        """Return new UserSettings with updated backup config."""
        return UserSettings(
            theme=self.theme,
            font=self.font,
            language=self.language,
            backup=backup,
            av_coding=self.av_coding,
        )

    def with_av_coding(self, av_coding: AVCodingConfig) -> UserSettings:
        """Return new UserSettings with updated AV coding config."""
        return UserSettings(
            theme=self.theme,
            font=self.font,
            language=self.language,
            backup=self.backup,
            av_coding=av_coding,
        )
