"""
Tests for MCP Case Tools

Implements QC-034:
- AC #5: Agent can list all cases
- AC #6: Agent can suggest case groupings
- AC #7: Agent can compare across cases
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from returns.result import Failure, Success

from src.contexts.cases.core.entities import AttributeType, Case, CaseAttribute
from src.contexts.shared import CaseId, SourceId

# ============================================================
# Fixtures
# ============================================================


@pytest.fixture
def case_tools(case_repo):
    """Create case tools for testing."""
    from src.infrastructure.mcp.case_tools import CaseTools

    return CaseTools(case_repo=case_repo)


@pytest.fixture
def sample_case() -> Case:
    """Create a sample case for testing."""
    return Case(
        id=CaseId(value=1),
        name="Participant A",
        description="First participant in study",
        memo="Important notes",
        attributes=(),
        source_ids=(),
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )


def save_case_with_attributes(case_repo, case: Case) -> None:
    """Helper to save a case with its attributes and source links."""
    # Save the case first
    case_repo.save(case)

    # Save attributes
    for attr in case.attributes:
        case_repo.save_attribute(case.id, attr)

    # Link sources
    for source_id in case.source_ids:
        case_repo.link_source(case.id, SourceId(value=source_id))


@pytest.fixture
def case_with_attributes() -> Case:
    """Create a case with attributes for testing."""
    return Case(
        id=CaseId(value=2),
        name="Participant B",
        description="Second participant",
        memo=None,
        attributes=(
            CaseAttribute(name="age", attr_type=AttributeType.NUMBER, value=30),
            CaseAttribute(name="gender", attr_type=AttributeType.TEXT, value="female"),
            CaseAttribute(name="urban", attr_type=AttributeType.BOOLEAN, value=True),
        ),
        source_ids=(10, 20),
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )


# ============================================================
# Tool Definitions Tests
# ============================================================


class TestToolDefinitions:
    """Tests for tool schema definitions."""

    def test_list_cases_tool_has_schema(self, case_tools):
        """list_cases tool has valid schema."""
        schemas = case_tools.get_tool_schemas()
        list_cases = next((s for s in schemas if s["name"] == "list_cases"), None)

        assert list_cases is not None
        assert "description" in list_cases
        assert "inputSchema" in list_cases

    def test_get_case_tool_has_schema(self, case_tools):
        """get_case tool has required parameters."""
        schemas = case_tools.get_tool_schemas()
        get_case = next((s for s in schemas if s["name"] == "get_case"), None)

        assert get_case is not None
        props = get_case["inputSchema"]["properties"]
        assert "case_id" in props
        assert "case_id" in get_case["inputSchema"]["required"]

    def test_suggest_case_groupings_tool_has_schema(self, case_tools):
        """suggest_case_groupings tool has valid schema."""
        schemas = case_tools.get_tool_schemas()
        tool = next((s for s in schemas if s["name"] == "suggest_case_groupings"), None)

        assert tool is not None
        props = tool["inputSchema"]["properties"]
        assert "attribute_names" in props
        assert "min_group_size" in props

    def test_compare_cases_tool_has_schema(self, case_tools):
        """compare_cases tool has required parameters."""
        schemas = case_tools.get_tool_schemas()
        tool = next((s for s in schemas if s["name"] == "compare_cases"), None)

        assert tool is not None
        props = tool["inputSchema"]["properties"]
        assert "case_ids" in props
        assert "case_ids" in tool["inputSchema"]["required"]


# ============================================================
# Tool Registration Tests
# ============================================================


class TestCaseToolsRegistration:
    """Tests for case tools registration."""

    def test_get_tool_schemas_returns_all_tools(self, case_tools):
        """get_tool_schemas returns all case tool schemas."""
        schemas = case_tools.get_tool_schemas()

        assert len(schemas) >= 2  # At minimum: list_cases, get_case
        names = [s["name"] for s in schemas]
        assert "list_cases" in names
        assert "get_case" in names
        assert "suggest_case_groupings" in names
        assert "compare_cases" in names

    def test_get_tool_names(self, case_tools):
        """get_tool_names returns list of tool names."""
        names = case_tools.get_tool_names()

        assert "list_cases" in names
        assert "get_case" in names
        assert "suggest_case_groupings" in names
        assert "compare_cases" in names


# ============================================================
# list_cases Tests (AC #5)
# ============================================================


class TestListCases:
    """Tests for AC #5: Agent can list all cases."""

    def test_returns_empty_list_when_no_cases(self, case_tools):
        """Returns empty list when project has no cases."""
        result = case_tools.execute("list_cases", {})

        assert isinstance(result, Success)
        data = result.unwrap()
        assert data["total_count"] == 0
        assert data["cases"] == []

    def test_returns_cases_with_details(
        self,
        case_tools,
        case_repo,
        sample_case: Case,
    ):
        """Returns case details."""
        case_repo.save(sample_case)

        result = case_tools.execute("list_cases", {})

        assert isinstance(result, Success)
        data = result.unwrap()
        assert data["total_count"] == 1
        case = data["cases"][0]
        assert case["case_id"] == 1
        assert case["name"] == "Participant A"
        assert case["description"] == "First participant in study"

    def test_returns_case_counts(
        self,
        case_tools,
        case_repo,
        case_with_attributes: Case,
    ):
        """Returns attribute and source counts."""
        save_case_with_attributes(case_repo, case_with_attributes)

        result = case_tools.execute("list_cases", {})

        assert isinstance(result, Success)
        case = result.unwrap()["cases"][0]
        assert case["attribute_count"] == 3
        assert case["source_count"] == 2


# ============================================================
# get_case Tests
# ============================================================


class TestGetCase:
    """Tests for getting case details."""

    def test_returns_case_with_all_details(
        self,
        case_tools,
        case_repo,
        case_with_attributes: Case,
    ):
        """Returns full case details including attributes."""
        save_case_with_attributes(case_repo, case_with_attributes)

        result = case_tools.execute("get_case", {"case_id": 2})

        assert isinstance(result, Success)
        data = result.unwrap()
        assert data["case_id"] == 2
        assert data["name"] == "Participant B"
        assert data["description"] == "Second participant"
        assert len(data["attributes"]) == 3
        assert data["source_count"] == 2
        assert 10 in data["source_ids"]
        assert 20 in data["source_ids"]

    def test_returns_attribute_details(
        self,
        case_tools,
        case_repo,
        case_with_attributes: Case,
    ):
        """Returns attribute name, type, and value."""
        save_case_with_attributes(case_repo, case_with_attributes)

        result = case_tools.execute("get_case", {"case_id": 2})

        assert isinstance(result, Success)
        attrs = result.unwrap()["attributes"]
        age_attr = next((a for a in attrs if a["name"] == "age"), None)
        assert age_attr is not None
        assert age_attr["type"] == "number"
        assert age_attr["value"] == 30

    def test_fails_for_nonexistent_case(self, case_tools):
        """Returns failure for non-existent case."""
        result = case_tools.execute("get_case", {"case_id": 999})

        assert isinstance(result, Failure)
        assert "not found" in result.failure().lower()

    def test_fails_with_missing_case_id(self, case_tools):
        """Returns failure when case_id is missing."""
        result = case_tools.execute("get_case", {})

        assert isinstance(result, Failure)
        assert "case_id" in result.failure().lower()


# ============================================================
# suggest_case_groupings Tests (AC #6)
# ============================================================


class TestSuggestCaseGroupings:
    """Tests for AC #6: Agent can suggest case groupings."""

    def test_returns_empty_groupings_with_no_cases(self, case_tools):
        """Returns empty groupings when no cases exist."""
        result = case_tools.execute("suggest_case_groupings", {})

        assert isinstance(result, Success)
        data = result.unwrap()
        assert data["groupings"] == []
        assert data["total_cases_analyzed"] == 0

    def test_suggests_groupings_based_on_attributes(
        self,
        case_tools,
        case_repo,
    ):
        """Suggests groupings based on attribute patterns."""
        # Create cases with similar attributes
        cases = [
            Case(
                id=CaseId(value=1),
                name="P1",
                attributes=(
                    CaseAttribute(
                        name="location", attr_type=AttributeType.TEXT, value="urban"
                    ),
                ),
            ),
            Case(
                id=CaseId(value=2),
                name="P2",
                attributes=(
                    CaseAttribute(
                        name="location", attr_type=AttributeType.TEXT, value="urban"
                    ),
                ),
            ),
            Case(
                id=CaseId(value=3),
                name="P3",
                attributes=(
                    CaseAttribute(
                        name="location", attr_type=AttributeType.TEXT, value="rural"
                    ),
                ),
            ),
            Case(
                id=CaseId(value=4),
                name="P4",
                attributes=(
                    CaseAttribute(
                        name="location", attr_type=AttributeType.TEXT, value="rural"
                    ),
                ),
            ),
        ]
        for case in cases:
            save_case_with_attributes(case_repo, case)

        result = case_tools.execute("suggest_case_groupings", {})

        assert isinstance(result, Success)
        data = result.unwrap()
        assert data["total_cases_analyzed"] == 4
        assert len(data["groupings"]) >= 1

    def test_grouping_includes_rationale(
        self,
        case_tools,
        case_repo,
    ):
        """Grouping suggestions include rationale."""
        cases = [
            Case(
                id=CaseId(value=1),
                name="P1",
                attributes=(
                    CaseAttribute(
                        name="location", attr_type=AttributeType.TEXT, value="urban"
                    ),
                ),
            ),
            Case(
                id=CaseId(value=2),
                name="P2",
                attributes=(
                    CaseAttribute(
                        name="location", attr_type=AttributeType.TEXT, value="urban"
                    ),
                ),
            ),
        ]
        for case in cases:
            save_case_with_attributes(case_repo, case)

        result = case_tools.execute("suggest_case_groupings", {})

        assert isinstance(result, Success)
        groupings = result.unwrap()["groupings"]
        if groupings:
            grouping = groupings[0]
            assert "group_name" in grouping
            assert "rationale" in grouping
            assert "attribute_basis" in grouping
            assert "cases" in grouping

    def test_respects_min_group_size(
        self,
        case_tools,
        case_repo,
    ):
        """Respects minimum group size parameter."""
        cases = [
            Case(
                id=CaseId(value=1),
                name="P1",
                attributes=(
                    CaseAttribute(
                        name="location", attr_type=AttributeType.TEXT, value="urban"
                    ),
                ),
            ),
            Case(
                id=CaseId(value=2),
                name="P2",
                attributes=(
                    CaseAttribute(
                        name="location", attr_type=AttributeType.TEXT, value="rural"
                    ),
                ),
            ),
            Case(
                id=CaseId(value=3),
                name="P3",
                attributes=(
                    CaseAttribute(
                        name="location", attr_type=AttributeType.TEXT, value="suburban"
                    ),
                ),
            ),
        ]
        for case in cases:
            save_case_with_attributes(case_repo, case)

        # With min_group_size=2, none should be grouped (each value is unique)
        result = case_tools.execute("suggest_case_groupings", {"min_group_size": 2})

        assert isinstance(result, Success)
        data = result.unwrap()
        # All should be ungrouped since each location appears only once
        assert len(data["ungrouped_case_ids"]) == 3

    def test_filters_by_attribute_names(
        self,
        case_tools,
        case_repo,
    ):
        """Focuses on specified attributes when provided."""
        cases = [
            Case(
                id=CaseId(value=1),
                name="P1",
                attributes=(
                    CaseAttribute(
                        name="location", attr_type=AttributeType.TEXT, value="urban"
                    ),
                    CaseAttribute(name="age", attr_type=AttributeType.NUMBER, value=25),
                ),
            ),
            Case(
                id=CaseId(value=2),
                name="P2",
                attributes=(
                    CaseAttribute(
                        name="location", attr_type=AttributeType.TEXT, value="rural"
                    ),
                    CaseAttribute(name="age", attr_type=AttributeType.NUMBER, value=25),
                ),
            ),
        ]
        for case in cases:
            save_case_with_attributes(case_repo, case)

        result = case_tools.execute(
            "suggest_case_groupings", {"attribute_names": ["age"]}
        )

        assert isinstance(result, Success)
        data = result.unwrap()
        # Should find grouping by age (both are 25), not by location
        if data["groupings"]:
            assert data["groupings"][0]["attribute_basis"] == "age"


# ============================================================
# compare_cases Tests (AC #7)
# ============================================================


class TestCompareCases:
    """Tests for AC #7: Agent can compare across cases."""

    def test_fails_with_less_than_two_cases(self, case_tools):
        """Returns failure when fewer than 2 cases provided."""
        result = case_tools.execute("compare_cases", {"case_ids": [1]})

        assert isinstance(result, Failure)
        assert "at least 2" in result.failure().lower()

    def test_fails_with_missing_case_ids(self, case_tools):
        """Returns failure when case_ids is missing."""
        result = case_tools.execute("compare_cases", {})

        assert isinstance(result, Failure)
        assert "case_ids" in result.failure().lower()

    def test_fails_for_nonexistent_cases(
        self,
        case_tools,
        case_repo,
        sample_case: Case,
    ):
        """Returns failure when any case doesn't exist."""
        case_repo.save(sample_case)

        result = case_tools.execute("compare_cases", {"case_ids": [1, 999]})

        assert isinstance(result, Failure)
        assert "not found" in result.failure().lower()

    def test_compares_two_cases(
        self,
        case_tools,
        case_repo,
    ):
        """Compares two cases and returns comparison data."""
        case1 = Case(
            id=CaseId(value=1),
            name="Participant A",
        )
        case2 = Case(
            id=CaseId(value=2),
            name="Participant B",
        )
        case_repo.save(case1)
        case_repo.save(case2)

        result = case_tools.execute("compare_cases", {"case_ids": [1, 2]})

        assert isinstance(result, Success)
        data = result.unwrap()
        assert len(data["cases"]) == 2
        assert data["cases"][0]["case_id"] == 1
        assert data["cases"][0]["case_name"] == "Participant A"
        assert data["cases"][1]["case_id"] == 2

    def test_returns_analysis_summary(
        self,
        case_tools,
        case_repo,
    ):
        """Returns a natural language analysis summary."""
        case1 = Case(id=CaseId(value=1), name="P1")
        case2 = Case(id=CaseId(value=2), name="P2")
        case_repo.save(case1)
        case_repo.save(case2)

        result = case_tools.execute("compare_cases", {"case_ids": [1, 2]})

        assert isinstance(result, Success)
        data = result.unwrap()
        assert "analysis_summary" in data
        assert isinstance(data["analysis_summary"], str)
        assert len(data["analysis_summary"]) > 0


# ============================================================
# Error Handling Tests
# ============================================================


class TestErrorHandling:
    """Tests for error handling."""

    def test_unknown_tool_returns_failure(self, case_tools):
        """Unknown tool name returns failure."""
        result = case_tools.execute("unknown_tool", {})

        assert isinstance(result, Failure)
        assert "Unknown tool" in result.failure()
