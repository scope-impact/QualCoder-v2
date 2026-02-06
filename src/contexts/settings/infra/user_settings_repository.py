"""
User Settings Repository - File-based Implementation.

Stores user-level settings in a JSON file in the platform-appropriate
config directory.
"""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

from src.contexts.projects.core import RecentProject
from src.contexts.settings.core.entities import (
    AVCodingConfig,
    BackendConfig,
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
    # Backend Operations
    # =========================================================================

    def get_backend_config(self) -> BackendConfig:
        """Get current backend configuration."""
        return self.load().backend

    def set_backend_config(self, backend: BackendConfig) -> None:
        """Set backend configuration."""
        settings = self.load()
        self.save(settings.with_backend(backend))

    def set_cloud_sync_enabled(self, enabled: bool) -> None:
        """Enable or disable cloud sync with Convex."""
        config = self.get_backend_config()
        self.set_backend_config(config.with_cloud_sync_enabled(enabled))

    def set_convex_url(self, convex_url: str | None) -> None:
        """Set the Convex deployment URL."""
        config = self.get_backend_config()
        self.set_backend_config(config.with_convex_url(convex_url))

    # =========================================================================
    # Recent Projects Operations
    # =========================================================================

    MAX_RECENT_PROJECTS = 10

    def get_recent_projects(self) -> list[RecentProject]:
        """
        Load recent projects from settings file.

        Returns:
            List of RecentProject entities ordered by last_opened (most recent first).
            Returns empty list if no recent projects or data is corrupt.
        """
        if not self._config_path.exists():
            return []

        try:
            with open(self._config_path, encoding="utf-8") as f:
                data = json.load(f)
            return self._recent_projects_from_list(data.get("recent_projects", []))
        except (json.JSONDecodeError, KeyError, TypeError, OSError):
            return []

    def add_recent_project(self, project: RecentProject) -> None:
        """
        Add or update a project in recent list.

        If the project already exists (by path), updates its last_opened timestamp.
        Maintains max 10 projects, removing oldest when limit exceeded.
        Projects are kept ordered by last_opened (most recent first).

        Args:
            project: RecentProject to add or update
        """
        projects = self.get_recent_projects()

        # Remove existing entry for this path if present
        projects = [p for p in projects if p.path != project.path]

        # Add the new/updated project
        projects.append(project)

        # Sort by last_opened descending (most recent first)
        projects.sort(key=lambda p: p.last_opened, reverse=True)

        # Keep only the most recent MAX_RECENT_PROJECTS
        projects = projects[: self.MAX_RECENT_PROJECTS]

        self._save_recent_projects(projects)

    def remove_recent_project(self, path: Path) -> None:
        """
        Remove a project from recent list.

        Args:
            path: Path of the project to remove
        """
        projects = self.get_recent_projects()
        projects = [p for p in projects if p.path != path]
        self._save_recent_projects(projects)

    def _save_recent_projects(self, projects: list[RecentProject]) -> None:
        """Save recent projects list to settings file."""
        # Load existing data or create empty dict
        data: dict[str, Any] = {}
        if self._config_path.exists():
            try:
                with open(self._config_path, encoding="utf-8") as f:
                    data = json.load(f)
            except (json.JSONDecodeError, OSError):
                data = {}

        # Update recent_projects in data
        data["recent_projects"] = self._recent_projects_to_list(projects)

        # Write atomically
        try:
            temp_path = self._config_path.with_suffix(".tmp")
            with open(temp_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            temp_path.replace(self._config_path)
        except (PermissionError, OSError):
            pass  # Silently fail; logging would go here in production

    def _recent_projects_to_list(
        self, projects: list[RecentProject]
    ) -> list[dict[str, Any]]:
        """Convert list of RecentProject to JSON-serializable list."""
        return [
            {
                "path": str(p.path),
                "name": p.name,
                "last_opened": p.last_opened.isoformat(),
            }
            for p in projects
        ]

    def _recent_projects_from_list(
        self, data: list[dict[str, Any]]
    ) -> list[RecentProject]:
        """Convert JSON list to list of RecentProject entities."""
        projects: list[RecentProject] = []
        for item in data:
            try:
                projects.append(
                    RecentProject(
                        path=Path(item["path"]),
                        name=item["name"],
                        last_opened=datetime.fromisoformat(item["last_opened"]),
                    )
                )
            except (KeyError, TypeError, ValueError):
                # Skip malformed entries
                continue

        # Sort by last_opened descending (most recent first)
        projects.sort(key=lambda p: p.last_opened, reverse=True)
        return projects

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
            "backend": {
                "cloud_sync_enabled": settings.backend.cloud_sync_enabled,
                "convex_url": settings.backend.convex_url,
                "convex_project_id": settings.backend.convex_project_id,
            },
        }

    def _from_dict(self, data: dict[str, Any]) -> UserSettings:
        """Convert dictionary to UserSettings."""
        theme_data = data.get("theme", {})
        font_data = data.get("font", {})
        language_data = data.get("language", {})
        backup_data = data.get("backup", {})
        av_coding_data = data.get("av_coding", {})
        backend_data = data.get("backend", {})

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
            backend=BackendConfig(
                cloud_sync_enabled=backend_data.get("cloud_sync_enabled", False),
                convex_url=backend_data.get("convex_url"),
                convex_project_id=backend_data.get("convex_project_id"),
            ),
        )
