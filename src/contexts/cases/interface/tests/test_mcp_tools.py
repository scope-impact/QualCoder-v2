"""
Cases Context: MCP Tools Unit Tests

Tests for CaseTools MCP interface layer.

Key business logic tested:
- Tool schema generation (get_tool_schemas)
- Tool execution dispatch (execute)
- Error handling for unknown tools
- list_cases tool success and failure paths
- get_case tool success and failure paths
- suggest_case_groupings tool success and failure paths
- compare_cases tool success and failure paths
- Context requirements via protocol
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING
from unittest.mock import Mock

import allure
import pytest

from src.contexts.cases.core.entities import AttributeType, Case, CaseAttribute
from src.contexts.cases.interface.mcp_tools import (
    CaseTools,
    ToolDefinition,
    ToolParameter,
    compare_cases_tool,
    get_case_tool,
    list_cases_tool,
    suggest_case_groupings_tool,
)
from src.shared import CaseId

if TYPE_CHECKING:
    pass

pytestmark = [
    pytest.mark.unit,
    allure.epic("QualCoder v2"),
    allure.feature("QC-034 Manage Cases"),
]


# =============================================================================
# Test Fixtures and Mocks
# =============================================================================


@dataclass
class MockCaseRepository:
    """Mock case repository for testing."""

    cases: list[Case] = field(default_factory=list)

    def get_all(self) -> list[Case]:
        return self.cases

    def get_by_id(self, case_id: CaseId) -> Case | None:
        for case in self.cases:
            if case.id == case_id:
                return case
        return None


@dataclass
class MockCasesContext:
    """Mock cases context for testing."""

    case_repo: MockCaseRepository | None = None


@dataclass
class MockProjectState:
    """Mock project state for testing."""

    project: object | None = None


class MockCaseToolsContext:
    """Mock context implementing CaseToolsContext protocol."""

    def __init__(
        self,
        state: MockProjectState | None = None,
        cases_context: MockCasesContext | None = None,
    ):
        self._state = state or MockProjectState(project=None)
        self._cases_context = cases_context

    @property
    def state(self):
        return self._state

    @property
    def cases_context(self):
        return self._cases_context


@pytest.fixture
def mock_project():
    """Create a mock project object."""
    return Mock(name="Test Project", path="/test/path.qda")


@pytest.fixture
def mock_case_repo():
    """Create an empty mock case repository."""
    return MockCaseRepository()


@pytest.fixture
def mock_case_repo_with_cases():
    """Create a mock case repository with test cases."""
    cases = [
        Case(
            id=CaseId(value="1"),
            name="Participant A",
            description="First participant",
            memo="Notes about A",
            attributes=(
                CaseAttribute(name="age", attr_type=AttributeType.NUMBER, value=25),
                CaseAttribute(name="gender", attr_type=AttributeType.TEXT, value="M"),
            ),
            source_ids=("10", "11"),
        ),
        Case(
            id=CaseId(value="2"),
            name="Participant B",
            description="Second participant",
            memo=None,
            attributes=(
                CaseAttribute(name="age", attr_type=AttributeType.NUMBER, value=30),
                CaseAttribute(name="gender", attr_type=AttributeType.TEXT, value="F"),
            ),
            source_ids=("12",),
        ),
        Case(
            id=CaseId(value="3"),
            name="Participant C",
            description="Third participant",
            memo="Different notes",
            attributes=(
                CaseAttribute(name="age", attr_type=AttributeType.NUMBER, value=25),
            ),
            source_ids=(),
        ),
    ]
    return MockCaseRepository(cases=cases)


@pytest.fixture
def context_no_project():
    """Create a context with no project open."""
    return MockCaseToolsContext(state=MockProjectState(project=None))


@pytest.fixture
def context_with_project(mock_project, mock_case_repo):
    """Create a context with a project open but empty case repo."""
    return MockCaseToolsContext(
        state=MockProjectState(project=mock_project),
        cases_context=MockCasesContext(case_repo=mock_case_repo),
    )


@pytest.fixture
def context_with_cases(mock_project, mock_case_repo_with_cases):
    """Create a context with a project and cases."""
    return MockCaseToolsContext(
        state=MockProjectState(project=mock_project),
        cases_context=MockCasesContext(case_repo=mock_case_repo_with_cases),
    )


# =============================================================================
# Tool Definition Tests
# =============================================================================


@allure.story("Tool Schema Generation")
@allure.severity(allure.severity_level.CRITICAL)
class TestToolDefinition:
    @allure.title("ToolParameter stores metadata with required and optional fields")
    @pytest.mark.parametrize(
        "name, type_, required, default, expected_default",
        [
            ("case_id", "string", True, None, None),
            ("limit", "integer", False, 10, 10),
        ],
        ids=["required-param", "optional-param-with-default"],
    )
    def test_tool_parameter_stores_metadata(
        self, name, type_, required, default, expected_default
    ):
        param = ToolParameter(
            name=name,
            type=type_,
            description=f"Description for {name}",
            required=required,
            default=default,
        )

        assert param.name == name
        assert param.type == type_
        assert param.required is required
        assert param.default == expected_default

    @allure.title("ToolDefinition to_schema returns MCP-compatible format with parameters")
    def test_tool_definition_to_schema(self):
        tool = ToolDefinition(
            name="get_case",
            description="Get a case by ID",
            parameters=(
                ToolParameter(
                    name="case_id",
                    type="string",
                    description="ID of the case",
                    required=True,
                ),
                ToolParameter(
                    name="include_sources",
                    type="boolean",
                    description="Include source details",
                    required=False,
                    default=True,
                ),
            ),
        )

        schema = tool.to_schema()

        assert schema["name"] == "get_case"
        assert schema["description"] == "Get a case by ID"
        assert schema["inputSchema"]["type"] == "object"

        # Required param
        assert "case_id" in schema["inputSchema"]["properties"]
        assert schema["inputSchema"]["properties"]["case_id"]["type"] == "string"
        assert "case_id" in schema["inputSchema"]["required"]

        # Optional param with default
        assert "include_sources" in schema["inputSchema"]["properties"]
        assert schema["inputSchema"]["properties"]["include_sources"]["default"] is True
        assert "include_sources" not in schema["inputSchema"]["required"]


@allure.story("Tool Schema Generation")
@allure.severity(allure.severity_level.CRITICAL)
class TestPredefinedToolSchemas:
    @allure.title("Predefined tool has correct schema")
    @pytest.mark.parametrize(
        "tool, expected_name, required_params, optional_params",
        [
            (list_cases_tool, "list_cases", [], []),
            (get_case_tool, "get_case", ["case_id"], []),
            (
                suggest_case_groupings_tool,
                "suggest_case_groupings",
                [],
                ["attribute_names", "min_group_size"],
            ),
            (compare_cases_tool, "compare_cases", ["case_ids"], []),
        ],
        ids=["list_cases", "get_case", "suggest_case_groupings", "compare_cases"],
    )
    def test_tool_schema(self, tool, expected_name, required_params, optional_params):
        schema = tool.to_schema()

        assert schema["name"] == expected_name
        for param in required_params:
            assert param in schema["inputSchema"]["properties"]
            assert param in schema["inputSchema"]["required"]
        for param in optional_params:
            assert param in schema["inputSchema"]["properties"]
            assert param not in schema["inputSchema"]["required"]

        # compare_cases has array type for case_ids
        if expected_name == "compare_cases":
            assert schema["inputSchema"]["properties"]["case_ids"]["type"] == "array"


# =============================================================================
# CaseTools Class Tests
# =============================================================================


@allure.story("CaseTools Initialization")
@allure.severity(allure.severity_level.CRITICAL)
class TestCaseToolsInitialization:
    @allure.title("CaseTools initializes and exposes tool schemas and names")
    def test_init_and_tool_listing(self, context_no_project):
        tools = CaseTools(ctx=context_no_project)

        assert tools._ctx is context_no_project

        schemas = tools.get_tool_schemas()
        assert len(schemas) == 4
        names = [s["name"] for s in schemas]
        assert names == tools.get_tool_names()
        assert set(names) == {
            "list_cases",
            "get_case",
            "suggest_case_groupings",
            "compare_cases",
        }


# =============================================================================
# Execute Dispatch Tests
# =============================================================================


@allure.story("Tool Execution Dispatch")
@allure.severity(allure.severity_level.CRITICAL)
class TestExecuteDispatch:
    @allure.title("execute returns error for unknown tool")
    def test_execute_unknown_tool(self, context_no_project):
        tools = CaseTools(ctx=context_no_project)

        result = tools.execute("unknown_tool", {})

        assert result["success"] is False
        assert result["error_code"] == "TOOL_NOT_FOUND"
        assert "unknown_tool" in result["error"]
        assert "suggestions" in result

    @allure.title("execute dispatches to correct handler")
    def test_execute_dispatches_correctly(self, context_with_project):
        tools = CaseTools(ctx=context_with_project)

        result = tools.execute("list_cases", {})

        assert result["success"] is True

    @allure.title("execute handles exceptions gracefully")
    def test_execute_handles_exception(self, context_no_project):
        tools = CaseTools(ctx=context_no_project)

        # Create a mock that raises when accessed
        class ExceptionRaiser:
            @property
            def state(self):
                raise RuntimeError("Test exception")

            @property
            def cases_context(self):
                raise RuntimeError("Test exception")

        tools._ctx = ExceptionRaiser()

        result = tools.execute("list_cases", {})

        assert result["success"] is False
        assert result["error_code"] == "TOOL_EXECUTION_ERROR"


# =============================================================================
# list_cases Tool Tests
# =============================================================================


@allure.story("list_cases Tool")
@allure.severity(allure.severity_level.CRITICAL)
class TestListCasesTool:
    @allure.title("list_cases fails when no project open")
    def test_list_cases_no_project(self, context_no_project):
        tools = CaseTools(ctx=context_no_project)

        result = tools.execute("list_cases", {})

        assert result["success"] is False
        assert "NO_PROJECT" in result["error_code"]
        assert "Open a project" in result["suggestions"][0]

    @allure.title("list_cases returns cases with summary info")
    def test_list_cases_with_cases(self, context_with_cases):
        tools = CaseTools(ctx=context_with_cases)

        result = tools.execute("list_cases", {})

        assert result["success"] is True
        assert result["data"]["total_count"] == 3
        cases = result["data"]["cases"]
        assert len(cases) == 3

        # Check first case has expected fields
        case_a = next(c for c in cases if c["name"] == "Participant A")
        assert case_a["case_id"] == "1"
        assert case_a["description"] == "First participant"
        assert case_a["attribute_count"] == 2
        assert case_a["source_count"] == 2

    @allure.title("list_cases returns empty list when no cases exist")
    def test_list_cases_empty(self, context_with_project):
        tools = CaseTools(ctx=context_with_project)

        result = tools.execute("list_cases", {})

        assert result["success"] is True
        assert result["data"]["total_count"] == 0
        assert result["data"]["cases"] == []


# =============================================================================
# get_case Tool Tests
# =============================================================================


@allure.story("get_case Tool")
@allure.severity(allure.severity_level.CRITICAL)
class TestGetCaseTool:
    @allure.title("get_case fails with validation errors")
    @pytest.mark.parametrize(
        "context_fixture, args, expected_error_code",
        [
            ("context_with_project", {}, "MISSING_PARAM"),
            ("context_no_project", {"case_id": 1}, "NO_PROJECT"),
            ("context_with_project", {"case_id": 999}, "NOT_FOUND"),
        ],
        ids=["missing-case-id", "no-project", "case-not-found"],
    )
    def test_get_case_errors(
        self, context_fixture, args, expected_error_code, request
    ):
        ctx = request.getfixturevalue(context_fixture)
        tools = CaseTools(ctx=ctx)

        result = tools.execute("get_case", args)

        assert result["success"] is False
        assert expected_error_code in result["error_code"]

    @allure.title("get_case returns full case details with attributes on success")
    def test_get_case_success(self, context_with_cases):
        tools = CaseTools(ctx=context_with_cases)

        result = tools.execute("get_case", {"case_id": 1})

        assert result["success"] is True
        data = result["data"]
        assert data["case_id"] == "1"
        assert data["name"] == "Participant A"
        assert data["description"] == "First participant"
        assert data["memo"] == "Notes about A"
        assert len(data["attributes"]) == 2
        assert data["source_count"] == 2
        assert data["source_ids"] == ["10", "11"]

        # Check attribute details
        attrs = data["attributes"]
        age_attr = next(a for a in attrs if a["name"] == "age")
        assert age_attr["type"] == "number"
        assert age_attr["value"] == 25

        gender_attr = next(a for a in attrs if a["name"] == "gender")
        assert gender_attr["type"] == "text"
        assert gender_attr["value"] == "M"


# =============================================================================
# suggest_case_groupings Tool Tests
# =============================================================================


@allure.story("suggest_case_groupings Tool")
@allure.severity(allure.severity_level.NORMAL)
class TestSuggestCaseGroupingsTool:
    @allure.title("suggest_case_groupings returns empty when no cases available")
    @pytest.mark.parametrize(
        "context_fixture",
        ["context_no_project", "context_with_project"],
        ids=["no-cases-context", "empty-repo"],
    )
    def test_suggest_groupings_empty(self, context_fixture, request):
        ctx = request.getfixturevalue(context_fixture)
        tools = CaseTools(ctx=ctx)

        result = tools.execute("suggest_case_groupings", {})

        assert result["success"] is True
        assert result["data"]["groupings"] == []
        assert result["data"]["total_cases_analyzed"] == 0

    @allure.title("suggest_case_groupings groups by attribute value")
    def test_suggest_groupings_by_attribute(self, context_with_cases):
        tools = CaseTools(ctx=context_with_cases)

        result = tools.execute("suggest_case_groupings", {"min_group_size": 2})

        assert result["success"] is True
        groupings = result["data"]["groupings"]
        assert len(groupings) > 0

        # Should find age=25 group (Participant A and C)
        age_group = next(
            (
                g
                for g in groupings
                if g["attribute_basis"] == "age" and "25" in g["group_name"]
            ),
            None,
        )
        assert age_group is not None
        assert len(age_group["cases"]) == 2

    @allure.title("suggest_case_groupings filters by attribute_names")
    def test_suggest_groupings_filter_attributes(self, context_with_cases):
        tools = CaseTools(ctx=context_with_cases)

        result = tools.execute(
            "suggest_case_groupings",
            {"attribute_names": ["gender"], "min_group_size": 1},
        )

        assert result["success"] is True
        groupings = result["data"]["groupings"]
        # Should only have gender-based groupings
        for g in groupings:
            assert g["attribute_basis"] == "gender"

    @allure.title("suggest_case_groupings respects min_group_size and identifies ungrouped")
    def test_suggest_groupings_min_size_and_ungrouped(self, context_with_cases):
        tools = CaseTools(ctx=context_with_cases)

        # With min_group_size=3, no groups should form (max is 2 for any value)
        result = tools.execute("suggest_case_groupings", {"min_group_size": 3})

        assert result["success"] is True
        assert result["data"]["groupings"] == []

        # With high min_group_size, all cases should be ungrouped
        result_high = tools.execute("suggest_case_groupings", {"min_group_size": 10})

        assert result_high["success"] is True
        ungrouped = result_high["data"]["ungrouped_case_ids"]
        assert len(ungrouped) == 3


# =============================================================================
# compare_cases Tool Tests
# =============================================================================


@allure.story("compare_cases Tool")
@allure.severity(allure.severity_level.NORMAL)
class TestCompareCasesTool:
    @allure.title("compare_cases fails with validation errors")
    @pytest.mark.parametrize(
        "context_fixture, args, expected_error_code",
        [
            ("context_with_project", {}, "MISSING_PARAM"),
            ("context_with_project", {"case_ids": [1]}, "INSUFFICIENT_CASES"),
            ("context_no_project", {"case_ids": [1, 2]}, "CASE_NOT_FOUND"),
            ("context_with_cases", {"case_ids": [1, 999]}, "CASE_NOT_FOUND"),
        ],
        ids=["missing-param", "insufficient-cases", "no-project", "case-not-found"],
    )
    def test_compare_cases_errors(
        self, context_fixture, args, expected_error_code, request
    ):
        ctx = request.getfixturevalue(context_fixture)
        tools = CaseTools(ctx=ctx)

        result = tools.execute("compare_cases", args)

        assert result["success"] is False
        assert expected_error_code in result["error_code"]

    @allure.title("compare_cases returns comparison data with analysis summary")
    def test_compare_cases_success(self, context_with_cases):
        tools = CaseTools(ctx=context_with_cases)

        # Two-case comparison
        result = tools.execute("compare_cases", {"case_ids": [1, 2]})

        assert result["success"] is True
        data = result["data"]
        assert len(data["cases"]) == 2
        assert "common_codes" in data
        assert "analysis_summary" in data

        case_1 = next(c for c in data["cases"] if c["case_id"] == "1")
        assert case_1["case_name"] == "Participant A"

        # Three-case comparison with summary content
        result_3 = tools.execute("compare_cases", {"case_ids": [1, 2, 3]})

        assert result_3["success"] is True
        summary = result_3["data"]["analysis_summary"]
        assert "3 cases" in summary
        assert "Participant A" in summary


# =============================================================================
# Edge Cases
# =============================================================================


@allure.story("Edge Cases")
@allure.severity(allure.severity_level.NORMAL)
class TestEdgeCases:
    @allure.title("Tools handle None cases_context and string case_id")
    def test_none_context_and_string_id(self, mock_project, context_with_cases):
        # None cases_context returns empty list
        ctx = MockCaseToolsContext(
            state=MockProjectState(project=mock_project),
            cases_context=None,
        )
        tools = CaseTools(ctx=ctx)

        result = tools.execute("list_cases", {})

        assert result["success"] is True
        assert result["data"]["total_count"] == 0

        # String case_id is handled correctly
        tools2 = CaseTools(ctx=context_with_cases)

        result2 = tools2.execute("get_case", {"case_id": "1"})

        assert result2["success"] is True
        assert result2["data"]["case_id"] == "1"

    @allure.title("suggest_case_groupings handles None min_group_size")
    def test_suggest_groupings_none_min_size(self, context_with_cases):
        tools = CaseTools(ctx=context_with_cases)

        # None should default to 2
        result = tools.execute("suggest_case_groupings", {"min_group_size": None})

        assert result["success"] is True
