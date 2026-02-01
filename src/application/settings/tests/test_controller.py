"""
Settings Application: Controller Tests

Tests for SettingsControllerImpl following 5-step controller pattern.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest
from returns.result import Failure, Success

pytestmark = pytest.mark.unit


@pytest.fixture
def temp_config_path():
    """Create a temporary config file path."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir) / "settings.json"


@pytest.fixture
def settings_repo(temp_config_path):
    """Create a settings repository with temp path."""
    from src.infrastructure.settings import UserSettingsRepository

    return UserSettingsRepository(config_path=temp_config_path)


@pytest.fixture
def controller(settings_repo):
    """Create a settings controller."""
    from src.application.settings import SettingsControllerImpl

    return SettingsControllerImpl(settings_repo=settings_repo)


class TestChangeTheme:
    """Tests for change_theme command."""

    def test_changes_theme_successfully(self, controller):
        """Should change theme and return success."""
        from src.application.settings import ChangeThemeCommand
        from src.domain.settings.events import ThemeChanged

        result = controller.change_theme(ChangeThemeCommand(theme="dark"))

        assert isinstance(result, Success)
        event = result.unwrap()
        assert isinstance(event, ThemeChanged)
        assert event.new_theme == "dark"

    def test_persists_theme_change(self, controller):
        """Should persist theme to repository."""
        from src.application.settings import ChangeThemeCommand

        controller.change_theme(ChangeThemeCommand(theme="dark"))

        theme = controller.get_theme()
        assert theme.name == "dark"

    def test_returns_failure_for_invalid_theme(self, controller):
        """Should return failure for invalid theme."""
        from src.application.settings import ChangeThemeCommand

        result = controller.change_theme(ChangeThemeCommand(theme="neon"))

        assert isinstance(result, Failure)


class TestChangeFont:
    """Tests for change_font command."""

    def test_changes_font_successfully(self, controller):
        """Should change font and return success."""
        from src.application.settings import ChangeFontCommand
        from src.domain.settings.events import FontChanged

        result = controller.change_font(ChangeFontCommand(family="Roboto", size=16))

        assert isinstance(result, Success)
        event = result.unwrap()
        assert isinstance(event, FontChanged)
        assert event.family == "Roboto"
        assert event.size == 16

    def test_persists_font_change(self, controller):
        """Should persist font to repository."""
        from src.application.settings import ChangeFontCommand

        controller.change_font(ChangeFontCommand(family="Roboto", size=18))

        font = controller.get_font()
        assert font.family == "Roboto"
        assert font.size == 18

    def test_returns_failure_for_invalid_font_family(self, controller):
        """Should return failure for invalid font family."""
        from src.application.settings import ChangeFontCommand

        result = controller.change_font(ChangeFontCommand(family="Comic Sans", size=14))

        assert isinstance(result, Failure)

    def test_returns_failure_for_invalid_font_size(self, controller):
        """Should return failure for invalid font size."""
        from src.application.settings import ChangeFontCommand

        result = controller.change_font(ChangeFontCommand(family="Inter", size=50))

        assert isinstance(result, Failure)


class TestChangeLanguage:
    """Tests for change_language command."""

    def test_changes_language_successfully(self, controller):
        """Should change language and return success."""
        from src.application.settings import ChangeLanguageCommand
        from src.domain.settings.events import LanguageChanged

        result = controller.change_language(ChangeLanguageCommand(language_code="es"))

        assert isinstance(result, Success)
        event = result.unwrap()
        assert isinstance(event, LanguageChanged)
        assert event.new_language == "es"

    def test_persists_language_change(self, controller):
        """Should persist language to repository."""
        from src.application.settings import ChangeLanguageCommand

        controller.change_language(ChangeLanguageCommand(language_code="de"))

        language = controller.get_language()
        assert language.code == "de"
        assert language.name == "Deutsch"

    def test_returns_failure_for_invalid_language(self, controller):
        """Should return failure for unsupported language."""
        from src.application.settings import ChangeLanguageCommand

        result = controller.change_language(ChangeLanguageCommand(language_code="xx"))

        assert isinstance(result, Failure)


class TestConfigureBackup:
    """Tests for configure_backup command."""

    def test_configures_backup_successfully(self, controller):
        """Should configure backup and return success."""
        from src.application.settings import ConfigureBackupCommand
        from src.domain.settings.events import BackupConfigChanged

        result = controller.configure_backup(
            ConfigureBackupCommand(
                enabled=True,
                interval_minutes=45,
                max_backups=8,
                backup_path="/my/backups",
            )
        )

        assert isinstance(result, Success)
        event = result.unwrap()
        assert isinstance(event, BackupConfigChanged)
        assert event.enabled is True
        assert event.interval_minutes == 45

    def test_persists_backup_config(self, controller):
        """Should persist backup config to repository."""
        from src.application.settings import ConfigureBackupCommand

        controller.configure_backup(
            ConfigureBackupCommand(
                enabled=True,
                interval_minutes=60,
                max_backups=10,
                backup_path=None,
            )
        )

        backup = controller.get_backup_config()
        assert backup.enabled is True
        assert backup.interval_minutes == 60
        assert backup.max_backups == 10

    def test_returns_failure_for_invalid_interval(self, controller):
        """Should return failure for invalid backup interval."""
        from src.application.settings import ConfigureBackupCommand

        result = controller.configure_backup(
            ConfigureBackupCommand(
                enabled=True,
                interval_minutes=1,  # Too small
                max_backups=5,
                backup_path=None,
            )
        )

        assert isinstance(result, Failure)


class TestConfigureAVCoding:
    """Tests for configure_av_coding command."""

    def test_configures_av_coding_successfully(self, controller):
        """Should configure AV coding and return success."""
        from src.application.settings import ConfigureAVCodingCommand
        from src.domain.settings.events import AVCodingConfigChanged

        result = controller.configure_av_coding(
            ConfigureAVCodingCommand(
                timestamp_format="MM:SS",
                speaker_format="Participant {n}",
            )
        )

        assert isinstance(result, Success)
        event = result.unwrap()
        assert isinstance(event, AVCodingConfigChanged)
        assert event.timestamp_format == "MM:SS"
        assert event.speaker_format == "Participant {n}"

    def test_persists_av_coding_config(self, controller):
        """Should persist AV coding config to repository."""
        from src.application.settings import ConfigureAVCodingCommand

        controller.configure_av_coding(
            ConfigureAVCodingCommand(
                timestamp_format="HH:MM:SS.mmm",
                speaker_format="S{n}",
            )
        )

        av = controller.get_av_coding_config()
        assert av.timestamp_format == "HH:MM:SS.mmm"
        assert av.speaker_format == "S{n}"

    def test_returns_failure_for_invalid_timestamp_format(self, controller):
        """Should return failure for invalid timestamp format."""
        from src.application.settings import ConfigureAVCodingCommand

        result = controller.configure_av_coding(
            ConfigureAVCodingCommand(
                timestamp_format="invalid",
                speaker_format="Speaker {n}",
            )
        )

        assert isinstance(result, Failure)

    def test_returns_failure_for_invalid_speaker_format(self, controller):
        """Should return failure for speaker format without {n}."""
        from src.application.settings import ConfigureAVCodingCommand

        result = controller.configure_av_coding(
            ConfigureAVCodingCommand(
                timestamp_format="HH:MM:SS",
                speaker_format="Speaker",  # Missing {n}
            )
        )

        assert isinstance(result, Failure)


class TestQueries:
    """Tests for query methods."""

    def test_get_current_settings(self, controller):
        """Should return all current settings."""
        from src.domain.settings.entities import UserSettings

        settings = controller.get_current_settings()

        assert isinstance(settings, UserSettings)
        assert settings.theme.name == "light"
        assert settings.font.family == "Inter"

    def test_get_theme(self, controller):
        """Should return current theme."""
        theme = controller.get_theme()

        assert theme.name == "light"

    def test_get_font(self, controller):
        """Should return current font."""
        font = controller.get_font()

        assert font.family == "Inter"
        assert font.size == 14

    def test_get_language(self, controller):
        """Should return current language."""
        language = controller.get_language()

        assert language.code == "en"

    def test_get_backup_config(self, controller):
        """Should return current backup config."""
        backup = controller.get_backup_config()

        assert backup.enabled is False
        assert backup.interval_minutes == 30

    def test_get_av_coding_config(self, controller):
        """Should return current AV coding config."""
        av = controller.get_av_coding_config()

        assert av.timestamp_format == "HH:MM:SS"
        assert av.speaker_format == "Speaker {n}"


class TestMultipleChanges:
    """Tests for multiple sequential changes."""

    def test_multiple_settings_changes_persist(self, controller):
        """Should persist multiple independent settings changes."""
        from src.application.settings import (
            ChangeFontCommand,
            ChangeLanguageCommand,
            ChangeThemeCommand,
        )

        controller.change_theme(ChangeThemeCommand(theme="dark"))
        controller.change_font(ChangeFontCommand(family="Roboto", size=16))
        controller.change_language(ChangeLanguageCommand(language_code="fr"))

        settings = controller.get_current_settings()
        assert settings.theme.name == "dark"
        assert settings.font.family == "Roboto"
        assert settings.font.size == 16
        assert settings.language.code == "fr"

    def test_failed_change_does_not_affect_other_settings(self, controller):
        """Should not modify other settings when one change fails."""
        from src.application.settings import ChangeFontCommand, ChangeThemeCommand

        # First, set theme successfully
        controller.change_theme(ChangeThemeCommand(theme="dark"))

        # Then try invalid font change
        result = controller.change_font(
            ChangeFontCommand(family="Invalid Font", size=14)
        )
        assert isinstance(result, Failure)

        # Theme should still be dark
        settings = controller.get_current_settings()
        assert settings.theme.name == "dark"
        # Font should still be default
        assert settings.font.family == "Inter"
