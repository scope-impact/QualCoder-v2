"""
Observability Settings End-to-End Tests

True E2E tests with FULL behavior - real file persistence and logging integration.
Tests the complete flow: UI action → Dialog → ViewModel → Service → Repository → JSON File

Also tests environment variable override and configure_logging() integration.

Implements QC-049 Observability:
- AC #3: Logging levels configurable via settings or environment
- AC #5: User documentation (verified by doc file existence)
"""

from __future__ import annotations

import logging
import tempfile
from pathlib import Path
from unittest.mock import patch

import allure
import pytest
from PySide6.QtWidgets import QApplication

pytestmark = [
    pytest.mark.e2e,
    allure.epic("QualCoder v2"),
    allure.feature("QC-049 Observability"),
]


# =============================================================================
# Fixtures (reuse the same pattern as test_settings_e2e.py)
# =============================================================================


@pytest.fixture
def temp_config_path():
    """Create a temporary config file path for settings persistence."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir) / "settings.json"


@pytest.fixture
def settings_repo(temp_config_path):
    """Create a settings repository connected to temp JSON file."""
    from src.contexts.settings.infra import UserSettingsRepository

    return UserSettingsRepository(config_path=temp_config_path)


@pytest.fixture
def settings_event_bus():
    """Create a lightweight event bus for settings tests."""
    from src.shared.infra.event_bus import EventBus

    return EventBus()


@pytest.fixture
def settings_provider(settings_repo, settings_event_bus):
    """Create a settings service for use as a provider."""
    from src.shared.presentation.services import SettingsService

    return SettingsService(settings_repo, event_bus=settings_event_bus)


@pytest.fixture
def settings_viewmodel(settings_provider):
    """Create SettingsViewModel with real service."""
    from src.contexts.settings.presentation import SettingsViewModel

    return SettingsViewModel(settings_provider=settings_provider)


@pytest.fixture
def settings_dialog(qapp, colors, settings_viewmodel):
    """Create a complete Settings Dialog for E2E testing with real persistence."""
    from src.contexts.settings.presentation.dialogs import SettingsDialog

    dialog = SettingsDialog(viewmodel=settings_viewmodel, colors=colors)
    yield dialog
    dialog.close()


@pytest.fixture(autouse=True)
def _reset_qualcoder_logger():
    """Reset the qualcoder logger between tests to allow reconfiguration."""
    yield
    root = logging.getLogger("qualcoder")
    root.handlers.clear()
    root.setLevel(logging.WARNING)


# =============================================================================
# AC #3: Log Level Configurable via UI
# =============================================================================


@allure.story("QC-049.03 Configure Log Level via Settings UI")
@allure.severity(allure.severity_level.CRITICAL)
class TestLogLevelUI:
    """E2E tests for log level configuration through the Settings dialog."""

    @allure.title("AC #3.1: Changing log level via combo persists to JSON file")
    def test_change_log_level_via_combo_persists_to_file(
        self, settings_dialog, settings_repo
    ):
        """E2E: Selecting a different log level in the combo box persists to disk."""
        with allure.step("Find DEBUG level in combo"):
            combo = settings_dialog._log_level_combo
            debug_index = combo.findData("DEBUG")
            assert debug_index >= 0

        with allure.step("Select DEBUG level"):
            combo.setCurrentIndex(debug_index)
            QApplication.processEvents()

        with allure.step("Verify log level persisted to repository"):
            settings = settings_repo.load()
            assert settings.observability.log_level == "DEBUG"

    @allure.title("AC #3.2: Changing log level to WARNING persists correctly")
    def test_change_log_level_to_warning(self, settings_dialog, settings_repo):
        """E2E: Selecting WARNING level persists to disk."""
        with allure.step("Select WARNING level"):
            combo = settings_dialog._log_level_combo
            warning_index = combo.findData("WARNING")
            combo.setCurrentIndex(warning_index)
            QApplication.processEvents()

        with allure.step("Verify WARNING persisted"):
            settings = settings_repo.load()
            assert settings.observability.log_level == "WARNING"

    @allure.title("AC #3.3: Default log level is INFO")
    def test_default_log_level_is_info(self, settings_repo):
        """E2E: Fresh settings file defaults to INFO log level."""
        with allure.step("Load default settings"):
            settings = settings_repo.load()

        with allure.step("Verify default is INFO"):
            assert settings.observability.log_level == "INFO"


# =============================================================================
# AC #3: File Logging Configurable via UI
# =============================================================================


@allure.story("QC-049.03 Configure File Logging via Settings UI")
@allure.severity(allure.severity_level.NORMAL)
class TestFileLoggingUI:
    """E2E tests for file logging toggle in the Settings dialog."""

    @allure.title("AC #3.4: Enabling file logging via checkbox persists to JSON file")
    def test_enable_file_logging_persists_to_file(self, settings_dialog, settings_repo):
        """E2E: Checking the file logging checkbox persists to disk."""
        with allure.step("Enable file logging checkbox"):
            settings_dialog._file_logging_cb.setChecked(True)
            QApplication.processEvents()

        with allure.step("Verify file logging enabled in repository"):
            settings = settings_repo.load()
            assert settings.observability.enable_file_logging is True

    @allure.title("AC #3.5: Disabling file logging via checkbox persists to JSON file")
    def test_disable_file_logging_persists_to_file(
        self, settings_dialog, settings_repo
    ):
        """E2E: Unchecking file logging after enabling it persists correctly."""
        with allure.step("Enable then disable file logging"):
            settings_dialog._file_logging_cb.setChecked(True)
            QApplication.processEvents()
            settings_dialog._file_logging_cb.setChecked(False)
            QApplication.processEvents()

        with allure.step("Verify file logging disabled in repository"):
            settings = settings_repo.load()
            assert settings.observability.enable_file_logging is False


# =============================================================================
# AC #3: Telemetry Configurable via UI
# =============================================================================


@allure.story("QC-049.03 Configure Telemetry via Settings UI")
@allure.severity(allure.severity_level.NORMAL)
class TestTelemetryUI:
    """E2E tests for telemetry toggle in the Settings dialog."""

    @allure.title("AC #3.6: Telemetry is enabled by default")
    def test_telemetry_enabled_by_default(self, settings_repo):
        """E2E: Fresh settings file defaults to telemetry enabled."""
        settings = settings_repo.load()
        assert settings.observability.enable_telemetry is True

    @allure.title("AC #3.7: Disabling telemetry via checkbox persists to JSON file")
    def test_disable_telemetry_persists_to_file(self, settings_dialog, settings_repo):
        """E2E: Unchecking the telemetry checkbox persists to disk."""
        with allure.step("Disable telemetry checkbox"):
            settings_dialog._telemetry_cb.setChecked(False)
            QApplication.processEvents()

        with allure.step("Verify telemetry disabled in repository"):
            settings = settings_repo.load()
            assert settings.observability.enable_telemetry is False


# =============================================================================
# AC #3: Environment Variable Override
# =============================================================================


@allure.story("QC-049.03 QUALCODER_LOG_LEVEL Environment Variable Override")
@allure.severity(allure.severity_level.CRITICAL)
class TestEnvVarOverride:
    """E2E tests for the QUALCODER_LOG_LEVEL environment variable override."""

    @allure.title("AC #3.8: Env var overrides settings-configured log level")
    def test_env_var_overrides_settings_level(self):
        """E2E: QUALCODER_LOG_LEVEL env var takes priority over level param."""
        from src.shared.infra.logging_config import configure_logging

        with (
            allure.step("Configure logging with INFO but env var set to DEBUG"),
            patch.dict("os.environ", {"QUALCODER_LOG_LEVEL": "DEBUG"}),
        ):
            configure_logging(level="INFO", enable_console=False)

        with allure.step("Verify logger uses DEBUG from env var"):
            root = logging.getLogger("qualcoder")
            assert root.level == logging.DEBUG

    @allure.title("AC #3.9: Without env var, settings level is used")
    def test_settings_level_used_without_env_var(self):
        """E2E: Without env var, the level parameter controls the logger."""
        from src.shared.infra.logging_config import configure_logging

        with (
            allure.step("Configure logging with WARNING, no env var"),
            patch.dict("os.environ", {}, clear=True),
        ):
            configure_logging(level="WARNING", enable_console=False)

        with allure.step("Verify logger uses WARNING from settings"):
            root = logging.getLogger("qualcoder")
            assert root.level == logging.WARNING

    @allure.title("AC #3.10: Env var is case-insensitive")
    def test_env_var_case_insensitive(self):
        """E2E: QUALCODER_LOG_LEVEL accepts lowercase values."""
        from src.shared.infra.logging_config import configure_logging

        with (
            allure.step("Set env var with lowercase 'debug'"),
            patch.dict("os.environ", {"QUALCODER_LOG_LEVEL": "debug"}),
        ):
            configure_logging(level="INFO", enable_console=False)

        with allure.step("Verify logger uses DEBUG"):
            root = logging.getLogger("qualcoder")
            assert root.level == logging.DEBUG


# =============================================================================
# AC #3: File Logging Integration
# =============================================================================


@allure.story("QC-049.03 File Logging Writes to Disk")
@allure.severity(allure.severity_level.NORMAL)
class TestFileLoggingIntegration:
    """E2E tests for configure_logging with file output."""

    @allure.title("AC #3.11: File logging creates log file and writes output")
    def test_file_logging_creates_file(self):
        """E2E: Passing a log_file path creates the file and writes to it."""
        from src.shared.infra.logging_config import configure_logging

        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / "test.log"

            with allure.step("Configure logging with file output"):
                configure_logging(
                    level="DEBUG", log_file=log_path, enable_console=False
                )

            with allure.step("Write a log message"):
                logger = logging.getLogger("qualcoder.test")
                logger.info("test message for file logging")

            with allure.step("Verify log file exists and contains the message"):
                assert log_path.exists()
                content = log_path.read_text()
                assert "test message for file logging" in content


# =============================================================================
# AC #3: Full Round-Trip (UI → File → Reload)
# =============================================================================


@allure.story("QC-049.03 Full Round-Trip Persistence")
@allure.severity(allure.severity_level.CRITICAL)
class TestObservabilityRoundTrip:
    """E2E tests for full round-trip: change in UI → persisted → reloaded in new dialog."""

    @allure.title(
        "AC #3.12: All observability settings survive dialog close and reopen"
    )
    def test_full_round_trip(self, qapp, colors, settings_repo, settings_event_bus):
        """E2E: Change all three settings, close dialog, open new one, verify loaded."""
        from src.contexts.settings.presentation import SettingsViewModel
        from src.contexts.settings.presentation.dialogs import SettingsDialog
        from src.shared.presentation.services import SettingsService

        with allure.step("Session 1: Change all observability settings"):
            provider1 = SettingsService(settings_repo, event_bus=settings_event_bus)
            vm1 = SettingsViewModel(settings_provider=provider1)
            dialog1 = SettingsDialog(viewmodel=vm1, colors=colors)

            # Change log level to ERROR
            error_index = dialog1._log_level_combo.findData("ERROR")
            dialog1._log_level_combo.setCurrentIndex(error_index)

            # Enable file logging
            dialog1._file_logging_cb.setChecked(True)

            # Disable telemetry
            dialog1._telemetry_cb.setChecked(False)

            QApplication.processEvents()
            dialog1.close()

        with allure.step("Verify all settings persisted to JSON file"):
            settings = settings_repo.load()
            assert settings.observability.log_level == "ERROR"
            assert settings.observability.enable_file_logging is True
            assert settings.observability.enable_telemetry is False

        with allure.step("Session 2: Open new dialog and verify settings loaded"):
            provider2 = SettingsService(settings_repo, event_bus=settings_event_bus)
            vm2 = SettingsViewModel(settings_provider=provider2)
            dialog2 = SettingsDialog(viewmodel=vm2, colors=colors)

            assert dialog2._log_level_combo.currentData() == "ERROR"
            assert dialog2._file_logging_cb.isChecked() is True
            assert dialog2._telemetry_cb.isChecked() is False

            dialog2.close()


# =============================================================================
# AC #3: Invalid Log Level Rejection
# =============================================================================


@allure.story("QC-049.03 Invalid Log Level Rejection")
@allure.severity(allure.severity_level.NORMAL)
class TestInvalidLogLevel:
    """E2E tests for rejecting invalid log levels through the command handler."""

    @allure.title("AC #3.13: Invalid log level is rejected by command handler")
    def test_invalid_log_level_rejected(self, settings_provider):
        """E2E: Passing an invalid log level returns a failure result."""
        with allure.step("Attempt to configure with invalid log level 'TRACE'"):
            result = settings_provider.configure_observability(
                log_level="TRACE",
                enable_file_logging=False,
                enable_telemetry=True,
            )

        with allure.step("Verify the operation failed"):
            assert result.is_failure


# =============================================================================
# AC #5: User Documentation Exists
# =============================================================================


@allure.story("QC-049.05 User Documentation")
@allure.severity(allure.severity_level.NORMAL)
class TestUserDocumentation:
    """E2E tests verifying observability documentation exists."""

    @allure.title("AC #5.1: Observability documentation page exists")
    def test_observability_doc_exists(self):
        """E2E: The observability user manual page exists and has content."""
        doc_path = (
            Path(__file__).parents[3] / "docs" / "user-manual" / "observability.md"
        )
        with allure.step("Verify observability.md exists"):
            assert doc_path.exists(), f"Missing: {doc_path}"

        with allure.step("Verify doc has meaningful content"):
            content = doc_path.read_text()
            assert "Log Level" in content
            assert "QUALCODER_LOG_LEVEL" in content
            assert "File Logging" in content
            assert "Telemetry" in content

    @allure.title("AC #5.2: Observability page linked from index")
    def test_observability_linked_from_index(self):
        """E2E: The index.md links to observability.md."""
        index_path = Path(__file__).parents[3] / "docs" / "user-manual" / "index.md"
        with allure.step("Verify index references observability page"):
            content = index_path.read_text()
            assert "observability.md" in content
