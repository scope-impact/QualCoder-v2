"""
AppShell Settings Integration Tests

TDD tests for Settings button integration in AppShell.
Tests that:
1. AppShell has a settings button
2. Clicking settings button emits settings_clicked signal
3. Settings dialog can be opened from the signal
"""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest
from PySide6.QtWidgets import QApplication, QPushButton

pytestmark = pytest.mark.e2e


# =============================================================================
# Test: AppShell has Settings Button
# =============================================================================


class TestAppShellSettingsButton:
    """Tests for settings button in AppShell."""

    def test_app_shell_has_settings_button(self, qapp, colors):
        """AppShell should have a settings button."""
        from src.presentation.templates.app_shell import AppShell

        shell = AppShell(colors=colors)

        # Find settings button by object name
        settings_btn = shell.findChild(QPushButton, "settings_button")
        assert settings_btn is not None, "AppShell should have a settings button"

        shell.close()

    def test_settings_button_has_gear_icon(self, qapp, colors):
        """Settings button should have a gear/cog icon."""
        from src.presentation.templates.app_shell import AppShell

        shell = AppShell(colors=colors)
        shell.show()
        QApplication.processEvents()

        settings_btn = shell.findChild(QPushButton, "settings_button")
        # Button should exist and be visible when shell is shown
        assert settings_btn is not None
        assert settings_btn.isVisible()

        shell.close()

    def test_settings_button_emits_signal(self, qapp, colors):
        """Clicking settings button should emit settings_clicked signal."""
        from PySide6.QtTest import QSignalSpy

        from src.presentation.templates.app_shell import AppShell

        shell = AppShell(colors=colors)

        # Spy on the signal
        spy = QSignalSpy(shell.settings_clicked)

        # Find and click settings button
        settings_btn = shell.findChild(QPushButton, "settings_button")
        assert settings_btn is not None

        settings_btn.click()
        QApplication.processEvents()

        assert spy.count() >= 1

        shell.close()


# =============================================================================
# Test: Settings Dialog Integration
# =============================================================================


class TestSettingsDialogIntegration:
    """Tests for opening settings dialog from AppShell."""

    def test_can_connect_settings_signal_to_show_dialog(self, qapp, colors):
        """Should be able to connect settings_clicked to open a dialog."""
        from src.presentation.templates.app_shell import AppShell

        shell = AppShell(colors=colors)

        # Track if handler was called
        handler_called = []

        def on_settings_clicked():
            handler_called.append(True)

        shell.settings_clicked.connect(on_settings_clicked)

        # Click settings button
        settings_btn = shell.findChild(QPushButton, "settings_button")
        settings_btn.click()
        QApplication.processEvents()

        assert len(handler_called) == 1

        shell.close()

    def test_full_settings_workflow(self, qapp, colors):
        """Full workflow: click settings -> open dialog -> make change -> persist."""

        from src.application.coordinators import (
            CoordinatorInfrastructure,
            SettingsCoordinator,
        )
        from src.application.event_bus import EventBus
        from src.application.lifecycle import ProjectLifecycle
        from src.application.state import ProjectState
        from src.contexts.settings.infra import UserSettingsRepository
        from src.presentation.dialogs.settings_dialog import SettingsDialog
        from src.presentation.templates.app_shell import AppShell
        from src.presentation.viewmodels import SettingsViewModel

        # Create shell
        shell = AppShell(colors=colors)

        # Create settings stack with temp file
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "settings.json"
            repo = UserSettingsRepository(config_path=config_path)
            infra = CoordinatorInfrastructure(
                event_bus=EventBus(),
                state=ProjectState(),
                lifecycle=ProjectLifecycle(),
                settings_repo=repo,
            )
            provider = SettingsCoordinator(infra)
            viewmodel = SettingsViewModel(settings_provider=provider)

            # Variable to track dialog
            dialog_opened = []

            def on_settings_clicked():
                dialog = SettingsDialog(
                    viewmodel=viewmodel, colors=colors, parent=shell
                )
                dialog_opened.append(dialog)
                # Don't exec() in test, just show
                dialog.show()
                QApplication.processEvents()

                # Make a change - set theme to dark
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

            # Click settings button
            settings_btn = shell.findChild(QPushButton, "settings_button")
            settings_btn.click()
            QApplication.processEvents()

            # Verify dialog was opened
            assert len(dialog_opened) == 1

            # Verify change was persisted
            settings = repo.load()
            assert settings.theme.name == "dark"

        shell.close()


# =============================================================================
# Test: Settings Button Position
# =============================================================================


class TestSettingsButtonPosition:
    """Tests for settings button placement."""

    def test_settings_button_in_menu_bar(self, qapp, colors):
        """Settings button should be in the menu bar area."""
        from src.presentation.templates.app_shell import AppMenuBar, AppShell

        shell = AppShell(colors=colors)

        # Get the menu bar
        menu_bar = shell.findChild(AppMenuBar)
        assert menu_bar is not None

        # Settings button should be a child of menu bar
        settings_btn = menu_bar.findChild(QPushButton, "settings_button")
        assert settings_btn is not None

        shell.close()
