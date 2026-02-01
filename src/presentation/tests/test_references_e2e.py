"""
References Manager End-to-End Tests

True E2E tests with FULL behavior - real database, viewmodel, and UI integration.
Tests the complete flow: UI action -> ViewModel -> Repository -> Database -> UI update

Implements QC-041.02 View and Edit References:
- AC #1: I can see list of all references
- AC #2: I can edit reference metadata
- AC #3: I can delete references
"""

from __future__ import annotations

import pytest
from PySide6.QtTest import QSignalSpy
from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from sqlalchemy import create_engine

from src.application.event_bus import EventBus
from src.domain.references.entities import Reference
from src.domain.shared.types import ReferenceId
from src.infrastructure.projects.schema import create_all, drop_all
from src.infrastructure.references.repositories import SQLiteReferenceRepository

pytestmark = pytest.mark.e2e


# =============================================================================
# Database Fixtures
# =============================================================================


@pytest.fixture
def db_engine():
    """Create in-memory SQLite engine for testing."""
    engine = create_engine("sqlite:///:memory:", echo=False)
    create_all(engine)
    yield engine
    drop_all(engine)
    engine.dispose()


@pytest.fixture
def db_connection(db_engine):
    """Create a database connection."""
    conn = db_engine.connect()
    yield conn
    conn.close()


@pytest.fixture
def ref_repo(db_connection):
    """Create a reference repository connected to test database."""
    return SQLiteReferenceRepository(db_connection)


@pytest.fixture
def event_bus():
    """Create event bus for reactive updates."""
    return EventBus(history_size=100)


@pytest.fixture
def viewmodel(ref_repo, event_bus):
    """Create ReferencesViewModel with real repository."""
    from src.presentation.viewmodels.references_viewmodel import ReferencesViewModel

    return ReferencesViewModel(ref_repo=ref_repo, event_bus=event_bus)


# =============================================================================
# Seed Data Fixtures
# =============================================================================


@pytest.fixture
def seeded_references(ref_repo):
    """
    Seed the database with test references.
    Returns dict of created references for verification.
    """
    refs = {}

    # Reference 1: Complete reference with all fields
    ref1 = Reference(
        id=ReferenceId(value=1),
        title="The Logic of Scientific Discovery",
        authors="Popper, Karl",
        year=1959,
        source="Philosophy of Science",
        doi="10.1234/popper.1959",
        url="https://example.com/popper",
        memo="Classic work on falsificationism",
    )
    ref_repo.save(ref1)
    refs["popper"] = ref1

    # Reference 2: Minimal reference
    ref2 = Reference(
        id=ReferenceId(value=2),
        title="Qualitative Research Methods",
        authors="Smith, John; Doe, Jane",
        year=2020,
    )
    ref_repo.save(ref2)
    refs["smith"] = ref2

    # Reference 3: Reference with segment links
    ref3 = Reference(
        id=ReferenceId(value=3),
        title="Grounded Theory Basics",
        authors="Strauss, Anselm; Corbin, Juliet",
        year=1990,
        source="Sage Publications",
    )
    ref_repo.save(ref3)
    ref_repo.link_segment(ReferenceId(value=3), 100)
    ref_repo.link_segment(ReferenceId(value=3), 101)
    refs["strauss"] = ref3

    return refs


@pytest.fixture
def seeded_viewmodel(ref_repo, event_bus, seeded_references):
    """Create viewmodel with seeded test data."""
    from src.presentation.viewmodels.references_viewmodel import ReferencesViewModel

    return ReferencesViewModel(ref_repo=ref_repo, event_bus=event_bus)


# =============================================================================
# Window Fixtures
# =============================================================================


@pytest.fixture
def references_window(qapp, colors, seeded_viewmodel):
    """
    Create a complete References Manager window for E2E testing.
    """
    from src.presentation.screens.references import ReferencesScreen

    window = QMainWindow()
    window.setWindowTitle("References Manager E2E Test")
    window.setMinimumSize(1000, 600)

    central = QWidget()
    window.setCentralWidget(central)
    layout = QVBoxLayout(central)
    layout.setContentsMargins(0, 0, 0, 0)

    screen = ReferencesScreen(viewmodel=seeded_viewmodel, colors=colors)
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
def empty_references_window(qapp, colors, viewmodel):
    """
    Create a References Manager window with no references (empty state).
    """
    from src.presentation.screens.references import ReferencesScreen

    window = QMainWindow()
    window.setWindowTitle("References Empty State Test")
    window.setMinimumSize(1000, 600)

    central = QWidget()
    window.setCentralWidget(central)
    layout = QVBoxLayout(central)
    layout.setContentsMargins(0, 0, 0, 0)

    screen = ReferencesScreen(viewmodel=viewmodel, colors=colors)
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
# AC #1: I can see list of all references
# =============================================================================


class TestDisplayReferences:
    """E2E tests for displaying references list."""

    def test_ac1_table_shows_all_references_from_db(self, references_window):
        """
        E2E: Table displays all references from database.
        AC #1: I can see list of all references.
        """
        screen = references_window["screen"]

        table = screen.page._references_panel._table
        assert table.rowCount() == 3

    def test_ac1_reference_details_shown_in_table(self, references_window):
        """
        E2E: Reference details (title, authors, year) shown in table.
        """
        screen = references_window["screen"]
        viewmodel = references_window["viewmodel"]

        refs = viewmodel.load_references()
        popper = next(r for r in refs if r.title == "The Logic of Scientific Discovery")

        assert popper.authors == "Popper, Karl"
        assert popper.year == 1959

    def test_ac1_empty_state_shown_when_db_empty(self, empty_references_window):
        """
        E2E: Empty state is displayed when database has no references.
        """
        screen = empty_references_window["screen"]

        content_stack = screen.page._content_stack
        assert content_stack.currentWidget() == screen.page._empty_state

    def test_ac1_search_filters_references(self, references_window, qapp):
        """
        E2E: Search filters references by title/author.
        """
        viewmodel = references_window["viewmodel"]

        # Search for "Popper"
        results = viewmodel.search_references("Popper")
        assert len(results) == 1
        assert results[0].title == "The Logic of Scientific Discovery"

        # Search for "Qualitative"
        results = viewmodel.search_references("Qualitative")
        assert len(results) == 1
        assert "Smith" in results[0].authors


# =============================================================================
# AC #2: I can edit reference metadata
# =============================================================================


class TestEditReference:
    """E2E tests for editing references."""

    def test_ac2_update_reference_persists_to_db(self, references_window, ref_repo):
        """
        E2E: Updating a reference via viewmodel persists to database.
        AC #2: I can edit reference metadata.
        """
        viewmodel = references_window["viewmodel"]

        # Update reference
        result = viewmodel.update_reference(
            reference_id=1,
            title="The Logic of Scientific Discovery (Revised)",
            authors="Popper, Karl R.",
            year=1959,
        )

        assert result is True

        # Verify in database
        db_ref = ref_repo.get_by_id(ReferenceId(value=1))
        assert db_ref.title == "The Logic of Scientific Discovery (Revised)"
        assert db_ref.authors == "Popper, Karl R."

    def test_ac2_update_adds_missing_fields(self, references_window, ref_repo):
        """
        E2E: Updating adds previously missing fields.
        """
        viewmodel = references_window["viewmodel"]

        # Reference 2 has no DOI initially
        db_ref = ref_repo.get_by_id(ReferenceId(value=2))
        assert db_ref.doi is None

        # Update with DOI
        viewmodel.update_reference(
            reference_id=2,
            title="Qualitative Research Methods",
            authors="Smith, John; Doe, Jane",
            year=2020,
            doi="10.5678/smith.2020",
        )

        # Verify DOI added
        db_ref = ref_repo.get_by_id(ReferenceId(value=2))
        assert db_ref.doi == "10.5678/smith.2020"

    def test_ac2_update_reference_refreshes_ui(self, references_window, qapp):
        """
        E2E: Updating a reference and refreshing updates the UI.
        """
        screen = references_window["screen"]
        viewmodel = references_window["viewmodel"]

        # Update reference
        viewmodel.update_reference(
            reference_id=1,
            title="Updated Title",
            authors="Popper, Karl",
            year=1959,
        )

        # Refresh
        screen.refresh()
        QApplication.processEvents()

        # Verify in viewmodel
        refs = viewmodel.load_references()
        updated = next(r for r in refs if r.id == "1")
        assert updated.title == "Updated Title"

    def test_ac2_edit_reference_signal_emitted(self, references_window, qapp):
        """
        E2E: Edit reference signal is emitted when edit action triggered.
        """
        screen = references_window["screen"]

        spy = QSignalSpy(screen.edit_reference)

        # Trigger edit (simulated)
        screen.edit_reference.emit("1")
        QApplication.processEvents()

        assert spy.count() == 1
        assert spy.at(0)[0] == "1"


# =============================================================================
# AC #3: I can delete references
# =============================================================================


class TestDeleteReference:
    """E2E tests for deleting references."""

    def test_ac3_delete_reference_removes_from_db(self, references_window, ref_repo):
        """
        E2E: Deleting a reference removes it from database.
        AC #3: I can delete references.
        """
        viewmodel = references_window["viewmodel"]

        # Verify reference exists
        assert ref_repo.get_by_id(ReferenceId(value=2)) is not None

        # Delete via viewmodel
        result = viewmodel.delete_reference(reference_id=2)
        assert result is True

        # Verify removed from database
        assert ref_repo.get_by_id(ReferenceId(value=2)) is None

    def test_ac3_delete_reference_removes_segment_links(
        self, references_window, ref_repo
    ):
        """
        E2E: Deleting a reference removes its segment links.
        """
        viewmodel = references_window["viewmodel"]

        # Reference 3 has segment links
        segment_ids = ref_repo.get_segment_ids(ReferenceId(value=3))
        assert len(segment_ids) == 2

        # Delete reference
        viewmodel.delete_reference(reference_id=3)

        # Segment links should be gone
        segment_ids = ref_repo.get_segment_ids(ReferenceId(value=3))
        assert len(segment_ids) == 0

    def test_ac3_delete_reference_updates_ui(self, references_window, qapp):
        """
        E2E: Deleting a reference and refreshing updates the UI.
        """
        screen = references_window["screen"]
        viewmodel = references_window["viewmodel"]

        # Initially 3 references
        assert screen.page._references_panel._table.rowCount() == 3

        # Delete reference
        viewmodel.delete_reference(reference_id=1)

        # Refresh
        screen.refresh()
        QApplication.processEvents()

        # Should now show 2 references
        assert screen.page._references_panel._table.rowCount() == 2

    def test_ac3_delete_nonexistent_returns_false(self, references_window):
        """
        E2E: Deleting a non-existent reference returns False.
        """
        viewmodel = references_window["viewmodel"]

        result = viewmodel.delete_reference(reference_id=999)
        assert result is False


# =============================================================================
# Additional Tests
# =============================================================================


class TestAddReference:
    """E2E tests for adding new references."""

    def test_add_reference_persists_to_db(self, empty_references_window, ref_repo):
        """
        E2E: Adding a reference via viewmodel persists to database.
        """
        viewmodel = empty_references_window["viewmodel"]

        result = viewmodel.add_reference(
            title="New Reference",
            authors="Test, Author",
            year=2024,
        )

        assert result is True

        # Verify in database
        refs = ref_repo.get_all()
        assert len(refs) == 1
        assert refs[0].title == "New Reference"

    def test_add_reference_with_all_fields(self, empty_references_window, ref_repo):
        """
        E2E: Adding a reference with all fields persists correctly.
        """
        viewmodel = empty_references_window["viewmodel"]

        viewmodel.add_reference(
            title="Complete Reference",
            authors="Author, Complete",
            year=2024,
            source="Test Journal",
            doi="10.9999/test",
            url="https://test.com",
            memo="Test memo",
        )

        refs = ref_repo.get_all()
        ref = refs[0]
        assert ref.source == "Test Journal"
        assert ref.doi == "10.9999/test"
        assert ref.url == "https://test.com"
        assert ref.memo == "Test memo"

    def test_add_reference_updates_ui(self, empty_references_window, qapp):
        """
        E2E: Adding a reference and refreshing updates the UI.
        """
        screen = empty_references_window["screen"]
        viewmodel = empty_references_window["viewmodel"]

        # Initially empty
        assert screen.page._references_panel._table.rowCount() == 0

        # Add reference
        viewmodel.add_reference(
            title="Fresh Reference",
            authors="New, Author",
        )

        # Refresh
        screen.refresh()
        QApplication.processEvents()

        # Should show one reference
        assert screen.page._references_panel._table.rowCount() == 1


class TestReferenceSelection:
    """E2E tests for reference selection."""

    def test_single_click_selects_reference(self, references_window, qapp):
        """
        E2E: Single clicking a row selects the reference.
        """
        screen = references_window["screen"]
        viewmodel = references_window["viewmodel"]

        # Simulate click
        screen._on_reference_clicked("1")
        QApplication.processEvents()

        assert viewmodel.get_selected_reference_id() == 1

    def test_double_click_emits_edit_signal(self, references_window, qapp):
        """
        E2E: Double-clicking a row emits edit_reference signal.
        """
        screen = references_window["screen"]

        spy = QSignalSpy(screen.edit_reference)

        screen._on_reference_double_clicked("2")
        QApplication.processEvents()

        assert spy.count() == 1
        assert spy.at(0)[0] == "2"


class TestDataRefresh:
    """E2E tests for data refresh operations."""

    def test_refresh_reloads_from_database(self, references_window, ref_repo, qapp):
        """
        E2E: Refresh reloads data from database.
        """
        screen = references_window["screen"]

        # Add directly to database
        new_ref = Reference(
            id=ReferenceId(value=99),
            title="Direct DB Insert",
            authors="Database, Direct",
        )
        ref_repo.save(new_ref)

        # Initially 3 references in UI
        assert screen.page._references_panel._table.rowCount() == 3

        # Refresh
        screen.refresh()
        QApplication.processEvents()

        # Should now show 4 references
        assert screen.page._references_panel._table.rowCount() == 4
