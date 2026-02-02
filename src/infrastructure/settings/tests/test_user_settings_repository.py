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
        from src.contexts.settings.core import UserSettings
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
        from src.contexts.settings.core import (
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
        from src.contexts.settings.core import UserSettings
        from src.infrastructure.settings import UserSettingsRepository

        # Use a nested path
        nested_path = temp_config_path.parent / "nested" / "dir" / "settings.json"
        repo = UserSettingsRepository(config_path=nested_path)

        repo.save(UserSettings.default())

        assert nested_path.exists()

    def test_round_trip_preserves_all_settings(self, temp_config_path):
        """Should preserve all settings through save and load."""
        from src.contexts.settings.core import (
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
        from src.contexts.settings.core import ThemePreference
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
        from src.contexts.settings.core import FontPreference
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
        from src.contexts.settings.core import LanguagePreference
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
        from src.contexts.settings.core import BackupConfig
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
        from src.contexts.settings.core import AVCodingConfig
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


class TestUserSettingsRepositoryRecentProjects:
    """Tests for recent projects operations."""

    def test_get_recent_projects_returns_empty_list_when_no_file(
        self, temp_config_path
    ):
        """Should return empty list when no config file exists."""
        from src.infrastructure.settings import UserSettingsRepository

        repo = UserSettingsRepository(config_path=temp_config_path)
        projects = repo.get_recent_projects()

        assert projects == []

    def test_get_recent_projects_returns_empty_list_when_no_recent_projects_key(
        self, temp_config_path
    ):
        """Should return empty list when config has no recent_projects key."""
        from src.infrastructure.settings import UserSettingsRepository

        # Write config without recent_projects
        temp_config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(temp_config_path, "w") as f:
            json.dump({"theme": {"name": "dark"}}, f)

        repo = UserSettingsRepository(config_path=temp_config_path)
        projects = repo.get_recent_projects()

        assert projects == []

    def test_add_recent_project_creates_entry(self, temp_config_path):
        """Should add a new project to recent list."""
        from datetime import UTC, datetime

        from src.contexts.projects.core import RecentProject
        from src.infrastructure.settings import UserSettingsRepository

        repo = UserSettingsRepository(config_path=temp_config_path)
        project = RecentProject(
            path=Path("/projects/test.qda"),
            name="Test Project",
            last_opened=datetime(2024, 1, 15, 10, 30, tzinfo=UTC),
        )

        repo.add_recent_project(project)

        projects = repo.get_recent_projects()
        assert len(projects) == 1
        assert projects[0].path == Path("/projects/test.qda")
        assert projects[0].name == "Test Project"
        assert projects[0].last_opened == datetime(2024, 1, 15, 10, 30, tzinfo=UTC)

    def test_add_recent_project_updates_existing_by_path(self, temp_config_path):
        """Should update existing project when path matches."""
        from datetime import UTC, datetime

        from src.contexts.projects.core import RecentProject
        from src.infrastructure.settings import UserSettingsRepository

        repo = UserSettingsRepository(config_path=temp_config_path)

        # Add initial project
        project1 = RecentProject(
            path=Path("/projects/test.qda"),
            name="Old Name",
            last_opened=datetime(2024, 1, 15, tzinfo=UTC),
        )
        repo.add_recent_project(project1)

        # Update same path with new name and timestamp
        project2 = RecentProject(
            path=Path("/projects/test.qda"),
            name="New Name",
            last_opened=datetime(2024, 1, 20, tzinfo=UTC),
        )
        repo.add_recent_project(project2)

        projects = repo.get_recent_projects()
        assert len(projects) == 1
        assert projects[0].name == "New Name"
        assert projects[0].last_opened == datetime(2024, 1, 20, tzinfo=UTC)

    def test_add_recent_project_orders_by_last_opened_descending(
        self, temp_config_path
    ):
        """Should keep projects ordered with most recent first."""
        from datetime import UTC, datetime

        from src.contexts.projects.core import RecentProject
        from src.infrastructure.settings import UserSettingsRepository

        repo = UserSettingsRepository(config_path=temp_config_path)

        # Add projects out of order
        repo.add_recent_project(
            RecentProject(
                path=Path("/projects/middle.qda"),
                name="Middle",
                last_opened=datetime(2024, 1, 15, tzinfo=UTC),
            )
        )
        repo.add_recent_project(
            RecentProject(
                path=Path("/projects/oldest.qda"),
                name="Oldest",
                last_opened=datetime(2024, 1, 10, tzinfo=UTC),
            )
        )
        repo.add_recent_project(
            RecentProject(
                path=Path("/projects/newest.qda"),
                name="Newest",
                last_opened=datetime(2024, 1, 20, tzinfo=UTC),
            )
        )

        projects = repo.get_recent_projects()
        assert len(projects) == 3
        assert projects[0].name == "Newest"
        assert projects[1].name == "Middle"
        assert projects[2].name == "Oldest"

    def test_add_recent_project_enforces_max_limit(self, temp_config_path):
        """Should remove oldest projects when exceeding max limit."""
        from datetime import UTC, datetime, timedelta

        from src.contexts.projects.core import RecentProject
        from src.infrastructure.settings import UserSettingsRepository

        repo = UserSettingsRepository(config_path=temp_config_path)

        # Add 12 projects (exceeds limit of 10)
        base_time = datetime(2024, 1, 1, tzinfo=UTC)
        for i in range(12):
            repo.add_recent_project(
                RecentProject(
                    path=Path(f"/projects/project{i}.qda"),
                    name=f"Project {i}",
                    last_opened=base_time + timedelta(days=i),
                )
            )

        projects = repo.get_recent_projects()
        assert len(projects) == 10

        # Should have kept the 10 most recent (indices 2-11)
        project_names = [p.name for p in projects]
        assert "Project 0" not in project_names
        assert "Project 1" not in project_names
        assert "Project 11" in project_names

    def test_remove_recent_project_by_path(self, temp_config_path):
        """Should remove project matching the given path."""
        from datetime import UTC, datetime

        from src.contexts.projects.core import RecentProject
        from src.infrastructure.settings import UserSettingsRepository

        repo = UserSettingsRepository(config_path=temp_config_path)

        # Add two projects
        repo.add_recent_project(
            RecentProject(
                path=Path("/projects/keep.qda"),
                name="Keep",
                last_opened=datetime(2024, 1, 15, tzinfo=UTC),
            )
        )
        repo.add_recent_project(
            RecentProject(
                path=Path("/projects/remove.qda"),
                name="Remove",
                last_opened=datetime(2024, 1, 20, tzinfo=UTC),
            )
        )

        repo.remove_recent_project(Path("/projects/remove.qda"))

        projects = repo.get_recent_projects()
        assert len(projects) == 1
        assert projects[0].name == "Keep"

    def test_remove_recent_project_no_op_if_not_found(self, temp_config_path):
        """Should not error when removing non-existent path."""
        from datetime import UTC, datetime

        from src.contexts.projects.core import RecentProject
        from src.infrastructure.settings import UserSettingsRepository

        repo = UserSettingsRepository(config_path=temp_config_path)

        repo.add_recent_project(
            RecentProject(
                path=Path("/projects/exists.qda"),
                name="Exists",
                last_opened=datetime(2024, 1, 15, tzinfo=UTC),
            )
        )

        # Should not raise
        repo.remove_recent_project(Path("/projects/not_exists.qda"))

        projects = repo.get_recent_projects()
        assert len(projects) == 1

    def test_get_recent_projects_handles_corrupted_entry(self, temp_config_path):
        """Should skip malformed entries and return valid ones."""
        from src.infrastructure.settings import UserSettingsRepository

        # Write config with mixed valid and invalid entries
        config_data = {
            "recent_projects": [
                {
                    "path": "/projects/valid.qda",
                    "name": "Valid",
                    "last_opened": "2024-01-15T10:00:00+00:00",
                },
                {"path": "/projects/missing_name.qda"},  # Missing required fields
                {
                    "path": "/projects/invalid_date.qda",
                    "name": "Invalid Date",
                    "last_opened": "not-a-date",
                },
                {
                    "path": "/projects/valid2.qda",
                    "name": "Valid 2",
                    "last_opened": "2024-01-20T10:00:00+00:00",
                },
            ]
        }
        temp_config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(temp_config_path, "w") as f:
            json.dump(config_data, f)

        repo = UserSettingsRepository(config_path=temp_config_path)
        projects = repo.get_recent_projects()

        # Should only have the two valid entries
        assert len(projects) == 2
        names = [p.name for p in projects]
        assert "Valid" in names
        assert "Valid 2" in names

    def test_recent_projects_preserves_other_settings(self, temp_config_path):
        """Should not overwrite other settings when saving recent projects."""
        from datetime import UTC, datetime

        from src.contexts.projects.core import RecentProject
        from src.contexts.settings.core import ThemePreference
        from src.infrastructure.settings import UserSettingsRepository

        repo = UserSettingsRepository(config_path=temp_config_path)

        # Set theme first
        repo.set_theme(ThemePreference(name="dark"))

        # Add a recent project
        repo.add_recent_project(
            RecentProject(
                path=Path("/projects/test.qda"),
                name="Test",
                last_opened=datetime(2024, 1, 15, tzinfo=UTC),
            )
        )

        # Theme should still be dark
        assert repo.get_theme().name == "dark"

        # Recent projects should be present
        projects = repo.get_recent_projects()
        assert len(projects) == 1

    def test_round_trip_preserves_recent_projects(self, temp_config_path):
        """Should preserve recent projects through save and reload."""
        from datetime import UTC, datetime

        from src.contexts.projects.core import RecentProject
        from src.infrastructure.settings import UserSettingsRepository

        repo = UserSettingsRepository(config_path=temp_config_path)

        original = RecentProject(
            path=Path("/projects/roundtrip.qda"),
            name="Round Trip Test",
            last_opened=datetime(2024, 6, 15, 14, 30, 45, tzinfo=UTC),
        )
        repo.add_recent_project(original)

        # Create new repo instance (simulates app restart)
        repo2 = UserSettingsRepository(config_path=temp_config_path)
        projects = repo2.get_recent_projects()

        assert len(projects) == 1
        loaded = projects[0]
        assert loaded.path == original.path
        assert loaded.name == original.name
        assert loaded.last_opened == original.last_opened
