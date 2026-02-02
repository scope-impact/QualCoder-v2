"""
Tests for CaseManagerViewModel

Unit tests using pure mocks (no database dependency).
Tests cover all ViewModel logic including failure scenarios.

Implements QC-034 presentation layer:
- AC #1: Researcher can create cases
- AC #2: Researcher can link sources to cases
- AC #3: Researcher can add case attributes
- AC #4: Researcher can view all data for a case
"""

from __future__ import annotations

import pytest

from src.contexts.cases.core.entities import AttributeType, CaseAttribute
from src.presentation.dto import CaseDTO, CaseSummaryDTO
from src.presentation.viewmodels.case_manager_viewmodel import CaseManagerViewModel
from src.presentation.viewmodels.tests.mocks import MockCaseManagerProvider, MockConfig

# ============================================================
# Fixtures
# ============================================================


@pytest.fixture
def mock_provider() -> MockCaseManagerProvider:
    """Create a fresh mock provider for each test."""
    return MockCaseManagerProvider()


@pytest.fixture
def viewmodel(mock_provider: MockCaseManagerProvider) -> CaseManagerViewModel:
    """Create a viewmodel with mock provider."""
    return CaseManagerViewModel(provider=mock_provider)


@pytest.fixture
def seeded_provider(mock_provider: MockCaseManagerProvider) -> MockCaseManagerProvider:
    """Create a mock provider with seeded test data."""
    mock_provider.seed_case(
        name="Participant A",
        description="First participant in study",
        memo="Important notes",
    )
    mock_provider.seed_case(
        name="Participant B",
        description="Second participant",
        attributes=(
            CaseAttribute(name="age", attr_type=AttributeType.NUMBER, value=30),
            CaseAttribute(name="gender", attr_type=AttributeType.TEXT, value="female"),
        ),
    )
    return mock_provider


@pytest.fixture
def seeded_viewmodel(
    seeded_provider: MockCaseManagerProvider,
) -> CaseManagerViewModel:
    """Create a viewmodel with seeded test data."""
    return CaseManagerViewModel(provider=seeded_provider)


# ============================================================
# Load Cases Tests
# ============================================================


class TestLoadCases:
    """Tests for loading cases."""

    def test_load_cases_returns_empty_list_for_no_cases(
        self,
        viewmodel: CaseManagerViewModel,
    ):
        """Returns empty list when no cases exist."""
        cases = viewmodel.load_cases()

        assert cases == []

    def test_load_cases_returns_case_dtos(
        self,
        seeded_viewmodel: CaseManagerViewModel,
    ):
        """Returns CaseDTO objects."""
        cases = seeded_viewmodel.load_cases()

        assert len(cases) == 2
        assert all(isinstance(c, CaseDTO) for c in cases)
        assert cases[0].name == "Participant A"
        assert cases[0].description == "First participant in study"

    def test_load_cases_includes_attribute_count(
        self,
        seeded_viewmodel: CaseManagerViewModel,
    ):
        """Includes attribute count in DTO."""
        cases = seeded_viewmodel.load_cases()

        # Find Participant B
        participant_b = next((c for c in cases if c.name == "Participant B"), None)
        assert participant_b is not None
        assert len(participant_b.attributes) == 2


# ============================================================
# Get Case Details Tests (AC #4)
# ============================================================


class TestGetCaseDetails:
    """Tests for AC #4: Researcher can view all data for a case."""

    def test_get_case_returns_dto(
        self,
        seeded_viewmodel: CaseManagerViewModel,
    ):
        """Returns CaseDTO for existing case."""
        case = seeded_viewmodel.get_case(1)

        assert case is not None
        assert isinstance(case, CaseDTO)
        assert case.id == "1"
        assert case.name == "Participant A"

    def test_get_case_returns_none_for_nonexistent(
        self,
        viewmodel: CaseManagerViewModel,
    ):
        """Returns None for non-existent case."""
        case = viewmodel.get_case(999)

        assert case is None

    def test_get_case_includes_attributes(
        self,
        seeded_viewmodel: CaseManagerViewModel,
    ):
        """Includes attributes in DTO."""
        case = seeded_viewmodel.get_case(2)

        assert case is not None
        assert len(case.attributes) == 2
        age_attr = next((a for a in case.attributes if a.name == "age"), None)
        assert age_attr is not None
        assert age_attr.attr_type == "number"
        assert age_attr.value == 30


# ============================================================
# Create Case Tests (AC #1)
# ============================================================


class TestCreateCase:
    """Tests for AC #1: Researcher can create cases."""

    def test_create_case_returns_true_on_success(
        self,
        viewmodel: CaseManagerViewModel,
    ):
        """Returns True when case is created successfully."""
        result = viewmodel.create_case(
            name="New Case",
            description="A new case",
        )

        assert result is True

    def test_create_case_adds_to_provider(
        self,
        viewmodel: CaseManagerViewModel,
        mock_provider: MockCaseManagerProvider,
    ):
        """Case is added to provider."""
        viewmodel.create_case(
            name="New Case",
            description="A new case",
        )

        cases = mock_provider.get_all_cases()
        assert len(cases) == 1
        assert cases[0].name == "New Case"

    def test_create_case_with_memo(
        self,
        viewmodel: CaseManagerViewModel,
        mock_provider: MockCaseManagerProvider,
    ):
        """Creates case with memo."""
        viewmodel.create_case(
            name="New Case",
            description="A new case",
            memo="Important notes",
        )

        cases = mock_provider.get_all_cases()
        assert cases[0].memo == "Important notes"

    def test_create_case_returns_false_for_duplicate_name(
        self,
        seeded_viewmodel: CaseManagerViewModel,
    ):
        """Returns False when case name already exists."""
        result = seeded_viewmodel.create_case(
            name="Participant A",  # Already exists
            description="Duplicate",
        )

        assert result is False


# ============================================================
# Create Case Failure Scenarios
# ============================================================


class TestCreateCaseFailures:
    """Tests for create case failure scenarios."""

    def test_create_case_returns_false_when_provider_fails(self):
        """Returns False when provider returns failure."""
        config = MockConfig(fail_create=True, create_error="Database error")
        provider = MockCaseManagerProvider(config=config)
        viewmodel = CaseManagerViewModel(provider=provider)

        result = viewmodel.create_case(name="Test Case")

        assert result is False

    def test_create_case_tracks_call_even_on_failure(self):
        """Tracks the call even when it fails."""
        config = MockConfig(fail_create=True)
        provider = MockCaseManagerProvider(config=config)
        viewmodel = CaseManagerViewModel(provider=provider)

        viewmodel.create_case(name="Test Case")

        assert (
            "create_case",
            {"name": "Test Case", "description": None, "memo": None},
        ) in provider.calls


# ============================================================
# Update Case Tests
# ============================================================


class TestUpdateCase:
    """Tests for updating case details."""

    def test_update_case_returns_true_on_success(
        self,
        seeded_viewmodel: CaseManagerViewModel,
    ):
        """Returns True when case is updated successfully."""
        result = seeded_viewmodel.update_case(
            case_id=1,
            name="Updated Name",
        )

        assert result is True

    def test_update_case_changes_name(
        self,
        seeded_viewmodel: CaseManagerViewModel,
        seeded_provider: MockCaseManagerProvider,
    ):
        """Updates case name."""
        seeded_viewmodel.update_case(
            case_id=1,
            name="Updated Name",
        )

        case = seeded_provider.get_case(1)
        assert case.name == "Updated Name"

    def test_update_case_returns_false_for_nonexistent(
        self,
        viewmodel: CaseManagerViewModel,
    ):
        """Returns False for non-existent case."""
        result = viewmodel.update_case(
            case_id=999,
            name="Updated Name",
        )

        assert result is False


# ============================================================
# Update Case Failure Scenarios
# ============================================================


class TestUpdateCaseFailures:
    """Tests for update case failure scenarios."""

    def test_update_case_returns_false_when_provider_fails(self):
        """Returns False when provider returns failure."""
        config = MockConfig(fail_update=True, update_error="Database error")
        provider = MockCaseManagerProvider(config=config)
        provider.seed_case(name="Test Case")
        viewmodel = CaseManagerViewModel(provider=provider)

        result = viewmodel.update_case(case_id=1, name="New Name")

        assert result is False


# ============================================================
# Delete Case Tests
# ============================================================


class TestDeleteCase:
    """Tests for deleting cases."""

    def test_delete_case_returns_true_on_success(
        self,
        seeded_viewmodel: CaseManagerViewModel,
    ):
        """Returns True when case is deleted successfully."""
        result = seeded_viewmodel.delete_case(1)

        assert result is True

    def test_delete_case_removes_from_provider(
        self,
        seeded_viewmodel: CaseManagerViewModel,
        seeded_provider: MockCaseManagerProvider,
    ):
        """Case is removed from provider."""
        seeded_viewmodel.delete_case(1)

        case = seeded_provider.get_case(1)
        assert case is None

    def test_delete_case_returns_false_for_nonexistent(
        self,
        viewmodel: CaseManagerViewModel,
    ):
        """Returns False for non-existent case."""
        result = viewmodel.delete_case(999)

        assert result is False

    def test_delete_case_clears_selection_if_selected(
        self,
        seeded_viewmodel: CaseManagerViewModel,
    ):
        """Clears selection when deleted case was selected."""
        seeded_viewmodel.select_case(1)
        seeded_viewmodel.delete_case(1)

        assert seeded_viewmodel.get_selected_case_id() is None


# ============================================================
# Delete Case Failure Scenarios
# ============================================================


class TestDeleteCaseFailures:
    """Tests for delete case failure scenarios."""

    def test_delete_case_returns_false_when_provider_fails(self):
        """Returns False when provider returns failure."""
        config = MockConfig(fail_delete=True, delete_error="Database error")
        provider = MockCaseManagerProvider(config=config)
        provider.seed_case(name="Test Case")
        viewmodel = CaseManagerViewModel(provider=provider)

        result = viewmodel.delete_case(1)

        assert result is False


# ============================================================
# Link Source Tests (AC #2)
# ============================================================


class TestLinkSource:
    """Tests for AC #2: Researcher can link sources to cases."""

    def test_link_source_returns_true_on_success(
        self,
        seeded_viewmodel: CaseManagerViewModel,
    ):
        """Returns True when source is linked successfully."""
        result = seeded_viewmodel.link_source(case_id=1, source_id=100)

        assert result is True

    def test_link_source_adds_to_case(
        self,
        seeded_viewmodel: CaseManagerViewModel,
        seeded_provider: MockCaseManagerProvider,
    ):
        """Source is linked to case."""
        seeded_viewmodel.link_source(case_id=1, source_id=100)

        case = seeded_provider.get_case(1)
        assert 100 in case.source_ids

    def test_link_source_returns_false_for_nonexistent_case(
        self,
        viewmodel: CaseManagerViewModel,
    ):
        """Returns False for non-existent case."""
        result = viewmodel.link_source(case_id=999, source_id=100)

        assert result is False

    def test_unlink_source_returns_true_on_success(
        self,
        seeded_viewmodel: CaseManagerViewModel,
        seeded_provider: MockCaseManagerProvider,
    ):
        """Returns True when source is unlinked successfully."""
        # First link the source
        seeded_provider.link_source(1, 100)

        result = seeded_viewmodel.unlink_source(case_id=1, source_id=100)

        assert result is True

    def test_unlink_source_removes_from_case(
        self,
        seeded_viewmodel: CaseManagerViewModel,
        seeded_provider: MockCaseManagerProvider,
    ):
        """Source is unlinked from case."""
        seeded_provider.link_source(1, 100)
        seeded_viewmodel.unlink_source(case_id=1, source_id=100)

        case = seeded_provider.get_case(1)
        assert 100 not in case.source_ids


# ============================================================
# Link Source Failure Scenarios
# ============================================================


class TestLinkSourceFailures:
    """Tests for link source failure scenarios."""

    def test_link_source_returns_false_when_provider_fails(self):
        """Returns False when provider returns failure."""
        config = MockConfig(fail_link=True, link_error="Database error")
        provider = MockCaseManagerProvider(config=config)
        provider.seed_case(name="Test Case")
        viewmodel = CaseManagerViewModel(provider=provider)

        result = viewmodel.link_source(case_id=1, source_id=100)

        assert result is False


# ============================================================
# Add Attribute Tests (AC #3)
# ============================================================


class TestAddAttribute:
    """Tests for AC #3: Researcher can add case attributes."""

    def test_add_attribute_returns_true_on_success(
        self,
        seeded_viewmodel: CaseManagerViewModel,
    ):
        """Returns True when attribute is added successfully."""
        result = seeded_viewmodel.add_attribute(
            case_id=1,
            name="occupation",
            attr_type="text",
            value="Engineer",
        )

        assert result is True

    def test_add_attribute_adds_to_case(
        self,
        seeded_viewmodel: CaseManagerViewModel,
        seeded_provider: MockCaseManagerProvider,
    ):
        """Attribute is added to case."""
        seeded_viewmodel.add_attribute(
            case_id=1,
            name="age",
            attr_type="number",
            value=25,
        )

        case = seeded_provider.get_case(1)
        assert case.get_attribute("age") is not None
        assert case.get_attribute("age").value == 25

    def test_add_attribute_returns_false_for_nonexistent_case(
        self,
        viewmodel: CaseManagerViewModel,
    ):
        """Returns False for non-existent case."""
        result = viewmodel.add_attribute(
            case_id=999,
            name="age",
            attr_type="number",
            value=25,
        )

        assert result is False

    def test_update_attribute_value(
        self,
        seeded_viewmodel: CaseManagerViewModel,
        seeded_provider: MockCaseManagerProvider,
    ):
        """Updates existing attribute value."""
        seeded_viewmodel.add_attribute(
            case_id=2,
            name="age",
            attr_type="number",
            value=35,  # Update from 30 to 35
        )

        case = seeded_provider.get_case(2)
        assert case.get_attribute("age").value == 35

    def test_remove_attribute_returns_true_on_success(
        self,
        seeded_viewmodel: CaseManagerViewModel,
    ):
        """Returns True when attribute is removed successfully."""
        result = seeded_viewmodel.remove_attribute(
            case_id=2,
            name="age",
        )

        assert result is True

    def test_remove_attribute_removes_from_case(
        self,
        seeded_viewmodel: CaseManagerViewModel,
        seeded_provider: MockCaseManagerProvider,
    ):
        """Attribute is removed from case."""
        seeded_viewmodel.remove_attribute(
            case_id=2,
            name="age",
        )

        case = seeded_provider.get_case(2)
        assert case.get_attribute("age") is None


# ============================================================
# Add Attribute Failure Scenarios
# ============================================================


class TestAddAttributeFailures:
    """Tests for add attribute failure scenarios."""

    def test_add_attribute_returns_false_when_provider_fails(self):
        """Returns False when provider returns failure."""
        config = MockConfig(fail_add_attribute=True, attribute_error="Database error")
        provider = MockCaseManagerProvider(config=config)
        provider.seed_case(name="Test Case")
        viewmodel = CaseManagerViewModel(provider=provider)

        result = viewmodel.add_attribute(
            case_id=1,
            name="age",
            attr_type="number",
            value=25,
        )

        assert result is False


# ============================================================
# Summary Tests
# ============================================================


class TestGetSummary:
    """Tests for getting case summary statistics."""

    def test_get_summary_returns_dto(
        self,
        viewmodel: CaseManagerViewModel,
    ):
        """Returns CaseSummaryDTO."""
        summary = viewmodel.get_summary()

        assert isinstance(summary, CaseSummaryDTO)

    def test_get_summary_counts_cases(
        self,
        seeded_viewmodel: CaseManagerViewModel,
    ):
        """Counts total cases."""
        summary = seeded_viewmodel.get_summary()

        assert summary.total_cases == 2

    def test_get_summary_counts_unique_attributes(
        self,
        seeded_viewmodel: CaseManagerViewModel,
    ):
        """Counts unique attribute names."""
        summary = seeded_viewmodel.get_summary()

        assert "age" in summary.unique_attribute_names
        assert "gender" in summary.unique_attribute_names


# ============================================================
# Selection Tests
# ============================================================


class TestCaseSelection:
    """Tests for case selection state."""

    def test_select_case(
        self,
        seeded_viewmodel: CaseManagerViewModel,
    ):
        """Selects a case."""
        seeded_viewmodel.select_case(1)

        assert seeded_viewmodel.get_selected_case_id() == 1

    def test_clear_selection(
        self,
        seeded_viewmodel: CaseManagerViewModel,
    ):
        """Clears case selection."""
        seeded_viewmodel.select_case(1)
        seeded_viewmodel.clear_selection()

        assert seeded_viewmodel.get_selected_case_id() is None


# ============================================================
# Search Tests
# ============================================================


class TestSearchCases:
    """Tests for searching cases."""

    def test_search_by_name(
        self,
        seeded_viewmodel: CaseManagerViewModel,
    ):
        """Searches cases by name."""
        results = seeded_viewmodel.search_cases("Participant A")

        assert len(results) == 1
        assert results[0].name == "Participant A"

    def test_search_is_case_insensitive(
        self,
        seeded_viewmodel: CaseManagerViewModel,
    ):
        """Search is case-insensitive."""
        results = seeded_viewmodel.search_cases("participant a")

        assert len(results) == 1

    def test_search_returns_empty_for_no_match(
        self,
        seeded_viewmodel: CaseManagerViewModel,
    ):
        """Returns empty list for no match."""
        results = seeded_viewmodel.search_cases("NonExistent")

        assert results == []


# ============================================================
# Call Tracking Tests (for verifying interactions)
# ============================================================


class TestCallTracking:
    """Tests for verifying provider method calls."""

    def test_load_cases_tracks_call(
        self,
        viewmodel: CaseManagerViewModel,
        mock_provider: MockCaseManagerProvider,
    ):
        """load_cases tracks the call to provider."""
        viewmodel.load_cases()

        assert ("get_all_cases", {}) in mock_provider.calls

    def test_create_case_tracks_call_with_args(
        self,
        viewmodel: CaseManagerViewModel,
        mock_provider: MockCaseManagerProvider,
    ):
        """create_case tracks the call with arguments."""
        viewmodel.create_case(name="Test", description="Desc", memo="Memo")

        assert (
            "create_case",
            {"name": "Test", "description": "Desc", "memo": "Memo"},
        ) in mock_provider.calls
