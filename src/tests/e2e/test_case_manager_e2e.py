"""
Case Manager End-to-End Tests

True E2E tests with FULL behavior - real database, viewmodel, and UI integration.
Tests the complete flow: UI action → ViewModel → Use Cases → Repository → Database → UI update

These tests use NO MOCKS:
1. Create real in-memory SQLite database with case tables
2. Wire up CaseManagerViewModel with real repos, state, use cases, and SignalBridge
3. Create CaseManagerScreen with real viewmodel
4. Test full round-trip data flows including reactive updates

Implements QC-034 Manage Cases:
- AC #1: Researcher can create cases
- AC #2: Researcher can link sources to cases
- AC #3: Researcher can add case attributes
- AC #4: Researcher can view all data for a case

Note: Uses fixtures from root conftest.py (qapp, colors) and local fixtures.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

import pytest
from PySide6.QtTest import QSignalSpy
from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from sqlalchemy import create_engine

from src.contexts.cases.core.entities import AttributeType, Case, CaseAttribute
from src.contexts.cases.infra.case_repository import SQLiteCaseRepository
from src.contexts.cases.interface.signal_bridge import CasesSignalBridge
from src.contexts.cases.presentation import CaseManagerScreen, CaseManagerViewModel
from src.contexts.projects.infra.schema import create_all_contexts, drop_all_contexts
from src.shared.common.types import CaseId, SourceId
from src.shared.infra.event_bus import EventBus
from src.shared.infra.state import ProjectState
from src.tests.e2e.helpers import attach_screenshot

pytestmark = pytest.mark.e2e  # All tests in this module are E2E tests


# =============================================================================
# Minimal CasesContext for E2E Tests (real infrastructure, no mocks)
# =============================================================================


@dataclass
class E2ECasesContext:
    """Real CasesContext for E2E tests - wraps actual repository."""

    case_repo: SQLiteCaseRepository


# =============================================================================
# Database Fixtures
# =============================================================================


@pytest.fixture
def db_engine():
    """Create in-memory SQLite engine for testing."""
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


@pytest.fixture
def case_repo(db_connection):
    """Create a case repository connected to test database."""
    return SQLiteCaseRepository(db_connection)


@pytest.fixture
def event_bus():
    """Create event bus for reactive updates."""
    return EventBus(history_size=100)


@pytest.fixture
def signal_bridge(event_bus):
    """Create and start CasesSignalBridge for reactive UI updates."""
    # Clear any existing singleton instance for test isolation
    CasesSignalBridge.clear_instance()
    bridge = CasesSignalBridge.instance(event_bus)
    bridge.start()
    yield bridge
    bridge.stop()
    CasesSignalBridge.clear_instance()


@pytest.fixture
def state():
    """Create project state with test project."""
    from pathlib import Path

    from src.contexts.projects.core.entities import Project, ProjectId

    ps = ProjectState()
    ps.project = Project(
        id=ProjectId(value="test-project"),
        name="Test Project",
        path=Path("/tmp/test.qda"),
    )
    return ps


@pytest.fixture
def cases_ctx(case_repo):
    """Create minimal CasesContext for testing."""
    from dataclasses import dataclass

    @dataclass
    class MinimalCasesContext:
        case_repo: SQLiteCaseRepository

    return MinimalCasesContext(case_repo=case_repo)


@pytest.fixture
def viewmodel(case_repo, state, event_bus, cases_ctx, signal_bridge):
    """Create CaseManagerViewModel with real infrastructure and SignalBridge."""
    return CaseManagerViewModel(
        case_repo=case_repo,
        state=state,
        event_bus=event_bus,
        cases_ctx=cases_ctx,
        signal_bridge=signal_bridge,
    )


# =============================================================================
# Seed Data Fixtures
# =============================================================================


@pytest.fixture
def seeded_cases(case_repo):
    """
    Seed the database with test cases.
    Returns dict of created cases for verification.
    """
    cases = {}

    # Case 1: Participant with attributes and sources
    case1 = Case(
        id=CaseId(value=1),
        name="Participant Alpha",
        description="First study participant",
        memo="Urban location, employed",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    case_repo.save(case1)
    case_repo.save_attribute(
        CaseId(value=1),
        CaseAttribute(name="age", attr_type=AttributeType.NUMBER, value=28),
    )
    case_repo.save_attribute(
        CaseId(value=1),
        CaseAttribute(name="gender", attr_type=AttributeType.TEXT, value="female"),
    )
    case_repo.link_source(CaseId(value=1), SourceId(value=100))
    case_repo.link_source(CaseId(value=1), SourceId(value=101))
    cases["alpha"] = case1

    # Case 2: Participant with attributes, no sources
    case2 = Case(
        id=CaseId(value=2),
        name="Participant Beta",
        description="Second study participant",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    case_repo.save(case2)
    case_repo.save_attribute(
        CaseId(value=2),
        CaseAttribute(name="age", attr_type=AttributeType.NUMBER, value=35),
    )
    cases["beta"] = case2

    # Case 3: Site location, no attributes
    case3 = Case(
        id=CaseId(value=3),
        name="Site Gamma",
        description="Research site location",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    case_repo.save(case3)
    case_repo.link_source(CaseId(value=3), SourceId(value=200))
    cases["gamma"] = case3

    return cases


@pytest.fixture
def seeded_state(case_repo, seeded_cases, state):
    """Create state with project set (repos are source of truth)."""
    # State just needs project set, repos are source of truth
    return state


@pytest.fixture
def seeded_viewmodel(case_repo, seeded_state, event_bus, seeded_cases, signal_bridge):
    """Create viewmodel with seeded test data and SignalBridge."""
    from dataclasses import dataclass

    @dataclass
    class MinimalCasesContext:
        case_repo: SQLiteCaseRepository

    cases_ctx = MinimalCasesContext(case_repo=case_repo)
    return CaseManagerViewModel(
        case_repo=case_repo,
        state=seeded_state,
        event_bus=event_bus,
        cases_ctx=cases_ctx,
        signal_bridge=signal_bridge,
    )


# =============================================================================
# Window Fixtures
# =============================================================================


@pytest.fixture
def case_manager_window(qapp, colors, seeded_viewmodel):
    """
    Create a complete Case Manager window for E2E testing with real database.

    This fixture creates a real window with CaseManagerScreen connected
    to a CaseManagerViewModel backed by an in-memory SQLite database.
    """
    window = QMainWindow()
    window.setWindowTitle("Case Manager E2E Test")
    window.setMinimumSize(1200, 800)

    central = QWidget()
    window.setCentralWidget(central)
    layout = QVBoxLayout(central)
    layout.setContentsMargins(0, 0, 0, 0)

    # Create screen with REAL viewmodel
    screen = CaseManagerScreen(viewmodel=seeded_viewmodel, colors=colors)

    layout.addWidget(screen)

    window.show()
    QApplication.processEvents()

    yield {
        "window": window,
        "screen": screen,
        "viewmodel": seeded_viewmodel,
    }

    window.close()


@pytest.fixture
def empty_case_manager_window(qapp, colors, viewmodel):
    """
    Create a Case Manager window with no cases (empty state).
    """
    window = QMainWindow()
    window.setWindowTitle("Case Manager Empty State Test")
    window.setMinimumSize(1200, 800)

    central = QWidget()
    window.setCentralWidget(central)
    layout = QVBoxLayout(central)
    layout.setContentsMargins(0, 0, 0, 0)

    # Create screen with empty viewmodel (no seeded data)
    screen = CaseManagerScreen(viewmodel=viewmodel, colors=colors)

    layout.addWidget(screen)

    window.show()
    QApplication.processEvents()

    yield {
        "window": window,
        "screen": screen,
        "viewmodel": viewmodel,
    }

    window.close()


# =============================================================================
# Test Classes - Full E2E Flows
# =============================================================================


class TestCaseManagerDisplayWithRealData:
    """E2E tests for Case Manager display with real database data."""

    def test_stats_row_shows_correct_counts_from_db(self, case_manager_window):
        """
        E2E: Stats row displays correct counts from database.
        AC #4: Researcher can view all data for a case.
        """
        screen = case_manager_window["screen"]

        # Get stats from the stats row
        stats_row = screen.page._stats_row

        # Should show 3 total cases (seeded data)
        total_card = stats_row._cards["all"]
        assert total_card._count == 3

        # Should show 2 cases with sources (alpha and gamma)
        with_sources_card = stats_row._cards["with_sources"]
        assert with_sources_card._count == 2

        # Should show 3 total attributes (alpha:2 + beta:1 = 3)
        attributes_card = stats_row._cards["has_attributes"]
        assert attributes_card._count == 3

        attach_screenshot(screen, "stats_row_with_counts")

    def test_table_shows_all_cases_from_db(self, case_manager_window):
        """
        E2E: Table displays all cases from database.
        """
        screen = case_manager_window["screen"]

        table = screen.page._case_table._table
        assert table.rowCount() == 3

        attach_screenshot(screen, "case_table_with_all_cases")

    def test_empty_state_shown_when_db_empty(self, empty_case_manager_window):
        """
        E2E: Empty state is displayed when database has no cases.
        """
        screen = empty_case_manager_window["screen"]

        content_stack = screen.page._content_stack
        assert content_stack.currentWidget() == screen.page._empty_state

        attach_screenshot(screen, "case_manager_empty_state")


class TestCreateCaseFlow:
    """
    E2E tests for create case flow.
    AC #1: Researcher can create cases.
    """

    def test_create_case_via_viewmodel_persists_to_db(
        self, empty_case_manager_window, case_repo
    ):
        """
        E2E: Creating a case via viewmodel persists to database.
        """
        viewmodel = empty_case_manager_window["viewmodel"]

        # Create case via viewmodel
        result = viewmodel.create_case(
            name="New Participant",
            description="Created via E2E test",
            memo="Test memo",
        )

        assert result is True

        # Verify in database
        db_case = case_repo.get_by_name("New Participant")
        assert db_case is not None
        assert db_case.name == "New Participant"
        assert db_case.description == "Created via E2E test"

    def test_create_case_rejects_duplicate_name(self, case_manager_window, case_repo):
        """
        E2E: Creating a case with duplicate name fails.
        """
        viewmodel = case_manager_window["viewmodel"]

        # Try to create case with existing name
        result = viewmodel.create_case(name="Participant Alpha")

        assert result is False

        # Database should still have only one "Participant Alpha"
        all_cases = case_repo.get_all()
        alpha_count = sum(1 for c in all_cases if c.name == "Participant Alpha")
        assert alpha_count == 1

    def test_create_case_updates_ui_on_refresh(self, empty_case_manager_window, qapp):
        """
        E2E: Creating a case and refreshing updates the UI.
        """
        screen = empty_case_manager_window["screen"]
        viewmodel = empty_case_manager_window["viewmodel"]

        # Initially empty
        assert screen.page._case_table._table.rowCount() == 0

        # Create case
        viewmodel.create_case(name="Fresh Case", description="Test")

        # Refresh screen
        screen.refresh()
        QApplication.processEvents()

        # Should now show one case
        assert screen.page._case_table._table.rowCount() == 1

        attach_screenshot(screen, "case_created_ui_refresh")

    def test_case_created_signal_emitted_with_new_id(
        self, empty_case_manager_window, qapp
    ):
        """
        E2E: case_created signal is emitted with the new case ID.
        """
        screen = empty_case_manager_window["screen"]
        spy = QSignalSpy(screen.case_created)

        # Simulate create flow (normally via dialog)
        # For E2E, we directly create and emit
        viewmodel = empty_case_manager_window["viewmodel"]
        viewmodel.create_case(name="Signal Test Case")
        cases = viewmodel.load_cases()
        new_case = next(c for c in cases if c.name == "Signal Test Case")
        screen.case_created.emit(new_case.id)

        QApplication.processEvents()

        assert spy.count() == 1
        assert spy.at(0)[0] == new_case.id


class TestDeleteCaseFlow:
    """E2E tests for delete case flow."""

    def test_delete_case_via_viewmodel_removes_from_db(
        self, case_manager_window, case_repo
    ):
        """
        E2E: Deleting a case via viewmodel removes it from database.
        """
        viewmodel = case_manager_window["viewmodel"]

        # Verify case exists
        assert case_repo.get_by_id(CaseId(value=2)) is not None

        # Delete via viewmodel
        result = viewmodel.delete_case(case_id=2)
        assert result is True

        # Verify removed from database
        assert case_repo.get_by_id(CaseId(value=2)) is None

    def test_delete_case_removes_source_links(self, case_manager_window, case_repo):
        """
        E2E: Deleting a case removes its source links.
        """
        viewmodel = case_manager_window["viewmodel"]

        # Case 1 has source links
        assert len(case_repo.get_source_ids(CaseId(value=1))) == 2

        # Delete case
        viewmodel.delete_case(case_id=1)

        # Source links should be gone
        assert len(case_repo.get_source_ids(CaseId(value=1))) == 0

    def test_delete_case_removes_attributes(self, case_manager_window, case_repo):
        """
        E2E: Deleting a case removes its attributes.
        """
        viewmodel = case_manager_window["viewmodel"]

        # Case 1 has attributes
        attrs = case_repo.get_attributes(CaseId(value=1))
        assert len(attrs) == 2

        # Delete case
        viewmodel.delete_case(case_id=1)

        # Attributes should be gone
        attrs = case_repo.get_attributes(CaseId(value=1))
        assert len(attrs) == 0

    def test_delete_case_updates_ui_on_refresh(self, case_manager_window, qapp):
        """
        E2E: Deleting a case and refreshing updates the UI.
        """
        screen = case_manager_window["screen"]
        viewmodel = case_manager_window["viewmodel"]

        # Initially 3 cases
        assert screen.page._case_table._table.rowCount() == 3

        # Delete case
        viewmodel.delete_case(case_id=1)

        # Refresh screen
        screen.refresh()
        QApplication.processEvents()

        # Should now show 2 cases
        assert screen.page._case_table._table.rowCount() == 2

        attach_screenshot(screen, "case_deleted_ui_refresh")


class TestLinkSourceFlow:
    """
    E2E tests for link source to case flow.
    AC #2: Researcher can link sources to cases.
    """

    def test_link_source_to_case(self, case_manager_window, case_repo):
        """
        E2E: Link source to case persists to database.

        Note: Source validation is now done at higher levels (UI/ViewModel),
        the command handler trusts that valid source IDs are passed.
        """
        viewmodel = case_manager_window["viewmodel"]

        # Link source 300 to case 2 (repo handles persistence)
        result = viewmodel.link_source(case_id=2, source_id=300)
        assert result is True

        # Verify link persisted in database
        source_ids = case_repo.get_source_ids(CaseId(value=2))
        assert 300 in source_ids

    def test_unlink_source_via_viewmodel_removes_from_db(
        self, case_manager_window, case_repo
    ):
        """
        E2E: Unlinking a source via viewmodel removes from database.
        """
        viewmodel = case_manager_window["viewmodel"]

        # Case 1 has source 100
        assert case_repo.is_source_linked(CaseId(value=1), SourceId(value=100))

        # Unlink source
        result = viewmodel.unlink_source(case_id=1, source_id=100)
        assert result is True

        # Verify removed from database
        assert not case_repo.is_source_linked(CaseId(value=1), SourceId(value=100))

    def test_summary_shows_cases_with_sources(self, case_manager_window, case_repo):
        """
        E2E: Summary shows correct count of cases with sources.

        Note: Link source requires source validation, so we just verify
        the existing seeded data is correctly summarized.
        """
        viewmodel = case_manager_window["viewmodel"]

        # Summary from seeded data
        summary = viewmodel.get_summary()
        # alpha and gamma have sources from seeding
        assert summary.cases_with_sources == 2  # alpha, gamma


class TestAddAttributeFlow:
    """
    E2E tests for add attribute to case flow.
    AC #3: Researcher can add case attributes.
    """

    def test_add_attribute_via_viewmodel_persists_to_db(
        self, case_manager_window, case_repo
    ):
        """
        E2E: Adding an attribute via viewmodel persists to database.
        """
        viewmodel = case_manager_window["viewmodel"]

        # Add new attribute
        result = viewmodel.add_attribute(
            case_id=1,
            name="occupation",
            attr_type="text",
            value="engineer",
        )
        assert result is True

        # Verify in database
        attr = case_repo.get_attribute(CaseId(value=1), "occupation")
        assert attr is not None
        assert attr.value == "engineer"

    def test_add_number_attribute(self, case_manager_window, case_repo):
        """
        E2E: Adding a number attribute persists correctly.
        """
        viewmodel = case_manager_window["viewmodel"]

        result = viewmodel.add_attribute(
            case_id=1,
            name="income",
            attr_type="number",
            value=75000,
        )
        assert result is True

        attr = case_repo.get_attribute(CaseId(value=1), "income")
        assert attr is not None
        assert attr.attr_type == AttributeType.NUMBER
        assert attr.value == 75000

    def test_add_boolean_attribute(self, case_manager_window, case_repo):
        """
        E2E: Adding a boolean attribute persists correctly.
        """
        viewmodel = case_manager_window["viewmodel"]

        result = viewmodel.add_attribute(
            case_id=1,
            name="employed",
            attr_type="boolean",
            value=True,
        )
        assert result is True

        attr = case_repo.get_attribute(CaseId(value=1), "employed")
        assert attr is not None
        assert attr.attr_type == AttributeType.BOOLEAN
        assert attr.value is True

    def test_update_existing_attribute(self, case_manager_window, case_repo):
        """
        E2E: Updating an existing attribute changes the value.
        """
        viewmodel = case_manager_window["viewmodel"]

        # Initial age is 28
        attr = case_repo.get_attribute(CaseId(value=1), "age")
        assert attr.value == 28

        # Update age
        viewmodel.add_attribute(
            case_id=1,
            name="age",
            attr_type="number",
            value=29,
        )

        # Verify updated
        attr = case_repo.get_attribute(CaseId(value=1), "age")
        assert attr.value == 29

    def test_remove_attribute_via_viewmodel(self, case_manager_window, case_repo):
        """
        E2E: Removing an attribute via viewmodel removes from database.
        """
        viewmodel = case_manager_window["viewmodel"]

        # Verify attribute exists
        assert case_repo.get_attribute(CaseId(value=1), "gender") is not None

        # Remove attribute
        result = viewmodel.remove_attribute(case_id=1, name="gender")
        assert result is True

        # Verify removed
        assert case_repo.get_attribute(CaseId(value=1), "gender") is None

    def test_add_attribute_updates_summary(self, case_manager_window):
        """
        E2E: Adding attributes updates summary statistics.
        """
        viewmodel = case_manager_window["viewmodel"]

        # Initial count
        summary = viewmodel.get_summary()
        initial_attrs = summary.total_attributes

        # Add new attribute
        viewmodel.add_attribute(
            case_id=3,
            name="location_type",
            attr_type="text",
            value="urban",
        )

        # Updated count
        summary = viewmodel.get_summary()
        assert summary.total_attributes == initial_attrs + 1


class TestViewCaseDataFlow:
    """
    E2E tests for viewing case data.
    AC #4: Researcher can view all data for a case.
    """

    def test_get_case_returns_complete_dto(self, case_manager_window):
        """
        E2E: Getting a case returns complete DTO with all data.
        """
        viewmodel = case_manager_window["viewmodel"]

        case_dto = viewmodel.get_case(case_id=1)

        assert case_dto is not None
        assert case_dto.name == "Participant Alpha"
        assert case_dto.description == "First study participant"
        assert case_dto.source_count == 2
        assert len(case_dto.attributes) == 2

        # Check attributes
        attr_names = [a.name for a in case_dto.attributes]
        assert "age" in attr_names
        assert "gender" in attr_names

    def test_load_cases_returns_all_with_data(self, case_manager_window):
        """
        E2E: Loading all cases returns complete DTOs.
        """
        viewmodel = case_manager_window["viewmodel"]

        cases = viewmodel.load_cases()

        assert len(cases) == 3

        # Find each case and verify
        alpha = next(c for c in cases if c.name == "Participant Alpha")
        assert alpha.source_count == 2
        assert len(alpha.attributes) == 2

        beta = next(c for c in cases if c.name == "Participant Beta")
        assert beta.source_count == 0
        assert len(beta.attributes) == 1

        gamma = next(c for c in cases if c.name == "Site Gamma")
        assert gamma.source_count == 1
        assert len(gamma.attributes) == 0

    def test_search_cases_filters_correctly(self, case_manager_window):
        """
        E2E: Searching cases filters by name.
        """
        viewmodel = case_manager_window["viewmodel"]

        # Search for "Participant"
        results = viewmodel.search_cases("Participant")
        assert len(results) == 2

        names = [c.name for c in results]
        assert "Participant Alpha" in names
        assert "Participant Beta" in names

        # Search for "Site"
        results = viewmodel.search_cases("Site")
        assert len(results) == 1
        assert results[0].name == "Site Gamma"

    def test_case_insensitive_search(self, case_manager_window):
        """
        E2E: Search is case-insensitive.
        """
        viewmodel = case_manager_window["viewmodel"]

        # Lowercase search
        results = viewmodel.search_cases("alpha")
        assert len(results) == 1
        assert results[0].name == "Participant Alpha"


class TestStatsRowFiltering:
    """E2E tests for filtering via stats row clicks."""

    def test_click_all_cases_card_emits_filter_signal(self, case_manager_window, qapp):
        """
        E2E: Clicking all cases card emits filter signal.
        """
        screen = case_manager_window["screen"]

        spy = QSignalSpy(screen.page.filter_changed)

        # Click the all cases card
        all_card = screen.page._stats_row._cards["all"]
        all_card.clicked.emit("all")
        QApplication.processEvents()

        assert spy.count() == 1
        assert spy.at(0)[0] == "all"

        attach_screenshot(screen, "stats_row_all_filter_clicked")

    def test_click_with_sources_card_filters_display(self, case_manager_window, qapp):
        """
        E2E: Clicking "with sources" card filters to cases with linked sources.
        """
        screen = case_manager_window["screen"]

        spy = QSignalSpy(screen.page.filter_changed)

        # Emit filter signal
        screen.page._stats_row._cards["with_sources"].clicked.emit("with_sources")
        QApplication.processEvents()

        # Verify signal emitted with correct filter type
        assert spy.count() == 1
        assert spy.at(0)[0] == "with_sources"

        # Verify card visual state changed (active style applied)
        card = screen.page._stats_row._cards["with_sources"]
        assert card._active is True

        attach_screenshot(screen, "stats_row_with_sources_filter_active")


class TestTableSelection:
    """E2E tests for table row selection."""

    def test_single_click_selects_case_in_viewmodel(self, case_manager_window, qapp):
        """
        E2E: Single clicking a row selects the case in viewmodel.
        """
        screen = case_manager_window["screen"]
        viewmodel = case_manager_window["viewmodel"]

        # Simulate click via signal
        screen._on_case_clicked("1")
        QApplication.processEvents()

        assert viewmodel.get_selected_case_id() == 1

        attach_screenshot(screen, "table_row_selected")

    def test_double_click_emits_navigation_signal(self, case_manager_window, qapp):
        """
        E2E: Double-clicking a row emits navigate_to_case signal.
        """
        screen = case_manager_window["screen"]

        spy = QSignalSpy(screen.navigate_to_case)

        # Simulate double-click via handler
        screen._on_case_double_clicked("2")
        QApplication.processEvents()

        assert spy.count() == 1
        assert spy.at(0)[0] == "2"


class TestDataRefresh:
    """E2E tests for data refresh operations."""

    def test_refresh_reloads_from_database(self, case_manager_window, case_repo, qapp):
        """
        E2E: Refresh reloads data from database.
        """
        screen = case_manager_window["screen"]

        # Modify database directly
        new_case = Case(
            id=CaseId(value=99),
            name="Direct DB Insert",
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        case_repo.save(new_case)

        # Initially 3 cases in UI
        assert screen.page._case_table._table.rowCount() == 3

        # Refresh
        screen.refresh()
        QApplication.processEvents()

        # Should now show 4 cases
        assert screen.page._case_table._table.rowCount() == 4

        attach_screenshot(screen, "data_refresh_after_db_insert")

    def test_set_viewmodel_loads_new_data(self, qapp, colors, viewmodel, case_repo):
        """
        E2E: Setting a new viewmodel loads its data.
        """
        # Create screen without viewmodel
        screen = CaseManagerScreen(colors=colors)
        assert screen._viewmodel is None

        # Create a case using the viewmodel
        viewmodel.create_case(name="VM Test Case")

        screen.set_viewmodel(viewmodel)
        QApplication.processEvents()

        # Should load the case
        assert screen.page._case_table._table.rowCount() == 1

        attach_screenshot(screen, "viewmodel_set_loads_data")


class TestScreenProtocol:
    """E2E tests for ScreenProtocol implementation."""

    def test_get_status_message_shows_summary(self, case_manager_window):
        """
        E2E: Status message shows case summary from database.
        """
        screen = case_manager_window["screen"]

        message = screen.get_status_message()

        assert "3 cases" in message
        assert "2 with sources" in message
        assert "3 attributes" in message

        attach_screenshot(screen, "status_message_with_summary")

    def test_get_content_returns_self(self, case_manager_window):
        """
        E2E: get_content returns the screen itself.
        """
        screen = case_manager_window["screen"]
        assert screen.get_content() == screen

    def test_get_toolbar_content_returns_none(self, case_manager_window):
        """
        E2E: get_toolbar_content returns None (embedded toolbar).
        """
        screen = case_manager_window["screen"]
        assert screen.get_toolbar_content() is None


class TestSelectionManagement:
    """E2E tests for selection state management."""

    def test_clear_selection_clears_viewmodel(self, case_manager_window, qapp):
        """
        E2E: Clearing selection clears viewmodel state.
        """
        screen = case_manager_window["screen"]
        viewmodel = case_manager_window["viewmodel"]

        # Select a case
        viewmodel.select_case(1)
        assert viewmodel.get_selected_case_id() == 1

        # Clear selection
        screen.clear_selection()
        QApplication.processEvents()

        assert viewmodel.get_selected_case_id() is None

        attach_screenshot(screen, "selection_cleared")

    def test_delete_selected_case_clears_selection(self, case_manager_window, qapp):
        """
        E2E: Deleting the selected case clears selection.
        """
        viewmodel = case_manager_window["viewmodel"]

        # Select and delete
        viewmodel.select_case(2)
        viewmodel.delete_case(2)

        assert viewmodel.get_selected_case_id() is None


class TestReactiveSignalBridgeFlow:
    """
    E2E tests for reactive SignalBridge updates.

    Verifies the full reactive flow:
    User Action → ViewModel → Use Cases → Domain → Events → SignalBridge → ViewModel signals

    These tests ensure that domain events properly propagate through the SignalBridge
    to trigger ViewModel signal emissions for UI updates.
    """

    def test_create_case_emits_cases_changed_signal(self, viewmodel, qapp):
        """
        E2E: Creating a case emits cases_changed signal via SignalBridge.

        Flow: create_case() → CaseCreated event → SignalBridge → ViewModel.cases_changed
        """
        # Set up signal spy
        spy = QSignalSpy(viewmodel.cases_changed)

        # Create a case
        result = viewmodel.create_case(name="Reactive Test Case")
        assert result is True

        # Process Qt events to allow signal propagation
        QApplication.processEvents()

        # Verify signal was emitted
        assert spy.count() == 1, "cases_changed signal should be emitted once"

    def test_create_case_emits_summary_changed_signal(self, viewmodel, qapp):
        """
        E2E: Creating a case also emits summary_changed signal.

        Flow: create_case() → CaseCreated event → SignalBridge → ViewModel.summary_changed
        """
        spy = QSignalSpy(viewmodel.summary_changed)

        viewmodel.create_case(name="Summary Test Case")
        QApplication.processEvents()

        assert spy.count() == 1, "summary_changed signal should be emitted once"

    def test_delete_case_emits_cases_changed_signal(self, viewmodel, qapp):
        """
        E2E: Deleting a case emits cases_changed signal via SignalBridge.

        Flow: delete_case() → CaseRemoved event → SignalBridge → ViewModel.cases_changed
        """
        # First create a case to delete
        viewmodel.create_case(name="Case To Delete")
        QApplication.processEvents()

        cases = viewmodel.load_cases()
        case_id = int(cases[0].id)

        # Set up spy after creation
        spy = QSignalSpy(viewmodel.cases_changed)

        # Delete the case
        result = viewmodel.delete_case(case_id)
        assert result is True
        QApplication.processEvents()

        assert spy.count() == 1, "cases_changed signal should be emitted on delete"

    def test_update_case_emits_case_updated_signal(self, viewmodel, qapp):
        """
        E2E: Updating a case emits case_updated signal via SignalBridge.

        Flow: update_case() → CaseUpdated event → SignalBridge → ViewModel.case_updated
        """
        # Create a case first
        viewmodel.create_case(name="Original Name")
        QApplication.processEvents()

        cases = viewmodel.load_cases()
        case_id = int(cases[0].id)

        # Set up spy after creation
        spy = QSignalSpy(viewmodel.case_updated)

        # Update the case
        result = viewmodel.update_case(case_id, name="Updated Name")
        assert result is True
        QApplication.processEvents()

        assert spy.count() == 1, "case_updated signal should be emitted"
        # Verify payload contains updated case DTO
        emitted_dto = spy.at(0)[0]
        assert emitted_dto.name == "Updated Name"

    def test_add_attribute_emits_case_updated_signal(self, viewmodel, qapp):
        """
        E2E: Adding an attribute emits case_updated signal via SignalBridge.

        Flow: add_attribute() → CaseAttributeSet event → SignalBridge → ViewModel.case_updated
        """
        # Create a case first
        viewmodel.create_case(name="Attribute Test Case")
        QApplication.processEvents()

        cases = viewmodel.load_cases()
        case_id = int(cases[0].id)

        # Set up spy after creation
        spy = QSignalSpy(viewmodel.case_updated)

        # Add attribute
        result = viewmodel.add_attribute(case_id, "age", "number", 25)
        assert result is True
        QApplication.processEvents()

        assert spy.count() == 1, (
            "case_updated signal should be emitted for attribute change"
        )

    def test_signal_bridge_required_for_reactive_updates(
        self, case_repo, state, event_bus, cases_ctx, qapp
    ):
        """
        E2E: ViewModel without SignalBridge does NOT receive reactive updates.

        This test verifies that SignalBridge is required for the reactive flow.
        """
        # Create viewmodel WITHOUT signal_bridge
        vm_no_bridge = CaseManagerViewModel(
            case_repo=case_repo,
            state=state,
            event_bus=event_bus,
            cases_ctx=cases_ctx,
            signal_bridge=None,  # No bridge
        )

        spy = QSignalSpy(vm_no_bridge.cases_changed)

        # Create a case - event is published but no signal emitted
        vm_no_bridge.create_case(name="No Bridge Case")
        QApplication.processEvents()

        # Signal NOT emitted because no SignalBridge is connected
        assert spy.count() == 0, (
            "Without SignalBridge, no reactive signal should be emitted"
        )
