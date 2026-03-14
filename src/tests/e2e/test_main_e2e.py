"""
Main Application E2E Tests

Tests critical paths through the real app entry point (src/main.py).
Verifies that all wiring is correct and the app works end-to-end.

Test Categories:
- Smoke Tests: Basic startup without a project (TestSmokeStartup)
- App Startup: Tests with pre-initialized project (TestAppStartup)
- Navigation: Menu and screen navigation (TestNavigation)
- Settings: Settings dialog integration (TestSettingsIntegration)
- User Journeys: Complete workflows (TestFullUserJourney)
"""

from __future__ import annotations

import tempfile
from pathlib import Path

import allure
import pytest
from PySide6.QtWidgets import QApplication, QPushButton

from src.tests.e2e.helpers import attach_screenshot
from src.tests.e2e.utils import DocScreenshot

pytestmark = [
    pytest.mark.e2e,
    allure.epic("QualCoder v2"),
    allure.feature("QC-026 Open & Navigate Project"),
]


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def fresh_app(qapp, colors):
    """
    Create a QualCoderApp with NO project open (real startup state).
    """
    from src.contexts.coding.interface.signal_bridge import CodingSignalBridge
    from src.main import QualCoderApp
    from src.shared.infra.app_context import create_app_context
    from src.shared.infra.signal_bridge.projects import ProjectSignalBridge
    from src.shared.presentation.services import DialogService

    app = QualCoderApp.__new__(QualCoderApp)
    app._app = qapp
    app._colors = colors
    app._ctx = create_app_context()
    app._dialog_service = DialogService(app._ctx)
    app._project_signal_bridge = ProjectSignalBridge.instance(app._ctx.event_bus)
    app._project_signal_bridge.start()
    app._coding_signal_bridge = CodingSignalBridge.instance(app._ctx.event_bus)
    app._coding_signal_bridge.start()
    app._shell = None
    app._screens = {}
    app._current_project_path = None

    yield app

    # Cleanup
    if app._shell:
        app._shell.close()
    app._ctx.stop()


@pytest.fixture
def app_instance(qapp, colors):
    """Create a QualCoderApp instance for testing."""
    import tempfile

    from sqlalchemy import create_engine

    from src.contexts.projects.core.entities import Project, ProjectId
    from src.contexts.projects.infra.schema import create_all_contexts
    from src.main import QualCoderApp
    from src.shared.infra.app_context import (
        CasesContext,
        CodingContext,
        ProjectsContext,
        SourcesContext,
        create_app_context,
    )
    from src.shared.infra.signal_bridge.projects import ProjectSignalBridge
    from src.shared.presentation.services import DialogService

    app = QualCoderApp.__new__(QualCoderApp)
    app._app = qapp
    app._colors = colors
    app._ctx = create_app_context()
    app._dialog_service = DialogService(app._ctx)

    engine = create_engine("sqlite:///:memory:", echo=False)
    create_all_contexts(engine)
    connection = engine.connect()

    app._ctx.sources_context = SourcesContext.create(connection)
    app._ctx.cases_context = CasesContext.create(connection)
    app._ctx.coding_context = CodingContext.create(connection)
    app._ctx.projects_context = ProjectsContext.create(connection)

    with tempfile.TemporaryDirectory() as tmp_dir:
        project_path = Path(tmp_dir) / "test_project.qda"
        app._ctx.state.project = Project(
            id=ProjectId.from_path(project_path),
            name="Test Project",
            path=project_path,
        )

        app._project_signal_bridge = ProjectSignalBridge.instance(app._ctx.event_bus)
        app._project_signal_bridge.start()
        app._shell = None
        app._screens = {}
        app._current_project_path = None

        yield app

        if app._shell:
            app._shell.close()

    connection.close()
    engine.dispose()
    app._ctx.stop()


# =============================================================================
# Smoke Tests (No Project State)
# =============================================================================


@allure.story("QC-026 Open Navigate Project")
class TestSmokeStartup:
    """
    Smoke tests for application startup without a project.
    """

    @allure.title(
        "App starts without project, shows project screen, and creates all screens"
    )
    @allure.severity(allure.severity_level.CRITICAL)
    def test_app_startup_and_screens(self, fresh_app):
        """App starts without errors, shows project screen, and all screens are created."""
        from src.contexts.projects.presentation import ProjectScreen

        # Verify contexts are None (no project open)
        assert fresh_app._ctx.sources_context is None
        assert fresh_app._ctx.cases_context is None
        assert fresh_app._ctx.coding_context is None
        assert fresh_app._ctx.projects_context is None

        # Setup shell should work even without a project
        fresh_app._setup_shell()
        assert fresh_app._shell is not None

        fresh_app._shell.show()
        QApplication.processEvents()

        # Verify project screen is shown
        assert isinstance(fresh_app._screens["project"], ProjectScreen)

        # Verify all screens created
        assert "project" in fresh_app._screens
        assert "files" in fresh_app._screens
        assert "cases" in fresh_app._screens
        assert "coding" in fresh_app._screens

        attach_screenshot(fresh_app._shell, "MainWindow - Project Screen on Startup")
        DocScreenshot.capture(fresh_app._shell, "main-window-startup", max_width=1000)

    @allure.title(
        "File manager works without viewmodel and navigation works without project"
    )
    @allure.severity(allure.severity_level.NORMAL)
    def test_empty_state_navigation(self, fresh_app):
        """File manager shows empty state, and all screens can be navigated without project."""
        fresh_app._setup_shell()
        fresh_app._shell.show()
        QApplication.processEvents()

        # Navigate to files screen - should not crash
        fresh_app._on_menu_click("files")
        QApplication.processEvents()

        files_screen = fresh_app._screens["files"]
        assert files_screen._viewmodel is None
        attach_screenshot(fresh_app._shell, "MainWindow - File Manager Empty State")

        # Navigate through all screens without crashing
        for screen_id in ["cases", "coding", "project"]:
            fresh_app._on_menu_click(screen_id)
            QApplication.processEvents()
        attach_screenshot(fresh_app._shell, "MainWindow - Navigation Complete")


@allure.story("QC-026.02 Create New Project")
class TestSmokeProjectLifecycle:
    """
    Smoke tests for project create/open lifecycle.
    """

    @allure.title(
        "AC #2-3: Create project initializes contexts, wires viewmodels, and connects signals"
    )
    @allure.severity(allure.severity_level.CRITICAL)
    def test_create_project_full_lifecycle(self, fresh_app):
        """Creating a project initializes contexts, wires viewmodels, and connects signal bridge."""
        fresh_app._setup_shell()

        # Contexts should be None before project creation
        assert fresh_app._ctx.sources_context is None
        assert fresh_app._screens["files"]._viewmodel is None
        assert fresh_app._screens["coding"]._viewmodel is None

        with tempfile.TemporaryDirectory() as tmp_dir:
            project_path = Path(tmp_dir) / "test_project.qda"

            # Create and open project
            create_result = fresh_app._ctx.create_project(
                name="Test Project",
                path=str(project_path),
            )
            assert create_result.is_success

            open_result = fresh_app._ctx.open_project(str(project_path))
            assert open_result.is_success

            # Contexts should now be initialized
            assert fresh_app._ctx.sources_context is not None
            assert fresh_app._ctx.cases_context is not None
            assert fresh_app._ctx.coding_context is not None

            # Wire viewmodels
            fresh_app._wire_viewmodels()

            # File manager and coding screen should now have viewmodels
            assert fresh_app._screens["files"]._viewmodel is not None
            assert fresh_app._screens["coding"]._viewmodel is not None

            # Verify signal bridge has all expected signals
            signal_bridge = fresh_app._coding_signal_bridge
            expected_signals = [
                "code_created",
                "code_deleted",
                "code_renamed",
                "code_color_changed",
                "code_memo_updated",
                "code_moved",
                "codes_merged",
                "category_created",
                "category_deleted",
                "segment_coded",
                "segment_uncoded",
            ]
            for signal_name in expected_signals:
                assert hasattr(signal_bridge, signal_name), (
                    f"CodingSignalBridge missing signal: {signal_name}"
                )


@allure.story("QC-026.01 Open Existing Project")
class TestSmokeOpenProject:
    """
    Smoke tests for opening existing projects.
    """

    @allure.title("AC #2: Opening project refreshes file manager")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_open_project_refreshes_file_manager(self, fresh_app):
        """Opening a project should refresh the file manager screen."""
        fresh_app._setup_shell()
        fresh_app._shell.show()
        QApplication.processEvents()

        with tempfile.TemporaryDirectory() as tmp_dir:
            project_path = Path(tmp_dir) / "test_project.qda"
            fresh_app._ctx.create_project("Test", str(project_path))
            fresh_app._ctx.open_project(str(project_path))
            fresh_app._wire_viewmodels()

            # Refresh should work without errors
            fresh_app._screens["files"].refresh()
            QApplication.processEvents()


@allure.story("QC-026.02 Create New Project")
class TestCreateProjectErrors:
    """
    Tests for project creation error handling.
    """

    @allure.title("Creating duplicate path fails but same name different path allowed")
    @allure.severity(allure.severity_level.NORMAL)
    def test_create_project_error_handling(self, fresh_app):
        """Creating at existing path fails, but same name different path is allowed."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            project_path = Path(tmp_dir) / "test_project.qda"

            # Create first project - should succeed
            result1 = fresh_app._ctx.create_project("Project 1", str(project_path))
            assert result1.is_success

            # Try to create another project at same path - should fail
            result2 = fresh_app._ctx.create_project("Project 2", str(project_path))
            assert result2.is_failure
            assert "already exists" in result2.error
            assert result2.error_code == "PROJECT_NOT_CREATED/DB_CREATION_FAILED"

            # Same name different path should work
            path2 = Path(tmp_dir) / "project2.qda"
            result3 = fresh_app._ctx.create_project("Project 1", str(path2))
            assert result3.is_success
            assert result3.unwrap().name == "Project 1"


# =============================================================================
# App Startup and Navigation Tests (With Pre-initialized Project)
# =============================================================================


@allure.story("QC-026.04 Switch Between Screens")
class TestNavigationAndScreens:
    """Tests that app startup, navigation, and screen loading works correctly."""

    @allure.title("Shell shows, menu navigation works, and all screens load")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_shell_and_navigation(self, app_instance):
        """Shell shows, menu navigates between screens, and all screens load correctly."""
        app_instance._setup_shell()
        app_instance._shell.show()
        QApplication.processEvents()
        assert app_instance._shell.isVisible()
        attach_screenshot(app_instance._shell, "MainWindow - Shell Visible")

        # Navigate to all screens
        for screen_id in ["files", "cases", "coding", "project"]:
            app_instance._on_menu_click(screen_id)
            QApplication.processEvents()
            assert app_instance._screens[screen_id] is not None

        attach_screenshot(app_instance._shell, "MainWindow - All Screens Navigation")

    @allure.title("Project screen has Open and Create buttons, file manager has page")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_screen_components(self, app_instance):
        """Project screen has action buttons and file manager has page component."""
        app_instance._setup_shell()

        # Check project screen buttons
        project_screen = app_instance._screens["project"]
        content = project_screen.get_content()
        buttons = content.findChildren(QPushButton)
        open_buttons = [b for b in buttons if "Open" in b.text()]
        create_buttons = [b for b in buttons if "Create" in b.text()]
        assert len(open_buttons) >= 1
        assert len(create_buttons) >= 1

        # Check file manager has page
        files_screen = app_instance._screens["files"]
        assert hasattr(files_screen, "_page")


@allure.story("QC-026 Open Navigate Project")
class TestSettingsIntegration:
    """Tests that settings button works in the full app."""

    @allure.title("Settings button exists and opens dialog")
    @allure.severity(allure.severity_level.NORMAL)
    def test_settings_button_opens_dialog(self, app_instance):
        """Settings button should exist in the shell and open settings dialog when clicked."""
        app_instance._setup_shell()
        app_instance._shell.show()
        QApplication.processEvents()

        settings_btn = app_instance._shell.findChild(QPushButton, "settings_button")
        assert settings_btn is not None

        dialogs_opened = []
        original_show = app_instance._dialog_service.show_settings_dialog

        def wrapped_show(*args, **kwargs):
            kwargs["blocking"] = False
            dialog = original_show(*args, **kwargs)
            dialogs_opened.append(dialog)
            return dialog

        app_instance._dialog_service.show_settings_dialog = wrapped_show
        settings_btn.click()
        QApplication.processEvents()

        assert len(dialogs_opened) == 1
        if dialogs_opened:
            dialogs_opened[0].close()


@allure.story("QC-026 Open Navigate Project")
class TestFullUserJourney:
    """Tests complete user workflows through the app."""

    @allure.title("User journey: Navigate screens and change theme in settings")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_journey_navigation_and_settings(self, app_instance):
        """User journey: Navigate through all screens and change theme in settings."""
        app_instance._setup_shell()
        app_instance._shell.show()
        QApplication.processEvents()

        # Navigate through all screens
        for screen in ["files", "cases", "coding", "project"]:
            app_instance._on_menu_click(screen)
            QApplication.processEvents()
        attach_screenshot(app_instance._shell, "MainWindow - User Journey Complete")

        # Change theme in settings
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "settings.json"

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
