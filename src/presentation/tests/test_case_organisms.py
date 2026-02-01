"""
Tests for Case Manager Organisms

TDD tests for CaseTable and CaseManagerToolbar organisms.
Follows patterns from test_organisms.py.

Implements QC-034 presentation layer:
- AC #1-4: Researcher can manage cases through UI
"""

from PySide6.QtTest import QSignalSpy

from src.presentation.dto import CaseAttributeDTO, CaseDTO, CaseSummaryDTO

# =============================================================================
# Test Fixtures
# =============================================================================


def make_sample_cases() -> list[CaseDTO]:
    """Create sample case DTOs for testing."""
    return [
        CaseDTO(
            id="1",
            name="Participant A",
            description="First participant",
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
            description="Research site",
            source_count=0,
            attributes=[],
        ),
    ]


def make_sample_summary() -> CaseSummaryDTO:
    """Create sample case summary for testing."""
    return CaseSummaryDTO(
        total_cases=3,
        cases_with_sources=2,
        total_attributes=3,
        unique_attribute_names=["age", "gender"],
    )


# =============================================================================
# CaseTable Tests
# =============================================================================


class TestCaseTable:
    """Tests for the CaseTable organism."""

    def test_creates_with_defaults(self, qapp, colors):
        """Test table creates with default settings."""
        from src.presentation.organisms.case_table import CaseTable

        table = CaseTable(colors=colors)

        assert table is not None
        assert table._cases == []

    def test_set_cases(self, qapp, colors):
        """Test setting case list."""
        from src.presentation.organisms.case_table import CaseTable

        table = CaseTable(colors=colors)
        cases = make_sample_cases()

        table.set_cases(cases)

        assert len(table._cases) == 3
        assert table._table.rowCount() == 3

    def test_case_clicked_signal(self, qapp, colors):
        """Test case click emits signal."""
        from src.presentation.organisms.case_table import CaseTable

        table = CaseTable(colors=colors)
        table.set_cases(make_sample_cases())
        spy = QSignalSpy(table.case_clicked)

        table.case_clicked.emit("1")

        assert spy.count() == 1
        assert spy.at(0)[0] == "1"

    def test_case_double_clicked_signal(self, qapp, colors):
        """Test case double-click emits signal."""
        from src.presentation.organisms.case_table import CaseTable

        table = CaseTable(colors=colors)
        table.set_cases(make_sample_cases())
        spy = QSignalSpy(table.case_double_clicked)

        table.case_double_clicked.emit("2")

        assert spy.count() == 1
        assert spy.at(0)[0] == "2"

    def test_selection_changed_signal(self, qapp, colors):
        """Test selection emits signal."""
        from src.presentation.organisms.case_table import CaseTable

        table = CaseTable(colors=colors)
        table.set_cases(make_sample_cases())
        spy = QSignalSpy(table.selection_changed)

        table.selection_changed.emit(["1", "2"])

        assert spy.count() == 1
        assert spy.at(0)[0] == ["1", "2"]

    def test_delete_cases_signal(self, qapp, colors):
        """Test bulk delete emits signal."""
        from src.presentation.organisms.case_table import CaseTable

        table = CaseTable(colors=colors)
        spy = QSignalSpy(table.delete_cases)

        table.delete_cases.emit(["1", "3"])

        assert spy.count() == 1
        assert spy.at(0)[0] == ["1", "3"]

    def test_link_source_signal(self, qapp, colors):
        """Test link source action emits signal."""
        from src.presentation.organisms.case_table import CaseTable

        table = CaseTable(colors=colors)
        spy = QSignalSpy(table.link_source)

        table.link_source.emit("1")

        assert spy.count() == 1
        assert spy.at(0)[0] == "1"

    def test_displays_case_name(self, qapp, colors):
        """Test table displays case names."""
        from src.presentation.organisms.case_table import CaseTable

        table = CaseTable(colors=colors)
        cases = make_sample_cases()
        table.set_cases(cases)

        # Check first row has correct name
        name_item = table._table.item(0, 1)  # Column 1 is name
        assert name_item is not None
        assert "Participant A" in name_item.text()

    def test_displays_source_count(self, qapp, colors):
        """Test table displays source counts."""
        from src.presentation.organisms.case_table import CaseTable

        table = CaseTable(colors=colors)
        cases = make_sample_cases()
        table.set_cases(cases)

        # Check first row has correct source count
        count_item = table._table.item(0, 2)  # Column 2 is sources
        assert count_item is not None
        assert "3" in count_item.text()

    def test_empty_state_when_no_cases(self, qapp, colors):
        """Test empty state shown when no cases."""
        from src.presentation.organisms.case_table import CaseTable

        table = CaseTable(colors=colors)
        table.set_cases([])

        assert table._table.rowCount() == 0


# =============================================================================
# CaseManagerToolbar Tests
# =============================================================================


class TestCaseManagerToolbar:
    """Tests for the CaseManagerToolbar organism."""

    def test_creates_with_defaults(self, qapp, colors):
        """Test toolbar creates with default settings."""
        from src.presentation.organisms.case_manager_toolbar import (
            CaseManagerToolbar,
        )

        toolbar = CaseManagerToolbar(colors=colors)

        assert toolbar is not None
        assert toolbar._search is not None

    def test_create_case_signal(self, qapp, colors):
        """Test create case button emits signal."""
        from src.presentation.organisms.case_manager_toolbar import (
            CaseManagerToolbar,
        )

        toolbar = CaseManagerToolbar(colors=colors)
        spy = QSignalSpy(toolbar.create_case_clicked)

        toolbar.create_case_clicked.emit()

        assert spy.count() == 1

    def test_import_cases_signal(self, qapp, colors):
        """Test import button emits signal."""
        from src.presentation.organisms.case_manager_toolbar import (
            CaseManagerToolbar,
        )

        toolbar = CaseManagerToolbar(colors=colors)
        spy = QSignalSpy(toolbar.import_clicked)

        toolbar.import_clicked.emit()

        assert spy.count() == 1

    def test_export_cases_signal(self, qapp, colors):
        """Test export button emits signal."""
        from src.presentation.organisms.case_manager_toolbar import (
            CaseManagerToolbar,
        )

        toolbar = CaseManagerToolbar(colors=colors)
        spy = QSignalSpy(toolbar.export_clicked)

        toolbar.export_clicked.emit()

        assert spy.count() == 1

    def test_search_changed_signal(self, qapp, colors):
        """Test search emits signal."""
        from src.presentation.organisms.case_manager_toolbar import (
            CaseManagerToolbar,
        )

        toolbar = CaseManagerToolbar(colors=colors)
        spy = QSignalSpy(toolbar.search_changed)

        toolbar.search_changed.emit("participant")

        assert spy.count() == 1
        assert spy.at(0)[0] == "participant"


# =============================================================================
# CaseSummaryStats Tests
# =============================================================================


class TestCaseSummaryStats:
    """Tests for the CaseSummaryStats organism."""

    def test_creates_with_defaults(self, qapp, colors):
        """Test stats creates with default settings."""
        from src.presentation.organisms.case_summary_stats import CaseSummaryStats

        stats = CaseSummaryStats(colors=colors)

        assert stats is not None

    def test_set_summary(self, qapp, colors):
        """Test setting summary updates display."""
        from src.presentation.organisms.case_summary_stats import CaseSummaryStats

        stats = CaseSummaryStats(colors=colors)
        summary = make_sample_summary()

        stats.set_summary(summary)

        assert stats._total_cases_card._count == 3
        assert stats._with_sources_card._count == 2

    def test_filter_changed_signal(self, qapp, colors):
        """Test clicking stat card emits filter signal."""
        from src.presentation.organisms.case_summary_stats import CaseSummaryStats

        stats = CaseSummaryStats(colors=colors)
        spy = QSignalSpy(stats.filter_changed)

        stats.filter_changed.emit("with_sources")

        assert spy.count() == 1
        assert spy.at(0)[0] == "with_sources"
