"""
E2E Test Fixtures

Shared fixtures for end-to-end tests.

IMPORTANT: E2E tests NEVER use mocks. All dependencies are real:
- Real in-memory SQLite database
- Real repositories
- Real ViewModels calling use cases directly

For unit tests with mocks, see src/presentation/viewmodels/tests/mocks.py
"""

from __future__ import annotations

import allure
import pytest
from PySide6.QtWidgets import QApplication
from sqlalchemy import create_engine

from src.contexts.projects.infra.schema import create_all_contexts, drop_all_contexts
from src.shared.infra.event_bus import EventBus

# =============================================================================
# Pytest Hooks for Allure Screenshots
# =============================================================================


def _capture_all_visible_widgets() -> list[bytes]:
    """Capture screenshots of all visible top-level widgets."""
    screenshots = []
    try:
        app = QApplication.instance()
        if app:
            for widget in app.topLevelWidgets():
                if widget.isVisible() and widget.width() > 0 and widget.height() > 0:
                    pixmap = widget.grab()
                    from io import BytesIO

                    buffer = BytesIO()
                    pixmap.save(buffer, "PNG")
                    screenshots.append(
                        (
                            widget.objectName() or widget.__class__.__name__,
                            buffer.getvalue(),
                        )
                    )
    except Exception:
        pass
    return screenshots


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Capture screenshot for all E2E tests in Allure report."""
    outcome = yield
    report = outcome.get_result()

    # Only capture after test execution (not setup/teardown)
    if report.when == "call":
        screenshots = _capture_all_visible_widgets()
        for name, data in screenshots:
            suffix = "_failure" if report.failed else ""
            attachment_name = (
                f"screenshot_{name}{suffix}"
                if len(screenshots) > 1
                else f"screenshot{suffix}"
            )
            allure.attach(
                data,
                name=attachment_name,
                attachment_type=allure.attachment_type.PNG,
            )


# =============================================================================
# Database Fixtures
# =============================================================================


@pytest.fixture
def db_engine():
    """Create in-memory SQLite engine for E2E testing."""
    engine = create_engine("sqlite:///:memory:", echo=False)
    create_all_contexts(engine)
    yield engine
    drop_all_contexts(engine)
    engine.dispose()


@pytest.fixture
def db_connection(db_engine):
    """Create a database connection."""
    conn = db_engine.connect()
    yield conn
    conn.close()


# =============================================================================
# Event Bus Fixture
# =============================================================================


@pytest.fixture
def event_bus():
    """Create event bus for reactive updates."""
    return EventBus(history_size=100)


# =============================================================================
# Repository Fixtures
# =============================================================================


@pytest.fixture
def case_repo(db_connection):
    """Create a real case repository."""
    from src.contexts.cases.infra.case_repository import SQLiteCaseRepository

    return SQLiteCaseRepository(db_connection)


@pytest.fixture
def code_repo(db_connection):
    """Create a real code repository."""
    from src.contexts.coding.infra.repositories import SQLiteCodeRepository

    return SQLiteCodeRepository(db_connection)


@pytest.fixture
def segment_repo(db_connection):
    """Create a real segment repository."""
    from src.contexts.coding.infra.repositories import SQLiteSegmentRepository

    return SQLiteSegmentRepository(db_connection)


@pytest.fixture
def category_repo(db_connection):
    """Create a real category repository."""
    from src.contexts.coding.infra.repositories import SQLiteCategoryRepository

    return SQLiteCategoryRepository(db_connection)


@pytest.fixture
def source_repo(db_connection):
    """Create a real source repository."""
    from src.contexts.sources.infra.source_repository import SQLiteSourceRepository

    return SQLiteSourceRepository(db_connection)


# =============================================================================
# Context Fixtures (bundles of repositories)
# =============================================================================


@pytest.fixture
def cases_context(case_repo):
    """Create a real cases context."""
    from src.shared.infra.app_context import CasesContext

    return CasesContext(case_repo=case_repo)


@pytest.fixture
def coding_context_bundle(code_repo, segment_repo):
    """Create a real coding context bundle."""
    from src.shared.infra.app_context import CodingContext

    return CodingContext(
        code_repo=code_repo,
        category_repo=None,  # Not needed for most tests
        segment_repo=segment_repo,
    )


# =============================================================================
# Project State Fixture (with test project for E2E)
# =============================================================================


@pytest.fixture
def project_state():
    """
    Create a real project state with a test project.

    For E2E tests, we need state.project to be set (not None)
    because use cases check for an open project.
    """
    from datetime import UTC, datetime
    from pathlib import Path

    from src.contexts.projects.core.entities import Project, ProjectId
    from src.shared.infra.state import ProjectState

    state = ProjectState()

    # Create a minimal project for testing
    project = Project(
        id=ProjectId(value="test-project"),
        name="Test Project",
        path=Path("/tmp/test_project.qda"),
        created_at=datetime.now(UTC),
    )

    # Set the project on state
    state.project = project

    return state


# =============================================================================
# ViewModel Fixtures (connected to REAL repositories)
# =============================================================================


@pytest.fixture
def case_viewmodel(case_repo, project_state, event_bus, cases_context):
    """
    Create a CaseManagerViewModel with real dependencies.

    This is the actual production setup, not a mock.
    """
    from src.contexts.cases.presentation import CaseManagerViewModel

    return CaseManagerViewModel(
        case_repo=case_repo,
        state=project_state,
        event_bus=event_bus,
        cases_ctx=cases_context,
    )


# =============================================================================
# Full Application Fixtures (tests real wiring from main.py)
# =============================================================================


@pytest.fixture
def wired_app(qapp, colors, tmp_path):
    """
    Create a fully-wired QualCoderApp with an open test project.

    This fixture tests the REAL wiring logic from main.py:
    - Calls actual _setup_shell() method
    - Calls actual _wire_viewmodels() method
    - Uses real signal bridges, repositories, and viewmodels

    Provides:
    - Real in-memory database with schema
    - All signal bridges started
    - ViewModels wired to screens (via main.py's _wire_viewmodels)
    - Ready for user interaction simulation

    Flow tested:
    Screen → ViewModel → Coordinator → Handler → Repository
    → EventBus → SignalBridge → ViewModel → Screen
    """
    from PySide6.QtWidgets import QApplication

    from src.contexts.cases.interface.signal_bridge import CasesSignalBridge
    from src.contexts.coding.interface.signal_bridge import CodingSignalBridge
    from src.main import QualCoderApp
    from src.shared.infra.app_context import create_app_context
    from src.shared.infra.signal_bridge.projects import ProjectSignalBridge
    from src.shared.presentation.services import DialogService

    # Clear singletons for test isolation
    CodingSignalBridge.clear_instance()
    CasesSignalBridge.clear_instance()
    ProjectSignalBridge.clear_instance()

    # Create app instance without calling __init__ (to avoid QApplication conflict)
    # Then set up attributes the same way __init__ does
    app = QualCoderApp.__new__(QualCoderApp)
    app._app = qapp
    app._colors = colors
    app._ctx = create_app_context()
    app._dialog_service = DialogService(app._ctx)

    # Create and start signal bridges (same as main.py __init__)
    app._project_signal_bridge = ProjectSignalBridge.instance(app._ctx.event_bus)
    app._project_signal_bridge.start()
    app._coding_signal_bridge = CodingSignalBridge.instance(app._ctx.event_bus)
    app._coding_signal_bridge.start()
    app._shell = None
    app._screens = {}
    app._current_project_path = None

    # Create and open test project (this initializes bounded contexts)
    project_path = tmp_path / "test_project.qda"
    create_result = app._ctx.create_project("Test Project", str(project_path))
    assert create_result.is_success, f"Failed to create project: {create_result.error}"

    open_result = app._ctx.open_project(str(project_path))
    assert open_result.is_success, f"Failed to open project: {open_result.error}"

    # Call the REAL wiring methods from main.py
    # This is what we're testing - the actual wiring logic
    app._setup_shell()
    app._wire_viewmodels()

    # Set proper size for headless screenshots
    app._shell.resize(1280, 800)
    app._shell.show()
    QApplication.processEvents()

    yield {
        "app": app,
        "shell": app._shell,
        "screens": app._screens,
        "ctx": app._ctx,
        "event_bus": app._ctx.event_bus,
        "coding_signal_bridge": app._coding_signal_bridge,
        "project_signal_bridge": app._project_signal_bridge,
        "project_path": project_path,
    }

    # Cleanup
    if app._shell:
        app._shell.close()
    app._ctx.stop()
    CodingSignalBridge.clear_instance()
    CasesSignalBridge.clear_instance()
    ProjectSignalBridge.clear_instance()


@pytest.fixture
def seeded_app(wired_app):
    """
    Wired app with pre-seeded test data.

    Extends wired_app with:
    - 2 text sources with content
    - 3 codes (ready for coding operations)

    Use this fixture when tests need data to work with.
    """
    from PySide6.QtWidgets import QApplication

    from src.contexts.coding.core.entities import Code, CodeId, Color
    from src.contexts.sources.core.entities import Source, SourceType
    from src.shared.common.types import SourceId

    ctx = wired_app["ctx"]

    # Seed sources
    source1 = Source(
        id=SourceId(value=1),
        name="interview_01.txt",
        fulltext="This is a positive experience. The learning was great. I enjoyed the process.",
        source_type=SourceType.TEXT,
    )
    source2 = Source(
        id=SourceId(value=2),
        name="interview_02.txt",
        fulltext="This was challenging. I struggled with some topics. But I persevered.",
        source_type=SourceType.TEXT,
    )
    ctx.sources_context.source_repo.save(source1)
    ctx.sources_context.source_repo.save(source2)

    # Seed codes
    code1 = Code(id=CodeId(value=1), name="Positive", color=Color.from_hex("#00FF00"))
    code2 = Code(id=CodeId(value=2), name="Challenge", color=Color.from_hex("#FF0000"))
    code3 = Code(id=CodeId(value=3), name="Learning", color=Color.from_hex("#0000FF"))
    ctx.coding_context.code_repo.save(code1)
    ctx.coding_context.code_repo.save(code2)
    ctx.coding_context.code_repo.save(code3)

    # Process events to ensure UI is updated
    QApplication.processEvents()

    wired_app["seeded"] = {
        "sources": [source1, source2],
        "codes": [code1, code2, code3],
    }

    return wired_app


@pytest.fixture
def coding_screen_ready(seeded_app):
    """
    Navigate to coding screen with first source loaded.

    Use this fixture for tests that need:
    - A fully wired app
    - Seeded data (sources and codes)
    - Coding screen visible with a document loaded
    """
    from PySide6.QtWidgets import QApplication

    app = seeded_app["app"]
    source = seeded_app["seeded"]["sources"][0]

    # Navigate to coding screen (uses main.py's _on_menu_click)
    app._on_menu_click("coding")
    QApplication.processEvents()

    # Load source into coding screen (uses main.py's _on_navigate_to_coding)
    app._on_navigate_to_coding(str(source.id.value))
    QApplication.processEvents()

    return seeded_app
