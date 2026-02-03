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
    allure.feature("Cases MCP Tools"),
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
            id=CaseId(value=1),
            name="Participant A",
            description="First participant",
            memo="Notes about A",
            attributes=(
                CaseAttribute(name="age", attr_type=AttributeType.NUMBER, value=25),
                CaseAttribute(name="gender", attr_type=AttributeType.TEXT, value="M"),
            ),
            source_ids=(10, 11),
        ),
        Case(
            id=CaseId(value=2),
            name="Participant B",
            description="Second participant",
            memo=None,
            attributes=(
                CaseAttribute(name="age", attr_type=AttributeType.NUMBER, value=30),
                CaseAttribute(name="gender", attr_type=AttributeType.TEXT, value="F"),
            ),
            source_ids=(12,),
        ),
        Case(
            id=CaseId(value=3),
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
    @allure.title("ToolParameter stores parameter metadata")
    def test_tool_parameter_stores_metadata(self):
        param = ToolParameter(
            name="case_id",
            type="integer",
            description="ID of the case",
            required=True,
            default=None,
        )

        assert param.name == "case_id"
        assert param.type == "integer"
        assert param.description == "ID of the case"
        assert param.required is True
        assert param.default is None

    @allure.title("ToolParameter optional parameters have defaults")
    def test_tool_parameter_optional_defaults(self):
        param = ToolParameter(
            name="limit",
            type="integer",
            description="Max results",
            required=False,
            default=10,
        )

        assert param.required is False
        assert param.default == 10

    @allure.title("ToolDefinition to_schema returns MCP-compatible format")
    def test_tool_definition_to_schema_basic(self):
        tool = ToolDefinition(
            name="test_tool",
            description="A test tool",
            parameters=(),
        )

        schema = tool.to_schema()

        assert schema["name"] == "test_tool"
        assert schema["description"] == "A test tool"
        assert schema["inputSchema"]["type"] == "object"
        assert schema["inputSchema"]["properties"] == {}
        assert schema["inputSchema"]["required"] == []

    @allure.title("ToolDefinition to_schema includes parameters")
    def test_tool_definition_to_schema_with_parameters(self):
        tool = ToolDefinition(
            name="get_case",
            description="Get a case by ID",
            parameters=(
                ToolParameter(
                    name="case_id",
                    type="integer",
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

        assert "case_id" in schema["inputSchema"]["properties"]
        assert schema["inputSchema"]["properties"]["case_id"]["type"] == "integer"
        assert "case_id" in schema["inputSchema"]["required"]

        assert "include_sources" in schema["inputSchema"]["properties"]
        assert schema["inputSchema"]["properties"]["include_sources"]["default"] is True
        assert "include_sources" not in schema["inputSchema"]["required"]


@allure.story("Tool Schema Generation")
@allure.severity(allure.severity_level.CRITICAL)
class TestPredefinedToolSchemas:
    @allure.title("list_cases tool has correct schema")
    def test_list_cases_tool_schema(self):
        schema = list_cases_tool.to_schema()

        assert schema["name"] == "list_cases"
        assert "List all cases" in schema["description"]
        assert schema["inputSchema"]["required"] == []

    @allure.title("get_case tool has correct schema with case_id parameter")
    def test_get_case_tool_schema(self):
        schema = get_case_tool.to_schema()

        assert schema["name"] == "get_case"
        assert "case_id" in schema["inputSchema"]["properties"]
        assert schema["inputSchema"]["properties"]["case_id"]["type"] == "integer"
        assert "case_id" in schema["inputSchema"]["required"]

    @allure.title("suggest_case_groupings tool has correct schema")
    def test_suggest_case_groupings_tool_schema(self):
        schema = suggest_case_groupings_tool.to_schema()

        assert schema["name"] == "suggest_case_groupings"
        assert "attribute_names" in schema["inputSchema"]["properties"]
        assert "min_group_size" in schema["inputSchema"]["properties"]
        # Both are optional
        assert "attribute_names" not in schema["inputSchema"]["required"]
        assert "min_group_size" not in schema["inputSchema"]["required"]

    @allure.title("compare_cases tool has correct schema with required case_ids")
    def test_compare_cases_tool_schema(self):
        schema = compare_cases_tool.to_schema()

        assert schema["name"] == "compare_cases"
        assert "case_ids" in schema["inputSchema"]["properties"]
        assert schema["inputSchema"]["properties"]["case_ids"]["type"] == "array"
        assert "case_ids" in schema["inputSchema"]["required"]


# =============================================================================
# CaseTools Class Tests
# =============================================================================


@allure.story("CaseTools Initialization")
@allure.severity(allure.severity_level.CRITICAL)
class TestCaseToolsInitialization:
    @allure.title("CaseTools initializes with context")
    def test_init_with_context(self, context_no_project):
        tools = CaseTools(ctx=context_no_project)

        assert tools._ctx is context_no_project

    @allure.title("get_tool_schemas returns all tool schemas")
    def test_get_tool_schemas(self, context_no_project):
        tools = CaseTools(ctx=context_no_project)

        schemas = tools.get_tool_schemas()

        assert len(schemas) == 4
        names = [s["name"] for s in schemas]
        assert "list_cases" in names
        assert "get_case" in names
        assert "suggest_case_groupings" in names
        assert "compare_cases" in names

    @allure.title("get_tool_names returns list of tool names")
    def test_get_tool_names(self, context_no_project):
        tools = CaseTools(ctx=context_no_project)

        names = tools.get_tool_names()

        assert names == [
            "list_cases",
            "get_case",
            "suggest_case_groupings",
            "compare_cases",
        ]


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

    @allure.title("list_cases returns empty list when no cases exist")
    def test_list_cases_empty(self, context_with_project):
        tools = CaseTools(ctx=context_with_project)

        result = tools.execute("list_cases", {})

        assert result["success"] is True
        assert result["data"]["total_count"] == 0
        assert result["data"]["cases"] == []

    @allure.title("list_cases returns all cases with summary info")
    def test_list_cases_with_cases(self, context_with_cases):
        tools = CaseTools(ctx=context_with_cases)

        result = tools.execute("list_cases", {})

        assert result["success"] is True
        assert result["data"]["total_count"] == 3
        cases = result["data"]["cases"]
        assert len(cases) == 3

        # Check first case has expected fields
        case_a = next(c for c in cases if c["name"] == "Participant A")
        assert case_a["case_id"] == 1
        assert case_a["description"] == "First participant"
        assert case_a["attribute_count"] == 2
        assert case_a["source_count"] == 2


# =============================================================================
# get_case Tool Tests
# =============================================================================


@allure.story("get_case Tool")
@allure.severity(allure.severity_level.CRITICAL)
class TestGetCaseTool:
    @allure.title("get_case fails when case_id missing")
    def test_get_case_missing_param(self, context_with_project):
        tools = CaseTools(ctx=context_with_project)

        result = tools.execute("get_case", {})

        assert result["success"] is False
        assert "MISSING_PARAM" in result["error_code"]

    @allure.title("get_case fails when no project open")
    def test_get_case_no_project(self, context_no_project):
        tools = CaseTools(ctx=context_no_project)

        result = tools.execute("get_case", {"case_id": 1})

        assert result["success"] is False
        assert "NO_PROJECT" in result["error_code"]

    @allure.title("get_case fails when case not found")
    def test_get_case_not_found(self, context_with_project):
        tools = CaseTools(ctx=context_with_project)

        result = tools.execute("get_case", {"case_id": 999})

        assert result["success"] is False
        assert "NOT_FOUND" in result["error_code"]

    @allure.title("get_case returns case details on success")
    def test_get_case_success(self, context_with_cases):
        tools = CaseTools(ctx=context_with_cases)

        result = tools.execute("get_case", {"case_id": 1})

        assert result["success"] is True
        data = result["data"]
        assert data["case_id"] == 1
        assert data["name"] == "Participant A"
        assert data["description"] == "First participant"
        assert data["memo"] == "Notes about A"
        assert len(data["attributes"]) == 2
        assert data["source_count"] == 2
        assert data["source_ids"] == [10, 11]

    @allure.title("get_case returns attributes with type and value")
    def test_get_case_attributes(self, context_with_cases):
        tools = CaseTools(ctx=context_with_cases)

        result = tools.execute("get_case", {"case_id": 1})

        attrs = result["data"]["attributes"]
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
    @allure.title("suggest_case_groupings returns empty when no cases_context")
    def test_suggest_groupings_no_cases_context(self, context_no_project):
        tools = CaseTools(ctx=context_no_project)

        # When no cases_context, returns empty groupings (no error)
        result = tools.execute("suggest_case_groupings", {})

        assert result["success"] is True
        assert result["data"]["groupings"] == []
        assert result["data"]["total_cases_analyzed"] == 0

    @allure.title("suggest_case_groupings returns empty when no cases")
    def test_suggest_groupings_no_cases(self, context_with_project):
        tools = CaseTools(ctx=context_with_project)

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

    @allure.title("suggest_case_groupings respects min_group_size")
    def test_suggest_groupings_min_size(self, context_with_cases):
        tools = CaseTools(ctx=context_with_cases)

        # With min_group_size=3, no groups should form (max is 2 for any value)
        result = tools.execute("suggest_case_groupings", {"min_group_size": 3})

        assert result["success"] is True
        assert result["data"]["groupings"] == []

    @allure.title("suggest_case_groupings identifies ungrouped cases")
    def test_suggest_groupings_ungrouped(self, context_with_cases):
        tools = CaseTools(ctx=context_with_cases)

        # With high min_group_size, all cases should be ungrouped
        result = tools.execute("suggest_case_groupings", {"min_group_size": 10})

        assert result["success"] is True
        ungrouped = result["data"]["ungrouped_case_ids"]
        assert len(ungrouped) == 3


# =============================================================================
# compare_cases Tool Tests
# =============================================================================


@allure.story("compare_cases Tool")
@allure.severity(allure.severity_level.NORMAL)
class TestCompareCasesTool:
    @allure.title("compare_cases fails when case_ids missing")
    def test_compare_cases_missing_param(self, context_with_project):
        tools = CaseTools(ctx=context_with_project)

        result = tools.execute("compare_cases", {})

        assert result["success"] is False
        assert "MISSING_PARAM" in result["error_code"]

    @allure.title("compare_cases fails with less than 2 cases")
    def test_compare_cases_insufficient_cases(self, context_with_project):
        tools = CaseTools(ctx=context_with_project)

        result = tools.execute("compare_cases", {"case_ids": [1]})

        assert result["success"] is False
        assert "INSUFFICIENT_CASES" in result["error_code"]

    @allure.title("compare_cases fails when no project open")
    def test_compare_cases_no_project(self, context_no_project):
        tools = CaseTools(ctx=context_no_project)

        result = tools.execute("compare_cases", {"case_ids": [1, 2]})

        # When no project, get_case fails with NO_PROJECT, which causes compare to fail
        assert result["success"] is False
        assert "CASE_NOT_FOUND" in result["error_code"]

    @allure.title("compare_cases fails when case not found")
    def test_compare_cases_case_not_found(self, context_with_cases):
        tools = CaseTools(ctx=context_with_cases)

        result = tools.execute("compare_cases", {"case_ids": [1, 999]})

        assert result["success"] is False
        assert "CASE_NOT_FOUND" in result["error_code"]

    @allure.title("compare_cases returns comparison data on success")
    def test_compare_cases_success(self, context_with_cases):
        tools = CaseTools(ctx=context_with_cases)

        result = tools.execute("compare_cases", {"case_ids": [1, 2]})

        assert result["success"] is True
        data = result["data"]
        assert len(data["cases"]) == 2
        assert "common_codes" in data
        assert "analysis_summary" in data

        # Check case comparison entries
        case_1 = next(c for c in data["cases"] if c["case_id"] == 1)
        assert case_1["case_name"] == "Participant A"

    @allure.title("compare_cases includes analysis summary")
    def test_compare_cases_summary(self, context_with_cases):
        tools = CaseTools(ctx=context_with_cases)

        result = tools.execute("compare_cases", {"case_ids": [1, 2, 3]})

        assert result["success"] is True
        summary = result["data"]["analysis_summary"]
        assert "3 cases" in summary
        assert "Participant A" in summary


# =============================================================================
# Edge Cases and Integration
# =============================================================================


@allure.story("Edge Cases")
@allure.severity(allure.severity_level.NORMAL)
class TestEdgeCases:
    @allure.title("Tools work with None cases_context")
    def test_none_cases_context(self, mock_project):
        ctx = MockCaseToolsContext(
            state=MockProjectState(project=mock_project),
            cases_context=None,
        )
        tools = CaseTools(ctx=ctx)

        result = tools.execute("list_cases", {})

        # Should return empty list when cases_context is None
        assert result["success"] is True
        assert result["data"]["total_count"] == 0

    @allure.title("get_case handles string case_id")
    def test_get_case_string_id(self, context_with_cases):
        tools = CaseTools(ctx=context_with_cases)

        # case_id should be converted to int
        result = tools.execute("get_case", {"case_id": "1"})

        assert result["success"] is True
        assert result["data"]["case_id"] == 1

    @allure.title("suggest_case_groupings handles None min_group_size")
    def test_suggest_groupings_none_min_size(self, context_with_cases):
        tools = CaseTools(ctx=context_with_cases)

        # None should default to 2
        result = tools.execute("suggest_case_groupings", {"min_group_size": None})

        assert result["success"] is True
