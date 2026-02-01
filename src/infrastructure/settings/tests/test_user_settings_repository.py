"""
Settings Infrastructure: Repository Tests

Tests for UserSettingsRepository file-based persistence.
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

pytestmark = pytest.mark.unit


@pytest.fixture
def temp_config_path():
    """Create a temporary config file path."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir) / "settings.json"


class TestUserSettingsRepositoryLoad:
    """Tests for loading settings."""

    def test_returns_default_settings_when_file_not_exists(self, temp_config_path):
        """Should return default settings when config file doesn't exist."""
        from src.domain.settings.entities import UserSettings
        from src.infrastructure.settings import UserSettingsRepository

        repo = UserSettingsRepository(config_path=temp_config_path)
        settings = repo.load()

        assert isinstance(settings, UserSettings)
        assert settings.theme.name == "light"
        assert settings.font.family == "Inter"
        assert settings.font.size == 14

    def test_loads_settings_from_existing_file(self, temp_config_path):
        """Should load settings from existing JSON file."""
        from src.infrastructure.settings import UserSettingsRepository

        # Write config file
        config_data = {
            "theme": {"name": "dark"},
            "font": {"family": "Roboto", "size": 16},
            "language": {"code": "es", "name": "Español"},
            "backup": {
                "enabled": True,
                "interval_minutes": 60,
                "max_backups": 10,
                "backup_path": "/backups",
            },
            "av_coding": {
                "timestamp_format": "MM:SS",
                "speaker_format": "P{n}",
            },
        }
        temp_config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(temp_config_path, "w") as f:
            json.dump(config_data, f)

        repo = UserSettingsRepository(config_path=temp_config_path)
        settings = repo.load()

        assert settings.theme.name == "dark"
        assert settings.font.family == "Roboto"
        assert settings.font.size == 16
        assert settings.language.code == "es"
        assert settings.backup.enabled is True
        assert settings.backup.interval_minutes == 60
        assert settings.av_coding.timestamp_format == "MM:SS"
        assert settings.av_coding.speaker_format == "P{n}"

    def test_returns_defaults_for_corrupted_file(self, temp_config_path):
        """Should return defaults when file contains invalid JSON."""
        from src.infrastructure.settings import UserSettingsRepository

        temp_config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(temp_config_path, "w") as f:
            f.write("not valid json {")

        repo = UserSettingsRepository(config_path=temp_config_path)
        settings = repo.load()

        # Should return defaults without raising
        assert settings.theme.name == "light"

    def test_handles_partial_config(self, temp_config_path):
        """Should use defaults for missing config sections."""
        from src.infrastructure.settings import UserSettingsRepository

        # Write partial config
        config_data = {"theme": {"name": "dark"}}
        temp_config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(temp_config_path, "w") as f:
            json.dump(config_data, f)

        repo = UserSettingsRepository(config_path=temp_config_path)
        settings = repo.load()

        assert settings.theme.name == "dark"
        # Other settings should have defaults
        assert settings.font.family == "Inter"
        assert settings.language.code == "en"


class TestUserSettingsRepositorySave:
    """Tests for saving settings."""

    def test_saves_settings_to_file(self, temp_config_path):
        """Should persist settings to JSON file."""
        from src.domain.settings.entities import (
            FontPreference,
            ThemePreference,
            UserSettings,
        )
        from src.infrastructure.settings import UserSettingsRepository

        repo = UserSettingsRepository(config_path=temp_config_path)

        settings = (
            UserSettings.default()
            .with_theme(ThemePreference(name="dark"))
            .with_font(FontPreference(family="Roboto", size=18))
        )

        repo.save(settings)

        # Verify file contents
        with open(temp_config_path) as f:
            data = json.load(f)

        assert data["theme"]["name"] == "dark"
        assert data["font"]["family"] == "Roboto"
        assert data["font"]["size"] == 18

    def test_creates_parent_directories(self, temp_config_path):
        """Should create parent directories if they don't exist."""
        from src.domain.settings.entities import UserSettings
        from src.infrastructure.settings import UserSettingsRepository

        # Use a nested path
        nested_path = temp_config_path.parent / "nested" / "dir" / "settings.json"
        repo = UserSettingsRepository(config_path=nested_path)

        repo.save(UserSettings.default())

        assert nested_path.exists()

    def test_round_trip_preserves_all_settings(self, temp_config_path):
        """Should preserve all settings through save and load."""
        from src.domain.settings.entities import (
            AVCodingConfig,
            BackupConfig,
            FontPreference,
            LanguagePreference,
            ThemePreference,
            UserSettings,
        )
        from src.infrastructure.settings import UserSettingsRepository

        repo = UserSettingsRepository(config_path=temp_config_path)

        original = UserSettings(
            theme=ThemePreference(name="dark"),
            font=FontPreference(family="JetBrains Mono", size=12),
            language=LanguagePreference(code="de", name="Deutsch"),
            backup=BackupConfig(
                enabled=True,
                interval_minutes=45,
                max_backups=7,
                backup_path="/custom/path",
            ),
            av_coding=AVCodingConfig(
                timestamp_format="HH:MM:SS.mmm",
                speaker_format="Interviewee {n}",
            ),
        )

        repo.save(original)
        loaded = repo.load()

        assert loaded.theme.name == original.theme.name
        assert loaded.font.family == original.font.family
        assert loaded.font.size == original.font.size
        assert loaded.language.code == original.language.code
        assert loaded.language.name == original.language.name
        assert loaded.backup.enabled == original.backup.enabled
        assert loaded.backup.interval_minutes == original.backup.interval_minutes
        assert loaded.backup.max_backups == original.backup.max_backups
        assert loaded.backup.backup_path == original.backup.backup_path
        assert loaded.av_coding.timestamp_format == original.av_coding.timestamp_format
        assert loaded.av_coding.speaker_format == original.av_coding.speaker_format


class TestUserSettingsRepositoryTheme:
    """Tests for theme-specific operations."""

    def test_get_theme(self, temp_config_path):
        """Should return current theme preference."""
        from src.infrastructure.settings import UserSettingsRepository

        repo = UserSettingsRepository(config_path=temp_config_path)
        theme = repo.get_theme()

        assert theme.name == "light"

    def test_set_theme(self, temp_config_path):
        """Should persist theme change."""
        from src.domain.settings.entities import ThemePreference
        from src.infrastructure.settings import UserSettingsRepository

        repo = UserSettingsRepository(config_path=temp_config_path)

        repo.set_theme(ThemePreference(name="dark"))

        assert repo.get_theme().name == "dark"
        # Other settings should be unchanged
        assert repo.get_font().family == "Inter"


class TestUserSettingsRepositoryFont:
    """Tests for font-specific operations."""

    def test_get_font(self, temp_config_path):
        """Should return current font preference."""
        from src.infrastructure.settings import UserSettingsRepository

        repo = UserSettingsRepository(config_path=temp_config_path)
        font = repo.get_font()

        assert font.family == "Inter"
        assert font.size == 14

    def test_set_font(self, temp_config_path):
        """Should persist font change."""
        from src.domain.settings.entities import FontPreference
        from src.infrastructure.settings import UserSettingsRepository

        repo = UserSettingsRepository(config_path=temp_config_path)

        repo.set_font(FontPreference(family="Fira Code", size=16))

        font = repo.get_font()
        assert font.family == "Fira Code"
        assert font.size == 16


class TestUserSettingsRepositoryLanguage:
    """Tests for language-specific operations."""

    def test_get_language(self, temp_config_path):
        """Should return current language preference."""
        from src.infrastructure.settings import UserSettingsRepository

        repo = UserSettingsRepository(config_path=temp_config_path)
        language = repo.get_language()

        assert language.code == "en"
        assert language.name == "English"

    def test_set_language(self, temp_config_path):
        """Should persist language change."""
        from src.domain.settings.entities import LanguagePreference
        from src.infrastructure.settings import UserSettingsRepository

        repo = UserSettingsRepository(config_path=temp_config_path)

        repo.set_language(LanguagePreference(code="fr", name="Français"))

        language = repo.get_language()
        assert language.code == "fr"
        assert language.name == "Français"


class TestUserSettingsRepositoryBackup:
    """Tests for backup-specific operations."""

    def test_get_backup_config(self, temp_config_path):
        """Should return current backup configuration."""
        from src.infrastructure.settings import UserSettingsRepository

        repo = UserSettingsRepository(config_path=temp_config_path)
        backup = repo.get_backup_config()

        assert backup.enabled is False
        assert backup.interval_minutes == 30
        assert backup.max_backups == 5

    def test_set_backup_config(self, temp_config_path):
        """Should persist backup config change."""
        from src.domain.settings.entities import BackupConfig
        from src.infrastructure.settings import UserSettingsRepository

        repo = UserSettingsRepository(config_path=temp_config_path)

        repo.set_backup_config(
            BackupConfig(
                enabled=True,
                interval_minutes=60,
                max_backups=10,
                backup_path="/my/backups",
            )
        )

        backup = repo.get_backup_config()
        assert backup.enabled is True
        assert backup.interval_minutes == 60
        assert backup.max_backups == 10
        assert backup.backup_path == "/my/backups"


class TestUserSettingsRepositoryAVCoding:
    """Tests for AV coding-specific operations."""

    def test_get_av_coding_config(self, temp_config_path):
        """Should return current AV coding configuration."""
        from src.infrastructure.settings import UserSettingsRepository

        repo = UserSettingsRepository(config_path=temp_config_path)
        av = repo.get_av_coding_config()

        assert av.timestamp_format == "HH:MM:SS"
        assert av.speaker_format == "Speaker {n}"

    def test_set_av_coding_config(self, temp_config_path):
        """Should persist AV coding config change."""
        from src.domain.settings.entities import AVCodingConfig
        from src.infrastructure.settings import UserSettingsRepository

        repo = UserSettingsRepository(config_path=temp_config_path)

        repo.set_av_coding_config(
            AVCodingConfig(
                timestamp_format="MM:SS",
                speaker_format="Participant {n}",
            )
        )

        av = repo.get_av_coding_config()
        assert av.timestamp_format == "MM:SS"
        assert av.speaker_format == "Participant {n}"
