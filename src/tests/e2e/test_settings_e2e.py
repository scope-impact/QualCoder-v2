"""
Settings Dialog End-to-End Tests

True E2E tests with FULL behavior - real file persistence and UI integration.
Tests the complete flow: UI action → Dialog → ViewModel → Service → Repository → JSON File

These tests:
1. Create a temporary JSON config file for settings persistence
2. Wire up SettingsViewModel with real UserSettingsRepository
3. Create SettingsDialog with real viewmodel
4. Test full round-trip data flows

Implements QC-038 Settings and Preferences:
- AC #1: Researcher can change UI theme (dark, light, colors)
- AC #2: Researcher can configure font size and family
- AC #3: Researcher can select application language
- AC #4: Researcher can configure automatic backups
- AC #5: Researcher can set timestamp format for AV coding
- AC #6: Researcher can configure speaker name format

Note: Uses fixtures from root conftest.py (qapp, colors) and local fixtures.

Reference: See test_open_navigate_project_e2e.py for Allure reporting patterns.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

import allure
import pytest
from PySide6.QtWidgets import QApplication, QDialog, QPushButton

pytestmark = [
    pytest.mark.e2e,
    allure.epic("QualCoder v2"),
    allure.feature("QC-038 Settings and Preferences"),
]


# =============================================================================
# Persistence Layer Fixtures
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


# =============================================================================
# Application Layer Fixtures
# =============================================================================


@pytest.fixture
def settings_provider(settings_repo):
    """Create a settings service for use as a provider."""
    from src.presentation.services import SettingsService

    return SettingsService(settings_repo)


@pytest.fixture
def settings_viewmodel(settings_provider):
    """Create SettingsViewModel with real service."""
    from src.presentation.viewmodels import SettingsViewModel

    return SettingsViewModel(settings_provider=settings_provider)


# =============================================================================
# Dialog Fixtures
# =============================================================================


@pytest.fixture
def settings_dialog(qapp, colors, settings_viewmodel):
    """
    Create a complete Settings Dialog for E2E testing with real persistence.

    This fixture creates a real dialog with SettingsViewModel backed by
    a JSON file in a temporary directory.
    """
    from src.presentation.dialogs.settings_dialog import SettingsDialog

    dialog = SettingsDialog(viewmodel=settings_viewmodel, colors=colors)
    yield dialog
    dialog.close()


# =============================================================================
# Test Classes - Settings Dialog Defaults
# =============================================================================


@allure.story("Settings Dialog Defaults")
@allure.severity(allure.severity_level.NORMAL)
class TestSettingsDialogDefaults:
    """E2E tests for Settings Dialog default values."""

    @allure.title("Dialog opens with light theme selected by default")
    def test_dialog_opens_with_default_theme(self, settings_dialog):
        """E2E: Dialog displays light theme selected by default."""
        with allure.step("Find theme buttons in dialog"):
            theme_buttons = [
                btn
                for btn in settings_dialog.findChildren(QPushButton)
                if btn.property("theme_value") is not None
            ]

        with allure.step("Verify light theme button is checked"):
            light_btn = next(
                (
                    btn
                    for btn in theme_buttons
                    if btn.property("theme_value") == "light"
                ),
                None,
            )
            assert light_btn is not None
            assert light_btn.isChecked()

    @allure.title("Dialog opens with font size 14 by default")
    def test_dialog_opens_with_default_font_size(self, settings_dialog):
        """E2E: Dialog displays font size 14 by default."""
        with allure.step("Verify font slider default value"):
            assert settings_dialog._font_slider.value() == 14

        with allure.step("Verify font size label shows 14px"):
            assert "14px" in settings_dialog._font_size_label.text()

    @allure.title("Dialog opens with English selected by default")
    def test_dialog_opens_with_default_language(self, settings_dialog):
        """E2E: Dialog displays English selected by default."""
        with allure.step("Verify language combo shows English"):
            assert settings_dialog._language_combo.currentData() == "en"


# =============================================================================
# Test Classes - Theme Changes (AC #1)
# =============================================================================


@allure.story("QC-038.02 Change UI Theme")
@allure.severity(allure.severity_level.CRITICAL)
class TestThemeChanges:
    """
    E2E tests for theme change flow.
    AC #1: Researcher can change UI theme (dark, light, colors).
    """

    @allure.title("AC #1: Changing theme to dark persists to JSON file")
    @allure.link("QC-038", name="Backlog Task")
    def test_change_theme_to_dark_persists_to_file(
        self, settings_dialog, settings_viewmodel, settings_repo
    ):
        """E2E: Changing theme via UI persists to JSON file."""
        with allure.step("Find dark theme button in dialog"):
            theme_buttons = [
                btn
                for btn in settings_dialog.findChildren(QPushButton)
                if btn.property("theme_value") is not None
            ]
            dark_btn = next(
                (btn for btn in theme_buttons if btn.property("theme_value") == "dark"),
                None,
            )

        with allure.step("Click dark theme button"):
            dark_btn.click()
            QApplication.processEvents()

        with allure.step("Verify theme persisted to repository"):
            settings = settings_repo.load()
            assert settings.theme.name == "dark"

    @allure.title("AC #1: Changing theme emits settings_changed signal")
    def test_change_theme_emits_settings_changed_signal(self, settings_dialog, qapp):
        """E2E: Changing theme emits settings_changed signal for reactive updates."""
        from PySide6.QtTest import QSignalSpy

        with allure.step("Set up signal spy"):
            spy = QSignalSpy(settings_dialog.settings_changed)

        with allure.step("Find and click dark theme button"):
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

        with allure.step("Verify signal emitted"):
            assert spy.count() >= 1


# =============================================================================
# Test Classes - Font Changes (AC #2)
# =============================================================================


@allure.story("QC-038.03 Configure Fonts")
@allure.severity(allure.severity_level.CRITICAL)
class TestFontChanges:
    """
    E2E tests for font configuration flow.
    AC #2: Researcher can configure font size and family.
    """

    @allure.title("AC #2: Changing font size via slider persists to JSON file")
    @allure.link("QC-038", name="Backlog Task")
    def test_change_font_size_via_slider_persists_to_file(
        self, settings_dialog, settings_repo
    ):
        """E2E: Changing font size via slider persists to JSON file."""
        with allure.step("Change font size to 18 via slider"):
            settings_dialog._font_slider.setValue(18)
            QApplication.processEvents()

        with allure.step("Verify font size persisted to repository"):
            settings = settings_repo.load()
            assert settings.font.size == 18

    @allure.title("AC #2: Changing font family via combo persists to JSON file")
    def test_change_font_family_via_combo_persists_to_file(
        self, settings_dialog, settings_repo
    ):
        """E2E: Changing font family via combo box persists to JSON file."""
        with allure.step("Find Roboto in combo box"):
            combo = settings_dialog._font_combo
            roboto_index = combo.findData("Roboto")
            assert roboto_index >= 0

        with allure.step("Select Roboto font"):
            combo.setCurrentIndex(roboto_index)
            QApplication.processEvents()

        with allure.step("Verify font family persisted to repository"):
            settings = settings_repo.load()
            assert settings.font.family == "Roboto"


# =============================================================================
# Test Classes - Language Changes (AC #3)
# =============================================================================


@allure.story("QC-038.04 Select Language")
@allure.severity(allure.severity_level.CRITICAL)
class TestLanguageChanges:
    """
    E2E tests for language selection flow.
    AC #3: Researcher can select application language.
    """

    @allure.title("AC #3: Selecting language via combo persists to JSON file")
    @allure.link("QC-038", name="Backlog Task")
    def test_change_language_via_combo_persists_to_file(
        self, settings_dialog, settings_repo
    ):
        """E2E: Selecting language via combo box persists to JSON file."""
        with allure.step("Find Spanish in language combo"):
            combo = settings_dialog._language_combo
            es_index = combo.findData("es")
            assert es_index >= 0

        with allure.step("Select Spanish language"):
            combo.setCurrentIndex(es_index)
            QApplication.processEvents()

        with allure.step("Verify language persisted to repository"):
            settings = settings_repo.load()
            assert settings.language.code == "es"


# =============================================================================
# Test Classes - Backup Config (AC #4)
# =============================================================================


@allure.story("QC-038.01 Configure Backups")
@allure.severity(allure.severity_level.CRITICAL)
class TestBackupChanges:
    """
    E2E tests for backup configuration flow.
    AC #4: Researcher can configure automatic backups.
    """

    @allure.title("AC #4: Enabling backup via checkbox persists to JSON file")
    @allure.link("QC-038", name="Backlog Task")
    def test_enable_backup_via_checkbox_persists_to_file(
        self, settings_dialog, settings_repo
    ):
        """E2E: Enabling backup via checkbox persists to JSON file."""
        with allure.step("Enable backup checkbox"):
            settings_dialog._backup_enabled.setChecked(True)
            QApplication.processEvents()

        with allure.step("Verify backup enabled in repository"):
            settings = settings_repo.load()
            assert settings.backup.enabled is True

    @allure.title("AC #4: Changing backup interval via spinbox persists to JSON file")
    def test_change_backup_interval_via_spinbox_persists_to_file(
        self, settings_dialog, settings_repo
    ):
        """E2E: Changing backup interval via spinbox persists to JSON file."""
        with allure.step("Enable backup first"):
            settings_dialog._backup_enabled.setChecked(True)

        with allure.step("Change backup interval to 60 minutes"):
            settings_dialog._backup_interval.setValue(60)
            QApplication.processEvents()

        with allure.step("Verify interval persisted to repository"):
            settings = settings_repo.load()
            assert settings.backup.interval_minutes == 60


# =============================================================================
# Test Classes - AV Coding Config (AC #5, #6)
# =============================================================================


@allure.story("QC-038.05 Configure Timestamp Format")
@allure.severity(allure.severity_level.CRITICAL)
class TestAVCodingChanges:
    """
    E2E tests for AV coding configuration flow.
    AC #5: Researcher can set timestamp format for AV coding.
    AC #6: Researcher can configure speaker name format.
    """

    @allure.title("AC #5: Changing timestamp format via combo persists to JSON file")
    @allure.link("QC-038", name="Backlog Task")
    def test_change_timestamp_format_via_combo_persists_to_file(
        self, settings_dialog, settings_repo
    ):
        """E2E: Changing timestamp format via combo box persists to JSON file."""
        with allure.step("Find MM:SS format in combo"):
            combo = settings_dialog._timestamp_combo
            mm_ss_index = combo.findData("MM:SS")
            assert mm_ss_index >= 0

        with allure.step("Select MM:SS format"):
            combo.setCurrentIndex(mm_ss_index)
            QApplication.processEvents()

        with allure.step("Verify timestamp format persisted to repository"):
            settings = settings_repo.load()
            assert settings.av_coding.timestamp_format == "MM:SS"

    @allure.title("AC #6: Changing speaker format via input persists to JSON file")
    def test_change_speaker_format_via_input_persists_to_file(
        self, settings_dialog, settings_repo
    ):
        """E2E: Changing speaker format via text input persists to JSON file."""
        with allure.step("Enter custom speaker format"):
            settings_dialog._speaker_format.setText("Participant {n}")
            QApplication.processEvents()

        with allure.step("Verify speaker format persisted to repository"):
            settings = settings_repo.load()
            assert settings.av_coding.speaker_format == "Participant {n}"

    @allure.title("AC #6: Speaker preview updates reactively on format change")
    def test_speaker_preview_updates_on_format_change(self, settings_dialog):
        """E2E: Speaker preview updates reactively when format changes."""
        with allure.step("Enter short speaker format"):
            settings_dialog._speaker_format.setText("P{n}")
            QApplication.processEvents()

        with allure.step("Verify preview shows formatted names"):
            preview_text = settings_dialog._speaker_preview.text()
            assert "P1" in preview_text
            assert "P2" in preview_text


# =============================================================================
# Test Classes - Dialog Navigation
# =============================================================================


@allure.story("Dialog Navigation")
@allure.severity(allure.severity_level.NORMAL)
class TestDialogNavigation:
    """E2E tests for dialog sidebar navigation."""

    @allure.title("Sidebar navigation switches content sections")
    def test_sidebar_switches_content_sections(self, settings_dialog):
        """E2E: Clicking sidebar items switches content sections."""
        sidebar = settings_dialog._sidebar

        with allure.step("Verify initially on Appearance section"):
            assert settings_dialog._content_stack.currentIndex() == 0

        with allure.step("Click Language section in sidebar"):
            sidebar.setCurrentRow(1)
            QApplication.processEvents()
            assert settings_dialog._content_stack.currentIndex() == 1

        with allure.step("Click Backup section in sidebar"):
            sidebar.setCurrentRow(2)
            QApplication.processEvents()
            assert settings_dialog._content_stack.currentIndex() == 2

        with allure.step("Click AV Coding section in sidebar"):
            sidebar.setCurrentRow(3)
            QApplication.processEvents()
            assert settings_dialog._content_stack.currentIndex() == 3


# =============================================================================
# Test Classes - Dialog Accept/Cancel
# =============================================================================


@allure.story("Dialog Accept/Cancel")
@allure.severity(allure.severity_level.NORMAL)
class TestDialogAcceptCancel:
    """E2E tests for dialog OK/Cancel behavior."""

    @allure.title("OK button accepts the dialog")
    def test_ok_button_accepts_dialog(self, qapp, colors, settings_viewmodel):
        """E2E: OK button accepts the dialog with Accepted result code."""
        from src.presentation.dialogs.settings_dialog import SettingsDialog

        with allure.step("Create settings dialog"):
            dialog = SettingsDialog(viewmodel=settings_viewmodel, colors=colors)

        with allure.step("Verify OK button exists"):
            ok_buttons = [
                btn for btn in dialog.findChildren(QPushButton) if btn.text() == "OK"
            ]
            assert len(ok_buttons) == 1

        with allure.step("Show dialog and accept"):
            dialog.show()
            QApplication.processEvents()
            dialog.accept()

        with allure.step("Verify dialog result is Accepted"):
            assert dialog.result() == QDialog.DialogCode.Accepted
            dialog.close()

    @allure.title("Cancel button rejects the dialog")
    def test_cancel_button_rejects_dialog(self, qapp, colors, settings_viewmodel):
        """E2E: Cancel button rejects the dialog with Rejected result code."""
        from src.presentation.dialogs.settings_dialog import SettingsDialog

        with allure.step("Create and show settings dialog"):
            dialog = SettingsDialog(viewmodel=settings_viewmodel, colors=colors)
            dialog.show()
            QApplication.processEvents()

        with allure.step("Reject dialog"):
            dialog.reject()

        with allure.step("Verify dialog result is Rejected"):
            assert dialog.result() == QDialog.DialogCode.Rejected
            dialog.close()


# =============================================================================
# Test Classes - Full Round-Trip (All ACs)
# =============================================================================


@allure.story("QC-038 Integration")
@allure.severity(allure.severity_level.CRITICAL)
class TestFullRoundTrip:
    """
    E2E tests for complete settings round-trip.
    Verifies all ACs together with persistence and reload.
    """

    @allure.title("Complete workflow: All 6 ACs persist to JSON and reload correctly")
    @allure.link("QC-038", name="Backlog Task")
    def test_all_settings_persist_and_reload_after_restart(
        self, qapp, colors, temp_config_path
    ):
        """
        E2E: All settings persist to JSON file and reload correctly.

        This test verifies complete round-trip for ALL 6 acceptance criteria:
        - AC #1: Theme (dark)
        - AC #2: Font size (16) and family (Roboto)
        - AC #3: Language (German)
        - AC #4: Backup enabled (True) and interval (45 minutes)
        - AC #5: Timestamp format (MM:SS)
        - AC #6: Speaker format (Interviewee {n})

        Flow: Dialog1 → JSON File → Dialog2 (verify reload)
        """
        from src.contexts.settings.infra import UserSettingsRepository
        from src.presentation.dialogs.settings_dialog import SettingsDialog
        from src.presentation.services import SettingsService
        from src.presentation.viewmodels import SettingsViewModel

        # =========================================================================
        # Session 1: Make changes to all settings
        # =========================================================================

        with allure.step("Create first dialog session"):
            repo1 = UserSettingsRepository(config_path=temp_config_path)
            provider1 = SettingsService(repo1)
            viewmodel1 = SettingsViewModel(settings_provider=provider1)
            dialog1 = SettingsDialog(viewmodel=viewmodel1, colors=colors)

        with allure.step("AC #1: Change theme to dark"):
            theme_buttons = [
                btn
                for btn in dialog1.findChildren(QPushButton)
                if btn.property("theme_value") == "dark"
            ]
            theme_buttons[0].click()

        with allure.step("AC #2: Change font size to 16"):
            dialog1._font_slider.setValue(16)

        with allure.step("AC #2: Change font family to Roboto"):
            roboto_index = dialog1._font_combo.findData("Roboto")
            dialog1._font_combo.setCurrentIndex(roboto_index)

        with allure.step("AC #3: Change language to German"):
            de_index = dialog1._language_combo.findData("de")
            dialog1._language_combo.setCurrentIndex(de_index)

        with allure.step("AC #4: Enable backup and set interval to 45 minutes"):
            dialog1._backup_enabled.setChecked(True)
            dialog1._backup_interval.setValue(45)

        with allure.step("AC #5: Change timestamp format to MM:SS"):
            mm_ss_index = dialog1._timestamp_combo.findData("MM:SS")
            dialog1._timestamp_combo.setCurrentIndex(mm_ss_index)

        with allure.step("AC #6: Change speaker format to custom"):
            dialog1._speaker_format.setText("Interviewee {n}")

        with allure.step("Close dialog (settings persisted to JSON)"):
            QApplication.processEvents()
            dialog1.close()

        # =========================================================================
        # Verify JSON file contains all settings
        # =========================================================================

        with allure.step("Verify all settings written to JSON file"):
            settings = repo1.load()
            assert settings.theme.name == "dark", "Theme not persisted"
            assert settings.font.size == 16, "Font size not persisted"
            assert settings.font.family == "Roboto", "Font family not persisted"
            assert settings.language.code == "de", "Language not persisted"
            assert settings.backup.enabled is True, "Backup enabled not persisted"
            assert settings.backup.interval_minutes == 45, (
                "Backup interval not persisted"
            )
            assert settings.av_coding.timestamp_format == "MM:SS", (
                "Timestamp not persisted"
            )
            assert settings.av_coding.speaker_format == "Interviewee {n}", (
                "Speaker format not persisted"
            )

        # =========================================================================
        # Session 2: Create new dialog and verify settings loaded from JSON
        # =========================================================================

        with allure.step("Create NEW dialog session (simulates app restart)"):
            repo2 = UserSettingsRepository(config_path=temp_config_path)
            provider2 = SettingsService(repo2)
            viewmodel2 = SettingsViewModel(settings_provider=provider2)
            dialog2 = SettingsDialog(viewmodel=viewmodel2, colors=colors)

        with allure.step("AC #1: Verify theme loaded as dark"):
            dark_btn = next(
                btn
                for btn in dialog2.findChildren(QPushButton)
                if btn.property("theme_value") == "dark"
            )
            assert dark_btn.isChecked(), "Theme not loaded from JSON"

        with allure.step("AC #2: Verify font size loaded as 16"):
            assert dialog2._font_slider.value() == 16, "Font size not loaded from JSON"

        with allure.step("AC #2: Verify font family loaded as Roboto"):
            assert dialog2._font_combo.currentData() == "Roboto", (
                "Font family not loaded from JSON"
            )

        with allure.step("AC #3: Verify language loaded as German"):
            assert dialog2._language_combo.currentData() == "de", (
                "Language not loaded from JSON"
            )

        with allure.step("AC #4: Verify backup enabled loaded as True"):
            assert dialog2._backup_enabled.isChecked() is True, (
                "Backup enabled not loaded from JSON"
            )

        with allure.step("AC #4: Verify backup interval loaded as 45"):
            assert dialog2._backup_interval.value() == 45, (
                "Backup interval not loaded from JSON"
            )

        with allure.step("AC #5: Verify timestamp format loaded as MM:SS"):
            assert dialog2._timestamp_combo.currentData() == "MM:SS", (
                "Timestamp format not loaded from JSON"
            )

        with allure.step("AC #6: Verify speaker format loaded as custom"):
            assert dialog2._speaker_format.text() == "Interviewee {n}", (
                "Speaker format not loaded from JSON"
            )

        with allure.step("Close dialog"):
            dialog2.close()


# =============================================================================
# Test Classes - UI Application (Theme/Font Actually Change)
# =============================================================================


@allure.story("QC-038 UI Application")
@allure.severity(allure.severity_level.CRITICAL)
class TestUIApplication:
    """
    E2E tests verifying settings actually change the UI.
    Tests that theme and font changes are applied to the application.
    """

    @allure.title("Theme change applies to AppShell and updates colors")
    @allure.link("QC-038", name="Backlog Task")
    def test_theme_change_applies_to_ui(self, qapp, temp_config_path):
        """
        E2E: Changing theme actually changes the UI colors.

        Verifies:
        1. AppShell starts with light theme colors
        2. After apply_theme('dark'), colors change to dark palette
        """
        from design_system import get_colors, get_theme
        from src.presentation.templates.app_shell import AppShell

        with allure.step("Create AppShell with light theme (default)"):
            light_colors = get_theme("light")
            shell = AppShell(colors=light_colors)

        with allure.step("Verify initial colors are light theme"):
            initial_bg = shell._colors.background
            assert initial_bg == light_colors.background

        with allure.step("Apply dark theme"):
            shell.apply_theme("dark")
            QApplication.processEvents()

        with allure.step("Verify colors changed to dark theme"):
            dark_colors = get_theme("dark")
            # After applying theme, global get_colors() returns dark
            current_colors = get_colors()
            assert current_colors.background == dark_colors.background
            assert shell._colors.background == dark_colors.background

        with allure.step("Cleanup"):
            shell.close()

    @allure.title("Font change applies to QApplication")
    def test_font_change_applies_to_ui(self, qapp):
        """
        E2E: Changing font actually changes the application font.

        Verifies:
        1. Get initial app font
        2. After apply_font(), app font changes
        """
        from design_system import get_colors
        from src.presentation.templates.app_shell import AppShell

        with allure.step("Create AppShell"):
            shell = AppShell(colors=get_colors())

        with allure.step("Get initial font"):
            _ = qapp.font()  # Just verify we can get the font

        with allure.step("Apply Roboto font at size 18"):
            shell.apply_font("Roboto", 18)
            QApplication.processEvents()

        with allure.step("Verify app font changed"):
            new_font = qapp.font()
            assert new_font.family() == "Roboto"
            assert new_font.pointSize() == 18

        with allure.step("Cleanup"):
            shell.close()

    @allure.title("load_and_apply_settings restores theme and font from JSON")
    def test_load_and_apply_settings_from_repository(self, qapp, temp_config_path):
        """
        E2E: Settings loaded from repository are applied to UI at startup.

        Verifies complete flow:
        1. Save dark theme + custom font to JSON
        2. Create new AppShell
        3. Call load_and_apply_settings()
        4. Verify theme and font applied
        """
        from design_system import get_colors, get_theme
        from src.contexts.settings.infra import UserSettingsRepository
        from src.presentation.templates.app_shell import AppShell

        with allure.step("Save dark theme and Roboto 16px to JSON"):
            repo = UserSettingsRepository(config_path=temp_config_path)
            settings = repo.load()
            # Modify settings
            settings = settings.with_theme(settings.theme.with_name("dark"))
            settings = settings.with_font(
                settings.font.with_family("Roboto").with_size(16)
            )
            repo.save(settings)

        with allure.step("Verify settings saved"):
            saved = repo.load()
            assert saved.theme.name == "dark"
            assert saved.font.family == "Roboto"
            assert saved.font.size == 16

        with allure.step("Create new AppShell and load settings"):
            shell = AppShell(colors=get_colors())
            shell.load_and_apply_settings(repo)
            QApplication.processEvents()

        with allure.step("Verify dark theme applied"):
            dark_colors = get_theme("dark")
            current_colors = get_colors()
            assert current_colors.background == dark_colors.background

        with allure.step("Verify font applied"):
            app_font = qapp.font()
            assert app_font.family() == "Roboto"
            assert app_font.pointSize() == 16

        with allure.step("Cleanup"):
            shell.close()

    @allure.title("Live settings update: theme changes while dialog is open")
    def test_live_settings_update_theme(self, qapp, temp_config_path):
        """
        E2E: Changing theme in open dialog immediately updates AppShell.

        This tests the full wired flow:
        1. AppShell with settings_changed connected
        2. User changes theme in dialog
        3. settings_changed signal fires
        4. AppShell.apply_theme() is called
        5. UI colors change immediately
        """
        from design_system import get_colors, get_theme
        from src.contexts.settings.infra import UserSettingsRepository
        from src.presentation.dialogs.settings_dialog import SettingsDialog
        from src.presentation.services.settings_service import SettingsService
        from src.presentation.templates.app_shell import AppShell
        from src.presentation.viewmodels import SettingsViewModel

        with allure.step("Create AppShell with light theme"):
            light_colors = get_theme("light")
            shell = AppShell(colors=light_colors)
            repo = UserSettingsRepository(config_path=temp_config_path)
            shell.load_and_apply_settings(repo)

        with allure.step("Verify initial theme is light"):
            assert shell._colors.background == light_colors.background

        with allure.step("Open settings dialog (non-blocking for test)"):
            settings_service = SettingsService(repo)
            viewmodel = SettingsViewModel(settings_provider=settings_service)
            dialog = SettingsDialog(
                viewmodel=viewmodel,
                colors=shell._colors,
                parent=shell,
            )

            # Wire up the same way AppShell.open_settings_dialog does
            def on_settings_changed():
                settings = repo.load()
                if settings.theme.name in ("light", "dark"):
                    shell.apply_theme(settings.theme.name)
                shell.apply_font(settings.font.family, settings.font.size)

            dialog.settings_changed.connect(on_settings_changed)
            dialog.show()
            QApplication.processEvents()

        with allure.step("Change theme to dark in dialog"):
            dark_btn = next(
                btn
                for btn in dialog.findChildren(QPushButton)
                if btn.property("theme_value") == "dark"
            )
            dark_btn.click()
            QApplication.processEvents()

        with allure.step("Verify AppShell colors changed to dark immediately"):
            dark_colors = get_theme("dark")
            current_colors = get_colors()
            assert current_colors.background == dark_colors.background
            assert shell._colors.background == dark_colors.background

        with allure.step("Cleanup"):
            dialog.close()
            shell.close()
