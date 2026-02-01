"""
Tests for Case Manager Screen

TDD tests for CaseManagerScreen that wraps CaseManagerPage
and integrates with CaseManagerViewModel.

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
# CaseManagerScreen Tests
# =============================================================================


class TestCaseManagerScreen:
    """Tests for the CaseManagerScreen."""

    def test_creates_with_defaults(self, qapp, colors):
        """Test screen creates with default settings."""
        from src.presentation.screens.case_manager import CaseManagerScreen

        screen = CaseManagerScreen(colors=colors)

        assert screen is not None
        assert screen._page is not None

    def test_creates_without_viewmodel(self, qapp, colors):
        """Test screen creates without viewmodel."""
        from src.presentation.screens.case_manager import CaseManagerScreen

        screen = CaseManagerScreen(colors=colors)

        assert screen._viewmodel is None

    def test_set_cases_directly(self, qapp, colors):
        """Test setting cases directly (without viewmodel)."""
        from src.presentation.screens.case_manager import CaseManagerScreen

        screen = CaseManagerScreen(colors=colors)
        cases = make_sample_cases()

        screen.set_cases(cases)

        # Should pass through to page
        assert screen.page is not None

    def test_set_summary_directly(self, qapp, colors):
        """Test setting summary directly (without viewmodel)."""
        from src.presentation.screens.case_manager import CaseManagerScreen

        screen = CaseManagerScreen(colors=colors)
        summary = make_sample_summary()

        screen.set_summary(summary)

        # Should pass through to page
        assert screen.page is not None

    def test_case_opened_signal(self, qapp, colors):
        """Test case opened signal."""
        from src.presentation.screens.case_manager import CaseManagerScreen

        screen = CaseManagerScreen(colors=colors)
        spy = QSignalSpy(screen.case_opened)

        screen.case_opened.emit("1")

        assert spy.count() == 1
        assert spy.at(0)[0] == "1"

    def test_navigate_to_case_signal(self, qapp, colors):
        """Test navigate to case signal."""
        from src.presentation.screens.case_manager import CaseManagerScreen

        screen = CaseManagerScreen(colors=colors)
        spy = QSignalSpy(screen.navigate_to_case)

        screen.navigate_to_case.emit("2")

        assert spy.count() == 1
        assert spy.at(0)[0] == "2"

    def test_cases_deleted_signal(self, qapp, colors):
        """Test cases deleted signal."""
        from src.presentation.screens.case_manager import CaseManagerScreen

        screen = CaseManagerScreen(colors=colors)
        spy = QSignalSpy(screen.cases_deleted)

        screen.cases_deleted.emit(["1", "2"])

        assert spy.count() == 1
        assert spy.at(0)[0] == ["1", "2"]

    def test_case_created_signal(self, qapp, colors):
        """Test case created signal."""
        from src.presentation.screens.case_manager import CaseManagerScreen

        screen = CaseManagerScreen(colors=colors)
        spy = QSignalSpy(screen.case_created)

        screen.case_created.emit("3")

        assert spy.count() == 1
        assert spy.at(0)[0] == "3"

    def test_get_selected_ids(self, qapp, colors):
        """Test getting selected IDs."""
        from src.presentation.screens.case_manager import CaseManagerScreen

        screen = CaseManagerScreen(colors=colors)

        # Initially empty
        assert screen.get_selected_ids() == []

    def test_clear_selection(self, qapp, colors):
        """Test clearing selection."""
        from src.presentation.screens.case_manager import CaseManagerScreen

        screen = CaseManagerScreen(colors=colors)

        # Should not raise
        screen.clear_selection()

        assert screen.get_selected_ids() == []

    def test_page_property(self, qapp, colors):
        """Test page property returns the page."""
        from src.presentation.screens.case_manager import CaseManagerScreen

        screen = CaseManagerScreen(colors=colors)

        assert screen.page is not None

    def test_get_content(self, qapp, colors):
        """Test ScreenProtocol get_content."""
        from src.presentation.screens.case_manager import CaseManagerScreen

        screen = CaseManagerScreen(colors=colors)

        assert screen.get_content() == screen

    def test_get_toolbar_content(self, qapp, colors):
        """Test ScreenProtocol get_toolbar_content."""
        from src.presentation.screens.case_manager import CaseManagerScreen

        screen = CaseManagerScreen(colors=colors)

        # Toolbar is embedded in page
        assert screen.get_toolbar_content() is None

    def test_get_status_message(self, qapp, colors):
        """Test ScreenProtocol get_status_message."""
        from src.presentation.screens.case_manager import CaseManagerScreen

        screen = CaseManagerScreen(colors=colors)

        message = screen.get_status_message()

        assert isinstance(message, str)
        assert "Ready" in message or "cases" in message.lower()
