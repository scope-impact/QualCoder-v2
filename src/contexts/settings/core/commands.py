"""
Settings Commands - Application Layer

Command objects for settings operations.
"""

from __future__ import annotations

from dataclasses import dataclass

# =============================================================================
# Theme Commands
# =============================================================================


@dataclass(frozen=True)
class ChangeThemeCommand:
    """Command to change the application theme."""

    theme: str  # "light", "dark", "system"


# =============================================================================
# Font Commands
# =============================================================================


@dataclass(frozen=True)
class ChangeFontCommand:
    """Command to change font settings."""

    family: str
    size: int


# =============================================================================
# Language Commands
# =============================================================================


@dataclass(frozen=True)
class ChangeLanguageCommand:
    """Command to change the application language."""

    language_code: str


# =============================================================================
# Backup Commands
# =============================================================================


@dataclass(frozen=True)
class ConfigureBackupCommand:
    """Command to configure automatic backups."""

    enabled: bool
    interval_minutes: int
    max_backups: int
    backup_path: str | None = None


# =============================================================================
# AV Coding Commands
# =============================================================================


@dataclass(frozen=True)
class ConfigureAVCodingCommand:
    """Command to configure AV coding settings."""

    timestamp_format: str
    speaker_format: str


# =============================================================================
# Cloud Sync Commands
# =============================================================================


@dataclass(frozen=True)
class ConfigureCloudSyncCommand:
    """Command to configure cloud sync settings."""

    enabled: bool
    convex_url: str | None = None
