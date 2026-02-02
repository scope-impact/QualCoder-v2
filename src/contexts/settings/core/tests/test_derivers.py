"""
Settings Context: Deriver Tests

Tests for pure functions that compose invariants and derive domain events.
"""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.unit


class TestDeriveThemeChange:
    """Tests for derive_theme_change deriver."""

    def test_changes_theme_with_valid_input(self):
        """Should create ThemeChanged event with valid theme."""
        from src.contexts.settings.core.derivers import derive_theme_change
        from src.contexts.settings.core.entities import UserSettings
        from src.contexts.settings.core.events import ThemeChanged

        settings = UserSettings.default()

        result = derive_theme_change(
            new_theme="dark",
            current_settings=settings,
        )

        assert isinstance(result, ThemeChanged)
        assert result.old_theme == "light"
        assert result.new_theme == "dark"

    def test_changes_to_system_theme(self):
        """Should create ThemeChanged event for system theme."""
        from src.contexts.settings.core.derivers import derive_theme_change
        from src.contexts.settings.core.entities import UserSettings
        from src.contexts.settings.core.events import ThemeChanged

        settings = UserSettings.default()

        result = derive_theme_change(
            new_theme="system",
            current_settings=settings,
        )

        assert isinstance(result, ThemeChanged)
        assert result.new_theme == "system"

    def test_fails_with_invalid_theme(self):
        """Should fail with InvalidTheme for unknown theme."""
        from returns.result import Failure

        from src.contexts.settings.core.derivers import (
            InvalidTheme,
            derive_theme_change,
        )
        from src.contexts.settings.core.entities import UserSettings

        settings = UserSettings.default()

        result = derive_theme_change(
            new_theme="neon",
            current_settings=settings,
        )

        assert isinstance(result, Failure)
        assert isinstance(result.failure(), InvalidTheme)
        assert "neon" in result.failure().message


class TestDeriveFontChange:
    """Tests for derive_font_change deriver."""

    def test_changes_font_with_valid_inputs(self):
        """Should create FontChanged event with valid font settings."""
        from src.contexts.settings.core.derivers import derive_font_change
        from src.contexts.settings.core.entities import UserSettings
        from src.contexts.settings.core.events import FontChanged

        settings = UserSettings.default()

        result = derive_font_change(
            family="Roboto",
            size=16,
            current_settings=settings,
        )

        assert isinstance(result, FontChanged)
        assert result.family == "Roboto"
        assert result.size == 16

    def test_fails_with_invalid_font_family(self):
        """Should fail with InvalidFontFamily for unknown font."""
        from returns.result import Failure

        from src.contexts.settings.core.derivers import (
            InvalidFontFamily,
            derive_font_change,
        )
        from src.contexts.settings.core.entities import UserSettings

        settings = UserSettings.default()

        result = derive_font_change(
            family="Comic Sans",
            size=14,
            current_settings=settings,
        )

        assert isinstance(result, Failure)
        assert isinstance(result.failure(), InvalidFontFamily)
        assert "Comic Sans" in result.failure().message

    def test_fails_with_font_size_too_small(self):
        """Should fail with InvalidFontSize for size below 10."""
        from returns.result import Failure

        from src.contexts.settings.core.derivers import (
            InvalidFontSize,
            derive_font_change,
        )
        from src.contexts.settings.core.entities import UserSettings

        settings = UserSettings.default()

        result = derive_font_change(
            family="Inter",
            size=8,
            current_settings=settings,
        )

        assert isinstance(result, Failure)
        assert isinstance(result.failure(), InvalidFontSize)

    def test_fails_with_font_size_too_large(self):
        """Should fail with InvalidFontSize for size above 24."""
        from returns.result import Failure

        from src.contexts.settings.core.derivers import (
            InvalidFontSize,
            derive_font_change,
        )
        from src.contexts.settings.core.entities import UserSettings

        settings = UserSettings.default()

        result = derive_font_change(
            family="Inter",
            size=30,
            current_settings=settings,
        )

        assert isinstance(result, Failure)
        assert isinstance(result.failure(), InvalidFontSize)

    def test_accepts_boundary_font_sizes(self):
        """Should accept font sizes at boundaries (10 and 24)."""
        from src.contexts.settings.core.derivers import derive_font_change
        from src.contexts.settings.core.entities import UserSettings
        from src.contexts.settings.core.events import FontChanged

        settings = UserSettings.default()

        # Test minimum
        result = derive_font_change(family="Inter", size=10, current_settings=settings)
        assert isinstance(result, FontChanged)
        assert result.size == 10

        # Test maximum
        result = derive_font_change(family="Inter", size=24, current_settings=settings)
        assert isinstance(result, FontChanged)
        assert result.size == 24


class TestDeriveLanguageChange:
    """Tests for derive_language_change deriver."""

    def test_changes_language_with_valid_code(self):
        """Should create LanguageChanged event with valid language code."""
        from src.contexts.settings.core.derivers import derive_language_change
        from src.contexts.settings.core.entities import UserSettings
        from src.contexts.settings.core.events import LanguageChanged

        settings = UserSettings.default()

        result = derive_language_change(
            new_language_code="es",
            current_settings=settings,
        )

        assert isinstance(result, LanguageChanged)
        assert result.old_language == "en"
        assert result.new_language == "es"
        assert result.language_name == "Español"

    def test_fails_with_invalid_language_code(self):
        """Should fail with InvalidLanguage for unsupported code."""
        from returns.result import Failure

        from src.contexts.settings.core.derivers import (
            InvalidLanguage,
            derive_language_change,
        )
        from src.contexts.settings.core.entities import UserSettings

        settings = UserSettings.default()

        result = derive_language_change(
            new_language_code="xx",
            current_settings=settings,
        )

        assert isinstance(result, Failure)
        assert isinstance(result.failure(), InvalidLanguage)
        assert "xx" in result.failure().message

    def test_supports_all_valid_languages(self):
        """Should accept all supported language codes."""
        from src.contexts.settings.core.derivers import derive_language_change
        from src.contexts.settings.core.entities import UserSettings
        from src.contexts.settings.core.events import LanguageChanged
        from src.contexts.settings.core.invariants import VALID_LANGUAGES

        settings = UserSettings.default()

        for code in VALID_LANGUAGES:
            result = derive_language_change(
                new_language_code=code,
                current_settings=settings,
            )
            assert isinstance(result, LanguageChanged)
            assert result.new_language == code


class TestDeriveBackupConfigChange:
    """Tests for derive_backup_config_change deriver."""

    def test_changes_backup_config_with_valid_inputs(self):
        """Should create BackupConfigChanged event with valid settings."""
        from src.contexts.settings.core.derivers import derive_backup_config_change
        from src.contexts.settings.core.entities import UserSettings
        from src.contexts.settings.core.events import BackupConfigChanged

        settings = UserSettings.default()

        result = derive_backup_config_change(
            enabled=True,
            interval_minutes=30,
            max_backups=5,
            backup_path="/tmp/backups",
            current_settings=settings,
        )

        assert isinstance(result, BackupConfigChanged)
        assert result.enabled is True
        assert result.interval_minutes == 30
        assert result.max_backups == 5
        assert result.backup_path == "/tmp/backups"

    def test_allows_none_backup_path(self):
        """Should accept None for backup_path."""
        from src.contexts.settings.core.derivers import derive_backup_config_change
        from src.contexts.settings.core.entities import UserSettings
        from src.contexts.settings.core.events import BackupConfigChanged

        settings = UserSettings.default()

        result = derive_backup_config_change(
            enabled=True,
            interval_minutes=30,
            max_backups=5,
            backup_path=None,
            current_settings=settings,
        )

        assert isinstance(result, BackupConfigChanged)
        assert result.backup_path is None

    def test_fails_with_interval_too_small(self):
        """Should fail with InvalidBackupInterval for interval below 5."""
        from returns.result import Failure

        from src.contexts.settings.core.derivers import (
            InvalidBackupInterval,
            derive_backup_config_change,
        )
        from src.contexts.settings.core.entities import UserSettings

        settings = UserSettings.default()

        result = derive_backup_config_change(
            enabled=True,
            interval_minutes=3,
            max_backups=5,
            backup_path=None,
            current_settings=settings,
        )

        assert isinstance(result, Failure)
        assert isinstance(result.failure(), InvalidBackupInterval)

    def test_fails_with_interval_too_large(self):
        """Should fail with InvalidBackupInterval for interval above 120."""
        from returns.result import Failure

        from src.contexts.settings.core.derivers import (
            InvalidBackupInterval,
            derive_backup_config_change,
        )
        from src.contexts.settings.core.entities import UserSettings

        settings = UserSettings.default()

        result = derive_backup_config_change(
            enabled=True,
            interval_minutes=150,
            max_backups=5,
            backup_path=None,
            current_settings=settings,
        )

        assert isinstance(result, Failure)
        assert isinstance(result.failure(), InvalidBackupInterval)

    def test_fails_with_max_backups_too_small(self):
        """Should fail with InvalidMaxBackups for max_backups below 1."""
        from returns.result import Failure

        from src.contexts.settings.core.derivers import (
            InvalidMaxBackups,
            derive_backup_config_change,
        )
        from src.contexts.settings.core.entities import UserSettings

        settings = UserSettings.default()

        result = derive_backup_config_change(
            enabled=True,
            interval_minutes=30,
            max_backups=0,
            backup_path=None,
            current_settings=settings,
        )

        assert isinstance(result, Failure)
        assert isinstance(result.failure(), InvalidMaxBackups)

    def test_fails_with_max_backups_too_large(self):
        """Should fail with InvalidMaxBackups for max_backups above 20."""
        from returns.result import Failure

        from src.contexts.settings.core.derivers import (
            InvalidMaxBackups,
            derive_backup_config_change,
        )
        from src.contexts.settings.core.entities import UserSettings

        settings = UserSettings.default()

        result = derive_backup_config_change(
            enabled=True,
            interval_minutes=30,
            max_backups=25,
            backup_path=None,
            current_settings=settings,
        )

        assert isinstance(result, Failure)
        assert isinstance(result.failure(), InvalidMaxBackups)

    def test_accepts_boundary_values(self):
        """Should accept values at boundaries."""
        from src.contexts.settings.core.derivers import derive_backup_config_change
        from src.contexts.settings.core.entities import UserSettings
        from src.contexts.settings.core.events import BackupConfigChanged

        settings = UserSettings.default()

        # Minimum interval and max_backups
        result = derive_backup_config_change(
            enabled=True,
            interval_minutes=5,
            max_backups=1,
            backup_path=None,
            current_settings=settings,
        )
        assert isinstance(result, BackupConfigChanged)

        # Maximum interval and max_backups
        result = derive_backup_config_change(
            enabled=True,
            interval_minutes=120,
            max_backups=20,
            backup_path=None,
            current_settings=settings,
        )
        assert isinstance(result, BackupConfigChanged)


class TestDeriveAVCodingConfigChange:
    """Tests for derive_av_coding_config_change deriver."""

    def test_changes_av_config_with_valid_inputs(self):
        """Should create AVCodingConfigChanged event with valid settings."""
        from src.contexts.settings.core.derivers import derive_av_coding_config_change
        from src.contexts.settings.core.entities import UserSettings
        from src.contexts.settings.core.events import AVCodingConfigChanged

        settings = UserSettings.default()

        result = derive_av_coding_config_change(
            timestamp_format="HH:MM:SS.mmm",
            speaker_format="Interviewer {n}",
            current_settings=settings,
        )

        assert isinstance(result, AVCodingConfigChanged)
        assert result.timestamp_format == "HH:MM:SS.mmm"
        assert result.speaker_format == "Interviewer {n}"

    def test_accepts_all_valid_timestamp_formats(self):
        """Should accept all valid timestamp formats."""
        from src.contexts.settings.core.derivers import derive_av_coding_config_change
        from src.contexts.settings.core.entities import UserSettings
        from src.contexts.settings.core.events import AVCodingConfigChanged
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

    def test_fails_with_invalid_timestamp_format(self):
        """Should fail with InvalidTimestampFormat for unknown format."""
        from returns.result import Failure

        from src.contexts.settings.core.derivers import (
            InvalidTimestampFormat,
            derive_av_coding_config_change,
        )
        from src.contexts.settings.core.entities import UserSettings

        settings = UserSettings.default()

        result = derive_av_coding_config_change(
            timestamp_format="YYYY-MM-DD",
            speaker_format="Speaker {n}",
            current_settings=settings,
        )

        assert isinstance(result, Failure)
        assert isinstance(result.failure(), InvalidTimestampFormat)
        assert "YYYY-MM-DD" in result.failure().message

    def test_fails_with_speaker_format_missing_placeholder(self):
        """Should fail with InvalidSpeakerFormat when {n} is missing."""
        from returns.result import Failure

        from src.contexts.settings.core.derivers import (
            InvalidSpeakerFormat,
            derive_av_coding_config_change,
        )
        from src.contexts.settings.core.entities import UserSettings

        settings = UserSettings.default()

        result = derive_av_coding_config_change(
            timestamp_format="HH:MM:SS",
            speaker_format="Speaker",
            current_settings=settings,
        )

        assert isinstance(result, Failure)
        assert isinstance(result.failure(), InvalidSpeakerFormat)

    def test_fails_with_empty_speaker_format(self):
        """Should fail with InvalidSpeakerFormat for empty format."""
        from returns.result import Failure

        from src.contexts.settings.core.derivers import (
            InvalidSpeakerFormat,
            derive_av_coding_config_change,
        )
        from src.contexts.settings.core.entities import UserSettings

        settings = UserSettings.default()

        result = derive_av_coding_config_change(
            timestamp_format="HH:MM:SS",
            speaker_format="",
            current_settings=settings,
        )

        assert isinstance(result, Failure)
        assert isinstance(result.failure(), InvalidSpeakerFormat)

    def test_accepts_various_speaker_formats(self):
        """Should accept various valid speaker formats with {n}."""
        from src.contexts.settings.core.derivers import derive_av_coding_config_change
        from src.contexts.settings.core.entities import UserSettings
        from src.contexts.settings.core.events import AVCodingConfigChanged

        settings = UserSettings.default()

        formats = [
            "Speaker {n}",
            "Participant {n}",
            "P{n}",
            "{n}",
            "Interviewee #{n}",
        ]

        for fmt in formats:
            result = derive_av_coding_config_change(
                timestamp_format="HH:MM:SS",
                speaker_format=fmt,
                current_settings=settings,
            )
            assert isinstance(result, AVCodingConfigChanged)
            assert result.speaker_format == fmt
