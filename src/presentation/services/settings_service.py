"""
Settings Service - Settings Provider for SettingsViewModel.

Provides the SettingsProvider interface by calling use cases directly.
This replaces SettingsCoordinator for the settings dialog functionality.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from returns.result import Result

from src.application.settings.commands import (
    ChangeFontCommand,
    ChangeLanguageCommand,
    ChangeThemeCommand,
    ConfigureAVCodingCommand,
    ConfigureBackupCommand,
)
from src.application.settings.usecases import (
    change_font,
    change_language,
    change_theme,
    configure_av_coding,
    configure_backup,
)

if TYPE_CHECKING:
    from src.contexts.settings.core.entities import UserSettings
    from src.contexts.settings.infra import UserSettingsRepository


class SettingsService:
    """
    Service implementing SettingsProvider protocol.

    Provides settings access by calling use cases directly.
    Used by SettingsViewModel to load and modify user settings.
    """

    def __init__(self, settings_repo: UserSettingsRepository) -> None:
        """
        Initialize the service.

        Args:
            settings_repo: Repository for persisting settings
        """
        self._settings_repo = settings_repo

    def get_all_settings(self) -> UserSettings:
        """Get all current user settings."""
        return self._settings_repo.load()

    def change_theme(self, theme: str) -> Result:
        """Change the UI theme."""
        command = ChangeThemeCommand(theme=theme)
        return change_theme(command=command, settings_repo=self._settings_repo)

    def change_font(self, family: str, size: int) -> Result:
        """Change font settings."""
        command = ChangeFontCommand(family=family, size=size)
        return change_font(command=command, settings_repo=self._settings_repo)

    def change_language(self, language_code: str) -> Result:
        """Change application language."""
        command = ChangeLanguageCommand(language_code=language_code)
        return change_language(command=command, settings_repo=self._settings_repo)

    def configure_backup(
        self,
        enabled: bool,
        interval_minutes: int,
        max_backups: int,
        backup_path: str | None = None,
    ) -> Result:
        """Configure backup settings."""
        command = ConfigureBackupCommand(
            enabled=enabled,
            interval_minutes=interval_minutes,
            max_backups=max_backups,
            backup_path=backup_path,
        )
        return configure_backup(command=command, settings_repo=self._settings_repo)

    def configure_av_coding(
        self,
        timestamp_format: str,
        speaker_format: str,
    ) -> Result:
        """Configure AV coding settings."""
        command = ConfigureAVCodingCommand(
            timestamp_format=timestamp_format,
            speaker_format=speaker_format,
        )
        return configure_av_coding(command=command, settings_repo=self._settings_repo)
