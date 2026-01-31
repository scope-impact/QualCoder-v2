"""
Tests for MCP Project Tools

Implements QC-026:
- AC #5: Agent can query current project context
- AC #6: Agent can navigate to a specific source or segment
"""

from pathlib import Path

import pytest
from returns.result import Failure, Success

from src.application.event_bus import EventBus
from src.application.projects.controller import (
    CreateProjectCommand,
    ProjectControllerImpl,
)
from src.domain.projects.entities import Source, SourceStatus, SourceType
from src.domain.shared.types import SourceId
from src.infrastructure.mcp.project_tools import (
    ProjectTools,
    get_project_context_tool,
    list_sources_tool,
    navigate_to_segment_tool,
    read_source_content_tool,
)


@pytest.fixture
def event_bus() -> EventBus:
    """Create an event bus for testing."""
    return EventBus(history_size=100)


@pytest.fixture
def project_controller(event_bus: EventBus) -> ProjectControllerImpl:
    """Create a project controller for testing."""
    return ProjectControllerImpl(
        event_bus=event_bus,
        source_repo=None,
        project_repo=None,
    )


@pytest.fixture
def project_tools(project_controller: ProjectControllerImpl) -> ProjectTools:
    """Create project tools for testing."""
    return ProjectTools(controller=project_controller)


@pytest.fixture
def sample_source() -> Source:
    """Create a sample source for testing."""
    return Source(
        id=SourceId(value=1),
        name="interview.txt",
        source_type=SourceType.TEXT,
        status=SourceStatus.READY,
        file_path=Path("/tmp/interview.txt"),
        origin="internal",
        memo=None,
        code_count=0,
        case_ids=(),
    )


class TestToolDefinitions:
    """Tests for tool schema definitions."""

    def test_get_project_context_tool_has_schema(self):
        """get_project_context tool has valid schema."""
        schema = get_project_context_tool.to_schema()

        assert schema["name"] == "get_project_context"
        assert "description" in schema
        assert "inputSchema" in schema

    def test_list_sources_tool_has_schema(self):
        """list_sources tool has valid schema."""
        schema = list_sources_tool.to_schema()

        assert schema["name"] == "list_sources"
        assert "source_type" in schema["inputSchema"]["properties"]

    def test_navigate_to_segment_tool_has_schema(self):
        """navigate_to_segment tool has required parameters."""
        schema = navigate_to_segment_tool.to_schema()

        assert schema["name"] == "navigate_to_segment"
        props = schema["inputSchema"]["properties"]
        assert "source_id" in props
        assert "start_pos" in props
        assert "end_pos" in props
        assert "highlight" in props

        # Required parameters
        required = schema["inputSchema"]["required"]
        assert "source_id" in required
        assert "start_pos" in required
        assert "end_pos" in required


class TestProjectToolsRegistration:
    """Tests for project tools registration."""

    def test_get_tool_schemas(self, project_tools: ProjectTools):
        """get_tool_schemas returns all tool schemas."""
        schemas = project_tools.get_tool_schemas()

        assert len(schemas) == 4
        names = [s["name"] for s in schemas]
        assert "get_project_context" in names
        assert "list_sources" in names
        assert "read_source_content" in names
        assert "navigate_to_segment" in names

    def test_get_tool_names(self, project_tools: ProjectTools):
        """get_tool_names returns list of tool names."""
        names = project_tools.get_tool_names()

        assert "get_project_context" in names
        assert "list_sources" in names
        assert "read_source_content" in names
        assert "navigate_to_segment" in names


class TestGetProjectContext:
    """Tests for AC #5: Agent can query current project context."""

    def test_returns_closed_when_no_project(self, project_tools: ProjectTools):
        """Returns project_open=False when no project is open."""
        result = project_tools.execute("get_project_context", {})

        assert isinstance(result, Success)
        context = result.unwrap()
        assert context["project_open"] is False

    def test_returns_project_info_when_open(
        self,
        project_controller: ProjectControllerImpl,
        project_tools: ProjectTools,
        tmp_path: Path,
    ):
        """Returns project info when a project is open."""
        # Create a project
        project_path = tmp_path / "test.qda"
        command = CreateProjectCommand(
            name="Test Project",
            path=str(project_path),
        )
        project_controller.create_project(command)

        result = project_tools.execute("get_project_context", {})

        assert isinstance(result, Success)
        context = result.unwrap()
        assert context["project_open"] is True
        assert context["project_name"] == "Test Project"
        assert "test.qda" in context["project_path"]

    def test_returns_source_count(
        self,
        project_controller: ProjectControllerImpl,
        project_tools: ProjectTools,
        sample_source: Source,
        tmp_path: Path,
    ):
        """Returns source count when project has sources."""
        # Create a project
        project_path = tmp_path / "test.qda"
        project_controller.create_project(
            CreateProjectCommand(
                name="Test",
                path=str(project_path),
            )
        )

        # Add a source manually (would normally use add_source command)
        project_controller._sources.append(sample_source)

        result = project_tools.execute("get_project_context", {})

        assert isinstance(result, Success)
        context = result.unwrap()
        assert context["source_count"] == 1


class TestListSources:
    """Tests for listing sources."""

    def test_returns_empty_list_when_no_sources(
        self,
        project_controller: ProjectControllerImpl,
        project_tools: ProjectTools,
        tmp_path: Path,
    ):
        """Returns empty list when project has no sources."""
        project_path = tmp_path / "test.qda"
        project_controller.create_project(
            CreateProjectCommand(
                name="Test",
                path=str(project_path),
            )
        )

        result = project_tools.execute("list_sources", {})

        assert isinstance(result, Success)
        data = result.unwrap()
        assert data["count"] == 0
        assert data["sources"] == []

    def test_returns_sources_with_details(
        self,
        project_controller: ProjectControllerImpl,
        project_tools: ProjectTools,
        sample_source: Source,
        tmp_path: Path,
    ):
        """Returns source details."""
        project_path = tmp_path / "test.qda"
        project_controller.create_project(
            CreateProjectCommand(
                name="Test",
                path=str(project_path),
            )
        )
        project_controller._sources.append(sample_source)

        result = project_tools.execute("list_sources", {})

        assert isinstance(result, Success)
        data = result.unwrap()
        assert data["count"] == 1
        source = data["sources"][0]
        assert source["id"] == 1
        assert source["name"] == "interview.txt"
        assert source["type"] == "text"

    def test_filters_by_source_type(
        self,
        project_controller: ProjectControllerImpl,
        project_tools: ProjectTools,
        tmp_path: Path,
    ):
        """Filters sources by type."""
        project_path = tmp_path / "test.qda"
        project_controller.create_project(
            CreateProjectCommand(
                name="Test",
                path=str(project_path),
            )
        )

        # Add text source
        text_source = Source(
            id=SourceId(value=1),
            name="doc.txt",
            source_type=SourceType.TEXT,
            status=SourceStatus.READY,
            file_path=Path("/tmp/doc.txt"),
            origin="internal",
            memo=None,
            code_count=0,
            case_ids=(),
        )

        # Add audio source
        audio_source = Source(
            id=SourceId(value=2),
            name="audio.mp3",
            source_type=SourceType.AUDIO,
            status=SourceStatus.READY,
            file_path=Path("/tmp/audio.mp3"),
            origin="internal",
            memo=None,
            code_count=0,
            case_ids=(),
        )

        project_controller._sources.extend([text_source, audio_source])

        # Filter by text
        result = project_tools.execute("list_sources", {"source_type": "text"})

        assert isinstance(result, Success)
        data = result.unwrap()
        assert data["count"] == 1
        assert data["sources"][0]["type"] == "text"

    def test_returns_source_metadata(
        self,
        project_controller: ProjectControllerImpl,
        project_tools: ProjectTools,
        tmp_path: Path,
    ):
        """AC #3: Returns source metadata (memo, file_size, origin)."""
        project_path = tmp_path / "test.qda"
        project_controller.create_project(
            CreateProjectCommand(
                name="Test",
                path=str(project_path),
            )
        )

        source_with_metadata = Source(
            id=SourceId(value=1),
            name="interview.txt",
            source_type=SourceType.TEXT,
            status=SourceStatus.CODED,
            file_path=Path("/tmp/interview.txt"),
            file_size=1024,
            origin="external",
            memo="Important interview with participant",
            code_count=5,
            case_ids=(),
        )
        project_controller._sources.append(source_with_metadata)

        result = project_tools.execute("list_sources", {})

        assert isinstance(result, Success)
        source = result.unwrap()["sources"][0]
        assert source["memo"] == "Important interview with participant"
        assert source["file_size"] == 1024
        assert source["origin"] == "external"

    def test_returns_coding_status(
        self,
        project_controller: ProjectControllerImpl,
        project_tools: ProjectTools,
        tmp_path: Path,
    ):
        """AC #4: Returns coding status per source (code_count, status)."""
        project_path = tmp_path / "test.qda"
        project_controller.create_project(
            CreateProjectCommand(
                name="Test",
                path=str(project_path),
            )
        )

        coded_source = Source(
            id=SourceId(value=1),
            name="coded_doc.txt",
            source_type=SourceType.TEXT,
            status=SourceStatus.CODED,
            file_path=Path("/tmp/coded_doc.txt"),
            origin="internal",
            memo=None,
            code_count=15,
            case_ids=(),
        )
        project_controller._sources.append(coded_source)

        result = project_tools.execute("list_sources", {})

        assert isinstance(result, Success)
        source = result.unwrap()["sources"][0]
        assert source["code_count"] == 15
        assert source["status"] == "coded"


class TestNavigateToSegment:
    """Tests for AC #6: Agent can navigate to a specific source or segment."""

    def test_fails_with_missing_source_id(self, project_tools: ProjectTools):
        """Fails when source_id is missing."""
        result = project_tools.execute(
            "navigate_to_segment",
            {
                "start_pos": 0,
                "end_pos": 100,
            },
        )

        assert isinstance(result, Failure)
        assert "source_id" in result.failure()

    def test_fails_with_missing_positions(self, project_tools: ProjectTools):
        """Fails when positions are missing."""
        result = project_tools.execute(
            "navigate_to_segment",
            {
                "source_id": 1,
            },
        )

        assert isinstance(result, Failure)
        assert "start_pos" in result.failure()

    def test_fails_for_nonexistent_source(
        self,
        project_controller: ProjectControllerImpl,
        project_tools: ProjectTools,
        tmp_path: Path,
    ):
        """Fails when source doesn't exist."""
        project_path = tmp_path / "test.qda"
        project_controller.create_project(
            CreateProjectCommand(
                name="Test",
                path=str(project_path),
            )
        )

        result = project_tools.execute(
            "navigate_to_segment",
            {
                "source_id": 999,
                "start_pos": 0,
                "end_pos": 100,
            },
        )

        assert isinstance(result, Failure)

    def test_navigates_to_segment_successfully(
        self,
        project_controller: ProjectControllerImpl,
        project_tools: ProjectTools,
        sample_source: Source,
        tmp_path: Path,
    ):
        """Successfully navigates to segment."""
        project_path = tmp_path / "test.qda"
        project_controller.create_project(
            CreateProjectCommand(
                name="Test",
                path=str(project_path),
            )
        )
        project_controller._sources.append(sample_source)

        result = project_tools.execute(
            "navigate_to_segment",
            {
                "source_id": 1,
                "start_pos": 50,
                "end_pos": 150,
                "highlight": True,
            },
        )

        assert isinstance(result, Success)
        data = result.unwrap()
        assert data["success"] is True
        assert data["navigated_to"]["source_id"] == 1
        assert data["navigated_to"]["start_pos"] == 50
        assert data["current_screen"] == "coding"

    def test_defaults_highlight_to_true(
        self,
        project_controller: ProjectControllerImpl,
        project_tools: ProjectTools,
        sample_source: Source,
        tmp_path: Path,
    ):
        """Defaults highlight to True when not specified."""
        project_path = tmp_path / "test.qda"
        project_controller.create_project(
            CreateProjectCommand(
                name="Test",
                path=str(project_path),
            )
        )
        project_controller._sources.append(sample_source)

        result = project_tools.execute(
            "navigate_to_segment",
            {
                "source_id": 1,
                "start_pos": 0,
                "end_pos": 100,
            },
        )

        assert isinstance(result, Success)
        data = result.unwrap()
        assert data["navigated_to"]["highlight"] is True


class TestReadSourceContent:
    """Tests for QC-027.09: Agent can read source content."""

    def test_tool_has_schema(self):
        """read_source_content tool has valid schema."""
        schema = read_source_content_tool.to_schema()

        assert schema["name"] == "read_source_content"
        props = schema["inputSchema"]["properties"]
        assert "source_id" in props
        assert "start_pos" in props
        assert "end_pos" in props
        assert "max_length" in props

    def test_returns_full_content(
        self,
        project_controller: ProjectControllerImpl,
        project_tools: ProjectTools,
        tmp_path: Path,
    ):
        """AC #1: Agent can get text content of a source."""
        project_path = tmp_path / "test.qda"
        project_controller.create_project(
            CreateProjectCommand(name="Test", path=str(project_path))
        )

        # Create source with content
        source = Source(
            id=SourceId(value=1),
            name="doc.txt",
            source_type=SourceType.TEXT,
            status=SourceStatus.READY,
            file_path=Path("/tmp/doc.txt"),
            origin="internal",
            memo=None,
            code_count=0,
            case_ids=(),
            fulltext="Hello World. This is test content.",
        )
        project_controller._sources.append(source)

        result = project_tools.execute("read_source_content", {"source_id": 1})

        assert isinstance(result, Success)
        data = result.unwrap()
        assert data["source_id"] == 1
        assert data["content"] == "Hello World. This is test content."
        assert data["start_pos"] == 0
        assert data["end_pos"] == 34

    def test_returns_content_range(
        self,
        project_controller: ProjectControllerImpl,
        project_tools: ProjectTools,
        tmp_path: Path,
    ):
        """AC #2: Agent can get content by position range."""
        project_path = tmp_path / "test.qda"
        project_controller.create_project(
            CreateProjectCommand(name="Test", path=str(project_path))
        )

        source = Source(
            id=SourceId(value=1),
            name="doc.txt",
            source_type=SourceType.TEXT,
            status=SourceStatus.READY,
            file_path=Path("/tmp/doc.txt"),
            origin="internal",
            memo=None,
            code_count=0,
            case_ids=(),
            fulltext="Hello World. This is test content.",
        )
        project_controller._sources.append(source)

        result = project_tools.execute(
            "read_source_content",
            {"source_id": 1, "start_pos": 0, "end_pos": 11},
        )

        assert isinstance(result, Success)
        data = result.unwrap()
        assert data["content"] == "Hello World"
        assert data["start_pos"] == 0
        assert data["end_pos"] == 11

    def test_returns_position_markers(
        self,
        project_controller: ProjectControllerImpl,
        project_tools: ProjectTools,
        tmp_path: Path,
    ):
        """AC #3: Agent receives content with position markers."""
        project_path = tmp_path / "test.qda"
        project_controller.create_project(
            CreateProjectCommand(name="Test", path=str(project_path))
        )

        source = Source(
            id=SourceId(value=1),
            name="doc.txt",
            source_type=SourceType.TEXT,
            status=SourceStatus.READY,
            file_path=Path("/tmp/doc.txt"),
            origin="internal",
            memo=None,
            code_count=0,
            case_ids=(),
            fulltext="Line one.\nLine two.\nLine three.",
        )
        project_controller._sources.append(source)

        result = project_tools.execute("read_source_content", {"source_id": 1})

        assert isinstance(result, Success)
        data = result.unwrap()
        assert data["total_length"] == 31  # "Line one.\nLine two.\nLine three."
        assert data["start_pos"] == 0
        assert data["end_pos"] == 31

    def test_paginates_large_content(
        self,
        project_controller: ProjectControllerImpl,
        project_tools: ProjectTools,
        tmp_path: Path,
    ):
        """AC #4: Large sources are paginated."""
        project_path = tmp_path / "test.qda"
        project_controller.create_project(
            CreateProjectCommand(name="Test", path=str(project_path))
        )

        # Create large content
        large_text = "A" * 10000
        source = Source(
            id=SourceId(value=1),
            name="large.txt",
            source_type=SourceType.TEXT,
            status=SourceStatus.READY,
            file_path=Path("/tmp/large.txt"),
            origin="internal",
            memo=None,
            code_count=0,
            case_ids=(),
            fulltext=large_text,
        )
        project_controller._sources.append(source)

        # Request with max_length
        result = project_tools.execute(
            "read_source_content",
            {"source_id": 1, "max_length": 1000},
        )

        assert isinstance(result, Success)
        data = result.unwrap()
        assert len(data["content"]) == 1000
        assert data["has_more"] is True
        assert data["total_length"] == 10000

    def test_fails_for_nonexistent_source(
        self,
        project_controller: ProjectControllerImpl,
        project_tools: ProjectTools,
        tmp_path: Path,
    ):
        """Returns failure for non-existent source."""
        project_path = tmp_path / "test.qda"
        project_controller.create_project(
            CreateProjectCommand(name="Test", path=str(project_path))
        )

        result = project_tools.execute("read_source_content", {"source_id": 999})

        assert isinstance(result, Failure)
        assert "not found" in result.failure().lower()


class TestUnknownTool:
    """Tests for error handling."""

    def test_unknown_tool_returns_failure(self, project_tools: ProjectTools):
        """Unknown tool name returns failure."""
        result = project_tools.execute("unknown_tool", {})

        assert isinstance(result, Failure)
        assert "Unknown tool" in result.failure()
