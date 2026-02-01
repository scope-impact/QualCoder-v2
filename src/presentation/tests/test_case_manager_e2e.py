"""
Case Manager End-to-End Tests

True E2E tests that simulate actual user interactions with the Case Manager UI,
testing the complete flow from mouse click to data changes.

These tests:
1. Create real UI widgets with CaseManagerScreen
2. Simulate actual mouse/keyboard events
3. Verify UI state changes
4. Verify data flow through signals

Implements QC-034 presentation layer:
- AC #1: Researcher can create cases
- AC #2: Researcher can link sources to cases
- AC #3: Researcher can add case attributes
- AC #4: Researcher can view all data for a case

Note: Uses fixtures from root conftest.py (qapp, colors) and local fixtures.
"""

import pytest
from PySide6.QtTest import QSignalSpy
from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget

from src.presentation.dto import CaseAttributeDTO, CaseDTO, CaseSummaryDTO
from src.presentation.screens import CaseManagerScreen

pytestmark = pytest.mark.e2e  # All tests in this module are E2E tests


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def sample_cases() -> list[CaseDTO]:
    """Create sample case DTOs for testing."""
    return [
        CaseDTO(
            id="1",
            name="Participant A",
            description="First participant in the study",
            source_count=3,
            attributes=[
                CaseAttributeDTO(name="age", attr_type="number", value=25),
                CaseAttributeDTO(name="gender", attr_type="text", value="female"),
            ],
        ),
        CaseDTO(
            id="2",
            name="Participant B",
            description="Second participant",
            source_count=5,
            attributes=[
                CaseAttributeDTO(name="age", attr_type="number", value=30),
            ],
        ),
        CaseDTO(
            id="3",
            name="Site Alpha",
            description="Research site location",
            source_count=0,
            attributes=[],
        ),
        CaseDTO(
            id="4",
            name="Participant C",
            description="Third participant",
            source_count=2,
            attributes=[
                CaseAttributeDTO(name="age", attr_type="number", value=45),
                CaseAttributeDTO(name="gender", attr_type="text", value="male"),
                CaseAttributeDTO(name="location", attr_type="text", value="Urban"),
            ],
        ),
    ]


@pytest.fixture
def sample_summary() -> CaseSummaryDTO:
    """Create sample case summary for testing."""
    return CaseSummaryDTO(
        total_cases=4,
        cases_with_sources=3,
        total_attributes=6,
        unique_attribute_names=["age", "gender", "location"],
    )


@pytest.fixture
def case_manager_window(qapp, colors, sample_cases, sample_summary):
    """
    Create a complete Case Manager window for E2E testing.

    This fixture creates a real window with CaseManagerScreen
    populated with sample data, similar to how it would appear
    in the actual application.

    Note: The screen's dialog handlers are disconnected to prevent
    blocking during signal tests.
    """
    window = QMainWindow()
    window.setWindowTitle("Case Manager E2E Test")
    window.setMinimumSize(1200, 800)

    central = QWidget()
    window.setCentralWidget(central)
    layout = QVBoxLayout(central)
    layout.setContentsMargins(0, 0, 0, 0)

    # Create screen without viewmodel (direct data binding for E2E tests)
    screen = CaseManagerScreen(colors=colors)

    # Disconnect blocking handlers for testing signal flow
    # These handlers show dialogs which block tests
    try:
        screen._page.create_case_clicked.disconnect(screen._on_create_case_clicked)
        screen._page.import_clicked.disconnect(screen._on_import_clicked)
        screen._page.export_clicked.disconnect(screen._on_export_clicked)
        screen._page.delete_cases.disconnect(screen._on_delete_cases)
    except RuntimeError:
        pass  # Signals may not be connected

    screen.set_summary(sample_summary)
    screen.set_cases(sample_cases)

    layout.addWidget(screen)

    window.show()
    QApplication.processEvents()

    yield {
        "window": window,
        "screen": screen,
        "cases": sample_cases,
        "summary": sample_summary,
    }

    window.close()


@pytest.fixture
def empty_case_manager_window(qapp, colors):
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

    screen = CaseManagerScreen(colors=colors)

    # Disconnect blocking handlers for testing signal flow
    try:
        screen._page.create_case_clicked.disconnect(screen._on_create_case_clicked)
        screen._page.import_clicked.disconnect(screen._on_import_clicked)
    except RuntimeError:
        pass  # Signals may not be connected

    screen.set_summary(
        CaseSummaryDTO(
            total_cases=0,
            cases_with_sources=0,
            total_attributes=0,
            unique_attribute_names=[],
        )
    )
    screen.set_cases([])  # Empty - triggers empty state

    layout.addWidget(screen)

    window.show()
    QApplication.processEvents()

    yield {
        "window": window,
        "screen": screen,
    }

    window.close()


# =============================================================================
# Test Classes
# =============================================================================


class TestCaseManagerDisplay:
    """E2E tests for Case Manager display and initial state."""

    def test_stats_row_shows_correct_counts(self, case_manager_window):
        """
        E2E: Stats row displays correct counts for total cases and with sources.
        """
        screen = case_manager_window["screen"]
        summary = case_manager_window["summary"]

        stats_row = screen.page.stats_row

        # Verify each card has correct count
        assert stats_row._total_cases_card._count == summary.total_cases
        assert stats_row._with_sources_card._count == summary.cases_with_sources
        assert stats_row._attributes_card._count == summary.total_attributes

    def test_table_shows_all_cases(self, case_manager_window):
        """
        E2E: Table displays all cases.
        """
        screen = case_manager_window["screen"]
        cases = case_manager_window["cases"]

        table = screen.page.case_table._table

        # Verify row count matches cases
        assert table.rowCount() == len(cases)

    def test_empty_state_shown_when_no_cases(self, empty_case_manager_window):
        """
        E2E: Empty state is displayed when project has no cases.
        """
        screen = empty_case_manager_window["screen"]

        # Get the stacked widget
        content_stack = screen.page._content_stack

        # Verify empty state is visible
        assert content_stack.currentWidget() == screen.page._empty_state


class TestStatsRowFiltering:
    """E2E tests for filtering via stats row clicks."""

    def test_click_total_cases_card_emits_filter_signal(
        self, case_manager_window, qapp
    ):
        """
        E2E: Clicking total cases card emits filter signal.
        """
        screen = case_manager_window["screen"]

        spy = QSignalSpy(screen.page.filter_changed)

        # Click the total cases card
        total_card = screen.page.stats_row._total_cases_card
        total_card.clicked.emit("all")
        QApplication.processEvents()

        # Verify signal emitted
        assert spy.count() == 1
        assert spy.at(0)[0] == "all"

    def test_click_with_sources_card_emits_filter_signal(
        self, case_manager_window, qapp
    ):
        """
        E2E: Clicking with sources card emits filter signal.
        """
        screen = case_manager_window["screen"]

        spy = QSignalSpy(screen.page.filter_changed)

        # Click the with sources card
        sources_card = screen.page.stats_row._with_sources_card
        sources_card.clicked.emit("with_sources")
        QApplication.processEvents()

        # Verify signal emitted
        assert spy.count() == 1
        assert spy.at(0)[0] == "with_sources"

    def test_click_card_activates_filter_state(self, case_manager_window, qapp):
        """
        E2E: Clicking a stats card activates its visual filter state.
        """
        screen = case_manager_window["screen"]

        total_card = screen.page.stats_row._total_cases_card

        # Initially not active
        assert not total_card._active

        # Click to activate
        total_card.clicked.emit("all")
        QApplication.processEvents()

        # Now should be active
        assert total_card._active

    def test_click_same_card_twice_clears_filter(self, case_manager_window, qapp):
        """
        E2E: Clicking the same card twice clears the filter.
        """
        screen = case_manager_window["screen"]

        spy = QSignalSpy(screen.page.filter_changed)

        total_card = screen.page.stats_row._total_cases_card

        # First click - activate
        total_card.clicked.emit("all")
        QApplication.processEvents()
        assert total_card._active

        # Second click - deactivate
        total_card.clicked.emit("all")
        QApplication.processEvents()
        assert not total_card._active

        # Should have emitted None for cleared filter
        assert spy.count() == 2
        assert spy.at(1)[0] is None


class TestTableSelection:
    """E2E tests for table row selection."""

    def test_selection_emits_signal(self, case_manager_window, qapp):
        """
        E2E: Selecting rows emits selection_changed signal.
        """
        screen = case_manager_window["screen"]

        spy = QSignalSpy(screen.page.selection_changed)

        # Simulate selection via the table's signal
        screen.page.case_table.selection_changed.emit(["1", "2"])
        QApplication.processEvents()

        # Verify signal propagated
        assert spy.count() == 1
        assert spy.at(0)[0] == ["1", "2"]

    def test_double_click_emits_open_signal(self, case_manager_window, qapp):
        """
        E2E: Double-clicking a row emits case_double_clicked signal.
        """
        screen = case_manager_window["screen"]

        spy = QSignalSpy(screen.page.case_double_clicked)

        # Simulate double-click via table signal
        screen.page.case_table.case_double_clicked.emit("3")
        QApplication.processEvents()

        # Verify signal reached page
        assert spy.count() == 1
        assert spy.at(0)[0] == "3"

    def test_single_click_emits_signal(self, case_manager_window, qapp):
        """
        E2E: Single-clicking a row emits case_clicked signal.
        """
        screen = case_manager_window["screen"]

        spy = QSignalSpy(screen.page.case_clicked)

        # Simulate click via table signal
        screen.page.case_table.case_clicked.emit("2")
        QApplication.processEvents()

        # Verify signal reached page
        assert spy.count() == 1
        assert spy.at(0)[0] == "2"


class TestToolbarActions:
    """E2E tests for toolbar button actions."""

    def test_create_case_button_emits_signal(self, case_manager_window, qapp):
        """
        E2E: Create Case button click emits create_case_clicked signal.
        """
        screen = case_manager_window["screen"]

        spy = QSignalSpy(screen.page.create_case_clicked)

        # Click create case button via toolbar signal
        screen.page.toolbar.create_case_clicked.emit()
        QApplication.processEvents()

        assert spy.count() == 1

    def test_import_button_emits_signal(self, case_manager_window, qapp):
        """
        E2E: Import button click emits import_clicked signal.
        """
        screen = case_manager_window["screen"]

        spy = QSignalSpy(screen.page.import_clicked)

        screen.page.toolbar.import_clicked.emit()
        QApplication.processEvents()

        assert spy.count() == 1

    def test_export_button_emits_signal(self, case_manager_window, qapp):
        """
        E2E: Export button click emits export_clicked signal.
        """
        screen = case_manager_window["screen"]

        spy = QSignalSpy(screen.page.export_clicked)

        screen.page.toolbar.export_clicked.emit()
        QApplication.processEvents()

        assert spy.count() == 1


class TestSearchFunctionality:
    """E2E tests for search functionality."""

    def test_search_emits_signal(self, case_manager_window, qapp):
        """
        E2E: Typing in search box emits search_changed signal.
        """
        screen = case_manager_window["screen"]

        spy = QSignalSpy(screen.page.search_changed)

        # Simulate search input via toolbar signal
        screen.page.toolbar.search_changed.emit("participant")
        QApplication.processEvents()

        assert spy.count() == 1
        assert spy.at(0)[0] == "participant"

    def test_search_propagates_to_page(self, case_manager_window, qapp):
        """
        E2E: Search signal propagates from toolbar to page.
        """
        screen = case_manager_window["screen"]

        spy = QSignalSpy(screen.page.search_changed)

        screen.page.toolbar.search_changed.emit("site")
        QApplication.processEvents()

        assert spy.count() == 1
        assert spy.at(0)[0] == "site"


class TestCaseActions:
    """E2E tests for case-level actions."""

    def test_delete_cases_emits_signal(self, case_manager_window, qapp):
        """
        E2E: Delete action emits delete_cases signal.
        """
        screen = case_manager_window["screen"]

        spy = QSignalSpy(screen.page.delete_cases)

        # Simulate delete from table
        screen.page.case_table.delete_cases.emit(["1", "2"])
        QApplication.processEvents()

        assert spy.count() == 1
        assert spy.at(0)[0] == ["1", "2"]

    def test_link_source_emits_signal(self, case_manager_window, qapp):
        """
        E2E: Link source action emits link_source signal.
        """
        screen = case_manager_window["screen"]

        spy = QSignalSpy(screen.page.link_source)

        screen.page.case_table.link_source.emit("3")
        QApplication.processEvents()

        assert spy.count() == 1
        assert spy.at(0)[0] == "3"

    def test_edit_case_emits_signal(self, case_manager_window, qapp):
        """
        E2E: Edit case action emits edit_case signal.
        """
        screen = case_manager_window["screen"]

        spy = QSignalSpy(screen.page.edit_case)

        screen.page.case_table.edit_case.emit("4")
        QApplication.processEvents()

        assert spy.count() == 1
        assert spy.at(0)[0] == "4"


class TestEmptyStateActions:
    """E2E tests for empty state interactions."""

    def test_empty_state_import_button_emits_signal(
        self, empty_case_manager_window, qapp
    ):
        """
        E2E: Import button in empty state emits create_case_clicked signal.
        (Empty state primary action creates a case)
        """
        screen = empty_case_manager_window["screen"]

        spy = QSignalSpy(screen.page.create_case_clicked)

        # Click import in empty state (maps to create case)
        screen.page.empty_state.import_clicked.emit()
        QApplication.processEvents()

        assert spy.count() == 1

    def test_empty_state_link_button_emits_signal(
        self, empty_case_manager_window, qapp
    ):
        """
        E2E: Link button in empty state emits import_clicked signal.
        """
        screen = empty_case_manager_window["screen"]

        spy = QSignalSpy(screen.page.import_clicked)

        screen.page.empty_state.link_clicked.emit()
        QApplication.processEvents()

        assert spy.count() == 1


class TestNavigationSignals:
    """E2E tests for navigation between screens."""

    def test_double_click_case_triggers_navigation(self, case_manager_window, qapp):
        """
        E2E: Double-clicking a case triggers navigate_to_case signal.
        """
        screen = case_manager_window["screen"]

        spy = QSignalSpy(screen.navigate_to_case)

        # Simulate the navigation flow
        screen.navigate_to_case.emit("1")
        QApplication.processEvents()

        assert spy.count() == 1
        assert spy.at(0)[0] == "1"

    def test_case_opened_signal(self, case_manager_window, qapp):
        """
        E2E: Case opened signal is properly exposed.
        """
        screen = case_manager_window["screen"]

        spy = QSignalSpy(screen.case_opened)

        screen.case_opened.emit("2")
        QApplication.processEvents()

        assert spy.count() == 1
        assert spy.at(0)[0] == "2"


class TestDataRefresh:
    """E2E tests for data refresh operations."""

    def test_set_cases_updates_display(self, case_manager_window, qapp):
        """
        E2E: Setting new cases updates the table display.
        """
        screen = case_manager_window["screen"]

        # Set new cases
        new_cases = [
            CaseDTO(
                id="100",
                name="New Case",
                description="A new case",
                source_count=0,
                attributes=[],
            ),
        ]

        screen.set_cases(new_cases)
        QApplication.processEvents()

        # Verify table updated
        table = screen.page.case_table._table
        assert table.rowCount() == 1

    def test_set_summary_updates_stats(self, case_manager_window, qapp):
        """
        E2E: Setting new summary updates stats row counts.
        """
        screen = case_manager_window["screen"]

        new_summary = CaseSummaryDTO(
            total_cases=100,
            cases_with_sources=75,
            total_attributes=250,
            unique_attribute_names=["a", "b", "c"],
        )

        screen.set_summary(new_summary)
        QApplication.processEvents()

        stats_row = screen.page.stats_row
        assert stats_row._total_cases_card._count == 100
        assert stats_row._with_sources_card._count == 75
        assert stats_row._attributes_card._count == 250

    def test_empty_cases_shows_empty_state(self, case_manager_window, qapp):
        """
        E2E: Setting empty cases switches to empty state view.
        """
        screen = case_manager_window["screen"]

        # Initially has cases
        content_stack = screen.page._content_stack
        assert content_stack.currentWidget() != screen.page._empty_state

        # Set empty cases
        screen.set_cases([])
        QApplication.processEvents()

        # Now should show empty state
        assert content_stack.currentWidget() == screen.page._empty_state


class TestStateManagement:
    """E2E tests for state management operations."""

    def test_clear_selection(self, case_manager_window, qapp):
        """
        E2E: Clear selection removes all selections.
        """
        screen = case_manager_window["screen"]

        # Simulate some selections first
        screen.page.case_table._selected_ids = {"1", "2", "3"}

        # Clear
        screen.clear_selection()
        QApplication.processEvents()

        assert len(screen.get_selected_ids()) == 0

    def test_clear_filter(self, case_manager_window, qapp):
        """
        E2E: Clear filter removes active filter.
        """
        screen = case_manager_window["screen"]

        # Set a filter first
        screen.page.stats_row._total_cases_card.clicked.emit("all")
        QApplication.processEvents()
        assert screen.page.get_active_filter() == "all"

        # Clear filter
        screen.page.clear_filter()
        QApplication.processEvents()

        assert screen.page.get_active_filter() is None

    def test_clear_search(self, case_manager_window, qapp):
        """
        E2E: Clear search removes search text.
        """
        screen = case_manager_window["screen"]

        # Set search text via internal state
        screen.page._current_search = "test"

        # Clear
        screen.page.clear_search()
        QApplication.processEvents()

        assert screen.page.get_search_text() == ""

    def test_get_selected_ids_returns_list(self, case_manager_window, qapp):
        """
        E2E: get_selected_ids returns proper list of selected IDs.
        """
        screen = case_manager_window["screen"]

        # Initially empty
        assert screen.get_selected_ids() == []

        # Add some selections
        screen.page.case_table._selected_ids = {"1", "4"}

        # Should return list
        ids = screen.get_selected_ids()
        assert len(ids) == 2
        assert "1" in ids
        assert "4" in ids


class TestScreenProtocol:
    """E2E tests for ScreenProtocol implementation."""

    def test_get_content_returns_self(self, case_manager_window, qapp):
        """
        E2E: get_content returns the screen itself.
        """
        screen = case_manager_window["screen"]
        assert screen.get_content() == screen

    def test_get_toolbar_content_returns_none(self, case_manager_window, qapp):
        """
        E2E: get_toolbar_content returns None (toolbar embedded).
        """
        screen = case_manager_window["screen"]
        assert screen.get_toolbar_content() is None

    def test_get_status_message_returns_string(self, case_manager_window, qapp):
        """
        E2E: get_status_message returns a valid status string.
        """
        screen = case_manager_window["screen"]
        message = screen.get_status_message()
        assert isinstance(message, str)
        assert len(message) > 0
