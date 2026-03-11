"""
Settings Context: Deriver Tests

Tests for pure functions that compose invariants and derive domain events.
"""

from __future__ import annotations

import allure
import pytest

from src.contexts.settings.core.derivers import (
    derive_av_coding_config_change,
    derive_backup_config_change,
    derive_font_change,
    derive_language_change,
    derive_theme_change,
)
from src.contexts.settings.core.entities import UserSettings
from src.contexts.settings.core.events import (
    AVCodingConfigChanged,
    BackupConfigChanged,
    FontChanged,
    LanguageChanged,
    ThemeChanged,
)
from src.contexts.settings.core.failure_events import SettingsNotChanged

pytestmark = [
    pytest.mark.unit,
    allure.epic("QualCoder v2"),
    allure.feature("QC-035 Settings"),
]


@allure.story("QC-035.02 Settings Derivers")
class TestDeriveThemeChange:
    """Tests for derive_theme_change deriver."""

    @allure.title("Valid theme changes produce ThemeChanged event")
    @pytest.mark.parametrize(
        "new_theme",
        [
            pytest.param("dark", id="dark"),
            pytest.param("system", id="system"),
        ],
    )
    def test_changes_theme_with_valid_input(self, new_theme):
        settings = UserSettings.default()
        result = derive_theme_change(new_theme=new_theme, current_settings=settings)

        assert isinstance(result, ThemeChanged)
        assert result.old_theme == "light"
        assert result.new_theme == new_theme

    @allure.title("Invalid theme name produces SettingsNotChanged")
    def test_fails_with_invalid_theme(self):
        settings = UserSettings.default()
        result = derive_theme_change(new_theme="neon", current_settings=settings)

        assert isinstance(result, SettingsNotChanged)
        assert result.reason == "INVALID_THEME"
        assert "neon" in result.message


@allure.story("QC-035.02 Settings Derivers")
class TestDeriveFontChange:
    """Tests for derive_font_change deriver."""

    @allure.title("Valid font settings produce FontChanged event")
    def test_changes_font_with_valid_inputs(self):
        settings = UserSettings.default()
        result = derive_font_change(family="Roboto", size=16, current_settings=settings)

        assert isinstance(result, FontChanged)
        assert result.family == "Roboto"
        assert result.size == 16

    @allure.title("Invalid font family or size produces SettingsNotChanged")
    @pytest.mark.parametrize(
        "family, size, expected_reason",
        [
            pytest.param("Comic Sans", 14, "INVALID_FONT_FAMILY", id="bad-family"),
            pytest.param("Inter", 8, "INVALID_FONT_SIZE", id="size-too-small"),
            pytest.param("Inter", 30, "INVALID_FONT_SIZE", id="size-too-large"),
        ],
    )
    def test_fails_with_invalid_font(self, family, size, expected_reason):
        settings = UserSettings.default()
        result = derive_font_change(family=family, size=size, current_settings=settings)

        assert isinstance(result, SettingsNotChanged)
        assert result.reason == expected_reason

    @allure.title("Boundary font sizes (10, 24) are accepted")
    @pytest.mark.parametrize("size", [10, 24], ids=["min-size", "max-size"])
    def test_accepts_boundary_font_sizes(self, size):
        settings = UserSettings.default()
        result = derive_font_change(family="Inter", size=size, current_settings=settings)

        assert isinstance(result, FontChanged)
        assert result.size == size


@allure.story("QC-035.02 Settings Derivers")
class TestDeriveLanguageChange:
    """Tests for derive_language_change deriver."""

    @allure.title("Valid language code produces LanguageChanged event")
    def test_changes_language_with_valid_code(self):
        settings = UserSettings.default()
        result = derive_language_change(new_language_code="es", current_settings=settings)

        assert isinstance(result, LanguageChanged)
        assert result.old_language == "en"
        assert result.new_language == "es"
        assert result.language_name == "Español"

    @allure.title("Invalid language code produces SettingsNotChanged")
    def test_fails_with_invalid_language_code(self):
        settings = UserSettings.default()
        result = derive_language_change(new_language_code="xx", current_settings=settings)

        assert isinstance(result, SettingsNotChanged)
        assert result.reason == "INVALID_LANGUAGE"
        assert "xx" in result.message

    @allure.title("All supported language codes are accepted")
    def test_supports_all_valid_languages(self):
        from src.contexts.settings.core.invariants import VALID_LANGUAGES

        settings = UserSettings.default()

        for code in VALID_LANGUAGES:
            result = derive_language_change(
                new_language_code=code, current_settings=settings
            )
            assert isinstance(result, LanguageChanged)
            assert result.new_language == code


@allure.story("QC-035.02 Settings Derivers")
class TestDeriveBackupConfigChange:
    """Tests for derive_backup_config_change deriver."""

    @allure.title("Valid backup config produces BackupConfigChanged event")
    @pytest.mark.parametrize(
        "backup_path",
        [
            pytest.param("/tmp/backups", id="with-path"),
            pytest.param(None, id="none-path"),
        ],
    )
    def test_changes_backup_config_with_valid_inputs(self, backup_path):
        settings = UserSettings.default()
        result = derive_backup_config_change(
            enabled=True,
            interval_minutes=30,
            max_backups=5,
            backup_path=backup_path,
            current_settings=settings,
        )

        assert isinstance(result, BackupConfigChanged)
        assert result.enabled is True
        assert result.interval_minutes == 30
        assert result.backup_path == backup_path

    @allure.title("Invalid backup interval or max_backups produces SettingsNotChanged")
    @pytest.mark.parametrize(
        "interval, max_b, expected_reason",
        [
            pytest.param(3, 5, "INVALID_BACKUP_INTERVAL", id="interval-too-small"),
            pytest.param(150, 5, "INVALID_BACKUP_INTERVAL", id="interval-too-large"),
            pytest.param(30, 0, "INVALID_MAX_BACKUPS", id="max-backups-too-small"),
            pytest.param(30, 25, "INVALID_MAX_BACKUPS", id="max-backups-too-large"),
        ],
    )
    def test_fails_with_invalid_backup_params(self, interval, max_b, expected_reason):
        settings = UserSettings.default()
        result = derive_backup_config_change(
            enabled=True,
            interval_minutes=interval,
            max_backups=max_b,
            backup_path=None,
            current_settings=settings,
        )

        assert isinstance(result, SettingsNotChanged)
        assert result.reason == expected_reason

    @allure.title("Boundary values (interval 5/120, max_backups 1/20) accepted")
    @pytest.mark.parametrize(
        "interval, max_b",
        [(5, 1), (120, 20)],
        ids=["min-boundaries", "max-boundaries"],
    )
    def test_accepts_boundary_values(self, interval, max_b):
        settings = UserSettings.default()
        result = derive_backup_config_change(
            enabled=True,
            interval_minutes=interval,
            max_backups=max_b,
            backup_path=None,
            current_settings=settings,
        )
        assert isinstance(result, BackupConfigChanged)


@allure.story("QC-035.02 Settings Derivers")
class TestDeriveAVCodingConfigChange:
    """Tests for derive_av_coding_config_change deriver."""

    @allure.title("Valid AV config produces AVCodingConfigChanged event")
    def test_changes_av_config_with_valid_inputs(self):
        settings = UserSettings.default()
        result = derive_av_coding_config_change(
            timestamp_format="HH:MM:SS.mmm",
            speaker_format="Interviewer {n}",
            current_settings=settings,
        )

        assert isinstance(result, AVCodingConfigChanged)
        assert result.timestamp_format == "HH:MM:SS.mmm"
        assert result.speaker_format == "Interviewer {n}"

    @allure.title("All valid timestamp formats are accepted")
    def test_accepts_all_valid_timestamp_formats(self):
        from src.contexts.settings.core.invariants import VALID_TIMESTAMP_FORMATS

        settings = UserSettings.default()

        for fmt in VALID_TIMESTAMP_FORMATS:
            result = derive_av_coding_config_change(
                timestamp_format=fmt,
                speaker_format="Speaker {n}",
                current_settings=settings,
            )
            assert isinstance(result, AVCodingConfigChanged)
            assert result.timestamp_format == fmt

    @allure.title("Invalid timestamp or speaker format produces SettingsNotChanged")
    @pytest.mark.parametrize(
        "ts_fmt, spk_fmt, expected_reason",
        [
            pytest.param(
                "YYYY-MM-DD", "Speaker {n}", "INVALID_TIMESTAMP_FORMAT", id="bad-ts"
            ),
            pytest.param(
                "HH:MM:SS", "Speaker", "INVALID_SPEAKER_FORMAT", id="missing-placeholder"
            ),
            pytest.param(
                "HH:MM:SS", "", "INVALID_SPEAKER_FORMAT", id="empty-speaker"
            ),
        ],
    )
    def test_fails_with_invalid_av_format(self, ts_fmt, spk_fmt, expected_reason):
        settings = UserSettings.default()
        result = derive_av_coding_config_change(
            timestamp_format=ts_fmt,
            speaker_format=spk_fmt,
            current_settings=settings,
        )

        assert isinstance(result, SettingsNotChanged)
        assert result.reason == expected_reason

    @allure.title("Various valid speaker formats with {{n}} placeholder accepted")
    @pytest.mark.parametrize(
        "fmt",
        ["Speaker {n}", "Participant {n}", "P{n}", "{n}", "Interviewee #{n}"],
        ids=["speaker", "participant", "short", "bare", "interviewee"],
    )
    def test_accepts_various_speaker_formats(self, fmt):
        settings = UserSettings.default()
        result = derive_av_coding_config_change(
            timestamp_format="HH:MM:SS",
            speaker_format=fmt,
            current_settings=settings,
        )
        assert isinstance(result, AVCodingConfigChanged)
        assert result.speaker_format == fmt
