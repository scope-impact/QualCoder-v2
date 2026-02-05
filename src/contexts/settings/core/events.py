"""
Settings Context: Domain Events

Events emitted when settings are changed. All events are immutable
and inherit from DomainEvent base class.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from src.shared.common.types import DomainEvent

# =============================================================================
# Theme Events
# =============================================================================


@dataclass(frozen=True)
class ThemeChanged(DomainEvent):
    """Emitted when the user changes the application theme."""

    event_type: str = field(default="settings.theme_changed", init=False)
    old_theme: str = ""
    new_theme: str = ""

    @classmethod
    def create(cls, old_theme: str, new_theme: str) -> ThemeChanged:
        """Factory method to create event with auto-generated metadata."""
        return cls(
            event_id=cls._generate_id(),
            occurred_at=cls._now(),
            old_theme=old_theme,
            new_theme=new_theme,
        )


# =============================================================================
# Font Events
# =============================================================================


@dataclass(frozen=True)
class FontChanged(DomainEvent):
    """Emitted when the user changes font settings."""

    event_type: str = field(default="settings.font_changed", init=False)
    old_family: str = ""
    old_size: int = 14
    family: str = ""
    size: int = 14

    @classmethod
    def create(
        cls,
        old_family: str,
        old_size: int,
        family: str,
        size: int,
    ) -> FontChanged:
        """Factory method to create event with auto-generated metadata."""
        return cls(
            event_id=cls._generate_id(),
            occurred_at=cls._now(),
            old_family=old_family,
            old_size=old_size,
            family=family,
            size=size,
        )


# =============================================================================
# Language Events
# =============================================================================


@dataclass(frozen=True)
class LanguageChanged(DomainEvent):
    """Emitted when the user changes the application language."""

    event_type: str = field(default="settings.language_changed", init=False)
    old_language: str = ""
    new_language: str = ""
    language_name: str = ""

    @classmethod
    def create(
        cls,
        old_language: str,
        new_language: str,
        language_name: str,
    ) -> LanguageChanged:
        """Factory method to create event with auto-generated metadata."""
        return cls(
            event_id=cls._generate_id(),
            occurred_at=cls._now(),
            old_language=old_language,
            new_language=new_language,
            language_name=language_name,
        )


# =============================================================================
# Backup Events
# =============================================================================


@dataclass(frozen=True)
class BackupConfigChanged(DomainEvent):
    """Emitted when the user changes backup configuration."""

    event_type: str = field(default="settings.backup_config_changed", init=False)
    old_enabled: bool = False
    old_interval_minutes: int = 30
    old_max_backups: int = 5
    old_backup_path: str | None = None
    enabled: bool = False
    interval_minutes: int = 30
    max_backups: int = 5
    backup_path: str | None = None

    @classmethod
    def create(
        cls,
        old_enabled: bool,
        old_interval_minutes: int,
        old_max_backups: int,
        old_backup_path: str | None,
        enabled: bool,
        interval_minutes: int,
        max_backups: int,
        backup_path: str | None,
    ) -> BackupConfigChanged:
        """Factory method to create event with auto-generated metadata."""
        return cls(
            event_id=cls._generate_id(),
            occurred_at=cls._now(),
            old_enabled=old_enabled,
            old_interval_minutes=old_interval_minutes,
            old_max_backups=old_max_backups,
            old_backup_path=old_backup_path,
            enabled=enabled,
            interval_minutes=interval_minutes,
            max_backups=max_backups,
            backup_path=backup_path,
        )


# =============================================================================
# AV Coding Events
# =============================================================================


@dataclass(frozen=True)
class AVCodingConfigChanged(DomainEvent):
    """Emitted when the user changes AV coding configuration."""

    event_type: str = field(default="settings.av_coding_config_changed", init=False)
    old_timestamp_format: str = ""
    old_speaker_format: str = ""
    timestamp_format: str = ""
    speaker_format: str = ""

    @classmethod
    def create(
        cls,
        old_timestamp_format: str,
        old_speaker_format: str,
        timestamp_format: str,
        speaker_format: str,
    ) -> AVCodingConfigChanged:
        """Factory method to create event with auto-generated metadata."""
        return cls(
            event_id=cls._generate_id(),
            occurred_at=cls._now(),
            old_timestamp_format=old_timestamp_format,
            old_speaker_format=old_speaker_format,
            timestamp_format=timestamp_format,
            speaker_format=speaker_format,
        )


# =============================================================================
# Cloud Sync Events
# =============================================================================


@dataclass(frozen=True)
class CloudSyncConfigChanged(DomainEvent):
    """Emitted when cloud sync configuration is changed."""

    event_type: str = field(default="settings.cloud_sync_config_changed", init=False)
    old_enabled: bool = False
    old_convex_url: str | None = None
    enabled: bool = False
    convex_url: str | None = None

    @classmethod
    def create(
        cls,
        old_enabled: bool,
        old_convex_url: str | None,
        enabled: bool,
        convex_url: str | None,
    ) -> CloudSyncConfigChanged:
        """Factory method to create event with auto-generated metadata."""
        return cls(
            event_id=cls._generate_id(),
            occurred_at=cls._now(),
            old_enabled=old_enabled,
            old_convex_url=old_convex_url,
            enabled=enabled,
            convex_url=convex_url,
        )


@dataclass(frozen=True)
class CloudSyncEnabled(DomainEvent):
    """Emitted when cloud sync is enabled."""

    event_type: str = field(default="settings.cloud_sync_enabled", init=False)
    convex_url: str = ""

    @classmethod
    def create(cls, convex_url: str) -> CloudSyncEnabled:
        """Factory method to create event with auto-generated metadata."""
        return cls(
            event_id=cls._generate_id(),
            occurred_at=cls._now(),
            convex_url=convex_url,
        )


@dataclass(frozen=True)
class CloudSyncDisabled(DomainEvent):
    """Emitted when cloud sync is disabled."""

    event_type: str = field(default="settings.cloud_sync_disabled", init=False)

    @classmethod
    def create(cls) -> CloudSyncDisabled:
        """Factory method to create event with auto-generated metadata."""
        return cls(
            event_id=cls._generate_id(),
            occurred_at=cls._now(),
        )
