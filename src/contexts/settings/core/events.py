"""
Settings Context: Domain Events

Events emitted when settings are changed. All events are immutable.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import uuid4


def _now() -> datetime:
    return datetime.now(UTC)


def _uuid() -> str:
    return str(uuid4())


# =============================================================================
# Theme Events
# =============================================================================


@dataclass(frozen=True)
class ThemeChanged:
    """Emitted when the user changes the application theme."""

    event_type: str = field(default="settings.theme_changed", init=False)
    old_theme: str = ""
    new_theme: str = ""
    event_id: str = field(default_factory=_uuid)
    occurred_at: datetime = field(default_factory=_now)


# =============================================================================
# Font Events
# =============================================================================


@dataclass(frozen=True)
class FontChanged:
    """Emitted when the user changes font settings."""

    event_type: str = field(default="settings.font_changed", init=False)
    old_family: str = ""
    old_size: int = 14
    family: str = ""
    size: int = 14
    event_id: str = field(default_factory=_uuid)
    occurred_at: datetime = field(default_factory=_now)


# =============================================================================
# Language Events
# =============================================================================


@dataclass(frozen=True)
class LanguageChanged:
    """Emitted when the user changes the application language."""

    event_type: str = field(default="settings.language_changed", init=False)
    old_language: str = ""
    new_language: str = ""
    language_name: str = ""
    event_id: str = field(default_factory=_uuid)
    occurred_at: datetime = field(default_factory=_now)


# =============================================================================
# Backup Events
# =============================================================================


@dataclass(frozen=True)
class BackupConfigChanged:
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
    event_id: str = field(default_factory=_uuid)
    occurred_at: datetime = field(default_factory=_now)


# =============================================================================
# AV Coding Events
# =============================================================================


@dataclass(frozen=True)
class AVCodingConfigChanged:
    """Emitted when the user changes AV coding configuration."""

    event_type: str = field(default="settings.av_coding_config_changed", init=False)
    old_timestamp_format: str = ""
    old_speaker_format: str = ""
    timestamp_format: str = ""
    speaker_format: str = ""
    event_id: str = field(default_factory=_uuid)
    occurred_at: datetime = field(default_factory=_now)
