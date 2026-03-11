"""
AppShell Settings Integration Tests

Tests for Settings button integration in AppShell.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

import allure
import pytest
from PySide6.QtWidgets import QApplication, QPushButton

pytestmark = pytest.mark.e2e


@allure.epic("Shared Presentation")
@allure.feature("Shared Presentation")
@allure.story("QC-000.11 App Shell")
class TestAppShellSettingsButton:
    """Tests for settings button in AppShell."""

    @allure.title("Settings button exists, is visible, and emits signal on click")
    def test_settings_button_exists_visible_emits_signal(self, qapp, colors):
        """AppShell has a visible settings button in the nav bar that emits settings_clicked."""
        from PySide6.QtTest import QSignalSpy

        from src.shared.presentation.templates.app_shell import AppShell, UnifiedNavBar

        shell = AppShell(colors=colors)
        shell.show()
        QApplication.processEvents()

        # Button exists in nav bar
        nav_bar = shell.findChild(UnifiedNavBar)
        assert nav_bar is not None
        settings_btn = nav_bar.findChild(QPushButton, "settings_button")
        assert settings_btn is not None
        assert settings_btn.isVisible()

        # Emits signal on click
        spy = QSignalSpy(shell.settings_clicked)
        settings_btn.click()
        QApplication.processEvents()
        assert spy.count() >= 1

        shell.close()

    @allure.title("Signal can be connected to open a settings dialog")
    def test_can_connect_settings_signal_to_handler(self, qapp, colors):
        """Should be able to connect settings_clicked to a handler."""
        from src.shared.presentation.templates.app_shell import AppShell

        shell = AppShell(colors=colors)
        handler_called = []

        shell.settings_clicked.connect(lambda: handler_called.append(True))

        settings_btn = shell.findChild(QPushButton, "settings_button")
        settings_btn.click()
        QApplication.processEvents()

        assert len(handler_called) == 1
        shell.close()

    @allure.title("Full settings workflow: click -> dialog -> change -> persist")
    def test_full_settings_workflow(self, qapp, colors):
        """Full workflow: click settings -> open dialog -> make change -> persist."""
        from src.contexts.settings.infra import UserSettingsRepository
        from src.contexts.settings.presentation import SettingsViewModel
        from src.contexts.settings.presentation.dialogs import SettingsDialog
        from src.shared.infra.event_bus import EventBus
        from src.shared.presentation.services import SettingsService
        from src.shared.presentation.templates.app_shell import AppShell

        shell = AppShell(colors=colors)

        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "settings.json"
            repo = UserSettingsRepository(config_path=config_path)
            event_bus = EventBus()
            provider = SettingsService(repo, event_bus=event_bus)
            viewmodel = SettingsViewModel(settings_provider=provider)

            dialog_opened = []

            def on_settings_clicked():
                dialog = SettingsDialog(
                    viewmodel=viewmodel, colors=colors, parent=shell
                )
                dialog_opened.append(dialog)
                dialog.show()
                QApplication.processEvents()

                theme_buttons = [
                    btn
                    for btn in dialog.findChildren(QPushButton)
                    if btn.property("theme_value") == "dark"
                ]
                if theme_buttons:
                    theme_buttons[0].click()
                    QApplication.processEvents()

                dialog.close()

            shell.settings_clicked.connect(on_settings_clicked)

            settings_btn = shell.findChild(QPushButton, "settings_button")
            settings_btn.click()
            QApplication.processEvents()

            assert len(dialog_opened) == 1
            settings = repo.load()
            assert settings.theme.name == "dark"

        shell.close()
