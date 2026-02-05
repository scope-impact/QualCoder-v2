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
    from src.shared.presentation.services import SettingsService

    return SettingsService(settings_repo)


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

    @allure.title("AC #1: Cloud sync checkbox exists in settings dialog")
    def test_cloud_sync_checkbox_exists(self, settings_dialog):
        """E2E: Settings dialog has cloud sync enable/disable checkbox."""
        with allure.step("Navigate to Database section"):
            settings_dialog._sidebar.setCurrentRow(4)
            QApplication.processEvents()

        with allure.step("Find cloud sync checkbox"):
            # Find the cloud sync checkbox by text
            cloud_sync_checkbox = None
            for cb in settings_dialog.findChildren(QCheckBox):
                if "cloud sync" in cb.text().lower():
                    cloud_sync_checkbox = cb
                    break

        with allure.step("Verify checkbox exists"):
            assert cloud_sync_checkbox is not None, "Cloud sync checkbox not found"
            assert "Convex" in cloud_sync_checkbox.text()

        attach_screenshot(settings_dialog, "Settings - Cloud Sync Checkbox")

    @allure.title("AC #1: Cloud sync is disabled by default")
    def test_cloud_sync_disabled_by_default(self, settings_dialog):
        """E2E: Cloud sync is off by default for new installations."""
        with allure.step("Navigate to Database section"):
            settings_dialog._sidebar.setCurrentRow(4)
            QApplication.processEvents()

        with allure.step("Find cloud sync checkbox"):
            cloud_sync_checkbox = None
            for cb in settings_dialog.findChildren(QCheckBox):
                if "cloud sync" in cb.text().lower():
                    cloud_sync_checkbox = cb
                    break

        with allure.step("Verify checkbox is unchecked by default"):
            assert cloud_sync_checkbox is not None
            assert not cloud_sync_checkbox.isChecked()

        attach_screenshot(settings_dialog, "Settings - Cloud Sync Default Off")

    @allure.title("AC #1: Enabling cloud sync shows Convex configuration")
    def test_enable_cloud_sync_shows_config(self, settings_dialog):
        """E2E: Checking cloud sync checkbox reveals Convex URL config."""
        with allure.step("Navigate to Database section"):
            # Database section is index 4 (Appearance=0, Language=1, Backup=2, AV=3, Database=4)
            settings_dialog._sidebar.setCurrentRow(4)
            QApplication.processEvents()

        with allure.step("Find cloud sync checkbox"):
            cloud_sync_checkbox = None
            for cb in settings_dialog.findChildren(QCheckBox):
                if "cloud sync" in cb.text().lower():
                    cloud_sync_checkbox = cb
                    break

        with allure.step("Enable cloud sync"):
            cloud_sync_checkbox.setChecked(True)
            QApplication.processEvents()

        with allure.step("Verify Convex config frame is visible"):
            # Access the internal frame directly
            convex_frame = settings_dialog._convex_config_frame
            assert convex_frame.isVisible(), "Convex config frame should be visible"

        with allure.step("Capture screenshot for documentation"):
            DocScreenshot.capture(
                settings_dialog, "settings-cloud-sync-enabled", max_width=800
            )

        attach_screenshot(settings_dialog, "Settings - Cloud Sync Enabled")

    @allure.title("AC #2: User can enter Convex URL")
    def test_enter_convex_url(self, settings_dialog):
        """E2E: User can configure the Convex deployment URL."""
        with allure.step("Navigate to Database section"):
            settings_dialog._sidebar.setCurrentRow(4)
            QApplication.processEvents()

        with allure.step("Enable cloud sync"):
            cloud_sync_checkbox = None
            for cb in settings_dialog.findChildren(QCheckBox):
                if "cloud sync" in cb.text().lower():
                    cloud_sync_checkbox = cb
                    break
            cloud_sync_checkbox.setChecked(True)
            QApplication.processEvents()

        with allure.step("Find Convex URL field"):
            convex_url_field = None
            for le in settings_dialog.findChildren(QLineEdit):
                if le.placeholderText() and "convex" in le.placeholderText().lower():
                    convex_url_field = le
                    break

        with allure.step("Enter Convex URL"):
            test_url = "https://my-project.convex.cloud"
            convex_url_field.setText(test_url)
            QApplication.processEvents()

        with allure.step("Verify URL is set"):
            assert convex_url_field.text() == test_url

        attach_screenshot(settings_dialog, "Settings - Convex URL Configured")

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

            # Enable
            cloud_sync_checkbox.setChecked(True)
            QApplication.processEvents()

            # Disable
            cloud_sync_checkbox.setChecked(False)
            QApplication.processEvents()

        with allure.step("Verify Convex config is hidden"):
            # Find the Convex config frame
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

    @allure.title("AC #6: Sync button hidden when offline")
    def test_sync_button_hidden_when_offline(self, sync_status_button):
        """E2E: Sync status button is hidden when cloud sync is disabled."""
        with allure.step("Set status to offline"):
            sync_status_button.set_status("offline")
            QApplication.processEvents()

        with allure.step("Verify button is hidden"):
            assert not sync_status_button.isVisible()

    @allure.title("AC #6: Sync button shows synced status")
    def test_sync_button_shows_synced(self, sync_status_button):
        """E2E: Sync button shows green check when synced."""
        with allure.step("Set status to synced"):
            sync_status_button.set_status("synced")
            QApplication.processEvents()

        with allure.step("Verify button is visible"):
            assert sync_status_button.isVisible()

        with allure.step("Verify tooltip"):
            assert "sync" in sync_status_button.toolTip().lower()

        attach_screenshot(sync_status_button, "SyncButton - Synced Status")

    @allure.title("AC #6: Sync button shows syncing status")
    def test_sync_button_shows_syncing(self, sync_status_button):
        """E2E: Sync button shows spinning icon when syncing."""
        with allure.step("Set status to syncing"):
            sync_status_button.set_status("syncing")
            QApplication.processEvents()

        with allure.step("Verify button is visible"):
            assert sync_status_button.isVisible()

        with allure.step("Verify tooltip indicates syncing"):
            assert "sync" in sync_status_button.toolTip().lower()

        attach_screenshot(sync_status_button, "SyncButton - Syncing Status")

    @allure.title("AC #6: Sync button shows error status")
    def test_sync_button_shows_error(self, sync_status_button):
        """E2E: Sync button shows error indicator with message."""
        with allure.step("Set status to error with message"):
            sync_status_button.set_status("error", error_message="Connection timeout")
            QApplication.processEvents()

        with allure.step("Verify button is visible"):
            assert sync_status_button.isVisible()

        with allure.step("Verify tooltip shows error"):
            tooltip = sync_status_button.toolTip()
            assert "error" in tooltip.lower() or "timeout" in tooltip.lower()

        attach_screenshot(sync_status_button, "SyncButton - Error Status")

    @allure.title("AC #6: Sync button shows pending count")
    def test_sync_button_shows_pending(self, sync_status_button):
        """E2E: Sync button tooltip shows pending changes count."""
        with allure.step("Set status to synced with pending changes"):
            sync_status_button.set_status("synced", pending_count=5)
            QApplication.processEvents()

        with allure.step("Verify pending count in tooltip"):
            tooltip = sync_status_button.toolTip()
            assert "5" in tooltip or "pending" in tooltip.lower()

        attach_screenshot(sync_status_button, "SyncButton - Pending Changes")

    @allure.title("AC #6: Clicking sync button emits signal")
    def test_sync_button_emits_signal(self, sync_status_button):
        """E2E: Clicking sync button emits sync_requested signal."""
        from PySide6.QtTest import QSignalSpy

        with allure.step("Set status to synced (clickable)"):
            sync_status_button.set_status("synced")
            QApplication.processEvents()

        with allure.step("Set up signal spy"):
            spy = QSignalSpy(sync_status_button.sync_requested)

        with allure.step("Click sync button"):
            sync_status_button.click()
            QApplication.processEvents()

        with allure.step("Verify signal was emitted"):
            assert spy.count() == 1


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
            service = SettingsService(repo)
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
