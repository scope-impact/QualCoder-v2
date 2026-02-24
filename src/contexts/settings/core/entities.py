"""
Settings Context: Domain Entities

Immutable entities and value objects representing user settings and preferences.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace

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
        return replace(self, family=new_family)

    def with_size(self, new_size: int) -> FontPreference:
        """Return new FontPreference with updated size."""
        return replace(self, size=new_size)


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
        return replace(self, enabled=enabled)

    def with_interval(self, interval_minutes: int) -> BackupConfig:
        """Return new BackupConfig with updated interval."""
        return replace(self, interval_minutes=interval_minutes)

    def with_max_backups(self, max_backups: int) -> BackupConfig:
        """Return new BackupConfig with updated max backups."""
        return replace(self, max_backups=max_backups)

    def with_backup_path(self, backup_path: str | None) -> BackupConfig:
        """Return new BackupConfig with updated backup path."""
        return replace(self, backup_path=backup_path)


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
        return replace(self, timestamp_format=timestamp_format)

    def with_speaker_format(self, speaker_format: str) -> AVCodingConfig:
        """Return new AVCodingConfig with updated speaker format."""
        return replace(self, speaker_format=speaker_format)


@dataclass(frozen=True)
class BackendConfig:
    """
    Database backend configuration value object.

    SQLite is always the primary database. Convex cloud sync is optional.
    When cloud_sync_enabled is True, changes are synced to Convex in real-time.
    """

    cloud_sync_enabled: bool = False  # Enable Convex cloud sync
    convex_url: str | None = None  # Convex deployment URL
    convex_project_id: str | None = None  # Convex project ID for the current project

    @property
    def uses_convex(self) -> bool:
        """Check if Convex cloud sync is enabled."""
        return self.cloud_sync_enabled and self.convex_url is not None

    def with_cloud_sync_enabled(self, enabled: bool) -> BackendConfig:
        """Return new BackendConfig with updated cloud sync state."""
        return BackendConfig(
            cloud_sync_enabled=enabled,
            convex_url=self.convex_url,
            convex_project_id=self.convex_project_id,
        )

    def with_convex_url(self, convex_url: str | None) -> BackendConfig:
        """Return new BackendConfig with updated Convex URL."""
        return BackendConfig(
            cloud_sync_enabled=self.cloud_sync_enabled,
            convex_url=convex_url,
            convex_project_id=self.convex_project_id,
        )

    def with_convex_project_id(self, project_id: str | None) -> BackendConfig:
        """Return new BackendConfig with updated Convex project ID."""
        return BackendConfig(
            cloud_sync_enabled=self.cloud_sync_enabled,
            convex_url=self.convex_url,
            convex_project_id=project_id,
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
    backend: BackendConfig = field(default_factory=BackendConfig)

    @classmethod
    def default(cls) -> UserSettings:
        """Create default user settings."""
        return cls()

    def with_theme(self, theme: ThemePreference) -> UserSettings:
        """Return new UserSettings with updated theme."""
        return replace(self, theme=theme)

    def with_font(self, font: FontPreference) -> UserSettings:
        """Return new UserSettings with updated font."""
        return replace(self, font=font)

    def with_language(self, language: LanguagePreference) -> UserSettings:
        """Return new UserSettings with updated language."""
        return replace(self, language=language)

    def with_backup(self, backup: BackupConfig) -> UserSettings:
        """Return new UserSettings with updated backup config."""
        return replace(self, backup=backup)

    def with_av_coding(self, av_coding: AVCodingConfig) -> UserSettings:
        """Return new UserSettings with updated AV coding config."""
        return replace(self, av_coding=av_coding)

    def with_backend(self, backend: BackendConfig) -> UserSettings:
        """Return new UserSettings with updated backend config."""
        return replace(self, backend=backend)
