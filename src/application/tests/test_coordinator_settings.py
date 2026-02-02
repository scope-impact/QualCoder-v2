"""
Coordinator Settings Integration Tests

TDD tests for settings dialog integration in ApplicationCoordinator.
Tests that:
1. Coordinator has show_settings_dialog method
2. Settings dialog can be opened via coordinator
3. Settings changes persist via coordinator
"""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest
from PySide6.QtWidgets import QApplication, QPushButton

pytestmark = pytest.mark.e2e


# =============================================================================
# Test: Coordinator has Settings Dialog Method
# =============================================================================


class TestCoordinatorSettingsMethod:
    """Tests for show_settings_dialog method."""

    def test_coordinator_has_show_settings_dialog_method(self):
        """Coordinator should have a show_settings_dialog method."""
        from src.application.coordinator import ApplicationCoordinator

        coordinator = ApplicationCoordinator()
        assert hasattr(coordinator, "show_settings_dialog")
        assert callable(coordinator.show_settings_dialog)

    def test_show_settings_dialog_returns_dialog(self, qapp, colors):
        """show_settings_dialog should return the dialog instance."""
        from src.application.coordinator import ApplicationCoordinator

        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "settings.json"
            coordinator = ApplicationCoordinator()

            dialog = coordinator.show_settings_dialog(
                parent=None,
                colors=colors,
                config_path=config_path,
                blocking=False,  # Don't block in test
            )

            assert dialog is not None
            dialog.close()


# =============================================================================
# Test: Settings Dialog Integration
# =============================================================================


class TestSettingsDialogIntegration:
    """Tests for settings dialog opened via coordinator."""

    def test_settings_changes_persist_via_coordinator(self, qapp, colors):
        """Settings changed via coordinator dialog should persist."""
        from src.application.coordinator import ApplicationCoordinator

        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "settings.json"
            coordinator = ApplicationCoordinator()

            # Open dialog
            dialog = coordinator.show_settings_dialog(
                parent=None,
                colors=colors,
                config_path=config_path,
                blocking=False,
            )

            # Change theme to dark
            theme_buttons = [
                btn
                for btn in dialog.findChildren(QPushButton)
                if btn.property("theme_value") == "dark"
            ]
            assert len(theme_buttons) > 0
            theme_buttons[0].click()
            QApplication.processEvents()

            dialog.close()

            # Verify change persisted
            from src.contexts.settings.infra import UserSettingsRepository

            repo = UserSettingsRepository(config_path=config_path)
            settings = repo.load()
            assert settings.theme.name == "dark"


# =============================================================================
# Test: AppShell to Coordinator Wiring
# =============================================================================


class TestAppShellCoordinatorWiring:
    """Tests for wiring AppShell settings button to coordinator."""

    def test_can_wire_app_shell_settings_to_coordinator(self, qapp, colors):
        """AppShell settings_clicked can be wired to coordinator."""
        from src.application.coordinator import ApplicationCoordinator
        from src.presentation.templates.app_shell import AppShell

        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "settings.json"
            coordinator = ApplicationCoordinator()
            shell = AppShell(colors=colors)

            dialogs_opened = []

            def on_settings_clicked():
                dialog = coordinator.show_settings_dialog(
                    parent=shell,
                    colors=colors,
                    config_path=config_path,
                    blocking=False,
                )
                dialogs_opened.append(dialog)

            shell.settings_clicked.connect(on_settings_clicked)

            # Click settings button
            settings_btn = shell.findChild(QPushButton, "settings_button")
            settings_btn.click()
            QApplication.processEvents()

            assert len(dialogs_opened) == 1
            assert dialogs_opened[0] is not None

            dialogs_opened[0].close()
            shell.close()

    def test_full_workflow_shell_to_coordinator_to_persistence(self, qapp, colors):
        """Full workflow: AppShell -> Coordinator -> Dialog -> Persistence."""
        from src.application.coordinator import ApplicationCoordinator
        from src.contexts.settings.infra import UserSettingsRepository
        from src.presentation.templates.app_shell import AppShell

        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "settings.json"
            coordinator = ApplicationCoordinator()
            shell = AppShell(colors=colors)

            def on_settings_clicked():
                dialog = coordinator.show_settings_dialog(
                    parent=shell,
                    colors=colors,
                    config_path=config_path,
                    blocking=False,
                )
                # Change font size
                dialog._font_slider.setValue(20)
                QApplication.processEvents()
                dialog.close()

            shell.settings_clicked.connect(on_settings_clicked)

            # Trigger workflow
            settings_btn = shell.findChild(QPushButton, "settings_button")
            settings_btn.click()
            QApplication.processEvents()

            # Verify persistence
            repo = UserSettingsRepository(config_path=config_path)
            settings = repo.load()
            assert settings.font.size == 20

            shell.close()
