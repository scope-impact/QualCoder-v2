"""
Settings Service - Settings Provider for SettingsViewModel.

Provides the SettingsProvider interface by calling use cases directly.
This replaces SettingsCoordinator for the settings dialog functionality.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from src.contexts.settings.core.commandHandlers import (
    change_font,
    change_language,
    change_theme,
    configure_av_coding,
    configure_backup,
    configure_observability,
)
from src.contexts.settings.core.commands import (
    ChangeFontCommand,
    ChangeLanguageCommand,
    ChangeThemeCommand,
    ConfigureAVCodingCommand,
    ConfigureBackupCommand,
    ConfigureObservabilityCommand,
)
from src.shared.common.operation_result import OperationResult

if TYPE_CHECKING:
    from src.contexts.settings.core.entities import UserSettings
    from src.contexts.settings.infra import UserSettingsRepository
    from src.shared.infra.event_bus import EventBus


class SettingsService:
    """
    Service implementing SettingsProvider protocol.

    Provides settings access by calling use cases directly.
    Used by SettingsViewModel to load and modify user settings.
    """

    def __init__(
        self,
        settings_repo: UserSettingsRepository,
        event_bus: EventBus,
    ) -> None:
        """
        Initialize the service.

        Args:
            settings_repo: Repository for persisting settings
            event_bus: Event bus for publishing domain events
        """
        self._settings_repo = settings_repo
        self._event_bus = event_bus

    def get_all_settings(self) -> UserSettings:
        """Get all current user settings."""
        return self._settings_repo.load()

    def change_theme(self, theme: str) -> OperationResult:
        """Change the UI theme."""
        command = ChangeThemeCommand(theme=theme)
        return change_theme(
            command=command,
            settings_repo=self._settings_repo,
            event_bus=self._event_bus,
        )

    def change_font(self, family: str, size: int) -> OperationResult:
        """Change font settings."""
        command = ChangeFontCommand(family=family, size=size)
        return change_font(
            command=command,
            settings_repo=self._settings_repo,
            event_bus=self._event_bus,
        )

    def change_language(self, language_code: str) -> OperationResult:
        """Change application language."""
        command = ChangeLanguageCommand(language_code=language_code)
        return change_language(
            command=command,
            settings_repo=self._settings_repo,
            event_bus=self._event_bus,
        )

    def configure_backup(
        self,
        enabled: bool,
        interval_minutes: int,
        max_backups: int,
        backup_path: str | None = None,
    ) -> OperationResult:
        """Configure backup settings."""
        command = ConfigureBackupCommand(
            enabled=enabled,
            interval_minutes=interval_minutes,
            max_backups=max_backups,
            backup_path=backup_path,
        )
        return configure_backup(
            command=command,
            settings_repo=self._settings_repo,
            event_bus=self._event_bus,
        )

    def configure_av_coding(
        self,
        timestamp_format: str,
        speaker_format: str,
    ) -> OperationResult:
        """Configure AV coding settings."""
        command = ConfigureAVCodingCommand(
            timestamp_format=timestamp_format,
            speaker_format=speaker_format,
        )
        return configure_av_coding(
            command=command,
            settings_repo=self._settings_repo,
            event_bus=self._event_bus,
        )

    def configure_observability(
        self,
        log_level: str,
        enable_file_logging: bool,
        enable_telemetry: bool,
    ) -> OperationResult:
        """Configure observability settings."""
        command = ConfigureObservabilityCommand(
            log_level=log_level,
            enable_file_logging=enable_file_logging,
            enable_telemetry=enable_telemetry,
        )
        return configure_observability(
            command=command,
            settings_repo=self._settings_repo,
            event_bus=self._event_bus,
        )
