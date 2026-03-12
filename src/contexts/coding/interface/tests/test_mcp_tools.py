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
    allure.feature("QC-028 Code Management"),
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
    session: Any = None


@dataclass
class NoCodingContext:
    """Mock context with no coding context (simulates missing project)."""

    coding_context: Any = None
    event_bus: Any = field(default_factory=MagicMock)
    session: Any = None


# ============================================================
# Fixtures
# ============================================================


@pytest.fixture
def sample_codes() -> list[Code]:
    """Create sample codes for testing."""
    return [
        Code(
            id=CodeId(value="1"),
            name="Theme",
            color=Color(255, 0, 0),
            memo="Main themes",
        ),
        Code(
            id=CodeId(value="2"),
            name="Challenge",
            color=Color(0, 255, 0),
            memo=None,
        ),
        Code(
            id=CodeId(value="3"),
            name="Positive",
            color=Color(0, 0, 255),
            memo="Positive experiences",
            category_id=CategoryId(value="1"),
        ),
    ]


@pytest.fixture
def sample_categories() -> list[Category]:
    """Create sample categories for testing."""
    return [
        Category(id=CategoryId(value="1"), name="Emotions"),
        Category(id=CategoryId(value="2"), name="Topics"),
    ]


@pytest.fixture
def sample_segments() -> list[TextSegment]:
    """Create sample segments for testing."""
    return [
        TextSegment(
            id=SegmentId(value="101"),
            source_id=SourceId(value="1"),
            code_id=CodeId(value="1"),
            position=TextPosition(start=0, end=50),
            selected_text="This is a sample text segment",
            memo="Important finding",
            importance=2,
        ),
        TextSegment(
            id=SegmentId(value="102"),
            source_id=SourceId(value="1"),
            code_id=CodeId(value="2"),
            position=TextPosition(start=100, end=150),
            selected_text="Another segment",
            memo=None,
            importance=0,
        ),
        TextSegment(
            id=SegmentId(value="103"),
            source_id=SourceId(value="2"),
            code_id=CodeId(value="1"),
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


@pytest.fixture
def no_coding_context() -> NoCodingContext:
    """Create mock context with coding_context=None."""
    return NoCodingContext()


# ============================================================
# ToolDefinition Tests
# ============================================================


@allure.story("QC-028.10 Tool Schema")
class TestToolDefinition:
    """Tests for ToolDefinition schema generation."""

    @pytest.mark.parametrize(
        "params, expected_required, expected_prop_checks",
        [
            pytest.param(
                (),
                [],
                {},
                id="empty_parameters",
            ),
            pytest.param(
                (ToolParameter(name="item_id", type="integer", description="The item ID", required=True),),
                ["item_id"],
                {"item_id": {"type": "integer"}},
                id="required_param",
            ),
            pytest.param(
                (ToolParameter(name="limit", type="integer", description="Max results", required=False, default=10),),
                [],
                {"limit": {"type": "integer", "default": 10}},
                id="optional_param_with_default",
            ),
            pytest.param(
                (ToolParameter(
                    name="operations", type="array", description="List of operations",
                    required=True, items={"type": "object", "properties": {"id": {"type": "integer"}}},
                ),),
                ["operations"],
                {"operations": {"type": "array", "items": {"type": "object", "properties": {"id": {"type": "integer"}}}}},
                id="array_param_with_items",
            ),
        ],
    )
    @allure.title("Generates correct schema for various parameter configurations")
    def test_to_schema_with_parameter_variants(
        self, params, expected_required, expected_prop_checks,
    ) -> None:
        """Tool parameters generate correct schema for empty, required, optional, and array types."""
        tool = ToolDefinition(
            name="test_tool",
            description="A test tool",
            parameters=params,
        )

        schema = tool.to_schema()

        assert schema["name"] == "test_tool"
        assert schema["description"] == "A test tool"
        assert schema["inputSchema"]["type"] == "object"
        assert schema["inputSchema"]["required"] == expected_required

        for param_name, checks in expected_prop_checks.items():
            assert param_name in schema["inputSchema"]["properties"]
            for key, value in checks.items():
                assert schema["inputSchema"]["properties"][param_name][key] == value


# ============================================================
# CodingTools Initialization and Schema Tests
# ============================================================


@allure.story("QC-028.10 Tool Schema")
class TestCodingToolsInit:
    """Tests for CodingTools initialization and schema methods."""

    @allure.title("Initializes with context, rejects None, and provides schemas")
    def test_init_schemas_and_names(self, mock_context: MockContext) -> None:
        """CodingTools initializes, rejects None, and provides consistent schemas and names."""
        tools = CodingTools(ctx=mock_context)
        assert tools is not None

        # Rejects None
        with pytest.raises(ValueError, match="ctx is required"):
            CodingTools(ctx=None)  # type: ignore

        # Schemas have required fields
        schemas = tools.get_tool_schemas()
        assert isinstance(schemas, list)
        assert len(schemas) > 0
        names = []
        for schema in schemas:
            assert "name" in schema
            assert "description" in schema
            assert "inputSchema" in schema
            names.append(schema["name"])

        for expected in ("batch_apply_codes", "list_codes", "get_code", "list_segments_for_source"):
            assert expected in names

        # Names match schemas
        tool_names = tools.get_tool_names()
        assert set(tool_names) == set(names)


# ============================================================
# Tool Execution Tests
# ============================================================


@allure.story("QC-028.14 Tool Dispatching")
class TestExecuteUnknownTool:
    """Tests for execute method with unknown tools."""

    @allure.title("Returns failure and suggestions for unknown tool")
    def test_returns_failure_and_suggestions_for_unknown_tool(
        self, coding_tools: CodingTools
    ) -> None:
        """execute returns failure with suggestions for unknown tool name."""
        result = coding_tools.execute("nonexistent_tool", {})

        assert result["success"] is False
        assert result["error_code"] == "TOOL_NOT_FOUND"
        assert "nonexistent_tool" in result["error"]
        assert "suggestions" in result
        assert any("list_codes" in s for s in result["suggestions"])


@allure.story("QC-028.14 Tool Dispatching")
class TestListCodesTool:
    """Tests for list_codes tool."""

    @allure.title("Returns all codes or empty list")
    def test_returns_codes_or_empty(
        self, coding_tools: CodingTools, empty_context: MockContext
    ) -> None:
        """list_codes returns all codes with attributes, or empty list when none exist."""
        result = coding_tools.execute("list_codes", {})
        assert result["success"] is True
        assert len(result["data"]) == 3
        theme_code = next((c for c in result["data"] if c["name"] == "Theme"), None)
        assert theme_code is not None
        assert theme_code["id"] == "1"
        assert theme_code["color"] == "#ff0000"

        # Empty
        empty_tools = CodingTools(ctx=empty_context)
        result = empty_tools.execute("list_codes", {})
        assert result["success"] is True
        assert result["data"] == []


@allure.story("QC-028.14 Tool Dispatching")
class TestGetCodeTool:
    """Tests for get_code tool."""

    @pytest.mark.parametrize(
        "args, expect_success, check_name, check_error_code",
        [
            pytest.param({"code_id": 1}, True, "Theme", None, id="code_without_category"),
            pytest.param({"code_id": 3}, True, "Positive", None, id="code_with_category"),
            pytest.param({}, False, None, "CODE_NOT_FOUND/MISSING_PARAM", id="missing_code_id"),
            pytest.param({"code_id": 999}, False, None, "CODE_NOT_FOUND/NOT_FOUND", id="nonexistent_code"),
        ],
    )
    @allure.title("Returns code by ID or failure for invalid input")
    def test_get_code(
        self, coding_tools: CodingTools,
        args: dict, expect_success: bool, check_name: str | None, check_error_code: str | None,
    ) -> None:
        """get_code returns code by ID or appropriate failure."""
        result = coding_tools.execute("get_code", args)

        assert result["success"] is expect_success
        if expect_success:
            assert result["data"]["name"] == check_name
        else:
            assert result["error_code"] == check_error_code


@allure.story("QC-028.14 Tool Dispatching")
class TestListSegmentsTool:
    """Tests for list_segments_for_source tool."""

    @allure.title("Returns segments, fails on missing param, returns empty for no-match")
    def test_list_segments_scenarios(self, coding_tools: CodingTools) -> None:
        """list_segments_for_source returns segments, fails on missing param, returns empty for no-match."""
        # Success with segments
        result = coding_tools.execute("list_segments_for_source", {"source_id": 1})
        assert result["success"] is True
        assert len(result["data"]) == 2
        for key in ("id", "source_id", "code_id", "start_position", "end_position", "selected_text"):
            assert key in result["data"][0]

        # Missing source_id
        result = coding_tools.execute("list_segments_for_source", {})
        assert result["success"] is False
        assert result["error_code"] == "SEGMENTS_NOT_LISTED/MISSING_PARAM"

        # No segments for source
        result = coding_tools.execute("list_segments_for_source", {"source_id": 999})
        assert result["success"] is True
        assert result["data"] == []


@allure.story("QC-028.14 Tool Dispatching")
class TestBatchApplyCodesTool:
    """Tests for batch_apply_codes tool."""

    @pytest.mark.parametrize(
        "args, expected_error_code, error_fragment",
        [
            pytest.param({}, "BATCH_APPLY_CODES/MISSING_PARAM", None, id="missing_operations"),
            pytest.param({"operations": []}, "BATCH_APPLY_CODES/EMPTY_BATCH", None, id="empty_operations"),
            pytest.param(
                {"operations": [{"code_id": 1}]},
                "BATCH_APPLY_CODES/INVALID_OPERATION", "index 0",
                id="malformed_operation",
            ),
        ],
    )
    @allure.title("Returns failure for invalid batch input")
    def test_returns_failure_for_invalid_input(
        self, coding_tools: CodingTools,
        args: dict, expected_error_code: str, error_fragment: str | None,
    ) -> None:
        """batch_apply_codes returns failure for missing, empty, or malformed operations."""
        result = coding_tools.execute("batch_apply_codes", args)
        assert result["success"] is False
        assert result["error_code"] == expected_error_code
        if error_fragment:
            assert error_fragment in result["error"]

    @allure.title("Applies codes successfully and publishes events")
    def test_applies_codes_and_publishes_events(self, mock_context: MockContext) -> None:
        """batch_apply_codes applies single and multiple codes, publishes events, and handles nonexistent codes."""
        tools = CodingTools(ctx=mock_context)

        # Single operation
        result = tools.execute(
            "batch_apply_codes",
            {"operations": [{"code_id": 1, "source_id": 1, "start_position": 200, "end_position": 250}]},
        )
        assert result["success"] is True
        assert result["data"]["total"] == 1
        assert result["data"]["succeeded"] == 1
        assert result["data"]["all_succeeded"] is True
        assert result["data"]["results"][0]["success"] is True
        assert mock_context.event_bus.publish.called

        # Multiple operations with optional fields
        result = tools.execute(
            "batch_apply_codes",
            {"operations": [
                {"code_id": 1, "source_id": 1, "start_position": 300, "end_position": 350, "memo": "Test memo"},
                {"code_id": 2, "source_id": 1, "start_position": 400, "end_position": 450, "importance": 2},
            ]},
        )
        assert result["success"] is True
        assert result["data"]["total"] == 2
        assert result["data"]["succeeded"] == 2

        # Nonexistent code
        result = tools.execute(
            "batch_apply_codes",
            {"operations": [{"code_id": 999, "source_id": 1, "start_position": 200, "end_position": 250}]},
        )
        assert result["success"] is False
        assert result["error_code"] == "BATCH_APPLY_CODES/ALL_FAILED"


# ============================================================
# Error Handling and Context Validation Tests
# ============================================================


@allure.story("QC-028.15 Error Handling")
class TestErrorHandlingAndContextValidation:
    """Tests for error handling and context validation."""

    @allure.title("Catches exceptions during execution")
    def test_handles_exception_during_execution(self, mock_context: MockContext) -> None:
        """execute catches exceptions and returns failure."""
        tools = CodingTools(ctx=mock_context)
        mock_context.coding_context.code_repo.get_all = MagicMock(
            side_effect=Exception("DB error")
        )

        result = tools.execute("list_codes", {})
        assert result["success"] is False
        assert result["error_code"] == "TOOL_EXECUTION_ERROR"
        assert "DB error" in result["error"]

    @pytest.mark.parametrize(
        "tool_name, args",
        [
            pytest.param("list_codes", {}, id="list_codes"),
            pytest.param("get_code", {"code_id": 1}, id="get_code"),
            pytest.param("list_segments_for_source", {"source_id": 1}, id="list_segments"),
            pytest.param(
                "batch_apply_codes",
                {"operations": [{"code_id": 1, "source_id": 1, "start_position": 0, "end_position": 10}]},
                id="batch_apply_codes",
            ),
        ],
    )
    @allure.title("Returns NO_CONTEXT failure when coding context is None")
    def test_returns_failure_when_coding_context_is_none(
        self, no_coding_context: NoCodingContext, tool_name: str, args: dict
    ) -> None:
        """All tools return NO_CONTEXT failure when coding_context is None."""
        tools = CodingTools(ctx=no_coding_context)
        result = tools.execute(tool_name, args)
        assert result["success"] is False
        assert "NO_CONTEXT" in result["error_code"]
