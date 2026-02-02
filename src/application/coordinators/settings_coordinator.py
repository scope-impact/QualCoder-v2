"""
Settings Coordinator - Global Settings Management.

Handles all settings-related operations. These are global operations
that don't require an open project.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from returns.result import Result

from src.application.coordinators.base import BaseCoordinator

if TYPE_CHECKING:
    from src.contexts.settings.core.entities import (
        AVCodingConfig,
        BackupConfig,
        FontPreference,
        LanguagePreference,
        ThemePreference,
        UserSettings,
    )


class SettingsCoordinator(BaseCoordinator):
    """
    Coordinator for settings operations.

    Manages:
    - Theme preferences
    - Font preferences
    - Language preferences
    - Backup configuration
    - AV coding configuration

    All settings operations are global (no project required).
    """

    # =========================================================================
    # Settings Commands
    # =========================================================================

    def change_theme(self, theme: str) -> Result:
        """
        Change the application theme.

        Args:
            theme: Theme name ("light", "dark", "system")

        Returns:
            Success with ThemeChanged event, or Failure with error
        """
        from src.application.settings.commands import ChangeThemeCommand
        from src.application.settings.usecases import change_theme

        command = ChangeThemeCommand(theme=theme)
        return change_theme(command, self.settings_repo, self.event_bus)

    def change_font(self, family: str, size: int) -> Result:
        """
        Change font settings.

        Args:
            family: Font family name
            size: Font size in pixels

        Returns:
            Success with FontChanged event, or Failure with error
        """
        from src.application.settings.commands import ChangeFontCommand
        from src.application.settings.usecases import change_font

        command = ChangeFontCommand(family=family, size=size)
        return change_font(command, self.settings_repo, self.event_bus)

    def change_language(self, language_code: str) -> Result:
        """
        Change the application language.

        Args:
            language_code: ISO 639-1 language code

        Returns:
            Success with LanguageChanged event, or Failure with error
        """
        from src.application.settings.commands import ChangeLanguageCommand
        from src.application.settings.usecases import change_language

        command = ChangeLanguageCommand(language_code=language_code)
        return change_language(command, self.settings_repo, self.event_bus)

    def configure_backup(
        self,
        enabled: bool,
        interval_minutes: int,
        max_backups: int,
        backup_path: str | None = None,
    ) -> Result:
        """
        Configure automatic backup settings.

        Args:
            enabled: Whether automatic backups are enabled
            interval_minutes: Backup interval in minutes
            max_backups: Maximum number of backups to keep
            backup_path: Optional custom backup path

        Returns:
            Success with BackupConfigChanged event, or Failure with error
        """
        from src.application.settings.commands import ConfigureBackupCommand
        from src.application.settings.usecases import configure_backup

        command = ConfigureBackupCommand(
            enabled=enabled,
            interval_minutes=interval_minutes,
            max_backups=max_backups,
            backup_path=backup_path,
        )
        return configure_backup(command, self.settings_repo, self.event_bus)

    def configure_av_coding(
        self,
        timestamp_format: str,
        speaker_format: str,
    ) -> Result:
        """
        Configure AV coding settings.

        Args:
            timestamp_format: Timestamp display format
            speaker_format: Speaker name format template

        Returns:
            Success with AVCodingConfigChanged event, or Failure with error
        """
        from src.application.settings.commands import ConfigureAVCodingCommand
        from src.application.settings.usecases import configure_av_coding

        command = ConfigureAVCodingCommand(
            timestamp_format=timestamp_format,
            speaker_format=speaker_format,
        )
        return configure_av_coding(command, self.settings_repo, self.event_bus)

    # =========================================================================
    # Settings Queries
    # =========================================================================

    def get_all_settings(self) -> UserSettings:
        """Get all current settings."""
        from src.application.settings.queries import get_all_settings

        return get_all_settings(self.settings_repo)

    def get_theme(self) -> ThemePreference:
        """Get current theme preference."""
        from src.application.settings.queries import get_theme

        return get_theme(self.settings_repo)

    def get_font(self) -> FontPreference:
        """Get current font preference."""
        from src.application.settings.queries import get_font

        return get_font(self.settings_repo)

    def get_language(self) -> LanguagePreference:
        """Get current language preference."""
        from src.application.settings.queries import get_language

        return get_language(self.settings_repo)

    def get_backup_config(self) -> BackupConfig:
        """Get current backup configuration."""
        from src.application.settings.queries import get_backup_config

        return get_backup_config(self.settings_repo)

    def get_av_coding_config(self) -> AVCodingConfig:
        """Get current AV coding configuration."""
        from src.application.settings.queries import get_av_coding_config

        return get_av_coding_config(self.settings_repo)
