"""
MCP Coding Tools Tests

Unit tests for the CodingTools MCP interface layer.

Tests cover:
- Tool schema generation (get_tool_schemas, get_tool_names)
- Tool dispatching (execute method)
- list_codes tool
- get_code tool
- list_segments_for_source tool
- batch_apply_codes tool

Uses mock repositories following project testing conventions.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from unittest.mock import MagicMock

import allure
import pytest

from src.contexts.coding.core.entities import (
    Category,
    Code,
    Color,
    TextPosition,
    TextSegment,
)
from src.contexts.coding.interface.mcp_tools import CodingTools
from src.contexts.coding.interface.tool_definitions import ToolDefinition, ToolParameter
from src.shared.common.types import CategoryId, CodeId, SegmentId, SourceId

pytestmark = [
    pytest.mark.unit,
    allure.epic("QualCoder v2"),
    allure.feature("Coding MCP Tools"),
]


# ============================================================
# Mock Repositories
# ============================================================


class MockCodeRepository:
    """Mock code repository for testing."""

    def __init__(self, codes: list[Code] | None = None):
        self._codes: dict[int, Code] = {}
        for code in codes or []:
            self._codes[code.id.value] = code

    def get_all(self) -> list[Code]:
        return list(self._codes.values())

    def get_by_id(self, code_id: CodeId) -> Code | None:
        return self._codes.get(code_id.value)

    def get_by_category(self, category_id: CategoryId) -> list[Code]:
        return [c for c in self._codes.values() if c.category_id == category_id]

    def save(self, code: Code) -> None:
        self._codes[code.id.value] = code

    def delete(self, code_id: CodeId) -> None:
        self._codes.pop(code_id.value, None)


class MockCategoryRepository:
    """Mock category repository for testing."""

    def __init__(self, categories: list[Category] | None = None):
        self._categories: dict[int, Category] = {}
        for cat in categories or []:
            self._categories[cat.id.value] = cat

    def get_all(self) -> list[Category]:
        return list(self._categories.values())

    def get_by_id(self, category_id: CategoryId) -> Category | None:
        return self._categories.get(category_id.value)

    def save(self, category: Category) -> None:
        self._categories[category.id.value] = category

    def delete(self, category_id: CategoryId) -> None:
        self._categories.pop(category_id.value, None)


class MockSegmentRepository:
    """Mock segment repository for testing."""

    def __init__(self, segments: list[TextSegment] | None = None):
        self._segments: dict[int, TextSegment] = {}
        for seg in segments or []:
            self._segments[seg.id.value] = seg
        self._next_id = 1000

    def get_all(self) -> list[TextSegment]:
        return list(self._segments.values())

    def get_by_id(self, segment_id: SegmentId) -> TextSegment | None:
        return self._segments.get(segment_id.value)

    def get_by_source(self, source_id: SourceId) -> list[TextSegment]:
        return [s for s in self._segments.values() if s.source_id == source_id]

    def get_by_code(self, code_id: CodeId) -> list[TextSegment]:
        return [s for s in self._segments.values() if s.code_id == code_id]

    def save(self, segment: TextSegment) -> None:
        self._segments[segment.id.value] = segment

    def delete(self, segment_id: SegmentId) -> None:
        self._segments.pop(segment_id.value, None)

    def delete_by_code(self, code_id: CodeId) -> int:
        to_delete = [
            s.id.value for s in self._segments.values() if s.code_id == code_id
        ]
        for sid in to_delete:
            del self._segments[sid]
        return len(to_delete)

    def reassign_code(self, from_code_id: CodeId, to_code_id: CodeId) -> int:
        count = 0
        for seg in list(self._segments.values()):
            if seg.code_id == from_code_id:
                # Create new segment with updated code_id
                new_seg = TextSegment(
                    id=seg.id,
                    source_id=seg.source_id,
                    code_id=to_code_id,
                    position=seg.position,
                    selected_text=seg.selected_text,
                    memo=seg.memo,
                    importance=seg.importance,
                )
                self._segments[seg.id.value] = new_seg
                count += 1
        return count


@dataclass
class MockCodingContext:
    """Mock coding context with repositories."""

    code_repo: MockCodeRepository = field(default_factory=MockCodeRepository)
    category_repo: MockCategoryRepository = field(
        default_factory=MockCategoryRepository
    )
    segment_repo: MockSegmentRepository = field(default_factory=MockSegmentRepository)


@dataclass
class MockContext:
    """Mock context implementing CodingToolsContext protocol."""

    coding_context: MockCodingContext = field(default_factory=MockCodingContext)
    event_bus: Any = field(default_factory=MagicMock)


# ============================================================
# Fixtures
# ============================================================


@pytest.fixture
def sample_codes() -> list[Code]:
    """Create sample codes for testing."""
    return [
        Code(
            id=CodeId(value=1),
            name="Theme",
            color=Color(255, 0, 0),
            memo="Main themes",
        ),
        Code(
            id=CodeId(value=2),
            name="Challenge",
            color=Color(0, 255, 0),
            memo=None,
        ),
        Code(
            id=CodeId(value=3),
            name="Positive",
            color=Color(0, 0, 255),
            memo="Positive experiences",
            category_id=CategoryId(value=1),
        ),
    ]


@pytest.fixture
def sample_categories() -> list[Category]:
    """Create sample categories for testing."""
    return [
        Category(id=CategoryId(value=1), name="Emotions"),
        Category(id=CategoryId(value=2), name="Topics"),
    ]


@pytest.fixture
def sample_segments() -> list[TextSegment]:
    """Create sample segments for testing."""
    return [
        TextSegment(
            id=SegmentId(value=101),
            source_id=SourceId(value=1),
            code_id=CodeId(value=1),
            position=TextPosition(start=0, end=50),
            selected_text="This is a sample text segment",
            memo="Important finding",
            importance=2,
        ),
        TextSegment(
            id=SegmentId(value=102),
            source_id=SourceId(value=1),
            code_id=CodeId(value=2),
            position=TextPosition(start=100, end=150),
            selected_text="Another segment",
            memo=None,
            importance=0,
        ),
        TextSegment(
            id=SegmentId(value=103),
            source_id=SourceId(value=2),
            code_id=CodeId(value=1),
            position=TextPosition(start=0, end=30),
            selected_text="Segment in another source",
            memo=None,
            importance=1,
        ),
    ]


@pytest.fixture
def mock_context(
    sample_codes: list[Code],
    sample_categories: list[Category],
    sample_segments: list[TextSegment],
) -> MockContext:
    """Create mock context with sample data."""
    coding_ctx = MockCodingContext(
        code_repo=MockCodeRepository(sample_codes),
        category_repo=MockCategoryRepository(sample_categories),
        segment_repo=MockSegmentRepository(sample_segments),
    )
    return MockContext(coding_context=coding_ctx)


@pytest.fixture
def coding_tools(mock_context: MockContext) -> CodingTools:
    """Create CodingTools instance with mock context."""
    return CodingTools(ctx=mock_context)


@pytest.fixture
def empty_context() -> MockContext:
    """Create empty mock context with no data."""
    return MockContext(coding_context=MockCodingContext())


# ============================================================
# ToolDefinition and ToolParameter Tests
# ============================================================


@allure.story("Tool Schema")
class TestToolDefinition:
    """Tests for ToolDefinition schema generation."""

    def test_to_schema_empty_parameters(self) -> None:
        """Tool with no parameters generates correct schema."""
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

    def test_to_schema_with_required_parameter(self) -> None:
        """Tool with required parameter generates correct schema."""
        tool = ToolDefinition(
            name="get_item",
            description="Get an item by ID",
            parameters=(
                ToolParameter(
                    name="item_id",
                    type="integer",
                    description="The item ID",
                    required=True,
                ),
            ),
        )

        schema = tool.to_schema()

        assert "item_id" in schema["inputSchema"]["properties"]
        assert schema["inputSchema"]["properties"]["item_id"]["type"] == "integer"
        assert "item_id" in schema["inputSchema"]["required"]

    def test_to_schema_with_optional_parameter(self) -> None:
        """Tool with optional parameter generates correct schema."""
        tool = ToolDefinition(
            name="search",
            description="Search items",
            parameters=(
                ToolParameter(
                    name="limit",
                    type="integer",
                    description="Max results",
                    required=False,
                    default=10,
                ),
            ),
        )

        schema = tool.to_schema()

        assert "limit" in schema["inputSchema"]["properties"]
        assert schema["inputSchema"]["properties"]["limit"]["default"] == 10
        assert "limit" not in schema["inputSchema"]["required"]

    def test_to_schema_with_array_parameter(self) -> None:
        """Tool with array parameter includes items schema."""
        tool = ToolDefinition(
            name="batch",
            description="Batch operation",
            parameters=(
                ToolParameter(
                    name="operations",
                    type="array",
                    description="List of operations",
                    required=True,
                    items={"type": "object", "properties": {"id": {"type": "integer"}}},
                ),
            ),
        )

        schema = tool.to_schema()

        assert schema["inputSchema"]["properties"]["operations"]["items"] == {
            "type": "object",
            "properties": {"id": {"type": "integer"}},
        }


# ============================================================
# CodingTools Initialization Tests
# ============================================================


@allure.story("Initialization")
class TestCodingToolsInit:
    """Tests for CodingTools initialization."""

    def test_init_with_context(self, mock_context: MockContext) -> None:
        """CodingTools initializes with valid context."""
        tools = CodingTools(ctx=mock_context)

        # Verify tools is properly initialized (no longer exposes _ctx)
        assert tools is not None
        assert tools.get_tool_names() is not None

    def test_init_raises_on_none_context(self) -> None:
        """CodingTools raises ValueError on None context."""
        with pytest.raises(ValueError, match="ctx is required"):
            CodingTools(ctx=None)  # type: ignore


# ============================================================
# get_tool_schemas Tests
# ============================================================


@allure.story("Tool Schema")
class TestGetToolSchemas:
    """Tests for get_tool_schemas method."""

    def test_returns_list_of_schemas(self, coding_tools: CodingTools) -> None:
        """get_tool_schemas returns list of tool schemas."""
        schemas = coding_tools.get_tool_schemas()

        assert isinstance(schemas, list)
        assert len(schemas) > 0

    def test_all_schemas_have_required_fields(self, coding_tools: CodingTools) -> None:
        """All tool schemas have name, description, and inputSchema."""
        schemas = coding_tools.get_tool_schemas()

        for schema in schemas:
            assert "name" in schema
            assert "description" in schema
            assert "inputSchema" in schema
            assert schema["inputSchema"]["type"] == "object"

    def test_includes_batch_apply_codes_tool(self, coding_tools: CodingTools) -> None:
        """Schemas include batch_apply_codes tool."""
        schemas = coding_tools.get_tool_schemas()
        names = [s["name"] for s in schemas]

        assert "batch_apply_codes" in names

    def test_includes_list_codes_tool(self, coding_tools: CodingTools) -> None:
        """Schemas include list_codes tool."""
        schemas = coding_tools.get_tool_schemas()
        names = [s["name"] for s in schemas]

        assert "list_codes" in names

    def test_includes_get_code_tool(self, coding_tools: CodingTools) -> None:
        """Schemas include get_code tool."""
        schemas = coding_tools.get_tool_schemas()
        names = [s["name"] for s in schemas]

        assert "get_code" in names

    def test_includes_list_segments_tool(self, coding_tools: CodingTools) -> None:
        """Schemas include list_segments_for_source tool."""
        schemas = coding_tools.get_tool_schemas()
        names = [s["name"] for s in schemas]

        assert "list_segments_for_source" in names


# ============================================================
# get_tool_names Tests
# ============================================================


@allure.story("Tool Schema")
class TestGetToolNames:
    """Tests for get_tool_names method."""

    def test_returns_list_of_names(self, coding_tools: CodingTools) -> None:
        """get_tool_names returns list of tool names."""
        names = coding_tools.get_tool_names()

        assert isinstance(names, list)
        # Core tools + AI-assisted tools (QC-028.07, QC-028.08, QC-029.07, QC-029.08)
        assert (
            len(names) >= 4
        )  # At minimum: batch_apply_codes, list_codes, get_code, list_segments
        assert "batch_apply_codes" in names
        assert "list_codes" in names

    def test_names_match_schemas(self, coding_tools: CodingTools) -> None:
        """Tool names match schema names."""
        names = set(coding_tools.get_tool_names())
        schema_names = {s["name"] for s in coding_tools.get_tool_schemas()}

        assert names == schema_names


# ============================================================
# execute Tests - Unknown Tool
# ============================================================


@allure.story("Tool Dispatching")
class TestExecuteUnknownTool:
    """Tests for execute method with unknown tools."""

    def test_returns_failure_for_unknown_tool(self, coding_tools: CodingTools) -> None:
        """execute returns failure for unknown tool name."""
        result = coding_tools.execute("nonexistent_tool", {})

        assert result["success"] is False
        assert result["error_code"] == "TOOL_NOT_FOUND"
        assert "nonexistent_tool" in result["error"]

    def test_suggests_available_tools(self, coding_tools: CodingTools) -> None:
        """execute suggests available tools on unknown tool."""
        result = coding_tools.execute("nonexistent_tool", {})

        assert "suggestions" in result
        suggestions = result["suggestions"]
        assert any("list_codes" in s for s in suggestions)


# ============================================================
# list_codes Tool Tests
# ============================================================


@allure.story("list_codes Tool")
class TestListCodesTool:
    """Tests for list_codes tool."""

    def test_returns_all_codes(self, coding_tools: CodingTools) -> None:
        """list_codes returns all codes."""
        result = coding_tools.execute("list_codes", {})

        assert result["success"] is True
        assert "data" in result
        assert len(result["data"]) == 3

    def test_returns_empty_list_when_no_codes(self, empty_context: MockContext) -> None:
        """list_codes returns empty list when no codes exist."""
        tools = CodingTools(ctx=empty_context)

        result = tools.execute("list_codes", {})

        assert result["success"] is True
        assert result["data"] == []

    def test_returns_code_with_correct_attributes(
        self, coding_tools: CodingTools
    ) -> None:
        """list_codes returns codes with expected attributes (serialized as dicts)."""
        result = coding_tools.execute("list_codes", {})

        assert result["success"] is True
        codes = result["data"]
        # Find the Theme code (now serialized as dict)
        theme_code = next((c for c in codes if c["name"] == "Theme"), None)
        assert theme_code is not None
        assert theme_code["id"] == 1
        assert theme_code["color"] == "#ff0000"  # Serialized as hex


# ============================================================
# get_code Tool Tests
# ============================================================


@allure.story("get_code Tool")
class TestGetCodeTool:
    """Tests for get_code tool."""

    def test_returns_code_by_id(self, coding_tools: CodingTools) -> None:
        """get_code returns code by ID (serialized as dict)."""
        result = coding_tools.execute("get_code", {"code_id": 1})

        assert result["success"] is True
        code = result["data"]
        # Data is serialized to JSON-compatible dict
        assert code["id"] == 1
        assert code["name"] == "Theme"

    def test_returns_failure_for_missing_code_id(
        self, coding_tools: CodingTools
    ) -> None:
        """get_code returns failure when code_id is missing."""
        result = coding_tools.execute("get_code", {})

        assert result["success"] is False
        assert result["error_code"] == "CODE_NOT_FOUND/MISSING_PARAM"

    def test_returns_failure_for_nonexistent_code(
        self, coding_tools: CodingTools
    ) -> None:
        """get_code returns failure for nonexistent code."""
        result = coding_tools.execute("get_code", {"code_id": 999})

        assert result["success"] is False
        assert result["error_code"] == "CODE_NOT_FOUND"

    def test_returns_code_with_category(self, coding_tools: CodingTools) -> None:
        """get_code returns code with category info (serialized as dict)."""
        result = coding_tools.execute("get_code", {"code_id": 3})

        assert result["success"] is True
        code = result["data"]
        # Data is serialized to JSON-compatible dict
        assert code["category_id"] == 1


# ============================================================
# list_segments_for_source Tool Tests
# ============================================================


@allure.story("list_segments_for_source Tool")
class TestListSegmentsTool:
    """Tests for list_segments_for_source tool."""

    def test_returns_segments_for_source(self, coding_tools: CodingTools) -> None:
        """list_segments_for_source returns segments for given source."""
        result = coding_tools.execute("list_segments_for_source", {"source_id": 1})

        assert result["success"] is True
        segments = result["data"]
        assert len(segments) == 2  # Source 1 has 2 segments

    def test_returns_failure_for_missing_source_id(
        self, coding_tools: CodingTools
    ) -> None:
        """list_segments_for_source returns failure when source_id is missing."""
        result = coding_tools.execute("list_segments_for_source", {})

        assert result["success"] is False
        assert result["error_code"] == "SEGMENTS_NOT_LISTED/MISSING_PARAM"

    def test_returns_empty_list_for_source_with_no_segments(
        self, coding_tools: CodingTools
    ) -> None:
        """list_segments_for_source returns empty list when source has no segments."""
        result = coding_tools.execute("list_segments_for_source", {"source_id": 999})

        assert result["success"] is True
        assert result["data"] == []

    def test_segment_has_expected_attributes(self, coding_tools: CodingTools) -> None:
        """Segments have expected attributes (serialized as dicts)."""
        result = coding_tools.execute("list_segments_for_source", {"source_id": 1})

        assert result["success"] is True
        segments = result["data"]
        segment = segments[0]
        # Segments are serialized to JSON-compatible dicts
        assert "id" in segment
        assert "source_id" in segment
        assert "code_id" in segment
        assert "start_position" in segment
        assert "end_position" in segment
        assert "selected_text" in segment


# ============================================================
# batch_apply_codes Tool Tests
# ============================================================


@allure.story("batch_apply_codes Tool")
class TestBatchApplyCodesTool:
    """Tests for batch_apply_codes tool."""

    def test_returns_failure_for_missing_operations(
        self, coding_tools: CodingTools
    ) -> None:
        """batch_apply_codes returns failure when operations is missing."""
        result = coding_tools.execute("batch_apply_codes", {})

        assert result["success"] is False
        assert result["error_code"] == "BATCH_APPLY_CODES/MISSING_PARAM"

    def test_returns_failure_for_empty_operations(
        self, coding_tools: CodingTools
    ) -> None:
        """batch_apply_codes returns failure for empty operations array."""
        result = coding_tools.execute("batch_apply_codes", {"operations": []})

        assert result["success"] is False
        assert result["error_code"] == "BATCH_APPLY_CODES/EMPTY_BATCH"

    def test_returns_failure_for_invalid_operation(
        self, coding_tools: CodingTools
    ) -> None:
        """batch_apply_codes returns failure for malformed operation."""
        result = coding_tools.execute(
            "batch_apply_codes",
            {
                "operations": [
                    {"code_id": 1}  # Missing required fields
                ]
            },
        )

        assert result["success"] is False
        assert result["error_code"] == "BATCH_APPLY_CODES/INVALID_OPERATION"
        assert "index 0" in result["error"]

    def test_applies_single_code_successfully(self, mock_context: MockContext) -> None:
        """batch_apply_codes applies single code successfully."""
        tools = CodingTools(ctx=mock_context)

        result = tools.execute(
            "batch_apply_codes",
            {
                "operations": [
                    {
                        "code_id": 1,
                        "source_id": 1,
                        "start_position": 200,
                        "end_position": 250,
                    }
                ]
            },
        )

        assert result["success"] is True
        assert result["data"]["total"] == 1
        assert result["data"]["succeeded"] == 1
        assert result["data"]["failed"] == 0
        assert result["data"]["all_succeeded"] is True

    def test_applies_multiple_codes_successfully(
        self, mock_context: MockContext
    ) -> None:
        """batch_apply_codes applies multiple codes successfully."""
        tools = CodingTools(ctx=mock_context)

        result = tools.execute(
            "batch_apply_codes",
            {
                "operations": [
                    {
                        "code_id": 1,
                        "source_id": 1,
                        "start_position": 200,
                        "end_position": 250,
                    },
                    {
                        "code_id": 2,
                        "source_id": 1,
                        "start_position": 300,
                        "end_position": 350,
                    },
                ]
            },
        )

        assert result["success"] is True
        assert result["data"]["total"] == 2
        assert result["data"]["succeeded"] == 2

    def test_includes_memo_in_operation(self, mock_context: MockContext) -> None:
        """batch_apply_codes includes memo when provided."""
        tools = CodingTools(ctx=mock_context)

        result = tools.execute(
            "batch_apply_codes",
            {
                "operations": [
                    {
                        "code_id": 1,
                        "source_id": 1,
                        "start_position": 200,
                        "end_position": 250,
                        "memo": "Test memo",
                    }
                ]
            },
        )

        assert result["success"] is True

    def test_includes_importance_in_operation(self, mock_context: MockContext) -> None:
        """batch_apply_codes includes importance when provided."""
        tools = CodingTools(ctx=mock_context)

        result = tools.execute(
            "batch_apply_codes",
            {
                "operations": [
                    {
                        "code_id": 1,
                        "source_id": 1,
                        "start_position": 200,
                        "end_position": 250,
                        "importance": 2,
                    }
                ]
            },
        )

        assert result["success"] is True

    def test_returns_individual_results_on_success(
        self, mock_context: MockContext
    ) -> None:
        """batch_apply_codes returns individual results for each operation."""
        tools = CodingTools(ctx=mock_context)

        result = tools.execute(
            "batch_apply_codes",
            {
                "operations": [
                    {
                        "code_id": 1,
                        "source_id": 1,
                        "start_position": 200,
                        "end_position": 250,
                    }
                ]
            },
        )

        assert result["success"] is True
        results = result["data"]["results"]
        assert len(results) == 1
        assert results[0]["index"] == 0
        assert results[0]["success"] is True
        assert results[0]["segment_id"] is not None

    def test_handles_nonexistent_code(self, mock_context: MockContext) -> None:
        """batch_apply_codes handles operation with nonexistent code."""
        tools = CodingTools(ctx=mock_context)

        result = tools.execute(
            "batch_apply_codes",
            {
                "operations": [
                    {
                        "code_id": 999,  # Nonexistent
                        "source_id": 1,
                        "start_position": 200,
                        "end_position": 250,
                    }
                ]
            },
        )

        # Should fail because all operations failed
        assert result["success"] is False
        assert result["error_code"] == "BATCH_APPLY_CODES/ALL_FAILED"

    def test_publishes_events_on_success(self, mock_context: MockContext) -> None:
        """batch_apply_codes publishes events for successful operations."""
        tools = CodingTools(ctx=mock_context)

        tools.execute(
            "batch_apply_codes",
            {
                "operations": [
                    {
                        "code_id": 1,
                        "source_id": 1,
                        "start_position": 200,
                        "end_position": 250,
                    }
                ]
            },
        )

        # Verify event_bus.publish was called
        assert mock_context.event_bus.publish.called


# ============================================================
# Error Handling Tests
# ============================================================


@allure.story("Error Handling")
class TestErrorHandling:
    """Tests for error handling in tool execution."""

    def test_handles_exception_during_execution(
        self, mock_context: MockContext
    ) -> None:
        """execute catches exceptions and returns failure."""
        tools = CodingTools(ctx=mock_context)

        # Make code_repo.get_all raise an exception (access via coding_context)
        mock_context.coding_context.code_repo.get_all = MagicMock(
            side_effect=Exception("DB error")
        )

        result = tools.execute("list_codes", {})

        assert result["success"] is False
        assert result["error_code"] == "TOOL_EXECUTION_ERROR"
        assert "DB error" in result["error"]


# ============================================================
# Context Validation Tests
# ============================================================


@allure.story("Context Validation")
class TestContextValidation:
    """Tests for context validation in tools."""

    def test_batch_apply_returns_failure_when_code_repo_is_none(self) -> None:
        """batch_apply_codes returns failure when coding_context is None."""

        @dataclass
        class ContextWithNoCodingContext:
            coding_context: Any = None
            event_bus: Any = field(default_factory=MagicMock)

        ctx = ContextWithNoCodingContext()
        tools = CodingTools(ctx=ctx)

        result = tools.execute(
            "batch_apply_codes",
            {
                "operations": [
                    {
                        "code_id": 1,
                        "source_id": 1,
                        "start_position": 0,
                        "end_position": 10,
                    }
                ]
            },
        )

        assert result["success"] is False
        assert "NO_CONTEXT" in result["error_code"]

    def test_list_codes_returns_failure_when_code_repo_is_none(self) -> None:
        """list_codes returns failure when coding_context is None."""

        @dataclass
        class ContextWithNoCodingContext:
            coding_context: Any = None
            event_bus: Any = field(default_factory=MagicMock)

        ctx = ContextWithNoCodingContext()
        tools = CodingTools(ctx=ctx)

        result = tools.execute("list_codes", {})

        assert result["success"] is False
        assert "NO_CONTEXT" in result["error_code"]

    def test_get_code_returns_failure_when_code_repo_is_none(self) -> None:
        """get_code returns failure when coding_context is None."""

        @dataclass
        class ContextWithNoCodingContext:
            coding_context: Any = None
            event_bus: Any = field(default_factory=MagicMock)

        ctx = ContextWithNoCodingContext()
        tools = CodingTools(ctx=ctx)

        result = tools.execute("get_code", {"code_id": 1})

        assert result["success"] is False
        assert "NO_CONTEXT" in result["error_code"]

    def test_list_segments_returns_failure_when_segment_repo_is_none(self) -> None:
        """list_segments returns failure when coding_context is None."""

        @dataclass
        class ContextWithNoCodingContext:
            coding_context: Any = None
            event_bus: Any = field(default_factory=MagicMock)

        ctx = ContextWithNoCodingContext()
        tools = CodingTools(ctx=ctx)

        result = tools.execute("list_segments_for_source", {"source_id": 1})

        assert result["success"] is False
        assert "NO_CONTEXT" in result["error_code"]
