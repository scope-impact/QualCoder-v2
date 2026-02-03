"""
Main Application E2E Tests

Tests critical paths through the real app entry point (src/main.py).
Verifies that all wiring is correct and the app works end-to-end.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest
from PySide6.QtWidgets import QApplication, QPushButton

pytestmark = pytest.mark.e2e


@pytest.fixture
def app_instance(qapp, colors):
    """Create a QualCoderApp instance for testing."""
    from src.application.app_context import get_app_context, reset_app_context
    from src.application.navigation.service import NavigationService
    from src.application.projects.signal_bridge import ProjectSignalBridge
    from src.main import FileManagerService, QualCoderApp
    from src.presentation.services import DialogService

    reset_app_context()

    app = QualCoderApp.__new__(QualCoderApp)
    app._app = qapp
    app._colors = colors
    app._ctx = get_app_context()
    app._dialog_service = DialogService(app._ctx)
    app._navigation_service = NavigationService(app._ctx)
    app._file_manager_service = FileManagerService(app._ctx)
    # Create signal bridge for reactive UI updates
    app._project_signal_bridge = ProjectSignalBridge.instance(app._ctx.event_bus)
    app._project_signal_bridge.start()
    app._shell = None
    app._screens = {}
    app._current_project_path = None

    yield app

    if app._shell:
        app._shell.close()
    app._ctx.stop()
    reset_app_context()


class TestAppStartup:
    """Tests that the app starts correctly."""

    def test_app_creates_shell(self, app_instance):
        """App should create the main shell window."""
        app_instance._setup_shell()
        assert app_instance._shell is not None

    def test_app_creates_all_screens(self, app_instance):
        """App should create all required screens."""
        app_instance._setup_shell()
        assert "project" in app_instance._screens
        assert "files" in app_instance._screens
        assert "cases" in app_instance._screens
        assert "coding" in app_instance._screens

    def test_app_starts_on_project_screen(self, app_instance):
        """App should start on the project selection screen."""
        from src.presentation.screens import ProjectScreen

        app_instance._setup_shell()
        assert isinstance(app_instance._screens["project"], ProjectScreen)

    def test_shell_can_show(self, app_instance):
        """Shell should be able to show without errors."""
        app_instance._setup_shell()
        app_instance._shell.show()
        QApplication.processEvents()
        assert app_instance._shell.isVisible()


class TestNavigation:
    """Tests that menu navigation works correctly."""

    def test_menu_click_switches_screen(self, app_instance):
        """Clicking menu should switch to corresponding screen."""
        app_instance._setup_shell()
        app_instance._shell.show()
        QApplication.processEvents()
        app_instance._on_menu_click("files")
        QApplication.processEvents()

    def test_can_navigate_to_all_screens(self, app_instance):
        """Should be able to navigate to all screens."""
        app_instance._setup_shell()
        app_instance._shell.show()
        QApplication.processEvents()
        for screen_id in ["project", "files", "cases", "coding"]:
            app_instance._on_menu_click(screen_id)
            QApplication.processEvents()


class TestSettingsIntegration:
    """Tests that settings button works in the full app."""

    def test_settings_button_exists(self, app_instance):
        """Settings button should exist in the shell."""
        app_instance._setup_shell()
        settings_btn = app_instance._shell.findChild(QPushButton, "settings_button")
        assert settings_btn is not None

    def test_settings_button_opens_dialog(self, app_instance):
        """Clicking settings should open settings dialog."""
        app_instance._setup_shell()
        app_instance._shell.show()
        QApplication.processEvents()

        dialogs_opened = []
        original_show = app_instance._dialog_service.show_settings_dialog

        def mock_show(*args, **kwargs):
            kwargs["blocking"] = False
            dialog = original_show(*args, **kwargs)
            dialogs_opened.append(dialog)
            return dialog

        app_instance._dialog_service.show_settings_dialog = mock_show
        settings_btn = app_instance._shell.findChild(QPushButton, "settings_button")
        settings_btn.click()
        QApplication.processEvents()

        assert len(dialogs_opened) == 1
        if dialogs_opened:
            dialogs_opened[0].close()


class TestProjectScreenActions:
    """Tests project screen Open/Create buttons."""

    def test_project_screen_has_open_button(self, app_instance):
        """Project screen should have Open Project button."""
        app_instance._setup_shell()
        project_screen = app_instance._screens["project"]
        content = project_screen.get_content()
        buttons = content.findChildren(QPushButton)
        open_buttons = [b for b in buttons if "Open" in b.text()]
        assert len(open_buttons) >= 1

    def test_project_screen_has_create_button(self, app_instance):
        """Project screen should have Create Project button."""
        app_instance._setup_shell()
        project_screen = app_instance._screens["project"]
        content = project_screen.get_content()
        buttons = content.findChildren(QPushButton)
        create_buttons = [b for b in buttons if "Create" in b.text()]
        assert len(create_buttons) >= 1


class TestFileManagerScreen:
    """Tests file manager screen in the app context."""

    def test_file_manager_screen_loads(self, app_instance):
        """File manager screen should load without errors."""
        app_instance._setup_shell()
        app_instance._shell.show()
        QApplication.processEvents()
        app_instance._on_menu_click("files")
        QApplication.processEvents()
        assert app_instance._screens["files"] is not None

    def test_file_manager_has_import_button(self, app_instance):
        """File manager should have import button."""
        app_instance._setup_shell()
        files_screen = app_instance._screens["files"]
        assert hasattr(files_screen, "_page")


class TestCaseManagerScreen:
    """Tests case manager screen in the app context."""

    def test_case_manager_screen_loads(self, app_instance):
        """Case manager screen should load without errors."""
        app_instance._setup_shell()
        app_instance._shell.show()
        QApplication.processEvents()
        app_instance._on_menu_click("cases")
        QApplication.processEvents()
        assert app_instance._screens["cases"] is not None


class TestFullUserJourney:
    """Tests complete user workflows through the app."""

    def test_journey_start_to_files(self, app_instance):
        """User journey: Start app -> Navigate through screens."""
        app_instance._setup_shell()
        app_instance._shell.show()
        QApplication.processEvents()

        for screen in ["files", "cases", "coding", "project"]:
            app_instance._on_menu_click(screen)
            QApplication.processEvents()

    def test_journey_settings_change(self, app_instance):
        """User journey: Open settings -> Change theme -> Verify."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "settings.json"
            app_instance._setup_shell()
            app_instance._shell.show()
            QApplication.processEvents()

            dialog = app_instance._dialog_service.show_settings_dialog(
                parent=app_instance._shell,
                colors=app_instance._colors,
                config_path=config_path,
                blocking=False,
            )
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

            from src.contexts.settings.infra import UserSettingsRepository

            repo = UserSettingsRepository(config_path=config_path)
            settings = repo.load()
            assert settings.theme.name == "dark"
