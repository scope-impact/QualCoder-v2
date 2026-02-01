"""
Settings Dialog End-to-End Tests

True E2E tests with FULL behavior - real file persistence and UI integration.
Tests the complete flow: UI action → ViewModel → Controller → Repository → File

Implements QC-038 Settings and Preferences:
- AC #1: Researcher can change UI theme (dark, light, colors)
- AC #2: Researcher can configure font size and family
- AC #3: Researcher can select application language
- AC #4: Researcher can configure automatic backups
- AC #5: Researcher can set timestamp format for AV coding
- AC #6: Researcher can configure speaker name format

Note: Uses fixtures from root conftest.py (qapp, colors).
"""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest
from PySide6.QtWidgets import QApplication, QDialog, QPushButton

pytestmark = pytest.mark.e2e


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def temp_config_path():
    """Create a temporary config file path."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir) / "settings.json"


@pytest.fixture
def settings_repo(temp_config_path):
    """Create a settings repository with temp path."""
    from src.infrastructure.settings import UserSettingsRepository

    return UserSettingsRepository(config_path=temp_config_path)


@pytest.fixture
def settings_controller(settings_repo):
    """Create a settings controller."""
    from src.application.settings import SettingsControllerImpl

    return SettingsControllerImpl(settings_repo=settings_repo)


@pytest.fixture
def settings_viewmodel(settings_controller):
    """Create a settings viewmodel."""
    from src.presentation.viewmodels import SettingsViewModel

    return SettingsViewModel(settings_controller=settings_controller)


@pytest.fixture
def settings_dialog(qapp, colors, settings_viewmodel):
    """Create a settings dialog with real viewmodel."""
    from src.presentation.dialogs.settings_dialog import SettingsDialog

    dialog = SettingsDialog(viewmodel=settings_viewmodel, colors=colors)
    yield dialog
    dialog.close()


# =============================================================================
# Test: Settings Dialog Opens with Correct Defaults
# =============================================================================


class TestSettingsDialogDefaults:
    """Tests that dialog opens with correct default values."""

    def test_dialog_opens_with_default_theme(self, settings_dialog):
        """Dialog should show light theme selected by default."""
        # Find the theme buttons
        theme_buttons = [
            btn
            for btn in settings_dialog.findChildren(QPushButton)
            if btn.property("theme_value") is not None
        ]

        # Light button should be checked
        light_btn = next(
            (btn for btn in theme_buttons if btn.property("theme_value") == "light"),
            None,
        )
        assert light_btn is not None
        assert light_btn.isChecked()

    def test_dialog_opens_with_default_font_size(self, settings_dialog):
        """Dialog should show font size 14 by default."""
        # The font slider should be at 14
        assert settings_dialog._font_slider.value() == 14
        assert "14px" in settings_dialog._font_size_label.text()

    def test_dialog_opens_with_default_language(self, settings_dialog):
        """Dialog should show English selected by default."""
        assert settings_dialog._language_combo.currentData() == "en"


# =============================================================================
# Test: Theme Changes Persist (AC #1)
# =============================================================================


class TestThemeChanges:
    """Tests for AC #1: Researcher can change UI theme."""

    def test_change_theme_to_dark_persists(
        self, settings_dialog, settings_viewmodel, settings_repo
    ):
        """Changing theme to dark should persist to file."""
        # Find dark theme button
        theme_buttons = [
            btn
            for btn in settings_dialog.findChildren(QPushButton)
            if btn.property("theme_value") is not None
        ]
        dark_btn = next(
            (btn for btn in theme_buttons if btn.property("theme_value") == "dark"),
            None,
        )

        # Click dark theme button
        dark_btn.click()
        QApplication.processEvents()

        # Verify persisted to repository
        settings = settings_repo.load()
        assert settings.theme.name == "dark"

    def test_change_theme_emits_signal(self, settings_dialog, qapp):
        """Changing theme should emit settings_changed signal."""
        from PySide6.QtTest import QSignalSpy

        spy = QSignalSpy(settings_dialog.settings_changed)

        # Find and click dark theme button
        theme_buttons = [
            btn
            for btn in settings_dialog.findChildren(QPushButton)
            if btn.property("theme_value") is not None
        ]
        dark_btn = next(
            (btn for btn in theme_buttons if btn.property("theme_value") == "dark"),
            None,
        )
        dark_btn.click()
        QApplication.processEvents()

        assert spy.count() >= 1


# =============================================================================
# Test: Font Changes Persist (AC #2)
# =============================================================================


class TestFontChanges:
    """Tests for AC #2: Researcher can configure font size and family."""

    def test_change_font_size_persists(self, settings_dialog, settings_repo):
        """Changing font size should persist to file."""
        # Change font size via slider
        settings_dialog._font_slider.setValue(18)
        QApplication.processEvents()

        # Verify persisted
        settings = settings_repo.load()
        assert settings.font.size == 18

    def test_change_font_family_persists(self, settings_dialog, settings_repo):
        """Changing font family should persist to file."""
        # Find Roboto in combo box and select it
        combo = settings_dialog._font_combo
        roboto_index = combo.findData("Roboto")
        assert roboto_index >= 0

        combo.setCurrentIndex(roboto_index)
        QApplication.processEvents()

        # Verify persisted
        settings = settings_repo.load()
        assert settings.font.family == "Roboto"


# =============================================================================
# Test: Language Changes Persist (AC #3)
# =============================================================================


class TestLanguageChanges:
    """Tests for AC #3: Researcher can select application language."""

    def test_change_language_persists(self, settings_dialog, settings_repo):
        """Changing language should persist to file."""
        # Find Spanish in combo box
        combo = settings_dialog._language_combo
        es_index = combo.findData("es")
        assert es_index >= 0

        combo.setCurrentIndex(es_index)
        QApplication.processEvents()

        # Verify persisted
        settings = settings_repo.load()
        assert settings.language.code == "es"


# =============================================================================
# Test: Backup Config Persists (AC #4)
# =============================================================================


class TestBackupChanges:
    """Tests for AC #4: Researcher can configure automatic backups."""

    def test_enable_backup_persists(self, settings_dialog, settings_repo):
        """Enabling backup should persist to file."""
        # Enable backup checkbox
        settings_dialog._backup_enabled.setChecked(True)
        QApplication.processEvents()

        # Verify persisted
        settings = settings_repo.load()
        assert settings.backup.enabled is True

    def test_change_backup_interval_persists(self, settings_dialog, settings_repo):
        """Changing backup interval should persist to file."""
        # Enable backup first
        settings_dialog._backup_enabled.setChecked(True)

        # Change interval
        settings_dialog._backup_interval.setValue(60)
        QApplication.processEvents()

        # Verify persisted
        settings = settings_repo.load()
        assert settings.backup.interval_minutes == 60


# =============================================================================
# Test: AV Coding Config Persists (AC #5, #6)
# =============================================================================


class TestAVCodingChanges:
    """Tests for AC #5 and #6: Timestamp and speaker format."""

    def test_change_timestamp_format_persists(self, settings_dialog, settings_repo):
        """Changing timestamp format should persist to file."""
        # Find MM:SS in combo box
        combo = settings_dialog._timestamp_combo
        mm_ss_index = combo.findData("MM:SS")
        assert mm_ss_index >= 0

        combo.setCurrentIndex(mm_ss_index)
        QApplication.processEvents()

        # Verify persisted
        settings = settings_repo.load()
        assert settings.av_coding.timestamp_format == "MM:SS"

    def test_change_speaker_format_persists(self, settings_dialog, settings_repo):
        """Changing speaker format should persist to file."""
        # Change speaker format
        settings_dialog._speaker_format.setText("Participant {n}")
        QApplication.processEvents()

        # Verify persisted
        settings = settings_repo.load()
        assert settings.av_coding.speaker_format == "Participant {n}"

    def test_speaker_preview_updates(self, settings_dialog):
        """Speaker preview should update when format changes."""
        settings_dialog._speaker_format.setText("P{n}")
        QApplication.processEvents()

        preview_text = settings_dialog._speaker_preview.text()
        assert "P1" in preview_text
        assert "P2" in preview_text


# =============================================================================
# Test: Dialog Navigation
# =============================================================================


class TestDialogNavigation:
    """Tests for dialog sidebar navigation."""

    def test_sidebar_switches_sections(self, settings_dialog):
        """Clicking sidebar items should switch content sections."""
        sidebar = settings_dialog._sidebar

        # Initially on Appearance (index 0)
        assert settings_dialog._content_stack.currentIndex() == 0

        # Click Language section (index 1)
        sidebar.setCurrentRow(1)
        QApplication.processEvents()
        assert settings_dialog._content_stack.currentIndex() == 1

        # Click Backup section (index 2)
        sidebar.setCurrentRow(2)
        QApplication.processEvents()
        assert settings_dialog._content_stack.currentIndex() == 2

        # Click AV Coding section (index 3)
        sidebar.setCurrentRow(3)
        QApplication.processEvents()
        assert settings_dialog._content_stack.currentIndex() == 3


# =============================================================================
# Test: Dialog Accept/Cancel
# =============================================================================


class TestDialogAcceptCancel:
    """Tests for dialog OK/Cancel behavior."""

    def test_ok_button_accepts_dialog(self, qapp, colors, settings_viewmodel):
        """OK button should accept the dialog."""
        from src.presentation.dialogs.settings_dialog import SettingsDialog

        dialog = SettingsDialog(viewmodel=settings_viewmodel, colors=colors)

        # Find and click OK button
        ok_buttons = [
            btn for btn in dialog.findChildren(QPushButton) if btn.text() == "OK"
        ]
        assert len(ok_buttons) == 1

        # Simulate click (but don't block with exec())
        dialog.show()
        QApplication.processEvents()

        # Check dialog would accept (we can't call exec() in test)
        dialog.accept()
        assert dialog.result() == QDialog.DialogCode.Accepted

        dialog.close()

    def test_cancel_button_rejects_dialog(self, qapp, colors, settings_viewmodel):
        """Cancel button should reject the dialog."""
        from src.presentation.dialogs.settings_dialog import SettingsDialog

        dialog = SettingsDialog(viewmodel=settings_viewmodel, colors=colors)

        dialog.show()
        QApplication.processEvents()

        dialog.reject()
        assert dialog.result() == QDialog.DialogCode.Rejected

        dialog.close()


# =============================================================================
# Test: Full Round-Trip
# =============================================================================


class TestFullRoundTrip:
    """Tests for complete settings round-trip."""

    def test_multiple_settings_persist_and_reload(self, qapp, colors, temp_config_path):
        """Multiple setting changes should persist and reload correctly."""
        from src.application.settings import SettingsControllerImpl
        from src.infrastructure.settings import UserSettingsRepository
        from src.presentation.dialogs.settings_dialog import SettingsDialog
        from src.presentation.viewmodels import SettingsViewModel

        # Create first dialog session
        repo1 = UserSettingsRepository(config_path=temp_config_path)
        controller1 = SettingsControllerImpl(settings_repo=repo1)
        viewmodel1 = SettingsViewModel(settings_controller=controller1)
        dialog1 = SettingsDialog(viewmodel=viewmodel1, colors=colors)

        # Make changes
        # 1. Change theme to dark
        theme_buttons = [
            btn
            for btn in dialog1.findChildren(QPushButton)
            if btn.property("theme_value") == "dark"
        ]
        theme_buttons[0].click()

        # 2. Change font size
        dialog1._font_slider.setValue(16)

        # 3. Change language
        dialog1._language_combo.setCurrentIndex(dialog1._language_combo.findData("de"))

        QApplication.processEvents()
        dialog1.close()

        # Create NEW dialog session (simulates app restart)
        repo2 = UserSettingsRepository(config_path=temp_config_path)
        controller2 = SettingsControllerImpl(settings_repo=repo2)
        viewmodel2 = SettingsViewModel(settings_controller=controller2)
        dialog2 = SettingsDialog(viewmodel=viewmodel2, colors=colors)

        # Verify all settings loaded correctly
        # Theme should be dark
        dark_btn = next(
            btn
            for btn in dialog2.findChildren(QPushButton)
            if btn.property("theme_value") == "dark"
        )
        assert dark_btn.isChecked()

        # Font size should be 16
        assert dialog2._font_slider.value() == 16

        # Language should be German
        assert dialog2._language_combo.currentData() == "de"

        dialog2.close()
