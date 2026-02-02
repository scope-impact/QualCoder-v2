"""
Tests for Settings Use Cases

Tests the functional use cases for settings operations.
"""

import pytest
from returns.result import Failure, Success

from src.application.event_bus import EventBus
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
from src.contexts.settings.core.events import (
    AVCodingConfigChanged,
    BackupConfigChanged,
    FontChanged,
    LanguageChanged,
    ThemeChanged,
)
from src.contexts.settings.infra import UserSettingsRepository


@pytest.fixture
def settings_repo(tmp_path):
    """Create a settings repository with temp config path."""
    config_path = tmp_path / "settings.json"
    return UserSettingsRepository(config_path=config_path)


@pytest.fixture
def event_bus():
    """Create an event bus for testing."""
    return EventBus(history_size=100)


class TestChangeThemeUseCase:
    """Tests for change_theme use case."""

    def test_change_to_dark_theme_succeeds(self, settings_repo, event_bus):
        """Changing to valid dark theme succeeds."""
        command = ChangeThemeCommand(theme="dark")

        result = change_theme(command, settings_repo, event_bus)

        assert isinstance(result, Success)
        event = result.unwrap()
        assert isinstance(event, ThemeChanged)
        assert event.new_theme == "dark"

    def test_change_to_light_theme_succeeds(self, settings_repo, event_bus):
        """Changing to valid light theme succeeds."""
        # First set to dark
        settings_repo.set_theme(settings_repo.get_theme().with_name("dark"))

        command = ChangeThemeCommand(theme="light")
        result = change_theme(command, settings_repo, event_bus)

        assert isinstance(result, Success)
        assert result.unwrap().new_theme == "light"

    def test_change_to_system_theme_succeeds(self, settings_repo, event_bus):
        """Changing to valid system theme succeeds."""
        command = ChangeThemeCommand(theme="system")

        result = change_theme(command, settings_repo, event_bus)

        assert isinstance(result, Success)
        assert result.unwrap().new_theme == "system"

    def test_invalid_theme_fails(self, settings_repo, event_bus):
        """Changing to invalid theme fails."""
        command = ChangeThemeCommand(theme="invalid")

        result = change_theme(command, settings_repo, event_bus)

        assert isinstance(result, Failure)
        assert "invalid" in result.failure().lower()

    def test_publishes_event_to_bus(self, settings_repo, event_bus):
        """Change publishes ThemeChanged event to bus."""
        received_events = []
        event_bus.subscribe_type(ThemeChanged, received_events.append)

        command = ChangeThemeCommand(theme="dark")
        change_theme(command, settings_repo, event_bus)

        assert len(received_events) == 1
        assert received_events[0].new_theme == "dark"

    def test_persists_to_repository(self, settings_repo, event_bus):
        """Change persists new theme to repository."""
        command = ChangeThemeCommand(theme="dark")

        change_theme(command, settings_repo, event_bus)

        assert settings_repo.get_theme().name == "dark"

    def test_works_without_event_bus(self, settings_repo):
        """Change works when event_bus is None."""
        command = ChangeThemeCommand(theme="dark")

        result = change_theme(command, settings_repo, event_bus=None)

        assert isinstance(result, Success)


class TestChangeFontUseCase:
    """Tests for change_font use case."""

    def test_change_font_succeeds(self, settings_repo, event_bus):
        """Changing to valid font succeeds."""
        command = ChangeFontCommand(family="Fira Code", size=16)

        result = change_font(command, settings_repo, event_bus)

        assert isinstance(result, Success)
        event = result.unwrap()
        assert isinstance(event, FontChanged)
        assert event.family == "Fira Code"
        assert event.size == 16

    def test_invalid_font_size_fails(self, settings_repo, event_bus):
        """Changing to invalid font size fails."""
        command = ChangeFontCommand(family="Inter", size=5)  # Too small

        result = change_font(command, settings_repo, event_bus)

        assert isinstance(result, Failure)

    def test_persists_to_repository(self, settings_repo, event_bus):
        """Change persists new font to repository."""
        command = ChangeFontCommand(family="Fira Code", size=16)

        change_font(command, settings_repo, event_bus)

        font = settings_repo.get_font()
        assert font.family == "Fira Code"
        assert font.size == 16


class TestChangeLanguageUseCase:
    """Tests for change_language use case."""

    def test_change_language_succeeds(self, settings_repo, event_bus):
        """Changing to valid language succeeds."""
        command = ChangeLanguageCommand(language_code="de")

        result = change_language(command, settings_repo, event_bus)

        assert isinstance(result, Success)
        event = result.unwrap()
        assert isinstance(event, LanguageChanged)
        assert event.new_language == "de"

    def test_invalid_language_fails(self, settings_repo, event_bus):
        """Changing to invalid language code fails."""
        command = ChangeLanguageCommand(language_code="xyz")

        result = change_language(command, settings_repo, event_bus)

        assert isinstance(result, Failure)

    def test_persists_to_repository(self, settings_repo, event_bus):
        """Change persists new language to repository."""
        command = ChangeLanguageCommand(language_code="de")

        change_language(command, settings_repo, event_bus)

        language = settings_repo.get_language()
        assert language.code == "de"


class TestConfigureBackupUseCase:
    """Tests for configure_backup use case."""

    def test_configure_backup_succeeds(self, settings_repo, event_bus):
        """Configuring valid backup settings succeeds."""
        command = ConfigureBackupCommand(
            enabled=True,
            interval_minutes=30,
            max_backups=5,
            backup_path="/tmp/backups",
        )

        result = configure_backup(command, settings_repo, event_bus)

        assert isinstance(result, Success)
        event = result.unwrap()
        assert isinstance(event, BackupConfigChanged)
        assert event.enabled is True
        assert event.interval_minutes == 30

    def test_invalid_interval_fails(self, settings_repo, event_bus):
        """Configuring invalid interval fails."""
        command = ConfigureBackupCommand(
            enabled=True,
            interval_minutes=1,  # Too small
            max_backups=5,
        )

        result = configure_backup(command, settings_repo, event_bus)

        assert isinstance(result, Failure)

    def test_persists_to_repository(self, settings_repo, event_bus):
        """Configure persists backup config to repository."""
        command = ConfigureBackupCommand(
            enabled=True,
            interval_minutes=60,
            max_backups=10,
        )

        configure_backup(command, settings_repo, event_bus)

        backup = settings_repo.get_backup_config()
        assert backup.enabled is True
        assert backup.interval_minutes == 60
        assert backup.max_backups == 10


class TestConfigureAVCodingUseCase:
    """Tests for configure_av_coding use case."""

    def test_configure_av_coding_succeeds(self, settings_repo, event_bus):
        """Configuring valid AV coding settings succeeds."""
        command = ConfigureAVCodingCommand(
            timestamp_format="HH:MM:SS.mmm",
            speaker_format="Participant {n}",
        )

        result = configure_av_coding(command, settings_repo, event_bus)

        assert isinstance(result, Success)
        event = result.unwrap()
        assert isinstance(event, AVCodingConfigChanged)
        assert event.timestamp_format == "HH:MM:SS.mmm"
        assert event.speaker_format == "Participant {n}"

    def test_invalid_timestamp_format_fails(self, settings_repo, event_bus):
        """Configuring invalid timestamp format fails."""
        command = ConfigureAVCodingCommand(
            timestamp_format="invalid",
            speaker_format="Speaker {n}",
        )

        result = configure_av_coding(command, settings_repo, event_bus)

        assert isinstance(result, Failure)

    def test_invalid_speaker_format_fails(self, settings_repo, event_bus):
        """Configuring speaker format without placeholder fails."""
        command = ConfigureAVCodingCommand(
            timestamp_format="HH:MM:SS",
            speaker_format="No placeholder here",  # Missing {n}
        )

        result = configure_av_coding(command, settings_repo, event_bus)

        assert isinstance(result, Failure)

    def test_persists_to_repository(self, settings_repo, event_bus):
        """Configure persists AV coding config to repository."""
        command = ConfigureAVCodingCommand(
            timestamp_format="MM:SS",
            speaker_format="Speaker {n}",
        )

        configure_av_coding(command, settings_repo, event_bus)

        av_coding = settings_repo.get_av_coding_config()
        assert av_coding.timestamp_format == "MM:SS"
        assert av_coding.speaker_format == "Speaker {n}"
