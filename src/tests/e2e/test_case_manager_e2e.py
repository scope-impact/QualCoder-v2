"""
Case Manager End-to-End Tests

True E2E tests with FULL behavior - real database, viewmodel, and UI integration.
Tests the complete flow: UI action -> ViewModel -> Use Cases -> Repository -> Database -> UI update

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

from datetime import UTC, datetime

import allure
import pytest
from PySide6.QtTest import QSignalSpy
from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget

from src.contexts.cases.core.entities import AttributeType, Case, CaseAttribute
from src.contexts.cases.interface.signal_bridge import CasesSignalBridge
from src.contexts.cases.presentation import CaseManagerScreen, CaseManagerViewModel
from src.shared.common.types import CaseId, SourceId
from src.tests.e2e.helpers import attach_screenshot

pytestmark = [
    pytest.mark.e2e,
    allure.epic("QualCoder v2"),
    allure.feature("QC-034 Manage Cases"),
]


@pytest.fixture
def signal_bridge(event_bus):
    """Create and start CasesSignalBridge for reactive UI updates."""
    CasesSignalBridge.clear_instance()
    bridge = CasesSignalBridge.instance(event_bus)
    bridge.start()
    yield bridge
    bridge.stop()
    CasesSignalBridge.clear_instance()


@pytest.fixture
def viewmodel(case_repo, project_state, event_bus, cases_context, signal_bridge):
    """Create CaseManagerViewModel with real infrastructure and SignalBridge."""
    return CaseManagerViewModel(
        case_repo=case_repo,
        state=project_state,
        event_bus=event_bus,
        cases_ctx=cases_context,
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
        id=CaseId(value="1"),
        name="Participant Alpha",
        description="First study participant",
        memo="Urban location, employed",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    case_repo.save(case1)
    case_repo.save_attribute(
        CaseId(value="1"),
        CaseAttribute(name="age", attr_type=AttributeType.NUMBER, value=28),
    )
    case_repo.save_attribute(
        CaseId(value="1"),
        CaseAttribute(name="gender", attr_type=AttributeType.TEXT, value="female"),
    )
    case_repo.link_source(CaseId(value="1"), SourceId(value="100"))
    case_repo.link_source(CaseId(value="1"), SourceId(value="101"))
    cases["alpha"] = case1

    # Case 2: Participant with attributes, no sources
    case2 = Case(
        id=CaseId(value="2"),
        name="Participant Beta",
        description="Second study participant",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    case_repo.save(case2)
    case_repo.save_attribute(
        CaseId(value="2"),
        CaseAttribute(name="age", attr_type=AttributeType.NUMBER, value=35),
    )
    cases["beta"] = case2

    # Case 3: Site location, no attributes
    case3 = Case(
        id=CaseId(value="3"),
        name="Site Gamma",
        description="Research site location",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    case_repo.save(case3)
    case_repo.link_source(CaseId(value="3"), SourceId(value="200"))
    cases["gamma"] = case3

    return cases


@pytest.fixture
def seeded_state(case_repo, seeded_cases, project_state):
    """Create state with project set (repos are source of truth)."""
    return project_state


@pytest.fixture
def seeded_viewmodel(
    case_repo, seeded_state, event_bus, seeded_cases, cases_context, signal_bridge
):
    """Create viewmodel with seeded test data and SignalBridge."""
    return CaseManagerViewModel(
        case_repo=case_repo,
        state=seeded_state,
        event_bus=event_bus,
        cases_ctx=cases_context,
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


@allure.story("QC-034.01 View Cases")
class TestCaseManagerDisplayWithRealData:
    """E2E tests for Case Manager display with real database data."""

    def test_stats_row_and_table_show_correct_data(self, case_manager_window):
        """
        E2E: Stats row displays correct counts and table shows all cases.
        AC #4: Researcher can view all data for a case.
        """
        screen = case_manager_window["screen"]

        # Stats row
        stats_row = screen.page._stats_row
        total_card = stats_row._cards["all"]
        assert total_card._count == 3

        with_sources_card = stats_row._cards["with_sources"]
        assert with_sources_card._count == 2

        attributes_card = stats_row._cards["has_attributes"]
        assert attributes_card._count == 3

        # Table
        table = screen.page._case_table._table
        assert table.rowCount() == 3

        attach_screenshot(screen, "stats_row_and_table_with_data")

    def test_empty_state_shown_when_db_empty(self, empty_case_manager_window):
        """
        E2E: Empty state is displayed when database has no cases.
        """
        screen = empty_case_manager_window["screen"]

        content_stack = screen.page._content_stack
        assert content_stack.currentWidget() == screen.page._empty_state

        attach_screenshot(screen, "case_manager_empty_state")


@allure.story("QC-034.02 Create Case")
class TestCreateCaseFlow:
    """
    E2E tests for create case flow.
    AC #1: Researcher can create cases.
    """

    def test_create_case_persists_and_rejects_duplicate(
        self, empty_case_manager_window, case_manager_window, case_repo
    ):
        """
        E2E: Creating a case persists to database; duplicate name fails.
        """
        viewmodel = empty_case_manager_window["viewmodel"]

        # Create case
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

        # Reject duplicate
        vm2 = case_manager_window["viewmodel"]
        result = vm2.create_case(name="Participant Alpha")
        assert result is False

        all_cases = case_repo.get_all()
        alpha_count = sum(1 for c in all_cases if c.name == "Participant Alpha")
        assert alpha_count == 1

    def test_create_case_updates_ui_and_emits_signal(
        self, empty_case_manager_window, qapp
    ):
        """
        E2E: Creating a case and refreshing updates UI; signal emitted with ID.
        """
        screen = empty_case_manager_window["screen"]
        viewmodel = empty_case_manager_window["viewmodel"]

        # Initially empty
        assert screen.page._case_table._table.rowCount() == 0

        # Create and refresh
        viewmodel.create_case(name="Fresh Case", description="Test")
        screen.refresh()
        QApplication.processEvents()
        assert screen.page._case_table._table.rowCount() == 1

        # Signal test
        spy = QSignalSpy(screen.case_created)
        viewmodel.create_case(name="Signal Test Case")
        cases = viewmodel.load_cases()
        new_case = next(c for c in cases if c.name == "Signal Test Case")
        screen.case_created.emit(new_case.id)
        QApplication.processEvents()

        assert spy.count() == 1
        assert spy.at(0)[0] == new_case.id

        attach_screenshot(screen, "case_created_ui_refresh")


@allure.story("QC-034.03 Delete Case")
class TestDeleteCaseFlow:
    """E2E tests for delete case flow."""

    def test_delete_case_removes_and_cascades(self, case_manager_window, case_repo):
        """
        E2E: Deleting a case removes it and cascades source links and attributes.
        """
        viewmodel = case_manager_window["viewmodel"]

        # Verify case 1 has links and attributes
        assert len(case_repo.get_source_ids(CaseId(value="1"))) == 2
        assert len(case_repo.get_attributes(CaseId(value="1"))) == 2

        # Delete case 1
        viewmodel.delete_case(case_id="1")

        # Source links and attributes gone
        assert len(case_repo.get_source_ids(CaseId(value="1"))) == 0
        assert len(case_repo.get_attributes(CaseId(value="1"))) == 0

        # Delete case 2 and verify removal
        assert case_repo.get_by_id(CaseId(value="2")) is not None
        result = viewmodel.delete_case(case_id="2")
        assert result is True
        assert case_repo.get_by_id(CaseId(value="2")) is None

    def test_delete_case_updates_ui_on_refresh(self, case_manager_window, qapp):
        """
        E2E: Deleting a case and refreshing updates the UI.
        """
        screen = case_manager_window["screen"]
        viewmodel = case_manager_window["viewmodel"]

        assert screen.page._case_table._table.rowCount() == 3

        viewmodel.delete_case(case_id="1")
        screen.refresh()
        QApplication.processEvents()

        assert screen.page._case_table._table.rowCount() == 2

        attach_screenshot(screen, "case_deleted_ui_refresh")


@allure.story("QC-034.04 Link Sources to Cases")
class TestLinkSourceFlow:
    """
    E2E tests for link source to case flow.
    AC #2: Researcher can link sources to cases.
    """

    def test_link_and_unlink_source(self, case_manager_window, case_repo):
        """
        E2E: Link and unlink sources to/from cases.
        """
        viewmodel = case_manager_window["viewmodel"]

        # Link source 300 to case 2
        result = viewmodel.link_source(case_id="2", source_id="300")
        assert result is True
        source_ids = case_repo.get_source_ids(CaseId(value="2"))
        assert "300" in source_ids

        # Unlink source 100 from case 1
        assert case_repo.is_source_linked(CaseId(value="1"), SourceId(value="100"))
        result = viewmodel.unlink_source(case_id="1", source_id="100")
        assert result is True
        assert not case_repo.is_source_linked(CaseId(value="1"), SourceId(value="100"))

    def test_summary_shows_cases_with_sources(self, case_manager_window, case_repo):
        """
        E2E: Summary shows correct count of cases with sources.
        """
        viewmodel = case_manager_window["viewmodel"]
        summary = viewmodel.get_summary()
        assert summary.cases_with_sources == 2  # alpha, gamma


@allure.story("QC-034.05 Case Attributes")
class TestAddAttributeFlow:
    """
    E2E tests for add attribute to case flow.
    AC #3: Researcher can add case attributes.
    """

    def test_add_text_and_typed_attributes(self, case_manager_window, case_repo):
        """
        E2E: Adding text, number, and boolean attributes persists correctly.
        """
        viewmodel = case_manager_window["viewmodel"]

        # Text attribute
        result = viewmodel.add_attribute(
            case_id="1",
            name="occupation",
            attr_type="text",
            value="engineer",
        )
        assert result is True
        attr = case_repo.get_attribute(CaseId(value="1"), "occupation")
        assert attr is not None
        assert attr.value == "engineer"

        # Number attribute
        result = viewmodel.add_attribute(
            case_id="1",
            name="income",
            attr_type="number",
            value=75000,
        )
        assert result is True
        attr = case_repo.get_attribute(CaseId(value="1"), "income")
        assert attr.attr_type == AttributeType.NUMBER
        assert attr.value == 75000

        # Boolean attribute
        result = viewmodel.add_attribute(
            case_id="1",
            name="employed",
            attr_type="boolean",
            value=True,
        )
        assert result is True
        attr = case_repo.get_attribute(CaseId(value="1"), "employed")
        assert attr.attr_type == AttributeType.BOOLEAN
        assert attr.value is True

    def test_update_remove_and_summary(self, case_manager_window, case_repo):
        """
        E2E: Update existing attribute, remove attribute, and verify summary updates.
        """
        viewmodel = case_manager_window["viewmodel"]

        # Update age
        attr = case_repo.get_attribute(CaseId(value="1"), "age")
        assert attr.value == 28
        viewmodel.add_attribute(case_id="1", name="age", attr_type="number", value=29)
        attr = case_repo.get_attribute(CaseId(value="1"), "age")
        assert attr.value == 29

        # Remove gender
        assert case_repo.get_attribute(CaseId(value="1"), "gender") is not None
        result = viewmodel.remove_attribute(case_id="1", name="gender")
        assert result is True
        assert case_repo.get_attribute(CaseId(value="1"), "gender") is None

        # Summary updates
        summary = viewmodel.get_summary()
        initial_attrs = summary.total_attributes
        viewmodel.add_attribute(
            case_id="3",
            name="location_type",
            attr_type="text",
            value="urban",
        )
        summary = viewmodel.get_summary()
        assert summary.total_attributes == initial_attrs + 1


@allure.story("QC-034.06 View Case Data")
class TestViewCaseDataFlow:
    """
    E2E tests for viewing case data.
    AC #4: Researcher can view all data for a case.
    """

    def test_get_case_and_load_all(self, case_manager_window):
        """
        E2E: Get single case DTO and load all cases with complete data.
        """
        viewmodel = case_manager_window["viewmodel"]

        # Single case
        case_dto = viewmodel.get_case(case_id="1")
        assert case_dto is not None
        assert case_dto.name == "Participant Alpha"
        assert case_dto.description == "First study participant"
        assert case_dto.source_count == 2
        assert len(case_dto.attributes) == 2
        attr_names = [a.name for a in case_dto.attributes]
        assert "age" in attr_names
        assert "gender" in attr_names

        # All cases
        cases = viewmodel.load_cases()
        assert len(cases) == 3

        alpha = next(c for c in cases if c.name == "Participant Alpha")
        assert alpha.source_count == 2
        assert len(alpha.attributes) == 2

        beta = next(c for c in cases if c.name == "Participant Beta")
        assert beta.source_count == 0
        assert len(beta.attributes) == 1

        gamma = next(c for c in cases if c.name == "Site Gamma")
        assert gamma.source_count == 1
        assert len(gamma.attributes) == 0

    def test_search_cases_filters_by_name(self, case_manager_window):
        """
        E2E: Searching cases filters by name (case-insensitive).
        """
        viewmodel = case_manager_window["viewmodel"]

        results = viewmodel.search_cases("Participant")
        assert len(results) == 2
        names = [c.name for c in results]
        assert "Participant Alpha" in names
        assert "Participant Beta" in names

        results = viewmodel.search_cases("Site")
        assert len(results) == 1
        assert results[0].name == "Site Gamma"

        results = viewmodel.search_cases("alpha")
        assert len(results) == 1
        assert results[0].name == "Participant Alpha"


@allure.story("QC-034.01 View Cases")
class TestStatsRowFiltering:
    """E2E tests for filtering via stats row clicks."""

    def test_clicking_stat_cards_emits_filter_signals(self, case_manager_window, qapp):
        """
        E2E: Clicking stat cards emits correct filter signals and updates active state.
        """
        screen = case_manager_window["screen"]

        spy_all = QSignalSpy(screen.page.filter_changed)
        all_card = screen.page._stats_row._cards["all"]
        all_card.clicked.emit("all")
        QApplication.processEvents()
        assert spy_all.count() == 1
        assert spy_all.at(0)[0] == "all"

        spy_sources = QSignalSpy(screen.page.filter_changed)
        screen.page._stats_row._cards["with_sources"].clicked.emit("with_sources")
        QApplication.processEvents()
        assert spy_sources.count() == 1
        assert spy_sources.at(0)[0] == "with_sources"

        card = screen.page._stats_row._cards["with_sources"]
        assert card._active is True

        attach_screenshot(screen, "stats_row_filter_cards")


@allure.story("QC-034.01 View Cases")
class TestTableSelection:
    """E2E tests for table row selection."""

    def test_click_selects_and_double_click_navigates(self, case_manager_window, qapp):
        """
        E2E: Single click selects case; double click emits navigate signal.
        """
        screen = case_manager_window["screen"]
        viewmodel = case_manager_window["viewmodel"]

        # Single click selects
        screen._on_case_clicked("1")
        QApplication.processEvents()
        assert viewmodel.get_selected_case_id() == "1"

        # Double click navigates
        spy = QSignalSpy(screen.navigate_to_case)
        screen._on_case_double_clicked("2")
        QApplication.processEvents()
        assert spy.count() == 1
        assert spy.at(0)[0] == "2"

        attach_screenshot(screen, "table_row_selected")


@allure.story("QC-034.07 Data Refresh")
class TestDataRefresh:
    """E2E tests for data refresh operations."""

    def test_refresh_and_set_viewmodel(
        self, case_manager_window, case_repo, qapp, colors, viewmodel
    ):
        """
        E2E: Refresh reloads from database; setting new viewmodel loads data.
        """
        screen = case_manager_window["screen"]

        # Insert directly and refresh
        new_case = Case(
            id=CaseId(value="99"),
            name="Direct DB Insert",
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        case_repo.save(new_case)
        assert screen.page._case_table._table.rowCount() == 3

        screen.refresh()
        QApplication.processEvents()
        assert screen.page._case_table._table.rowCount() == 4

        attach_screenshot(screen, "data_refresh_after_db_insert")

        # Set viewmodel on new screen
        screen2 = CaseManagerScreen(colors=colors)
        assert screen2._viewmodel is None
        viewmodel.create_case(name="VM Test Case")
        screen2.set_viewmodel(viewmodel)
        QApplication.processEvents()
        # Should show all cases from the shared repo (3 seeded + 1 inserted + 1 VM)
        assert screen2.page._case_table._table.rowCount() == 5


@allure.story("QC-034.01 View Cases")
class TestScreenProtocol:
    """E2E tests for ScreenProtocol implementation."""

    def test_status_message_and_protocol_conformance(self, case_manager_window):
        """
        E2E: Status message shows summary; screen conforms to protocol.
        """
        screen = case_manager_window["screen"]

        message = screen.get_status_message()
        assert "3 cases" in message
        assert "2 with sources" in message
        assert "3 attributes" in message

        assert screen.get_content() == screen
        assert screen.get_toolbar_content() is None

        attach_screenshot(screen, "status_message_with_summary")


@allure.story("QC-034.01 View Cases")
class TestSelectionManagement:
    """E2E tests for selection state management."""

    def test_clear_and_delete_clears_selection(self, case_manager_window, qapp):
        """
        E2E: Clearing selection and deleting selected case both clear viewmodel state.
        """
        screen = case_manager_window["screen"]
        viewmodel = case_manager_window["viewmodel"]

        # Select and clear
        viewmodel.select_case("1")
        assert viewmodel.get_selected_case_id() == "1"
        screen.clear_selection()
        QApplication.processEvents()
        assert viewmodel.get_selected_case_id() is None

        # Select and delete
        viewmodel.select_case("2")
        viewmodel.delete_case("2")
        assert viewmodel.get_selected_case_id() is None

        attach_screenshot(screen, "selection_cleared")


@allure.story("QC-034.07 Data Refresh")
class TestReactiveSignalBridgeFlow:
    """
    E2E tests for reactive SignalBridge updates.

    Verifies the full reactive flow:
    User Action -> ViewModel -> Use Cases -> Domain -> Events -> SignalBridge -> ViewModel signals
    """

    def test_create_delete_update_emit_signals(self, viewmodel, qapp):
        """
        E2E: Create, delete, and update operations emit reactive signals.
        """
        # Create emits both signals
        cases_spy = QSignalSpy(viewmodel.cases_changed)
        summary_spy = QSignalSpy(viewmodel.summary_changed)
        result = viewmodel.create_case(name="Reactive Test Case")
        assert result is True
        QApplication.processEvents()
        assert cases_spy.count() == 1
        assert summary_spy.count() == 1

        cases = viewmodel.load_cases()
        case_id = cases[0].id

        # Update emits case_updated
        update_spy = QSignalSpy(viewmodel.case_updated)
        result = viewmodel.update_case(case_id, name="Updated Name")
        assert result is True
        QApplication.processEvents()
        assert update_spy.count() == 1
        emitted_dto = update_spy.at(0)[0]
        assert emitted_dto.name == "Updated Name"

        # Delete emits cases_changed
        delete_spy = QSignalSpy(viewmodel.cases_changed)
        result = viewmodel.delete_case(case_id)
        assert result is True
        QApplication.processEvents()
        assert delete_spy.count() == 1

    def test_attribute_signal_and_bridge_required(
        self, viewmodel, case_repo, project_state, event_bus, cases_context, qapp
    ):
        """
        E2E: Adding attribute emits signal; no signal without bridge.
        """
        # Create case first
        viewmodel.create_case(name="Attribute Test Case")
        QApplication.processEvents()
        cases = viewmodel.load_cases()
        case_id = cases[0].id

        # Attribute emits case_updated
        spy = QSignalSpy(viewmodel.case_updated)
        result = viewmodel.add_attribute(case_id, "age", "number", 25)
        assert result is True
        QApplication.processEvents()
        assert spy.count() == 1

        # Without bridge, no signal
        vm_no_bridge = CaseManagerViewModel(
            case_repo=case_repo,
            state=project_state,
            event_bus=event_bus,
            cases_ctx=cases_context,
            signal_bridge=None,
        )
        no_bridge_spy = QSignalSpy(vm_no_bridge.cases_changed)
        vm_no_bridge.create_case(name="No Bridge Case")
        QApplication.processEvents()
        assert no_bridge_spy.count() == 0, (
            "Without SignalBridge, no reactive signal should be emitted"
        )
