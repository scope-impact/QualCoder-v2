"""
Tests for CaseManagerViewModel

Implements QC-034 presentation layer:
- AC #1: Researcher can create cases
- AC #2: Researcher can link sources to cases
- AC #3: Researcher can add case attributes
- AC #4: Researcher can view all data for a case
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from src.contexts.cases.core.entities import AttributeType, Case, CaseAttribute
from src.contexts.shared.core.types import CaseId, SourceId
from src.presentation.dto import CaseDTO, CaseSummaryDTO

# ============================================================
# Fixtures
# ============================================================


@pytest.fixture
def case_manager_viewmodel(case_repo, event_bus):
    """Create a case manager viewmodel for testing."""
    from src.presentation.viewmodels.case_manager_viewmodel import (
        CaseManagerViewModel,
    )

    return CaseManagerViewModel(case_repo=case_repo, event_bus=event_bus)


@pytest.fixture
def sample_case(case_repo) -> Case:
    """Create and save a sample case."""
    case = Case(
        id=CaseId(value=1),
        name="Participant A",
        description="First participant in study",
        memo="Important notes",
        attributes=(),
        source_ids=(),
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    case_repo.save(case)
    return case


@pytest.fixture
def case_with_attributes(case_repo) -> Case:
    """Create and save a case with attributes."""
    case = Case(
        id=CaseId(value=2),
        name="Participant B",
        description="Second participant",
        memo=None,
        attributes=(
            CaseAttribute(name="age", attr_type=AttributeType.NUMBER, value=30),
            CaseAttribute(name="gender", attr_type=AttributeType.TEXT, value="female"),
        ),
        source_ids=(),
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    case_repo.save(case)
    # Save attributes separately
    for attr in case.attributes:
        case_repo.save_attribute(case.id, attr)
    return case


# ============================================================
# Load Cases Tests
# ============================================================


class TestLoadCases:
    """Tests for loading cases."""

    def test_load_cases_returns_empty_list_for_no_cases(
        self,
        case_manager_viewmodel,
    ):
        """Returns empty list when no cases exist."""
        cases = case_manager_viewmodel.load_cases()

        assert cases == []

    def test_load_cases_returns_case_dtos(
        self,
        case_manager_viewmodel,
        sample_case: Case,
    ):
        """Returns CaseDTO objects."""
        cases = case_manager_viewmodel.load_cases()

        assert len(cases) == 1
        assert isinstance(cases[0], CaseDTO)
        assert cases[0].id == "1"
        assert cases[0].name == "Participant A"
        assert cases[0].description == "First participant in study"

    def test_load_cases_includes_attribute_count(
        self,
        case_manager_viewmodel,
        case_with_attributes: Case,
    ):
        """Includes attribute count in DTO."""
        cases = case_manager_viewmodel.load_cases()

        assert len(cases) == 1
        assert len(cases[0].attributes) == 2


# ============================================================
# Get Case Details Tests (AC #4)
# ============================================================


class TestGetCaseDetails:
    """Tests for AC #4: Researcher can view all data for a case."""

    def test_get_case_returns_dto(
        self,
        case_manager_viewmodel,
        sample_case: Case,
    ):
        """Returns CaseDTO for existing case."""
        case = case_manager_viewmodel.get_case(1)

        assert case is not None
        assert isinstance(case, CaseDTO)
        assert case.id == "1"
        assert case.name == "Participant A"

    def test_get_case_returns_none_for_nonexistent(
        self,
        case_manager_viewmodel,
    ):
        """Returns None for non-existent case."""
        case = case_manager_viewmodel.get_case(999)

        assert case is None

    def test_get_case_includes_attributes(
        self,
        case_manager_viewmodel,
        case_with_attributes: Case,
    ):
        """Includes attributes in DTO."""
        case = case_manager_viewmodel.get_case(2)

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
        case_manager_viewmodel,
    ):
        """Returns True when case is created successfully."""
        result = case_manager_viewmodel.create_case(
            name="New Case",
            description="A new case",
        )

        assert result is True

    def test_create_case_adds_to_repository(
        self,
        case_manager_viewmodel,
        case_repo,
    ):
        """Case is added to repository."""
        case_manager_viewmodel.create_case(
            name="New Case",
            description="A new case",
        )

        cases = case_repo.get_all()
        assert len(cases) == 1
        assert cases[0].name == "New Case"

    def test_create_case_with_memo(
        self,
        case_manager_viewmodel,
        case_repo,
    ):
        """Creates case with memo."""
        case_manager_viewmodel.create_case(
            name="New Case",
            description="A new case",
            memo="Important notes",
        )

        cases = case_repo.get_all()
        assert cases[0].memo == "Important notes"

    def test_create_case_returns_false_for_duplicate_name(
        self,
        case_manager_viewmodel,
        sample_case: Case,
    ):
        """Returns False when case name already exists."""
        result = case_manager_viewmodel.create_case(
            name="Participant A",  # Already exists
            description="Duplicate",
        )

        assert result is False


# ============================================================
# Update Case Tests
# ============================================================


class TestUpdateCase:
    """Tests for updating case details."""

    def test_update_case_returns_true_on_success(
        self,
        case_manager_viewmodel,
        sample_case: Case,
    ):
        """Returns True when case is updated successfully."""
        result = case_manager_viewmodel.update_case(
            case_id=1,
            name="Updated Name",
        )

        assert result is True

    def test_update_case_changes_name(
        self,
        case_manager_viewmodel,
        case_repo,
        sample_case: Case,
    ):
        """Updates case name."""
        case_manager_viewmodel.update_case(
            case_id=1,
            name="Updated Name",
        )

        case = case_repo.get_by_id(CaseId(value=1))
        assert case.name == "Updated Name"

    def test_update_case_returns_false_for_nonexistent(
        self,
        case_manager_viewmodel,
    ):
        """Returns False for non-existent case."""
        result = case_manager_viewmodel.update_case(
            case_id=999,
            name="Updated Name",
        )

        assert result is False


# ============================================================
# Delete Case Tests
# ============================================================


class TestDeleteCase:
    """Tests for deleting cases."""

    def test_delete_case_returns_true_on_success(
        self,
        case_manager_viewmodel,
        sample_case: Case,
    ):
        """Returns True when case is deleted successfully."""
        result = case_manager_viewmodel.delete_case(1)

        assert result is True

    def test_delete_case_removes_from_repository(
        self,
        case_manager_viewmodel,
        case_repo,
        sample_case: Case,
    ):
        """Case is removed from repository."""
        case_manager_viewmodel.delete_case(1)

        case = case_repo.get_by_id(CaseId(value=1))
        assert case is None

    def test_delete_case_returns_false_for_nonexistent(
        self,
        case_manager_viewmodel,
    ):
        """Returns False for non-existent case."""
        result = case_manager_viewmodel.delete_case(999)

        assert result is False


# ============================================================
# Link Source Tests (AC #2)
# ============================================================


class TestLinkSource:
    """Tests for AC #2: Researcher can link sources to cases."""

    def test_link_source_returns_true_on_success(
        self,
        case_manager_viewmodel,
        sample_case: Case,
    ):
        """Returns True when source is linked successfully."""
        result = case_manager_viewmodel.link_source(case_id=1, source_id=100)

        assert result is True

    def test_link_source_adds_to_case(
        self,
        case_manager_viewmodel,
        case_repo,
        sample_case: Case,
    ):
        """Source is linked to case."""
        case_manager_viewmodel.link_source(case_id=1, source_id=100)

        case = case_repo.get_by_id(CaseId(value=1))
        assert 100 in case.source_ids

    def test_link_source_returns_false_for_nonexistent_case(
        self,
        case_manager_viewmodel,
    ):
        """Returns False for non-existent case."""
        result = case_manager_viewmodel.link_source(case_id=999, source_id=100)

        assert result is False

    def test_unlink_source_returns_true_on_success(
        self,
        case_manager_viewmodel,
        case_repo,
        sample_case: Case,
    ):
        """Returns True when source is unlinked successfully."""
        # First link the source
        case_repo.link_source(CaseId(value=1), SourceId(value=100))

        result = case_manager_viewmodel.unlink_source(case_id=1, source_id=100)

        assert result is True

    def test_unlink_source_removes_from_case(
        self,
        case_manager_viewmodel,
        case_repo,
        sample_case: Case,
    ):
        """Source is unlinked from case."""
        case_repo.link_source(CaseId(value=1), SourceId(value=100))

        case_manager_viewmodel.unlink_source(case_id=1, source_id=100)

        case = case_repo.get_by_id(CaseId(value=1))
        assert 100 not in case.source_ids


# ============================================================
# Add Attribute Tests (AC #3)
# ============================================================


class TestAddAttribute:
    """Tests for AC #3: Researcher can add case attributes."""

    def test_add_attribute_returns_true_on_success(
        self,
        case_manager_viewmodel,
        sample_case: Case,
    ):
        """Returns True when attribute is added successfully."""
        result = case_manager_viewmodel.add_attribute(
            case_id=1,
            name="age",
            attr_type="number",
            value=25,
        )

        assert result is True

    def test_add_attribute_adds_to_case(
        self,
        case_manager_viewmodel,
        case_repo,
        sample_case: Case,
    ):
        """Attribute is added to case."""
        case_manager_viewmodel.add_attribute(
            case_id=1,
            name="age",
            attr_type="number",
            value=25,
        )

        case = case_repo.get_by_id(CaseId(value=1))
        assert case.get_attribute("age") is not None
        assert case.get_attribute("age").value == 25

    def test_add_attribute_returns_false_for_nonexistent_case(
        self,
        case_manager_viewmodel,
    ):
        """Returns False for non-existent case."""
        result = case_manager_viewmodel.add_attribute(
            case_id=999,
            name="age",
            attr_type="number",
            value=25,
        )

        assert result is False

    def test_update_attribute_value(
        self,
        case_manager_viewmodel,
        case_repo,
        case_with_attributes: Case,
    ):
        """Updates existing attribute value."""
        case_manager_viewmodel.add_attribute(
            case_id=2,
            name="age",
            attr_type="number",
            value=35,  # Update from 30 to 35
        )

        case = case_repo.get_by_id(CaseId(value=2))
        assert case.get_attribute("age").value == 35

    def test_remove_attribute_returns_true_on_success(
        self,
        case_manager_viewmodel,
        case_with_attributes: Case,
    ):
        """Returns True when attribute is removed successfully."""
        result = case_manager_viewmodel.remove_attribute(
            case_id=2,
            name="age",
        )

        assert result is True

    def test_remove_attribute_removes_from_case(
        self,
        case_manager_viewmodel,
        case_repo,
        case_with_attributes: Case,
    ):
        """Attribute is removed from case."""
        case_manager_viewmodel.remove_attribute(
            case_id=2,
            name="age",
        )

        case = case_repo.get_by_id(CaseId(value=2))
        assert case.get_attribute("age") is None


# ============================================================
# Summary Tests
# ============================================================


class TestGetSummary:
    """Tests for getting case summary statistics."""

    def test_get_summary_returns_dto(
        self,
        case_manager_viewmodel,
    ):
        """Returns CaseSummaryDTO."""
        summary = case_manager_viewmodel.get_summary()

        assert isinstance(summary, CaseSummaryDTO)

    def test_get_summary_counts_cases(
        self,
        case_manager_viewmodel,
        sample_case: Case,
        case_with_attributes: Case,
    ):
        """Counts total cases."""
        summary = case_manager_viewmodel.get_summary()

        assert summary.total_cases == 2

    def test_get_summary_counts_unique_attributes(
        self,
        case_manager_viewmodel,
        case_with_attributes: Case,
    ):
        """Counts unique attribute names."""
        summary = case_manager_viewmodel.get_summary()

        assert "age" in summary.unique_attribute_names
        assert "gender" in summary.unique_attribute_names


# ============================================================
# Selection Tests
# ============================================================


class TestCaseSelection:
    """Tests for case selection state."""

    def test_select_case(
        self,
        case_manager_viewmodel,
        sample_case: Case,
    ):
        """Selects a case."""
        case_manager_viewmodel.select_case(1)

        assert case_manager_viewmodel.get_selected_case_id() == 1

    def test_clear_selection(
        self,
        case_manager_viewmodel,
        sample_case: Case,
    ):
        """Clears case selection."""
        case_manager_viewmodel.select_case(1)
        case_manager_viewmodel.clear_selection()

        assert case_manager_viewmodel.get_selected_case_id() is None


# ============================================================
# Search Tests
# ============================================================


class TestSearchCases:
    """Tests for searching cases."""

    def test_search_by_name(
        self,
        case_manager_viewmodel,
        sample_case: Case,
        case_with_attributes: Case,
    ):
        """Searches cases by name."""
        results = case_manager_viewmodel.search_cases("Participant A")

        assert len(results) == 1
        assert results[0].name == "Participant A"

    def test_search_is_case_insensitive(
        self,
        case_manager_viewmodel,
        sample_case: Case,
    ):
        """Search is case-insensitive."""
        results = case_manager_viewmodel.search_cases("participant a")

        assert len(results) == 1

    def test_search_returns_empty_for_no_match(
        self,
        case_manager_viewmodel,
        sample_case: Case,
    ):
        """Returns empty list for no match."""
        results = case_manager_viewmodel.search_cases("NonExistent")

        assert results == []
