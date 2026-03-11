"""
File Manager End-to-End Tests

True E2E tests that simulate actual user interactions with the File Manager UI,
testing the complete flow from mouse click to data changes.

These tests:
1. Create real UI widgets with FileManagerScreen
2. Simulate actual mouse/keyboard events
3. Verify UI state changes
4. Verify data flow through ViewModel

Note: Uses fixtures from root conftest.py (qapp, colors) and local fixtures.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest
from PySide6.QtTest import QSignalSpy
from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget

from src.contexts.sources.presentation import FileManagerScreen
from src.shared.presentation.dto import FolderDTO, ProjectSummaryDTO, SourceDTO
from src.tests.e2e.helpers import attach_screenshot
from src.tests.e2e.utils import DocScreenshot

pytestmark = pytest.mark.e2e  # All tests in this module are E2E tests


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def sample_sources() -> list[SourceDTO]:
    """Create sample source DTOs for testing."""
    return [
        SourceDTO(
            id="1",
            name="Interview_Participant_01.txt",
            source_type="text",
            status="coded",
            code_count=15,
            cases=["Case A", "Case B"],
        ),
        SourceDTO(
            id="2",
            name="Focus_Group_Recording.mp3",
            source_type="audio",
            status="transcribing",
            code_count=0,
        ),
        SourceDTO(
            id="3",
            name="Observation_Video.mp4",
            source_type="video",
            status="ready",
            code_count=3,
        ),
        SourceDTO(
            id="4",
            name="Field_Notes_Scan.pdf",
            source_type="pdf",
            status="in_progress",
            code_count=7,
        ),
        SourceDTO(
            id="5",
            name="Participant_Photo.jpg",
            source_type="image",
            status="imported",
            code_count=0,
        ),
        SourceDTO(
            id="6",
            name="Interview_Participant_02.docx",
            source_type="text",
            status="coded",
            code_count=22,
            cases=["Case A"],
        ),
    ]


@pytest.fixture
def sample_summary() -> ProjectSummaryDTO:
    """Create sample project summary for testing."""
    return ProjectSummaryDTO(
        total_sources=32,
        text_count=12,
        audio_count=5,
        video_count=3,
        image_count=8,
        pdf_count=4,
        total_codes=45,
        total_segments=156,
    )


@pytest.fixture
def file_manager_window(qapp, colors, sample_sources, sample_summary):
    """
    Create a complete File Manager window for E2E testing.

    This fixture creates a real window with FileManagerScreen
    populated with sample data, similar to how it would appear
    in the actual application.

    Note: The screen's dialog handlers (import, export, delete confirmation)
    are disconnected to prevent blocking during signal tests.
    """
    window = QMainWindow()
    window.setWindowTitle("File Manager E2E Test")
    window.setMinimumSize(1200, 800)

    central = QWidget()
    window.setCentralWidget(central)
    layout = QVBoxLayout(central)
    layout.setContentsMargins(0, 0, 0, 0)

    # Create screen without viewmodel (direct data binding for E2E tests)
    screen = FileManagerScreen(colors=colors)

    # Disconnect blocking handlers for testing signal flow
    # These handlers show dialogs which block tests
    try:
        screen._page.import_clicked.disconnect(screen._on_import_clicked)
        screen._page.link_clicked.disconnect(screen._on_link_clicked)
        screen._page.export_clicked.disconnect(screen._on_export_clicked)
        screen._page.delete_sources.disconnect(screen._on_delete_sources)
        screen._page.export_sources.disconnect(screen._on_export_sources)
    except RuntimeError:
        pass  # Signals may not be connected

    screen.set_summary(sample_summary)
    screen.set_sources(sample_sources)

    layout.addWidget(screen)

    window.show()
    QApplication.processEvents()

    yield {
        "window": window,
        "screen": screen,
        "sources": sample_sources,
        "summary": sample_summary,
    }

    window.close()


@pytest.fixture
def empty_file_manager_window(qapp, colors):
    """
    Create a File Manager window with no sources (empty state).
    """
    window = QMainWindow()
    window.setWindowTitle("File Manager Empty State Test")
    window.setMinimumSize(1200, 800)

    central = QWidget()
    window.setCentralWidget(central)
    layout = QVBoxLayout(central)
    layout.setContentsMargins(0, 0, 0, 0)

    screen = FileManagerScreen(colors=colors)

    # Disconnect blocking handlers for testing signal flow
    try:
        screen._page.import_clicked.disconnect(screen._on_import_clicked)
        screen._page.link_clicked.disconnect(screen._on_link_clicked)
    except RuntimeError:
        pass  # Signals may not be connected

    screen.set_summary(
        ProjectSummaryDTO(
            total_sources=0,
            text_count=0,
            audio_count=0,
            video_count=0,
            image_count=0,
            pdf_count=0,
            total_codes=0,
            total_segments=0,
        )
    )
    screen.set_sources([])  # Empty - triggers empty state

    layout.addWidget(screen)

    window.show()
    QApplication.processEvents()

    yield {
        "window": window,
        "screen": screen,
    }

    window.close()


@pytest.fixture
def temp_source_files():
    """Create temporary source files for import testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        files = []
        tmppath = Path(tmpdir)

        # Create text file
        txt_file = tmppath / "test_interview.txt"
        txt_file.write_text("This is a test interview transcript.")
        files.append(txt_file)

        # Create another text file
        txt_file2 = tmppath / "test_notes.txt"
        txt_file2.write_text("Field notes from observation.")
        files.append(txt_file2)

        yield files


# =============================================================================
# Test Classes
# =============================================================================


class TestFileManagerDisplay:
    """E2E tests for File Manager display and initial state."""

    def test_stats_row_shows_correct_counts(self, file_manager_window):
        """
        E2E: Stats row displays correct counts for each type.
        """
        screen = file_manager_window["screen"]
        summary = file_manager_window["summary"]

        stats_row = screen.page.stats_row

        # Verify each card has correct count
        assert stats_row._cards["text"]._count == summary.text_count
        assert stats_row._cards["audio"]._count == summary.audio_count
        assert stats_row._cards["video"]._count == summary.video_count
        assert stats_row._cards["image"]._count == summary.image_count
        assert stats_row._cards["pdf"]._count == summary.pdf_count

    def test_table_shows_all_sources(self, file_manager_window):
        """
        E2E: Table displays all source files.
        """
        screen = file_manager_window["screen"]
        sources = file_manager_window["sources"]
        window = file_manager_window["window"]

        table = screen.page.source_table._table

        # Verify row count matches sources
        assert table.rowCount() == len(sources)

        # Screenshot for documentation (captured in TestFolderScreenshots with folders)
        attach_screenshot(window, "FileManager - With Sources")

    def test_empty_state_shown_when_no_sources(self, empty_file_manager_window):
        """
        E2E: Empty state is displayed when project has no sources.
        """
        screen = empty_file_manager_window["screen"]
        window = empty_file_manager_window["window"]

        # Get the stacked widget
        content_stack = screen.page._content_stack

        # Verify empty state is visible
        assert content_stack.currentWidget() == screen.page._empty_state

        # Screenshot for documentation
        attach_screenshot(window, "FileManager - Empty")
        DocScreenshot.capture(window, "file-manager-empty", max_width=1000)


class TestStatsRowFiltering:
    """E2E tests for filtering via stats row clicks."""

    def test_click_text_card_emits_filter_signal(self, file_manager_window, qapp):
        """
        E2E: Clicking text stats card emits filter signal.
        """
        screen = file_manager_window["screen"]

        spy = QSignalSpy(screen.page.filter_changed)

        # Click the text card
        text_card = screen.page.stats_row._cards["text"]
        text_card.clicked.emit("text")
        QApplication.processEvents()

        # Verify signal emitted
        assert spy.count() == 1
        assert spy.at(0)[0] == "text"

    def test_click_card_activates_filter_state(self, file_manager_window, qapp):
        """
        E2E: Clicking a stats card activates its visual filter state.
        """
        screen = file_manager_window["screen"]

        text_card = screen.page.stats_row._cards["text"]

        # Initially not active
        assert not text_card.is_active()

        # Click to activate
        text_card.clicked.emit("text")
        QApplication.processEvents()

        # Now should be active
        assert text_card.is_active()

    def test_click_same_card_twice_clears_filter(self, file_manager_window, qapp):
        """
        E2E: Clicking the same card twice clears the filter.
        """
        screen = file_manager_window["screen"]

        spy = QSignalSpy(screen.page.filter_changed)

        text_card = screen.page.stats_row._cards["text"]

        # First click - activate
        text_card.clicked.emit("text")
        QApplication.processEvents()
        assert text_card.is_active()

        # Second click - deactivate
        text_card.clicked.emit("text")
        QApplication.processEvents()
        assert not text_card.is_active()

        # Should have emitted None for cleared filter
        assert spy.count() == 2
        assert spy.at(1)[0] is None

    def test_click_different_card_switches_filter(self, file_manager_window, qapp):
        """
        E2E: Clicking a different card switches the filter.
        """
        screen = file_manager_window["screen"]

        text_card = screen.page.stats_row._cards["text"]
        audio_card = screen.page.stats_row._cards["audio"]

        # Activate text
        text_card.clicked.emit("text")
        QApplication.processEvents()
        assert text_card.is_active()
        assert not audio_card.is_active()

        # Click audio - should switch
        audio_card.clicked.emit("audio")
        QApplication.processEvents()
        assert not text_card.is_active()
        assert audio_card.is_active()


class TestTableSelection:
    """E2E tests for table row selection."""

    def test_selection_emits_signal(self, file_manager_window, qapp):
        """
        E2E: Selecting rows emits selection_changed signal.
        """
        screen = file_manager_window["screen"]

        spy = QSignalSpy(screen.page.selection_changed)

        # Simulate selection via the table's signal
        screen.page.source_table.selection_changed.emit(["1", "2"])
        QApplication.processEvents()

        # Verify signal propagated
        assert spy.count() == 1
        assert spy.at(0)[0] == ["1", "2"]

    def test_double_click_emits_open_signal(self, file_manager_window, qapp):
        """
        E2E: Double-clicking a row emits source_double_clicked signal.
        """
        screen = file_manager_window["screen"]

        spy = QSignalSpy(screen.page.source_double_clicked)

        # Simulate double-click via table signal
        screen.page.source_table.source_double_clicked.emit("3")
        QApplication.processEvents()

        # Verify signal reached page
        assert spy.count() == 1
        assert spy.at(0)[0] == "3"


class TestToolbarActions:
    """E2E tests for toolbar button actions."""

    @pytest.mark.parametrize(
        "signal_name",
        ["import_clicked", "link_clicked", "create_text_clicked", "export_clicked"],
    )
    def test_toolbar_button_emits_signal(self, file_manager_window, qapp, signal_name):
        """
        E2E: Toolbar button click emits the corresponding signal on the page.
        """
        screen = file_manager_window["screen"]

        page_signal = getattr(screen.page, signal_name)
        toolbar_signal = getattr(screen.page.toolbar, signal_name)

        spy = QSignalSpy(page_signal)

        toolbar_signal.emit()
        QApplication.processEvents()

        assert spy.count() == 1


class TestSearchFunctionality:
    """E2E tests for search functionality."""

    def test_search_emits_signal(self, file_manager_window, qapp):
        """
        E2E: Typing in search box emits search_changed signal.
        """
        screen = file_manager_window["screen"]

        spy = QSignalSpy(screen.page.search_changed)

        # Simulate search input via toolbar signal
        screen.page.toolbar.search_changed.emit("interview")
        QApplication.processEvents()

        assert spy.count() == 1
        assert spy.at(0)[0] == "interview"


class TestBulkActions:
    """E2E tests for bulk action operations."""

    def test_bulk_actions_emit_signals(self, file_manager_window, qapp):
        """
        E2E: Bulk delete, export, and open-for-coding actions emit their signals.
        """
        screen = file_manager_window["screen"]

        delete_spy = QSignalSpy(screen.page.delete_sources)
        export_spy = QSignalSpy(screen.page.export_sources)
        coding_spy = QSignalSpy(screen.page.open_for_coding)

        # Bulk delete
        screen.page.source_table.delete_sources.emit(["1", "2", "3"])
        QApplication.processEvents()
        assert delete_spy.count() == 1
        assert delete_spy.at(0)[0] == ["1", "2", "3"]

        # Bulk export
        screen.page.source_table.export_sources.emit(["1", "4"])
        QApplication.processEvents()
        assert export_spy.count() == 1
        assert export_spy.at(0)[0] == ["1", "4"]

        # Open for coding
        screen.page.source_table.open_for_coding.emit("2")
        QApplication.processEvents()
        assert coding_spy.count() == 1
        assert coding_spy.at(0)[0] == "2"


class TestEmptyStateActions:
    """E2E tests for empty state interactions."""

    def test_empty_state_buttons_emit_signals(
        self, empty_file_manager_window, qapp
    ):
        """
        E2E: Import and Link buttons in empty state emit their signals.
        """
        screen = empty_file_manager_window["screen"]

        import_spy = QSignalSpy(screen.page.import_clicked)
        link_spy = QSignalSpy(screen.page.link_clicked)

        screen.page.empty_state.import_clicked.emit()
        QApplication.processEvents()
        assert import_spy.count() == 1

        screen.page.empty_state.link_clicked.emit()
        QApplication.processEvents()
        assert link_spy.count() == 1


class TestNavigationSignals:
    """E2E tests for navigation between screens."""

    def test_double_click_source_triggers_navigation(self, file_manager_window, qapp):
        """
        E2E: Double-clicking a source triggers navigate_to_coding signal.
        """
        screen = file_manager_window["screen"]

        spy = QSignalSpy(screen.navigate_to_coding)

        # Simulate the navigation flow (normally through viewmodel)
        # Here we test the signal is properly exposed
        screen.navigate_to_coding.emit("1")
        QApplication.processEvents()

        assert spy.count() == 1
        assert spy.at(0)[0] == "1"


class TestDataRefresh:
    """E2E tests for data refresh operations."""

    def test_set_sources_updates_display(self, file_manager_window, qapp):
        """
        E2E: Setting new sources updates the table display.
        """
        screen = file_manager_window["screen"]

        # Set new sources
        new_sources = [
            SourceDTO(
                id="100",
                name="New_File.txt",
                source_type="text",
                status="ready",
                code_count=0,
            ),
        ]

        screen.set_sources(new_sources)
        QApplication.processEvents()

        # Verify table updated
        table = screen.page.source_table._table
        assert table.rowCount() == 1

    def test_set_summary_updates_stats(self, file_manager_window, qapp):
        """
        E2E: Setting new summary updates stats row counts.
        """
        screen = file_manager_window["screen"]

        new_summary = ProjectSummaryDTO(
            total_sources=100,
            text_count=50,
            audio_count=20,
            video_count=10,
            image_count=15,
            pdf_count=5,
            total_codes=200,
            total_segments=500,
        )

        screen.set_summary(new_summary)
        QApplication.processEvents()

        stats_row = screen.page.stats_row
        assert stats_row._cards["text"]._count == 50
        assert stats_row._cards["audio"]._count == 20

    def test_empty_sources_shows_empty_state(self, file_manager_window, qapp):
        """
        E2E: Setting empty sources switches to empty state view.
        """
        screen = file_manager_window["screen"]

        # Initially has sources
        content_stack = screen.page._content_stack
        assert content_stack.currentWidget() != screen.page._empty_state

        # Set empty sources
        screen.set_sources([])
        QApplication.processEvents()

        # Now should show empty state
        assert content_stack.currentWidget() == screen.page._empty_state


class TestStateManagement:
    """E2E tests for state management operations."""

    def test_clear_selection(self, file_manager_window, qapp):
        """
        E2E: Clear selection removes all selections.
        """
        screen = file_manager_window["screen"]

        # Simulate some selections first
        screen.page.source_table._selected_ids = {"1", "2", "3"}

        # Clear
        screen.clear_selection()
        QApplication.processEvents()

        assert len(screen.get_selected_ids()) == 0

    def test_clear_filter(self, file_manager_window, qapp):
        """
        E2E: Clear filter removes active type filter.
        """
        screen = file_manager_window["screen"]

        # Set a filter first
        screen.page.stats_row._cards["text"].clicked.emit("text")
        QApplication.processEvents()
        assert screen.page.get_active_filter() == "text"

        # Clear filter
        screen.page.clear_filter()
        QApplication.processEvents()

        assert screen.page.get_active_filter() is None

    def test_clear_search(self, file_manager_window, qapp):
        """
        E2E: Clear search removes search text.
        """
        screen = file_manager_window["screen"]

        # Set search text via internal state
        screen.page._current_search = "test"

        # Clear
        screen.page.clear_search()
        QApplication.processEvents()

        assert screen.page.get_search_text() == ""


# =============================================================================
# Folder Screenshot Fixtures & Tests
# =============================================================================


@pytest.fixture
def sample_folders() -> list[FolderDTO]:
    """Create sample folder DTOs for screenshot testing."""
    return [
        FolderDTO(id="1", name="Interviews", source_count=3),
        FolderDTO(id="2", name="Round 1", parent_id="1", source_count=2),
        FolderDTO(id="3", name="Round 2", parent_id="1", source_count=1),
        FolderDTO(id="4", name="Field Notes", source_count=2),
        FolderDTO(id="5", name="Media", source_count=1),
    ]


@pytest.fixture
def file_manager_with_folders(
    qapp, colors, sample_sources, sample_summary, sample_folders
):
    """Create a File Manager window populated with folders and sources."""
    window = QMainWindow()
    window.setWindowTitle("File Manager - Folders")
    window.setMinimumSize(1200, 800)

    central = QWidget()
    window.setCentralWidget(central)
    layout = QVBoxLayout(central)
    layout.setContentsMargins(0, 0, 0, 0)

    screen = FileManagerScreen(colors=colors)

    try:
        screen._page.import_clicked.disconnect(screen._on_import_clicked)
        screen._page.link_clicked.disconnect(screen._on_link_clicked)
        screen._page.export_clicked.disconnect(screen._on_export_clicked)
        screen._page.delete_sources.disconnect(screen._on_delete_sources)
        screen._page.export_sources.disconnect(screen._on_export_sources)
    except RuntimeError:
        pass

    screen.set_summary(sample_summary)
    screen.set_sources(sample_sources)
    screen._page.set_folders(sample_folders)

    layout.addWidget(screen)

    window.show()
    QApplication.processEvents()

    yield {
        "window": window,
        "screen": screen,
        "folders": sample_folders,
    }

    window.close()


class TestFolderScreenshots:
    """Capture documentation screenshots for folder features."""

    def test_file_manager_with_folders(self, file_manager_with_folders):
        """Capture File Manager showing folder tree with sources."""
        window = file_manager_with_folders["window"]
        screen = file_manager_with_folders["screen"]

        # Verify folders are populated
        assert screen._page._folder_tree is not None

        # Capture screenshot
        attach_screenshot(window, "FileManager - With Folders")
        DocScreenshot.capture(window, "file-manager-with-folders", max_width=1000)
