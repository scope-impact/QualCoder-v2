"""
Cloud Sync End-to-End Tests

E2E tests for Cloud Sync feature (QC-047).
Tests the settings UI for enabling/configuring cloud sync with Convex.

Implements QC-047 Cloud Sync with Convex:
- AC #1: Enable/disable cloud sync in Settings
- AC #2: Configure cloud sync connection URL
- AC #6: Researcher can see sync connection status

Reference: See test_settings_e2e.py for Settings testing patterns.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

import allure
import pytest
from PySide6.QtWidgets import QApplication, QCheckBox, QLineEdit

from src.tests.e2e.helpers import attach_screenshot
from src.tests.e2e.utils.doc_screenshot import DocScreenshot

pytestmark = [
    pytest.mark.e2e,
    allure.epic("QualCoder v2"),
    allure.feature("QC-047 Cloud Sync"),
]


# =============================================================================
# Fixtures
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
def settings_provider(settings_repo):
    """Create a settings service for use as a provider."""
    from src.shared.infra.event_bus import EventBus
    from src.shared.presentation.services import SettingsService

    return SettingsService(settings_repo, EventBus())


@pytest.fixture
def settings_viewmodel(settings_provider):
    """Create SettingsViewModel with real service."""
    from src.contexts.settings.presentation import SettingsViewModel

    return SettingsViewModel(settings_provider=settings_provider)


@pytest.fixture
def settings_dialog(qapp, colors, settings_viewmodel):
    """Create Settings Dialog for E2E testing."""
    from src.contexts.settings.presentation.dialogs import SettingsDialog

    dialog = SettingsDialog(viewmodel=settings_viewmodel, colors=colors)
    dialog.show()
    QApplication.processEvents()
    yield dialog
    dialog.close()


@pytest.fixture
def sync_status_button(qapp, colors):
    """Create SyncStatusButton for E2E testing."""
    from src.shared.presentation.molecules import SyncStatusButton

    button = SyncStatusButton(colors=colors)
    button.show()
    QApplication.processEvents()
    yield button
    button.close()


# =============================================================================
# Test Classes - Cloud Sync Settings (AC #1, #2)
# =============================================================================


@allure.story("QC-047.01 Cloud Sync Settings")
@allure.severity(allure.severity_level.CRITICAL)
class TestCloudSyncSettings:
    """
    E2E tests for cloud sync settings UI.
    AC #1: Enable/disable cloud sync in Settings
    AC #2: Configure cloud sync connection URL
    """

    @allure.title("AC #1: Cloud sync checkbox exists and is disabled by default")
    def test_cloud_sync_checkbox_exists_and_default_off(self, settings_dialog):
        """E2E: Settings dialog has cloud sync checkbox, disabled by default."""
        with allure.step("Navigate to Database section"):
            settings_dialog._sidebar.setCurrentRow(4)
            QApplication.processEvents()

        with allure.step("Find cloud sync checkbox"):
            cloud_sync_checkbox = None
            for cb in settings_dialog.findChildren(QCheckBox):
                if "cloud sync" in cb.text().lower():
                    cloud_sync_checkbox = cb
                    break

        with allure.step("Verify checkbox exists and is unchecked"):
            assert cloud_sync_checkbox is not None, "Cloud sync checkbox not found"
            assert "Convex" in cloud_sync_checkbox.text()
            assert not cloud_sync_checkbox.isChecked()

        attach_screenshot(settings_dialog, "Settings - Cloud Sync Default Off")

    @allure.title(
        "AC #1+2: Enable cloud sync shows config and user can enter Convex URL"
    )
    def test_enable_cloud_sync_and_enter_url(self, settings_dialog):
        """E2E: Enabling cloud sync shows config, user can enter URL."""
        with allure.step("Navigate to Database section"):
            settings_dialog._sidebar.setCurrentRow(4)
            QApplication.processEvents()

        with allure.step("Find and enable cloud sync"):
            cloud_sync_checkbox = None
            for cb in settings_dialog.findChildren(QCheckBox):
                if "cloud sync" in cb.text().lower():
                    cloud_sync_checkbox = cb
                    break
            cloud_sync_checkbox.setChecked(True)
            QApplication.processEvents()

        with allure.step("Verify Convex config frame is visible"):
            convex_frame = settings_dialog._convex_config_frame
            assert convex_frame.isVisible()

        with allure.step("Find and enter Convex URL"):
            convex_url_field = None
            for le in settings_dialog.findChildren(QLineEdit):
                if le.placeholderText() and "convex" in le.placeholderText().lower():
                    convex_url_field = le
                    break
            test_url = "https://my-project.convex.cloud"
            convex_url_field.setText(test_url)
            QApplication.processEvents()
            assert convex_url_field.text() == test_url

        with allure.step("Capture screenshot for documentation"):
            DocScreenshot.capture(
                settings_dialog, "settings-cloud-sync-enabled", max_width=800
            )

        attach_screenshot(settings_dialog, "Settings - Cloud Sync Enabled")

    @allure.title("AC #1: Disabling cloud sync hides Convex configuration")
    def test_disable_cloud_sync_hides_config(self, settings_dialog):
        """E2E: Unchecking cloud sync hides the Convex URL config."""
        with allure.step("Navigate to Database section"):
            settings_dialog._sidebar.setCurrentRow(4)
            QApplication.processEvents()

        with allure.step("Enable then disable cloud sync"):
            cloud_sync_checkbox = None
            for cb in settings_dialog.findChildren(QCheckBox):
                if "cloud sync" in cb.text().lower():
                    cloud_sync_checkbox = cb
                    break
            cloud_sync_checkbox.setChecked(True)
            QApplication.processEvents()
            cloud_sync_checkbox.setChecked(False)
            QApplication.processEvents()

        with allure.step("Verify Convex config is hidden"):
            convex_frame = settings_dialog._convex_config_frame
            assert not convex_frame.isVisible()

        attach_screenshot(settings_dialog, "Settings - Cloud Sync Disabled")


# =============================================================================
# Test Classes - Sync Status Button (AC #6)
# =============================================================================


@allure.story("QC-047.04 Sync Status Indicator")
@allure.severity(allure.severity_level.NORMAL)
class TestSyncStatusButton:
    """
    E2E tests for sync status button in nav bar.
    AC #6: Researcher can see sync connection status
    """

    @allure.title("AC #6: Sync button shows offline, synced, and syncing statuses")
    def test_sync_button_offline_synced_syncing(self, sync_status_button):
        """E2E: Sync status button shows correct states for offline, synced, syncing."""
        with allure.step("Set status to offline - button hidden"):
            sync_status_button.set_status("offline")
            QApplication.processEvents()
            assert not sync_status_button.isVisible()

        with allure.step("Set status to synced - button visible"):
            sync_status_button.set_status("synced")
            QApplication.processEvents()
            assert sync_status_button.isVisible()
            assert "sync" in sync_status_button.toolTip().lower()

        with allure.step("Set status to syncing - button visible"):
            sync_status_button.set_status("syncing")
            QApplication.processEvents()
            assert sync_status_button.isVisible()
            assert "sync" in sync_status_button.toolTip().lower()

        attach_screenshot(sync_status_button, "SyncButton - Status States")

    @allure.title("AC #6: Sync button shows error, pending, and emits click signal")
    def test_sync_button_error_pending_and_signal(self, sync_status_button):
        """E2E: Sync button shows error/pending states and emits sync_requested signal."""
        from PySide6.QtTest import QSignalSpy

        with allure.step("Set status to error with message"):
            sync_status_button.set_status("error", error_message="Connection timeout")
            QApplication.processEvents()
            assert sync_status_button.isVisible()
            tooltip = sync_status_button.toolTip()
            assert "error" in tooltip.lower() or "timeout" in tooltip.lower()

        with allure.step("Set status with pending count"):
            sync_status_button.set_status("synced", pending_count=5)
            QApplication.processEvents()
            tooltip = sync_status_button.toolTip()
            assert "5" in tooltip or "pending" in tooltip.lower()

        with allure.step("Click sync button and verify signal"):
            spy = QSignalSpy(sync_status_button.sync_requested)
            sync_status_button.click()
            QApplication.processEvents()
            assert spy.count() == 1

        attach_screenshot(sync_status_button, "SyncButton - Error and Pending")


# =============================================================================
# Test Classes - Settings Persistence
# =============================================================================


@allure.story("QC-047.01 Cloud Sync Settings Persistence")
@allure.severity(allure.severity_level.CRITICAL)
class TestCloudSyncPersistence:
    """
    E2E tests for cloud sync settings persistence.
    Ensures settings survive application restarts.
    """

    @allure.title("Cloud sync settings persist to JSON")
    def test_cloud_sync_settings_persist(self, temp_config_path, colors):
        """E2E: Cloud sync settings are saved to JSON config file."""
        from src.contexts.settings.infra import UserSettingsRepository
        from src.contexts.settings.presentation import SettingsViewModel
        from src.contexts.settings.presentation.dialogs import SettingsDialog
        from src.shared.presentation.services import SettingsService

        with allure.step("Create settings with cloud sync enabled"):
            repo = UserSettingsRepository(config_path=temp_config_path)
            from src.shared.infra.event_bus import EventBus

            service = SettingsService(repo, EventBus())
            viewmodel = SettingsViewModel(settings_provider=service)

            dialog = SettingsDialog(viewmodel=viewmodel, colors=colors)
            dialog.show()
            QApplication.processEvents()

            # Set URL first, then enable cloud sync (URL required to enable)
            viewmodel.set_convex_url("https://test.convex.cloud")
            viewmodel.set_cloud_sync_enabled(True)
            QApplication.processEvents()

            # Trigger save via the service/repo path
            # The viewmodel auto-saves on changes, but let's verify
            dialog.close()

        with allure.step("Reload settings and verify persistence"):
            # Create new repo/viewmodel to simulate app restart
            repo2 = UserSettingsRepository(config_path=temp_config_path)
            settings = repo2.load()

            # Check that cloud sync settings were persisted
            assert settings.backend.cloud_sync_enabled is True
            assert settings.backend.convex_url == "https://test.convex.cloud"
