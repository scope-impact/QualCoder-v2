"""
Tests for Cases Tools Schema.

Verifies MCP tool definitions for case management operations.
"""

from __future__ import annotations

from src.agent_context.schemas.cases_tools import (
    CASES_RESOURCES,
    CASES_TOOLS,
    CaseSummaryOutput,
    CaseWithSourcesOutput,
    CreateCaseInput,
    CreateCaseOutput,
    ListCasesOutput,
)
from src.domain.shared.agent import TrustLevel


class TestCasesToolDefinitions:
    """Tests for CASES_TOOLS definitions."""

    def test_list_cases_tool_defined(self):
        """Verify list_cases tool is properly defined."""
        tool = next((t for t in CASES_TOOLS if t["name"] == "list_cases"), None)
        assert tool is not None
        assert tool["trust_level"] == TrustLevel.AUTONOMOUS
        assert tool["description"]

    def test_get_case_tool_defined(self):
        """Verify get_case tool is properly defined."""
        tool = next((t for t in CASES_TOOLS if t["name"] == "get_case"), None)
        assert tool is not None
        assert "case_id" in tool["input_schema"]["properties"]
        assert "case_id" in tool["input_schema"]["required"]

    def test_create_case_tool_defined(self):
        """Verify create_case tool is properly defined."""
        tool = next((t for t in CASES_TOOLS if t["name"] == "create_case"), None)
        assert tool is not None
        assert tool["trust_level"] == TrustLevel.SUGGEST
        assert "name" in tool["input_schema"]["properties"]
        assert "name" in tool["input_schema"]["required"]

    def test_delete_case_requires_confirmation(self):
        """Verify delete_case requires user confirmation."""
        tool = next((t for t in CASES_TOOLS if t["name"] == "delete_case"), None)
        assert tool is not None
        assert tool["trust_level"] == TrustLevel.REQUIRE

    def test_link_source_tool_defined(self):
        """Verify link_source_to_case tool is properly defined."""
        tool = next(
            (t for t in CASES_TOOLS if t["name"] == "link_source_to_case"), None
        )
        assert tool is not None
        assert tool["trust_level"] == TrustLevel.NOTIFY
        assert "case_id" in tool["input_schema"]["required"]
        assert "source_id" in tool["input_schema"]["required"]

    def test_set_attribute_tool_defined(self):
        """Verify set_case_attribute tool is properly defined."""
        tool = next((t for t in CASES_TOOLS if t["name"] == "set_case_attribute"), None)
        assert tool is not None
        props = tool["input_schema"]["properties"]
        assert "case_id" in props
        assert "attr_name" in props
        assert "attr_type" in props
        assert "attr_value" in props
        # Verify attr_type has valid enum values
        assert props["attr_type"]["enum"] == ["text", "number", "date", "boolean"]

    def test_all_tools_have_required_fields(self):
        """Verify all tools have name, description, trust_level, and input_schema."""
        for tool in CASES_TOOLS:
            assert "name" in tool, f"Tool missing name: {tool}"
            assert "description" in tool, f"Tool {tool['name']} missing description"
            assert "trust_level" in tool, f"Tool {tool['name']} missing trust_level"
            assert "input_schema" in tool, f"Tool {tool['name']} missing input_schema"


class TestCasesResourceDefinitions:
    """Tests for CASES_RESOURCES definitions."""

    def test_cases_list_resource(self):
        """Verify cases list resource is defined."""
        resource = next(
            (r for r in CASES_RESOURCES if r["uri_template"] == "qualcoder://cases"),
            None,
        )
        assert resource is not None
        assert resource["name"] == "All Cases"

    def test_case_details_resource(self):
        """Verify case details resource is defined."""
        resource = next(
            (
                r
                for r in CASES_RESOURCES
                if r["uri_template"] == "qualcoder://cases/{case_id}"
            ),
            None,
        )
        assert resource is not None
        assert resource["name"] == "Case Details"

    def test_all_resources_have_mime_type(self):
        """Verify all resources have application/json mime type."""
        for resource in CASES_RESOURCES:
            assert resource["mime_type"] == "application/json"


class TestInputSchemas:
    """Tests for input dataclass schemas."""

    def test_create_case_input(self):
        """Verify CreateCaseInput schema."""
        input_obj = CreateCaseInput(
            name="Participant 01",
            description="First participant",
            memo="Recruited via clinic",
        )
        assert input_obj.name == "Participant 01"
        assert input_obj.description == "First participant"

    def test_create_case_input_minimal(self):
        """Verify CreateCaseInput with only required fields."""
        input_obj = CreateCaseInput(name="P01")
        assert input_obj.name == "P01"
        assert input_obj.description is None
        assert input_obj.memo is None


class TestOutputSchemas:
    """Tests for output dataclass schemas."""

    def test_create_case_output(self):
        """Verify CreateCaseOutput schema."""
        output = CreateCaseOutput(case_id=1, name="P01")
        assert output.case_id == 1
        assert output.name == "P01"

    def test_case_summary_output(self):
        """Verify CaseSummaryOutput schema."""
        summary = CaseSummaryOutput(
            case_id=1,
            name="P01",
            description="Participant one",
            attribute_count=3,
            source_count=2,
        )
        assert summary.case_id == 1
        assert summary.attribute_count == 3

    def test_list_cases_output(self):
        """Verify ListCasesOutput schema."""
        cases = [
            CaseSummaryOutput(
                case_id=1,
                name="P01",
                description=None,
                attribute_count=2,
                source_count=1,
            ),
            CaseSummaryOutput(
                case_id=2,
                name="P02",
                description=None,
                attribute_count=1,
                source_count=3,
            ),
        ]
        output = ListCasesOutput(cases=cases, total_count=2)
        assert output.total_count == 2
        assert len(output.cases) == 2

    def test_case_with_sources_output(self):
        """Verify CaseWithSourcesOutput schema."""
        output = CaseWithSourcesOutput(
            case_id=1,
            name="P01",
            description="First participant",
            memo=None,
            attributes=[],
            source_count=2,
            source_ids=[10, 20],
        )
        assert output.case_id == 1
        assert output.source_count == 2
        assert 10 in output.source_ids
