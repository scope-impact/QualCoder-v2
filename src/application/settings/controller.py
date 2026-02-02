"""
Settings Controller - Application Service

Orchestrates domain operations for user settings management by:
1. Loading current settings from repository
2. Calling pure domain derivers
3. Persisting changes on success
4. Publishing domain events

This is the "Imperative Shell" that coordinates the "Functional Core".
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from returns.result import Failure, Result, Success

from src.application.settings.commands import (
    ChangeFontCommand,
    ChangeLanguageCommand,
    ChangeThemeCommand,
    ConfigureAVCodingCommand,
    ConfigureBackupCommand,
)
from src.domain.settings.derivers import (
    derive_av_coding_config_change,
    derive_backup_config_change,
    derive_font_change,
    derive_language_change,
    derive_theme_change,
)
from src.domain.settings.entities import (
    AVCodingConfig,
    BackupConfig,
    FontPreference,
    LanguagePreference,
    ThemePreference,
    UserSettings,
)
from src.domain.settings.events import (
    AVCodingConfigChanged,
    BackupConfigChanged,
    FontChanged,
    LanguageChanged,
    ThemeChanged,
)
from src.domain.settings.invariants import VALID_LANGUAGES

if TYPE_CHECKING:
    from src.application.event_bus import EventBus
    from src.infrastructure.settings import UserSettingsRepository


# =============================================================================
# Controller Implementation
# =============================================================================


class SettingsControllerImpl:
    """
    Implementation of the Settings Controller.

    Coordinates between:
    - Domain derivers (pure business logic)
    - Repository (settings persistence)
    - Event bus (event publishing)
    """

    def __init__(
        self,
        settings_repo: UserSettingsRepository,
        event_bus: EventBus | None = None,
    ) -> None:
        """
        Initialize the controller with dependencies.

        Args:
            settings_repo: Repository for user settings persistence
            event_bus: Optional event bus for publishing domain events
        """
        self._settings_repo = settings_repo
        self._event_bus = event_bus

    # =========================================================================
    # Theme Commands (AC #1)
    # =========================================================================

    def change_theme(self, command: ChangeThemeCommand) -> Result:
        """
        Change the application theme.

        Args:
            command: Command with new theme name

        Returns:
            Success with ThemeChanged event, or Failure with reason
        """
        # Step 1: Build current state
        current_settings = self._settings_repo.load()

        # Step 2: Derive event or failure
        result = derive_theme_change(
            new_theme=command.theme,
            current_settings=current_settings,
        )

        if isinstance(result, Failure):
            return result

        event: ThemeChanged = result

        # Step 3: Persist new theme
        new_theme = ThemePreference(name=command.theme)
        self._settings_repo.set_theme(new_theme)

        # Step 4: Publish event
        if self._event_bus:
            self._event_bus.publish(event)

        return Success(event)

    # =========================================================================
    # Font Commands (AC #2)
    # =========================================================================

    def change_font(self, command: ChangeFontCommand) -> Result:
        """
        Change font settings.

        Args:
            command: Command with font family and size

        Returns:
            Success with FontChanged event, or Failure with reason
        """
        # Step 1: Build current state
        current_settings = self._settings_repo.load()

        # Step 2: Derive event or failure
        result = derive_font_change(
            family=command.family,
            size=command.size,
            current_settings=current_settings,
        )

        if isinstance(result, Failure):
            return result

        event: FontChanged = result

        # Step 3: Persist new font
        new_font = FontPreference(family=command.family, size=command.size)
        self._settings_repo.set_font(new_font)

        # Step 4: Publish event
        if self._event_bus:
            self._event_bus.publish(event)

        return Success(event)

    # =========================================================================
    # Language Commands (AC #3)
    # =========================================================================

    def change_language(self, command: ChangeLanguageCommand) -> Result:
        """
        Change application language.

        Args:
            command: Command with language code

        Returns:
            Success with LanguageChanged event, or Failure with reason
        """
        # Step 1: Build current state
        current_settings = self._settings_repo.load()

        # Step 2: Derive event or failure
        result = derive_language_change(
            new_language_code=command.language_code,
            current_settings=current_settings,
        )

        if isinstance(result, Failure):
            return result

        event: LanguageChanged = result

        # Step 3: Persist new language
        language_name = VALID_LANGUAGES.get(command.language_code, "Unknown")
        new_language = LanguagePreference(
            code=command.language_code,
            name=language_name,
        )
        self._settings_repo.set_language(new_language)

        # Step 4: Publish event
        if self._event_bus:
            self._event_bus.publish(event)

        return Success(event)

    # =========================================================================
    # Backup Commands (AC #4)
    # =========================================================================

    def configure_backup(self, command: ConfigureBackupCommand) -> Result:
        """
        Configure automatic backup settings.

        Args:
            command: Command with backup configuration

        Returns:
            Success with BackupConfigChanged event, or Failure with reason
        """
        # Step 1: Build current state
        current_settings = self._settings_repo.load()

        # Step 2: Derive event or failure
        result = derive_backup_config_change(
            enabled=command.enabled,
            interval_minutes=command.interval_minutes,
            max_backups=command.max_backups,
            backup_path=command.backup_path,
            current_settings=current_settings,
        )

        if isinstance(result, Failure):
            return result

        event: BackupConfigChanged = result

        # Step 3: Persist new backup config
        new_backup = BackupConfig(
            enabled=command.enabled,
            interval_minutes=command.interval_minutes,
            max_backups=command.max_backups,
            backup_path=command.backup_path,
        )
        self._settings_repo.set_backup_config(new_backup)

        # Step 4: Publish event
        if self._event_bus:
            self._event_bus.publish(event)

        return Success(event)

    # =========================================================================
    # AV Coding Commands (AC #5, #6)
    # =========================================================================

    def configure_av_coding(self, command: ConfigureAVCodingCommand) -> Result:
        """
        Configure AV coding settings.

        Args:
            command: Command with timestamp format and speaker format

        Returns:
            Success with AVCodingConfigChanged event, or Failure with reason
        """
        # Step 1: Build current state
        current_settings = self._settings_repo.load()

        # Step 2: Derive event or failure
        result = derive_av_coding_config_change(
            timestamp_format=command.timestamp_format,
            speaker_format=command.speaker_format,
            current_settings=current_settings,
        )

        if isinstance(result, Failure):
            return result

        event: AVCodingConfigChanged = result

        # Step 3: Persist new AV coding config
        new_av_coding = AVCodingConfig(
            timestamp_format=command.timestamp_format,
            speaker_format=command.speaker_format,
        )
        self._settings_repo.set_av_coding_config(new_av_coding)

        # Step 4: Publish event
        if self._event_bus:
            self._event_bus.publish(event)

        return Success(event)

    # =========================================================================
    # Queries
    # =========================================================================

    def get_current_settings(self) -> UserSettings:
        """Get all current settings."""
        return self._settings_repo.load()

    def get_theme(self) -> ThemePreference:
        """Get current theme preference."""
        return self._settings_repo.get_theme()

    def get_font(self) -> FontPreference:
        """Get current font preference."""
        return self._settings_repo.get_font()

    def get_language(self) -> LanguagePreference:
        """Get current language preference."""
        return self._settings_repo.get_language()

    def get_backup_config(self) -> BackupConfig:
        """Get current backup configuration."""
        return self._settings_repo.get_backup_config()

    def get_av_coding_config(self) -> AVCodingConfig:
        """Get current AV coding configuration."""
        return self._settings_repo.get_av_coding_config()
