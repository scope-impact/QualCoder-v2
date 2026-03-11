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

    @allure.title("Valid theme changes produce ThemeChanged, invalid produces SettingsNotChanged")
    @pytest.mark.parametrize(
        "new_theme, expect_success",
        [
            pytest.param("dark", True, id="dark"),
            pytest.param("system", True, id="system"),
            pytest.param("neon", False, id="invalid"),
        ],
    )
    def test_theme_change(self, new_theme, expect_success):
        settings = UserSettings.default()
        result = derive_theme_change(new_theme=new_theme, current_settings=settings)

        if expect_success:
            assert isinstance(result, ThemeChanged)
            assert result.old_theme == "light"
            assert result.new_theme == new_theme
        else:
            assert isinstance(result, SettingsNotChanged)
            assert result.reason == "INVALID_THEME"
            assert new_theme in result.message


@allure.story("QC-035.02 Settings Derivers")
class TestDeriveFontChange:
    """Tests for derive_font_change deriver."""

    @allure.title("Valid font changes produce FontChanged, invalid produces SettingsNotChanged")
    @pytest.mark.parametrize(
        "family, size, expect_success, expected_reason",
        [
            pytest.param("Roboto", 16, True, None, id="valid"),
            pytest.param("Inter", 10, True, None, id="min-boundary"),
            pytest.param("Inter", 24, True, None, id="max-boundary"),
            pytest.param("Comic Sans", 14, False, "INVALID_FONT_FAMILY", id="bad-family"),
            pytest.param("Inter", 8, False, "INVALID_FONT_SIZE", id="size-too-small"),
            pytest.param("Inter", 30, False, "INVALID_FONT_SIZE", id="size-too-large"),
        ],
    )
    def test_font_change(self, family, size, expect_success, expected_reason):
        settings = UserSettings.default()
        result = derive_font_change(family=family, size=size, current_settings=settings)

        if expect_success:
            assert isinstance(result, FontChanged)
            assert result.family == family
            assert result.size == size
        else:
            assert isinstance(result, SettingsNotChanged)
            assert result.reason == expected_reason


@allure.story("QC-035.02 Settings Derivers")
class TestDeriveLanguageChange:
    """Tests for derive_language_change deriver."""

    @allure.title("Valid language code produces LanguageChanged, invalid produces SettingsNotChanged")
    def test_language_change_valid_and_invalid(self):
        settings = UserSettings.default()

        # Valid change
        result = derive_language_change(new_language_code="es", current_settings=settings)
        assert isinstance(result, LanguageChanged)
        assert result.old_language == "en"
        assert result.new_language == "es"
        assert result.language_name == "Español"

        # Invalid language code
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

    @allure.title("Valid backup config produces BackupConfigChanged, invalid produces SettingsNotChanged")
    @pytest.mark.parametrize(
        "interval, max_b, backup_path, expect_success, expected_reason",
        [
            pytest.param(30, 5, "/tmp/backups", True, None, id="with-path"),
            pytest.param(30, 5, None, True, None, id="none-path"),
            pytest.param(5, 1, None, True, None, id="min-boundaries"),
            pytest.param(120, 20, None, True, None, id="max-boundaries"),
            pytest.param(3, 5, None, False, "INVALID_BACKUP_INTERVAL", id="interval-too-small"),
            pytest.param(150, 5, None, False, "INVALID_BACKUP_INTERVAL", id="interval-too-large"),
            pytest.param(30, 0, None, False, "INVALID_MAX_BACKUPS", id="max-backups-too-small"),
            pytest.param(30, 25, None, False, "INVALID_MAX_BACKUPS", id="max-backups-too-large"),
        ],
    )
    def test_backup_config_change(self, interval, max_b, backup_path, expect_success, expected_reason):
        settings = UserSettings.default()
        result = derive_backup_config_change(
            enabled=True,
            interval_minutes=interval,
            max_backups=max_b,
            backup_path=backup_path,
            current_settings=settings,
        )

        if expect_success:
            assert isinstance(result, BackupConfigChanged)
            assert result.enabled is True
            assert result.interval_minutes == interval
            assert result.backup_path == backup_path
        else:
            assert isinstance(result, SettingsNotChanged)
            assert result.reason == expected_reason


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

    @allure.title("All valid timestamp and speaker formats are accepted")
    def test_accepts_all_valid_formats(self):
        from src.contexts.settings.core.invariants import VALID_TIMESTAMP_FORMATS

        settings = UserSettings.default()

        # All timestamp formats
        for fmt in VALID_TIMESTAMP_FORMATS:
            result = derive_av_coding_config_change(
                timestamp_format=fmt,
                speaker_format="Speaker {n}",
                current_settings=settings,
            )
            assert isinstance(result, AVCodingConfigChanged)
            assert result.timestamp_format == fmt

        # Various speaker formats with {n} placeholder
        for fmt in ["Speaker {n}", "Participant {n}", "P{n}", "{n}", "Interviewee #{n}"]:
            result = derive_av_coding_config_change(
                timestamp_format="HH:MM:SS",
                speaker_format=fmt,
                current_settings=settings,
            )
            assert isinstance(result, AVCodingConfigChanged)
            assert result.speaker_format == fmt

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
