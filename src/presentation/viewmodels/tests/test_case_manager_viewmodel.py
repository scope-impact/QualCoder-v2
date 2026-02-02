"""
Tests for CaseManagerViewModel

Unit tests using in-memory SQLite (per user preference).
Tests cover all ViewModel logic including failure scenarios.

Implements QC-034 presentation layer:
- AC #1: Researcher can create cases
- AC #2: Researcher can link sources to cases
- AC #3: Researcher can add case attributes
- AC #4: Researcher can view all data for a case
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

import pytest
from sqlalchemy import create_engine

from src.application.event_bus import EventBus
from src.application.state import ProjectState
from src.contexts.cases.core.entities import AttributeType, Case, CaseAttribute
from src.contexts.cases.infra.case_repository import SQLiteCaseRepository
from src.contexts.projects.infra.schema import create_all_contexts, drop_all_contexts
from src.contexts.shared.core.types import CaseId, SourceId
from src.presentation.dto import CaseDTO, CaseSummaryDTO
from src.presentation.viewmodels.case_manager_viewmodel import CaseManagerViewModel

# ============================================================
# Mock CasesContext (minimal for testing)
# ============================================================


@dataclass
class MockCasesContext:
    """Mock CasesContext wrapping real repository for tests."""

    case_repo: SQLiteCaseRepository


# ============================================================
# Fixtures - In-memory SQLite per user preference
# ============================================================


@pytest.fixture
def engine():
    """Create an in-memory SQLite engine."""
    engine = create_engine("sqlite:///:memory:")
    create_all_contexts(engine)
    yield engine
    drop_all_contexts(engine)


@pytest.fixture
def connection(engine):
    """Create a database connection."""
    with engine.connect() as conn:
        yield conn


@pytest.fixture
def case_repo(connection) -> SQLiteCaseRepository:
    """Create a case repository."""
    return SQLiteCaseRepository(connection)


@pytest.fixture
def state() -> ProjectState:
    """Create project state with mock project."""
    ps = ProjectState()
    # Set a mock project so use cases don't fail
    ps.project = type("Project", (), {"name": "Test Project"})()
    return ps


@pytest.fixture
def event_bus() -> EventBus:
    """Create an event bus."""
    return EventBus()


@pytest.fixture
def cases_ctx(case_repo) -> MockCasesContext:
    """Create cases context wrapping the repo."""
    return MockCasesContext(case_repo=case_repo)


@pytest.fixture
def viewmodel(
    case_repo: SQLiteCaseRepository,
    state: ProjectState,
    event_bus: EventBus,
    cases_ctx: MockCasesContext,
) -> CaseManagerViewModel:
    """Create a viewmodel with real in-memory infrastructure."""
    return CaseManagerViewModel(
        case_repo=case_repo,
        state=state,
        event_bus=event_bus,
        cases_ctx=cases_ctx,
    )


@pytest.fixture
def seeded_repo(case_repo: SQLiteCaseRepository) -> SQLiteCaseRepository:
    """Seed the repo with test data."""
    # Seed Participant A
    case_a = Case(
        id=CaseId(value=1),
        name="Participant A",
        description="First participant in study",
        memo="Important notes",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    case_repo.save(case_a)

    # Seed Participant B with attributes
    case_b = Case(
        id=CaseId(value=2),
        name="Participant B",
        description="Second participant",
        attributes=(
            CaseAttribute(name="age", attr_type=AttributeType.NUMBER, value=30),
            CaseAttribute(name="gender", attr_type=AttributeType.TEXT, value="female"),
        ),
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    case_repo.save(case_b)

    return case_repo


@pytest.fixture
def seeded_state(
    seeded_repo: SQLiteCaseRepository, state: ProjectState
) -> ProjectState:
    """Create state synced with seeded repo."""
    state.cases = seeded_repo.get_all()
    return state


@pytest.fixture
def seeded_viewmodel(
    seeded_repo: SQLiteCaseRepository,
    seeded_state: ProjectState,
    event_bus: EventBus,
) -> CaseManagerViewModel:
    """Create a viewmodel with seeded test data."""
    cases_ctx = MockCasesContext(case_repo=seeded_repo)
    return CaseManagerViewModel(
        case_repo=seeded_repo,
        state=seeded_state,
        event_bus=event_bus,
        cases_ctx=cases_ctx,
    )


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

    def test_create_case_adds_to_repo(
        self,
        viewmodel: CaseManagerViewModel,
        case_repo: SQLiteCaseRepository,
    ):
        """Case is added to repository."""
        viewmodel.create_case(
            name="New Case",
            description="A new case",
        )

        cases = case_repo.get_all()
        assert len(cases) == 1
        assert cases[0].name == "New Case"

    def test_create_case_with_memo(
        self,
        viewmodel: CaseManagerViewModel,
        case_repo: SQLiteCaseRepository,
    ):
        """Creates case with memo."""
        viewmodel.create_case(
            name="New Case",
            description="A new case",
            memo="Important notes",
        )

        cases = case_repo.get_all()
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

    def test_create_case_returns_false_for_empty_name(
        self,
        viewmodel: CaseManagerViewModel,
    ):
        """Returns False when case name is empty."""
        result = viewmodel.create_case(name="")
        assert result is False

    def test_create_case_returns_false_for_whitespace_name(
        self,
        viewmodel: CaseManagerViewModel,
    ):
        """Returns False when case name is whitespace-only."""
        result = viewmodel.create_case(name="   ")
        assert result is False


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
        seeded_repo: SQLiteCaseRepository,
    ):
        """Updates case name."""
        seeded_viewmodel.update_case(
            case_id=1,
            name="Updated Name",
        )

        case = seeded_repo.get_by_id(CaseId(value=1))
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

    def test_update_case_returns_false_for_empty_name(
        self,
        seeded_viewmodel: CaseManagerViewModel,
    ):
        """Returns False when case name is empty."""
        result = seeded_viewmodel.update_case(case_id=1, name="")
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

    def test_delete_case_removes_from_repo(
        self,
        seeded_viewmodel: CaseManagerViewModel,
        seeded_repo: SQLiteCaseRepository,
    ):
        """Case is removed from repository."""
        seeded_viewmodel.delete_case(1)

        case = seeded_repo.get_by_id(CaseId(value=1))
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

    def test_delete_nonexistent_case_returns_false(
        self,
        viewmodel: CaseManagerViewModel,
    ):
        """Returns False for non-existent case."""
        result = viewmodel.delete_case(999)
        assert result is False


# ============================================================
# Link Source Tests (AC #2)
# ============================================================


class TestLinkSource:
    """Tests for AC #2: Researcher can link sources to cases."""

    def test_link_source_returns_false_when_source_not_in_state(
        self,
        seeded_viewmodel: CaseManagerViewModel,
    ):
        """Returns False when source doesn't exist in state (validation)."""
        # Note: The use case validates that source exists in ProjectState
        # Since we don't have the source in state, this should return False
        result = seeded_viewmodel.link_source(case_id=1, source_id=100)

        # This is expected to fail because source 100 isn't in state
        assert result is False

    def test_link_source_validates_source_exists(
        self,
        seeded_viewmodel: CaseManagerViewModel,
    ):
        """Validates that source exists before linking."""
        # This test documents the validation behavior
        result = seeded_viewmodel.link_source(case_id=1, source_id=999)
        assert result is False  # Source 999 doesn't exist

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
        seeded_repo: SQLiteCaseRepository,
    ):
        """Returns True when source is unlinked successfully."""
        # First link the source
        seeded_repo.link_source(CaseId(value=1), SourceId(value=100))

        result = seeded_viewmodel.unlink_source(case_id=1, source_id=100)

        assert result is True

    def test_unlink_source_removes_from_case(
        self,
        seeded_viewmodel: CaseManagerViewModel,
        seeded_repo: SQLiteCaseRepository,
    ):
        """Source is unlinked from case."""
        seeded_repo.link_source(CaseId(value=1), SourceId(value=100))
        seeded_viewmodel.unlink_source(case_id=1, source_id=100)

        case = seeded_repo.get_by_id(CaseId(value=1))
        assert 100 not in case.source_ids


# ============================================================
# Link Source Failure Scenarios
# ============================================================


class TestLinkSourceFailures:
    """Tests for link source failure scenarios."""

    def test_link_source_to_nonexistent_case_returns_false(
        self,
        viewmodel: CaseManagerViewModel,
    ):
        """Returns False when case doesn't exist."""
        result = viewmodel.link_source(case_id=999, source_id=100)
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
        seeded_repo: SQLiteCaseRepository,
    ):
        """Attribute is added to case."""
        seeded_viewmodel.add_attribute(
            case_id=1,
            name="occupation",
            attr_type="text",
            value="Engineer",
        )

        case = seeded_repo.get_by_id(CaseId(value=1))
        assert case.get_attribute("occupation") is not None
        assert case.get_attribute("occupation").value == "Engineer"

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
        seeded_repo: SQLiteCaseRepository,
    ):
        """Updates existing attribute value."""
        seeded_viewmodel.add_attribute(
            case_id=2,
            name="age",
            attr_type="number",
            value=35,  # Update from 30 to 35
        )

        case = seeded_repo.get_by_id(CaseId(value=2))
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
        seeded_repo: SQLiteCaseRepository,
    ):
        """Attribute is removed from case."""
        seeded_viewmodel.remove_attribute(
            case_id=2,
            name="age",
        )

        case = seeded_repo.get_by_id(CaseId(value=2))
        assert case.get_attribute("age") is None


# ============================================================
# Add Attribute Failure Scenarios
# ============================================================


class TestAddAttributeFailures:
    """Tests for add attribute failure scenarios."""

    def test_add_attribute_to_nonexistent_case_returns_false(
        self,
        viewmodel: CaseManagerViewModel,
    ):
        """Returns False when case doesn't exist."""
        result = viewmodel.add_attribute(
            case_id=999,
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
# Integration Tests (verify data flows correctly)
# ============================================================


class TestIntegration:
    """Tests for verifying data flows correctly through the system."""

    def test_create_and_load_case(
        self,
        viewmodel: CaseManagerViewModel,
    ):
        """Create a case and verify it can be loaded."""
        viewmodel.create_case(name="Test Case", description="Test description")

        cases = viewmodel.load_cases()

        assert len(cases) == 1
        assert cases[0].name == "Test Case"
        assert cases[0].description == "Test description"

    def test_update_and_verify_case(
        self,
        seeded_viewmodel: CaseManagerViewModel,
    ):
        """Update a case and verify changes persist."""
        seeded_viewmodel.update_case(case_id=1, name="New Name")

        case = seeded_viewmodel.get_case(1)

        assert case is not None
        assert case.name == "New Name"
