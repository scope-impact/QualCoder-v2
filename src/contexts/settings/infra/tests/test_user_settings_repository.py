"""
Settings Infrastructure: Repository Tests

Tests for UserSettingsRepository file-based persistence.
"""

from __future__ import annotations

import json
import tempfile
from datetime import UTC, datetime, timedelta
from pathlib import Path

import allure
import pytest

from src.contexts.settings.core.entities import (
    AVCodingConfig,
    BackupConfig,
    FontPreference,
    LanguagePreference,
    ThemePreference,
    UserSettings,
)
from src.contexts.settings.infra import UserSettingsRepository

pytestmark = [
    pytest.mark.unit,
    allure.epic("QualCoder v2"),
    allure.feature("QC-038 Settings and Preferences"),
]


@pytest.fixture
def temp_config_path():
    """Create a temporary config file path."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir) / "settings.json"


def _write_config(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f)


@allure.story("QC-035.01 User Settings")
class TestUserSettingsRepositoryLoad:
    """Tests for loading settings."""

    @allure.title("Returns defaults when file missing, corrupted, or partial")
    @pytest.mark.parametrize(
        "setup, expected_theme, expected_font",
        [
            pytest.param("missing", "light", "Inter", id="file-not-exists"),
            pytest.param("corrupted", "light", "Inter", id="corrupted-json"),
            pytest.param("partial", "dark", "Inter", id="partial-config"),
        ],
    )
    def test_returns_defaults_for_missing_or_bad_config(
        self, temp_config_path, setup, expected_theme, expected_font
    ):
        if setup == "corrupted":
            _write_config(temp_config_path, {})
            with open(temp_config_path, "w") as f:
                f.write("not valid json {")
        elif setup == "partial":
            _write_config(temp_config_path, {"theme": {"name": "dark"}})

        repo = UserSettingsRepository(config_path=temp_config_path)
        settings = repo.load()

        assert isinstance(settings, UserSettings)
        assert settings.theme.name == expected_theme
        assert settings.font.family == expected_font

    @allure.title("Loads all settings from existing JSON file")
    def test_loads_settings_from_existing_file(self, temp_config_path):
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
        _write_config(temp_config_path, config_data)

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


@allure.story("QC-035.01 User Settings")
class TestUserSettingsRepositorySave:
    """Tests for saving settings."""

    @allure.title("Saves settings, creates dirs, and round-trips all fields")
    def test_saves_and_round_trips_settings(self, temp_config_path):
        nested_path = temp_config_path.parent / "nested" / "dir" / "settings.json"
        repo = UserSettingsRepository(config_path=nested_path)

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

        # Verify file was created in nested directory
        assert nested_path.exists()
        with open(nested_path) as f:
            data = json.load(f)
        assert data["theme"]["name"] == "dark"
        assert data["font"]["family"] == "JetBrains Mono"
        assert data["font"]["size"] == 12

        # Round-trip: load back and verify all fields preserved
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


@allure.story("QC-035.01 User Settings")
class TestUserSettingsRepositorySubSettings:
    """Tests for individual settings get/set operations."""

    @allure.title(
        "Get and set individual sub-settings (theme, font, language, backup, av_coding)"
    )
    @pytest.mark.parametrize(
        "setting_type",
        [
            pytest.param("theme", id="theme"),
            pytest.param("font", id="font"),
            pytest.param("language", id="language"),
            pytest.param("backup", id="backup"),
            pytest.param("av_coding", id="av_coding"),
        ],
    )
    def test_sub_setting_get_set(self, temp_config_path, setting_type):
        repo = UserSettingsRepository(config_path=temp_config_path)

        if setting_type == "theme":
            assert repo.get_theme().name == "light"
            repo.set_theme(ThemePreference(name="dark"))
            assert repo.get_theme().name == "dark"
            assert repo.get_font().family == "Inter"  # other settings unchanged

        elif setting_type == "font":
            assert repo.get_font().family == "Inter"
            assert repo.get_font().size == 14
            repo.set_font(FontPreference(family="Fira Code", size=16))
            font = repo.get_font()
            assert font.family == "Fira Code"
            assert font.size == 16

        elif setting_type == "language":
            assert repo.get_language().code == "en"
            assert repo.get_language().name == "English"
            repo.set_language(LanguagePreference(code="fr", name="Français"))
            language = repo.get_language()
            assert language.code == "fr"
            assert language.name == "Français"

        elif setting_type == "backup":
            backup = repo.get_backup_config()
            assert backup.enabled is False
            assert backup.interval_minutes == 30
            assert backup.max_backups == 5
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

        elif setting_type == "av_coding":
            av = repo.get_av_coding_config()
            assert av.timestamp_format == "HH:MM:SS"
            assert av.speaker_format == "Speaker {n}"
            repo.set_av_coding_config(
                AVCodingConfig(
                    timestamp_format="MM:SS",
                    speaker_format="Participant {n}",
                )
            )
            av = repo.get_av_coding_config()
            assert av.timestamp_format == "MM:SS"
            assert av.speaker_format == "Participant {n}"


@allure.story("QC-035.01 User Settings")
class TestUserSettingsRepositoryRecentProjects:
    """Tests for recent projects operations."""

    @allure.title("Returns empty list when no file or no recent_projects key")
    @pytest.mark.parametrize(
        "setup",
        [
            pytest.param("no_file", id="no-file"),
            pytest.param("no_key", id="no-recent-projects-key"),
        ],
    )
    def test_get_recent_projects_returns_empty(self, temp_config_path, setup):
        if setup == "no_key":
            _write_config(temp_config_path, {"theme": {"name": "dark"}})

        repo = UserSettingsRepository(config_path=temp_config_path)
        assert repo.get_recent_projects() == []

    @allure.title("Add, update, order, and enforce max limit on recent projects")
    def test_add_update_order_and_limit_recent_projects(self, temp_config_path):
        from src.contexts.projects.core import RecentProject

        repo = UserSettingsRepository(config_path=temp_config_path)

        # Add initial project
        project1 = RecentProject(
            path=Path("/projects/test.qda"),
            name="Old Name",
            last_opened=datetime(2024, 1, 15, 10, 30, tzinfo=UTC),
        )
        repo.add_recent_project(project1)

        projects = repo.get_recent_projects()
        assert len(projects) == 1
        assert projects[0].path == Path("/projects/test.qda")
        assert projects[0].name == "Old Name"

        # Update same path with new name/timestamp
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

        # Add multiple projects and verify ordering (descending by last_opened)
        for name, day in [("Middle", 15), ("Oldest", 10), ("Newest", 20)]:
            repo.add_recent_project(
                RecentProject(
                    path=Path(f"/projects/{name.lower()}.qda"),
                    name=name,
                    last_opened=datetime(2024, 1, day, tzinfo=UTC),
                )
            )

        projects = repo.get_recent_projects()
        names = [p.name for p in projects]
        assert names.index("Newest") < names.index("Middle") < names.index("Oldest")

        # Enforce max limit (add 12 total, should keep only 10)
        repo2 = UserSettingsRepository(
            config_path=temp_config_path.parent / "limit.json"
        )
        base_time = datetime(2024, 1, 1, tzinfo=UTC)
        for i in range(12):
            repo2.add_recent_project(
                RecentProject(
                    path=Path(f"/projects/project{i}.qda"),
                    name=f"Project {i}",
                    last_opened=base_time + timedelta(days=i),
                )
            )

        projects = repo2.get_recent_projects()
        assert len(projects) == 10
        project_names = [p.name for p in projects]
        assert "Project 0" not in project_names
        assert "Project 1" not in project_names
        assert "Project 11" in project_names

    @allure.title(
        "Remove project, handle corrupted entries, and preserve settings on round trip"
    )
    def test_remove_corrupted_entries_and_round_trip(self, temp_config_path):
        from src.contexts.projects.core import RecentProject

        repo = UserSettingsRepository(config_path=temp_config_path)

        # Remove project by path (including no-op for missing)
        for name in ["Keep", "Remove"]:
            repo.add_recent_project(
                RecentProject(
                    path=Path(f"/projects/{name.lower()}.qda"),
                    name=name,
                    last_opened=datetime(2024, 1, 15, tzinfo=UTC),
                )
            )

        repo.remove_recent_project(Path("/projects/remove.qda"))
        projects = repo.get_recent_projects()
        assert len(projects) == 1
        assert projects[0].name == "Keep"

        # No-op for non-existent path
        repo.remove_recent_project(Path("/projects/not_exists.qda"))
        assert len(repo.get_recent_projects()) == 1

        # Handle corrupted entries gracefully
        corrupted_path = temp_config_path.parent / "corrupted.json"
        config_data = {
            "recent_projects": [
                {
                    "path": "/projects/valid.qda",
                    "name": "Valid",
                    "last_opened": "2024-01-15T10:00:00+00:00",
                },
                {"path": "/projects/missing_name.qda"},
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
        _write_config(corrupted_path, config_data)

        repo2 = UserSettingsRepository(config_path=corrupted_path)
        projects = repo2.get_recent_projects()
        assert len(projects) == 2
        names = [p.name for p in projects]
        assert "Valid" in names
        assert "Valid 2" in names

        # Round trip preserves other settings
        rt_path = temp_config_path.parent / "roundtrip.json"
        repo3 = UserSettingsRepository(config_path=rt_path)
        repo3.set_theme(ThemePreference(name="dark"))

        original = RecentProject(
            path=Path("/projects/roundtrip.qda"),
            name="Round Trip Test",
            last_opened=datetime(2024, 6, 15, 14, 30, 45, tzinfo=UTC),
        )
        repo3.add_recent_project(original)

        assert repo3.get_theme().name == "dark"

        # Simulate app restart
        repo4 = UserSettingsRepository(config_path=rt_path)
        projects = repo4.get_recent_projects()
        assert len(projects) == 1
        loaded = projects[0]
        assert loaded.path == original.path
        assert loaded.name == original.name
        assert loaded.last_opened == original.last_opened
