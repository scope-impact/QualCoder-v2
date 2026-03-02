"""
Settings Context: Failure Events

Publishable failure events for the settings bounded context.
These events can be published to the event bus and trigger policies.

Event naming convention: SETTINGS_NOT_CHANGED/{REASON}
"""

from __future__ import annotations

from dataclasses import dataclass

from src.shared.common.failure_events import FailureEvent


@dataclass(frozen=True)
class SettingsNotChanged(FailureEvent):
    """Failure event: Settings change failed."""

    value: str | None = None

    # =========================================================================
    # Theme Failures
    # =========================================================================

    @classmethod
    def invalid_theme(cls, theme: str) -> SettingsNotChanged:
        """Theme is not valid."""
        return cls(
            event_id=cls._generate_id(),
            occurred_at=cls._now(),
            event_type="SETTINGS_NOT_CHANGED/INVALID_THEME",
            value=theme,
        )

    # =========================================================================
    # Font Failures
    # =========================================================================

    @classmethod
    def invalid_font_family(cls, family: str) -> SettingsNotChanged:
        """Font family is not supported."""
        return cls(
            event_id=cls._generate_id(),
            occurred_at=cls._now(),
            event_type="SETTINGS_NOT_CHANGED/INVALID_FONT_FAMILY",
            value=family,
        )

    @classmethod
    def invalid_font_size(cls, size: int) -> SettingsNotChanged:
        """Font size is outside valid range."""
        return cls(
            event_id=cls._generate_id(),
            occurred_at=cls._now(),
            event_type="SETTINGS_NOT_CHANGED/INVALID_FONT_SIZE",
            value=str(size),
        )

    # =========================================================================
    # Language Failures
    # =========================================================================

    @classmethod
    def invalid_language(cls, code: str) -> SettingsNotChanged:
        """Language code is not supported."""
        return cls(
            event_id=cls._generate_id(),
            occurred_at=cls._now(),
            event_type="SETTINGS_NOT_CHANGED/INVALID_LANGUAGE",
            value=code,
        )

    # =========================================================================
    # Backup Failures
    # =========================================================================

    @classmethod
    def invalid_backup_interval(cls, interval: int) -> SettingsNotChanged:
        """Backup interval is outside valid range."""
        return cls(
            event_id=cls._generate_id(),
            occurred_at=cls._now(),
            event_type="SETTINGS_NOT_CHANGED/INVALID_BACKUP_INTERVAL",
            value=str(interval),
        )

    @classmethod
    def invalid_max_backups(cls, max_backups: int) -> SettingsNotChanged:
        """Max backups is outside valid range."""
        return cls(
            event_id=cls._generate_id(),
            occurred_at=cls._now(),
            event_type="SETTINGS_NOT_CHANGED/INVALID_MAX_BACKUPS",
            value=str(max_backups),
        )

    # =========================================================================
    # AV Coding Failures
    # =========================================================================

    @classmethod
    def invalid_timestamp_format(cls, fmt: str) -> SettingsNotChanged:
        """Timestamp format is not valid."""
        return cls(
            event_id=cls._generate_id(),
            occurred_at=cls._now(),
            event_type="SETTINGS_NOT_CHANGED/INVALID_TIMESTAMP_FORMAT",
            value=fmt,
        )

    @classmethod
    def invalid_speaker_format(cls, fmt: str) -> SettingsNotChanged:
        """Speaker format is not valid."""
        return cls(
            event_id=cls._generate_id(),
            occurred_at=cls._now(),
            event_type="SETTINGS_NOT_CHANGED/INVALID_SPEAKER_FORMAT",
            value=fmt,
        )

    # =========================================================================
    # Observability Failures
    # =========================================================================

    @classmethod
    def invalid_log_level(cls, level: str) -> SettingsNotChanged:
        """Log level is not valid."""
        return cls(
            event_id=cls._generate_id(),
            occurred_at=cls._now(),
            event_type="SETTINGS_NOT_CHANGED/INVALID_LOG_LEVEL",
            value=level,
        )

    # =========================================================================
    # Message
    # =========================================================================

    @property
    def message(self) -> str:
        """Human-readable error message."""
        match self.reason:
            case "INVALID_THEME":
                return f"Invalid theme '{self.value}'. Must be: light, dark, or system"
            case "INVALID_FONT_FAMILY":
                return f"Font family '{self.value}' is not supported"
            case "INVALID_FONT_SIZE":
                return f"Font size {self.value} is invalid. Must be between 10 and 24"
            case "INVALID_LANGUAGE":
                return f"Language code '{self.value}' is not supported"
            case "INVALID_BACKUP_INTERVAL":
                return f"Backup interval {self.value} minutes is invalid. Must be between 5 and 120"
            case "INVALID_MAX_BACKUPS":
                return f"Max backups {self.value} is invalid. Must be between 1 and 20"
            case "INVALID_TIMESTAMP_FORMAT":
                return f"Timestamp format '{self.value}' is invalid. Use HH:MM:SS, HH:MM:SS.mmm, or MM:SS"
            case "INVALID_SPEAKER_FORMAT":
                return f"Speaker format '{self.value}' must contain {{n}} placeholder"
            case "INVALID_LOG_LEVEL":
                return f"Log level '{self.value}' is invalid. Must be: DEBUG, INFO, WARNING, or ERROR"
            case _:
                return super().message


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
                "Cloud: https://<project>.convex.cloud",
                "Self-hosted: http://127.0.0.1:<port> or http://localhost:<port>",
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


__all__ = ["CloudSyncSettingsFailed", "SettingsNotChanged"]
