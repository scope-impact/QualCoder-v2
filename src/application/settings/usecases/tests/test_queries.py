"""
Tests for Settings Queries

Tests the query functions for retrieving settings data.
"""

import pytest

from src.application.settings.queries import (
    get_all_settings,
    get_av_coding_config,
    get_backup_config,
    get_font,
    get_language,
    get_theme,
)
from src.contexts.settings.core.entities import (
    AVCodingConfig,
    BackupConfig,
    FontPreference,
    LanguagePreference,
    ThemePreference,
    UserSettings,
)
from src.contexts.settings.infra import UserSettingsRepository


@pytest.fixture
def settings_repo(tmp_path):
    """Create a settings repository with temp config path."""
    config_path = tmp_path / "settings.json"
    return UserSettingsRepository(config_path=config_path)


class TestGetAllSettings:
    """Tests for get_all_settings query."""

    def test_returns_user_settings(self, settings_repo):
        """Returns UserSettings object."""
        result = get_all_settings(settings_repo)

        assert isinstance(result, UserSettings)

    def test_returns_defaults_for_new_repo(self, settings_repo):
        """Returns default settings for new repository."""
        result = get_all_settings(settings_repo)

        assert result.theme.name == "light"
        assert result.font.family == "Inter"
        assert result.language.code == "en"


class TestGetTheme:
    """Tests for get_theme query."""

    def test_returns_theme_preference(self, settings_repo):
        """Returns ThemePreference object."""
        result = get_theme(settings_repo)

        assert isinstance(result, ThemePreference)

    def test_returns_default_theme(self, settings_repo):
        """Returns default light theme for new repository."""
        result = get_theme(settings_repo)

        assert result.name == "light"

    def test_returns_updated_theme(self, settings_repo):
        """Returns theme after it's been changed."""
        settings_repo.set_theme(ThemePreference(name="dark"))

        result = get_theme(settings_repo)

        assert result.name == "dark"


class TestGetFont:
    """Tests for get_font query."""

    def test_returns_font_preference(self, settings_repo):
        """Returns FontPreference object."""
        result = get_font(settings_repo)

        assert isinstance(result, FontPreference)

    def test_returns_default_font(self, settings_repo):
        """Returns default font for new repository."""
        result = get_font(settings_repo)

        assert result.family == "Inter"
        assert result.size == 14

    def test_returns_updated_font(self, settings_repo):
        """Returns font after it's been changed."""
        settings_repo.set_font(FontPreference(family="Fira Code", size=16))

        result = get_font(settings_repo)

        assert result.family == "Fira Code"
        assert result.size == 16


class TestGetLanguage:
    """Tests for get_language query."""

    def test_returns_language_preference(self, settings_repo):
        """Returns LanguagePreference object."""
        result = get_language(settings_repo)

        assert isinstance(result, LanguagePreference)

    def test_returns_default_language(self, settings_repo):
        """Returns default English for new repository."""
        result = get_language(settings_repo)

        assert result.code == "en"
        assert result.name == "English"


class TestGetBackupConfig:
    """Tests for get_backup_config query."""

    def test_returns_backup_config(self, settings_repo):
        """Returns BackupConfig object."""
        result = get_backup_config(settings_repo)

        assert isinstance(result, BackupConfig)

    def test_returns_default_backup_config(self, settings_repo):
        """Returns default backup config for new repository."""
        result = get_backup_config(settings_repo)

        assert result.enabled is False
        assert result.interval_minutes == 30
        assert result.max_backups == 5


class TestGetAVCodingConfig:
    """Tests for get_av_coding_config query."""

    def test_returns_av_coding_config(self, settings_repo):
        """Returns AVCodingConfig object."""
        result = get_av_coding_config(settings_repo)

        assert isinstance(result, AVCodingConfig)

    def test_returns_default_av_coding_config(self, settings_repo):
        """Returns default AV coding config for new repository."""
        result = get_av_coding_config(settings_repo)

        assert result.timestamp_format == "HH:MM:SS"
        assert result.speaker_format == "Speaker {n}"
