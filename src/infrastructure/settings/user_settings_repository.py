"""
User Settings Repository - File-based Implementation.

Stores user-level settings in a JSON file in the platform-appropriate
config directory.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any

from src.domain.settings.entities import (
    AVCodingConfig,
    BackupConfig,
    FontPreference,
    LanguagePreference,
    ThemePreference,
    UserSettings,
)


class UserSettingsRepository:
    """
    Repository for user-level application settings.

    Stores settings in a JSON file in the user's config directory.
    Uses platform-appropriate paths:
    - Linux: ~/.config/qualcoder/settings.json
    - macOS: ~/Library/Application Support/QualCoder/settings.json
    - Windows: %APPDATA%/QualCoder/settings.json
    """

    def __init__(self, config_path: Path | None = None) -> None:
        """
        Initialize the repository.

        Args:
            config_path: Optional custom path for settings file.
                        If not provided, uses platform default.
        """
        self._config_path = config_path or self._get_default_path()
        self._ensure_config_dir()

    def _get_default_path(self) -> Path:
        """Get platform-appropriate config path."""
        if sys.platform == "linux":
            config_dir = Path.home() / ".config" / "qualcoder"
        elif sys.platform == "darwin":
            config_dir = Path.home() / "Library" / "Application Support" / "QualCoder"
        else:  # Windows
            appdata = os.environ.get("APPDATA", str(Path.home()))
            config_dir = Path(appdata) / "QualCoder"

        return config_dir / "settings.json"

    def _ensure_config_dir(self) -> None:
        """Ensure the config directory exists."""
        self._config_path.parent.mkdir(parents=True, exist_ok=True)

    # =========================================================================
    # Core Operations
    # =========================================================================

    def load(self) -> UserSettings:
        """
        Load settings from file or return defaults.

        Returns:
            UserSettings with loaded values or defaults if file doesn't exist
        """
        if not self._config_path.exists():
            return UserSettings.default()

        try:
            with open(self._config_path, encoding="utf-8") as f:
                data = json.load(f)
            return self._from_dict(data)
        except (json.JSONDecodeError, KeyError, TypeError):
            # Return defaults if file is corrupted
            return UserSettings.default()

    def save(self, settings: UserSettings) -> bool:
        """
        Persist settings to file.

        Args:
            settings: UserSettings to save

        Returns:
            True if save succeeded, False if an error occurred
        """
        try:
            data = self._to_dict(settings)
            # Write to temp file first, then rename for atomic write
            temp_path = self._config_path.with_suffix(".tmp")
            with open(temp_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            temp_path.replace(self._config_path)
            return True
        except (PermissionError, OSError):
            # Log would go here in production
            return False

    # =========================================================================
    # Theme Operations
    # =========================================================================

    def get_theme(self) -> ThemePreference:
        """Get current theme preference."""
        return self.load().theme

    def set_theme(self, theme: ThemePreference) -> None:
        """Set theme preference."""
        settings = self.load()
        self.save(settings.with_theme(theme))

    # =========================================================================
    # Font Operations
    # =========================================================================

    def get_font(self) -> FontPreference:
        """Get current font preference."""
        return self.load().font

    def set_font(self, font: FontPreference) -> None:
        """Set font preference."""
        settings = self.load()
        self.save(settings.with_font(font))

    # =========================================================================
    # Language Operations
    # =========================================================================

    def get_language(self) -> LanguagePreference:
        """Get current language preference."""
        return self.load().language

    def set_language(self, language: LanguagePreference) -> None:
        """Set language preference."""
        settings = self.load()
        self.save(settings.with_language(language))

    # =========================================================================
    # Backup Operations
    # =========================================================================

    def get_backup_config(self) -> BackupConfig:
        """Get current backup configuration."""
        return self.load().backup

    def set_backup_config(self, backup: BackupConfig) -> None:
        """Set backup configuration."""
        settings = self.load()
        self.save(settings.with_backup(backup))

    # =========================================================================
    # AV Coding Operations
    # =========================================================================

    def get_av_coding_config(self) -> AVCodingConfig:
        """Get current AV coding configuration."""
        return self.load().av_coding

    def set_av_coding_config(self, av_coding: AVCodingConfig) -> None:
        """Set AV coding configuration."""
        settings = self.load()
        self.save(settings.with_av_coding(av_coding))

    # =========================================================================
    # Serialization
    # =========================================================================

    def _to_dict(self, settings: UserSettings) -> dict[str, Any]:
        """Convert UserSettings to dictionary for JSON serialization."""
        return {
            "theme": {
                "name": settings.theme.name,
            },
            "font": {
                "family": settings.font.family,
                "size": settings.font.size,
            },
            "language": {
                "code": settings.language.code,
                "name": settings.language.name,
            },
            "backup": {
                "enabled": settings.backup.enabled,
                "interval_minutes": settings.backup.interval_minutes,
                "max_backups": settings.backup.max_backups,
                "backup_path": settings.backup.backup_path,
            },
            "av_coding": {
                "timestamp_format": settings.av_coding.timestamp_format,
                "speaker_format": settings.av_coding.speaker_format,
            },
        }

    def _from_dict(self, data: dict[str, Any]) -> UserSettings:
        """Convert dictionary to UserSettings."""
        theme_data = data.get("theme", {})
        font_data = data.get("font", {})
        language_data = data.get("language", {})
        backup_data = data.get("backup", {})
        av_coding_data = data.get("av_coding", {})

        return UserSettings(
            theme=ThemePreference(
                name=theme_data.get("name", "light"),
            ),
            font=FontPreference(
                family=font_data.get("family", "Inter"),
                size=font_data.get("size", 14),
            ),
            language=LanguagePreference(
                code=language_data.get("code", "en"),
                name=language_data.get("name", "English"),
            ),
            backup=BackupConfig(
                enabled=backup_data.get("enabled", False),
                interval_minutes=backup_data.get("interval_minutes", 30),
                max_backups=backup_data.get("max_backups", 5),
                backup_path=backup_data.get("backup_path"),
            ),
            av_coding=AVCodingConfig(
                timestamp_format=av_coding_data.get("timestamp_format", "HH:MM:SS"),
                speaker_format=av_coding_data.get("speaker_format", "Speaker {n}"),
            ),
        )
