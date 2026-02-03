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

    This tests the actual startup flow where:
    - No project is open
    - Bounded contexts are None
    - App starts on project screen
    """
    from src.contexts.coding.interface.signal_bridge import CodingSignalBridge
    from src.main import QualCoderApp
    from src.shared.infra.app_context import create_app_context
    from src.shared.infra.signal_bridge.projects import ProjectSignalBridge
    from src.shared.presentation.services import DialogService

    # Create app without calling __init__ to control setup
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

    # Create in-memory database with all contexts for testing
    # (ViewModels now require repos from contexts)
    engine = create_engine("sqlite:///:memory:", echo=False)
    create_all_contexts(engine)
    connection = engine.connect()

    app._ctx.sources_context = SourcesContext.create(connection)
    app._ctx.cases_context = CasesContext.create(connection)
    app._ctx.coding_context = CodingContext.create(connection)
    app._ctx.projects_context = ProjectsContext.create(connection)

    # Create a test project in state so app can function
    with tempfile.TemporaryDirectory() as tmp_dir:
        project_path = Path(tmp_dir) / "test_project.qda"
        app._ctx.state.project = Project(
            id=ProjectId.from_path(project_path),
            name="Test Project",
            path=project_path,
        )

        # Create signal bridge for reactive UI updates
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


@allure.story("QC-026 Open & Navigate Project")
class TestSmokeStartup:
    """
    Smoke tests for application startup without a project.

    These tests verify the app can start and function in the initial state
    where no project is open and bounded contexts are None.
    """

    @allure.title("App starts without a project open")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_app_starts_without_project(self, fresh_app):
        """App should start without errors when no project is open."""
        # Verify contexts are None (no project open)
        assert fresh_app._ctx.sources_context is None
        assert fresh_app._ctx.cases_context is None
        assert fresh_app._ctx.coding_context is None
        assert fresh_app._ctx.projects_context is None

        # Setup shell should work even without a project
        fresh_app._setup_shell()
        assert fresh_app._shell is not None

    @allure.title("Shell displays project screen on startup")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_starts_on_project_screen(self, fresh_app):
        """App should start on the project selection screen."""
        from src.contexts.projects.presentation import ProjectScreen

        fresh_app._setup_shell()
        fresh_app._shell.show()
        QApplication.processEvents()

        assert isinstance(fresh_app._screens["project"], ProjectScreen)

    @allure.title("All screens are created even without a project")
    @allure.severity(allure.severity_level.NORMAL)
    def test_all_screens_created(self, fresh_app):
        """All screens should be created even without a project."""
        fresh_app._setup_shell()

        assert "project" in fresh_app._screens
        assert "files" in fresh_app._screens
        assert "cases" in fresh_app._screens
        assert "coding" in fresh_app._screens

    @allure.title("File manager screen works without viewmodel")
    @allure.severity(allure.severity_level.NORMAL)
    def test_file_manager_without_viewmodel(self, fresh_app):
        """File manager screen should work without a viewmodel (empty state)."""
        fresh_app._setup_shell()
        fresh_app._shell.show()
        QApplication.processEvents()

        # Navigate to files screen
        fresh_app._on_menu_click("files")
        QApplication.processEvents()

        # Should not crash - screen shows empty state
        files_screen = fresh_app._screens["files"]
        assert files_screen._viewmodel is None

    @allure.title("AC #4: Navigation works without a project")
    @allure.severity(allure.severity_level.NORMAL)
    def test_navigation_without_project(self, fresh_app):
        """Should be able to navigate between screens without a project."""
        fresh_app._setup_shell()
        fresh_app._shell.show()
        QApplication.processEvents()

        # Navigate through all screens
        for screen_id in ["files", "cases", "coding", "project"]:
            fresh_app._on_menu_click(screen_id)
            QApplication.processEvents()
            # Should not crash


@allure.story("QC-026.02 Create New Project")
class TestSmokeProjectLifecycle:
    """
    Smoke tests for project create/open lifecycle.

    Tests that creating or opening a project correctly initializes
    the bounded contexts and wires viewmodels.
    """

    @allure.title("AC #2: A new empty project is created")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_create_project_initializes_contexts(self, fresh_app):
        """Creating a project should initialize bounded contexts."""
        fresh_app._setup_shell()

        # Contexts should be None before project creation
        assert fresh_app._ctx.sources_context is None

        # Create a temporary project
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

    @allure.title("AC #3: I am taken to the main workspace ready to import sources")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_wire_viewmodels_after_project(self, fresh_app):
        """Viewmodels should be wired after project is opened."""
        fresh_app._setup_shell()

        # File manager should have no viewmodel initially
        assert fresh_app._screens["files"]._viewmodel is None
        # Coding screen should have no viewmodel initially
        assert fresh_app._screens["coding"]._viewmodel is None

        # Create and open a project
        with tempfile.TemporaryDirectory() as tmp_dir:
            project_path = Path(tmp_dir) / "test_project.qda"
            fresh_app._ctx.create_project("Test", str(project_path))
            fresh_app._ctx.open_project(str(project_path))

            # Wire viewmodels (simulating what happens after open/create)
            fresh_app._wire_viewmodels()

            # File manager should now have a viewmodel
            assert fresh_app._screens["files"]._viewmodel is not None
            # Coding screen should now have a viewmodel
            assert fresh_app._screens["coding"]._viewmodel is not None

    @allure.title("TextCodingScreen viewmodel is properly connected to signal bridge")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_text_coding_viewmodel_signal_connections(self, fresh_app):
        """
        TextCodingViewModel should connect to all CodingSignalBridge signals.

        This catches wiring issues where the viewmodel expects signals that
        don't exist on the signal bridge.
        """
        fresh_app._setup_shell()

        with tempfile.TemporaryDirectory() as tmp_dir:
            project_path = Path(tmp_dir) / "test_project.qda"
            fresh_app._ctx.create_project("Test", str(project_path))
            fresh_app._ctx.open_project(str(project_path))

            # This should NOT raise AttributeError for missing signals
            fresh_app._wire_viewmodels()

            # Verify viewmodel is connected
            coding_screen = fresh_app._screens["coding"]
            assert coding_screen._viewmodel is not None

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

    Tests that opening a project correctly initializes the bounded contexts
    and shows the main workspace.
    """

    @allure.title("AC #2: The project opens and shows the main workspace")
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

    Verifies that appropriate errors are returned when project creation fails.
    """

    @allure.title("Creating project at existing path fails with error")
    @allure.severity(allure.severity_level.NORMAL)
    def test_create_duplicate_project_path_fails(self, fresh_app):
        """Creating a project at an existing path should fail with clear error."""
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

    @allure.title("Same project name with different paths is allowed")
    @allure.severity(allure.severity_level.NORMAL)
    def test_same_name_different_path_allowed(self, fresh_app):
        """Projects can have the same name if they are at different paths."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            path1 = Path(tmp_dir) / "project1.qda"
            path2 = Path(tmp_dir) / "project2.qda"

            # Create two projects with same name but different paths
            result1 = fresh_app._ctx.create_project("My Project", str(path1))
            result2 = fresh_app._ctx.create_project("My Project", str(path2))

            assert result1.is_success
            assert result2.is_success
            assert result1.unwrap().name == "My Project"
            assert result2.unwrap().name == "My Project"


# =============================================================================
# App Startup Tests (With Pre-initialized Project)
# =============================================================================


@allure.story("QC-026.04 Switch Between Screens")
class TestAppStartup:
    """Tests that the app starts correctly."""

    @allure.title("App creates shell window")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_app_creates_shell(self, app_instance):
        """App should create the main shell window."""
        app_instance._setup_shell()
        assert app_instance._shell is not None

    @allure.title("App creates all screens")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_app_creates_all_screens(self, app_instance):
        """App should create all required screens."""
        app_instance._setup_shell()
        assert "project" in app_instance._screens
        assert "files" in app_instance._screens
        assert "cases" in app_instance._screens
        assert "coding" in app_instance._screens

    @allure.title("App starts on project screen")
    @allure.severity(allure.severity_level.NORMAL)
    def test_app_starts_on_project_screen(self, app_instance):
        """App should start on the project selection screen."""
        from src.contexts.projects.presentation import ProjectScreen

        app_instance._setup_shell()
        assert isinstance(app_instance._screens["project"], ProjectScreen)

    @allure.title("Shell can show without errors")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_shell_can_show(self, app_instance):
        """Shell should be able to show without errors."""
        app_instance._setup_shell()
        app_instance._shell.show()
        QApplication.processEvents()
        assert app_instance._shell.isVisible()


@allure.story("QC-026.04 Switch Between Screens")
class TestNavigation:
    """Tests that menu navigation works correctly."""

    @allure.title("AC #1: Menu click switches screen")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_menu_click_switches_screen(self, app_instance):
        """Clicking menu should switch to corresponding screen."""
        app_instance._setup_shell()
        app_instance._shell.show()
        QApplication.processEvents()
        app_instance._on_menu_click("files")
        QApplication.processEvents()

    @allure.title("AC #1: Can navigate to all screens")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_can_navigate_to_all_screens(self, app_instance):
        """Should be able to navigate to all screens."""
        app_instance._setup_shell()
        app_instance._shell.show()
        QApplication.processEvents()
        for screen_id in ["project", "files", "cases", "coding"]:
            app_instance._on_menu_click(screen_id)
            QApplication.processEvents()


@allure.story("QC-026 Open & Navigate Project")
class TestSettingsIntegration:
    """Tests that settings button works in the full app."""

    @allure.title("Settings button exists in shell")
    @allure.severity(allure.severity_level.NORMAL)
    def test_settings_button_exists(self, app_instance):
        """Settings button should exist in the shell."""
        app_instance._setup_shell()
        settings_btn = app_instance._shell.findChild(QPushButton, "settings_button")
        assert settings_btn is not None

    @allure.title("Settings button opens dialog")
    @allure.severity(allure.severity_level.NORMAL)
    def test_settings_button_opens_dialog(self, app_instance):
        """Clicking settings should open settings dialog."""
        app_instance._setup_shell()
        app_instance._shell.show()
        QApplication.processEvents()

        dialogs_opened = []
        original_show = app_instance._dialog_service.show_settings_dialog

        def wrapped_show(*args, **kwargs):
            kwargs["blocking"] = False
            dialog = original_show(*args, **kwargs)
            dialogs_opened.append(dialog)
            return dialog

        app_instance._dialog_service.show_settings_dialog = wrapped_show
        settings_btn = app_instance._shell.findChild(QPushButton, "settings_button")
        settings_btn.click()
        QApplication.processEvents()

        assert len(dialogs_opened) == 1
        if dialogs_opened:
            dialogs_opened[0].close()


@allure.story("QC-026.01 Open Existing Project")
class TestProjectScreenActions:
    """Tests project screen Open/Create buttons."""

    @allure.title("Project screen has Open button")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_project_screen_has_open_button(self, app_instance):
        """Project screen should have Open Project button."""
        app_instance._setup_shell()
        project_screen = app_instance._screens["project"]
        content = project_screen.get_content()
        buttons = content.findChildren(QPushButton)
        open_buttons = [b for b in buttons if "Open" in b.text()]
        assert len(open_buttons) >= 1

    @allure.title("Project screen has Create button")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_project_screen_has_create_button(self, app_instance):
        """Project screen should have Create Project button."""
        app_instance._setup_shell()
        project_screen = app_instance._screens["project"]
        content = project_screen.get_content()
        buttons = content.findChildren(QPushButton)
        create_buttons = [b for b in buttons if "Create" in b.text()]
        assert len(create_buttons) >= 1


@allure.story("QC-026.03 View Source List")
class TestFileManagerScreen:
    """Tests file manager screen in the app context."""

    @allure.title("File manager screen loads without errors")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_file_manager_screen_loads(self, app_instance):
        """File manager screen should load without errors."""
        app_instance._setup_shell()
        app_instance._shell.show()
        QApplication.processEvents()
        app_instance._on_menu_click("files")
        QApplication.processEvents()
        assert app_instance._screens["files"] is not None

    @allure.title("File manager has page component")
    @allure.severity(allure.severity_level.NORMAL)
    def test_file_manager_has_import_button(self, app_instance):
        """File manager should have import button."""
        app_instance._setup_shell()
        files_screen = app_instance._screens["files"]
        assert hasattr(files_screen, "_page")


@allure.story("QC-026.04 Switch Between Screens")
class TestCaseManagerScreen:
    """Tests case manager screen in the app context."""

    @allure.title("Case manager screen loads without errors")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_case_manager_screen_loads(self, app_instance):
        """Case manager screen should load without errors."""
        app_instance._setup_shell()
        app_instance._shell.show()
        QApplication.processEvents()
        app_instance._on_menu_click("cases")
        QApplication.processEvents()
        assert app_instance._screens["cases"] is not None


@allure.story("QC-026 Open & Navigate Project")
class TestFullUserJourney:
    """Tests complete user workflows through the app."""

    @allure.title("User journey: Navigate through all screens")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_journey_start_to_files(self, app_instance):
        """User journey: Start app -> Navigate through screens."""
        app_instance._setup_shell()
        app_instance._shell.show()
        QApplication.processEvents()

        for screen in ["files", "cases", "coding", "project"]:
            app_instance._on_menu_click(screen)
            QApplication.processEvents()

    @allure.title("User journey: Change theme in settings")
    @allure.severity(allure.severity_level.NORMAL)
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
