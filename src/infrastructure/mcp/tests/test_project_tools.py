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
from src.application.lifecycle import ProjectLifecycle
from src.application.state import ProjectState
from src.contexts.projects.core.entities import (
    Project,
    ProjectId,
    Source,
    SourceStatus,
    SourceType,
)
from src.contexts.shared import SourceId
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
def app_context(event_bus: EventBus):
    """Create an AppContext for testing."""
    from src.application.app_context import AppContext
    from src.contexts.settings.infra import UserSettingsRepository

    state = ProjectState()
    lifecycle = ProjectLifecycle()
    settings_repo = UserSettingsRepository()

    ctx = AppContext(
        event_bus=event_bus,
        state=state,
        lifecycle=lifecycle,
        settings_repo=settings_repo,
        signal_bridge=None,  # No Qt in tests
    )
    return ctx


@pytest.fixture
def project_tools(app_context) -> ProjectTools:
    """Create project tools for testing."""
    return ProjectTools(ctx=app_context)


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


def _setup_project(app_context, tmp_path: Path, name: str = "Test Project"):
    """Helper to set up a project in the AppContext state."""
    project_path = tmp_path / "test.qda"
    project = Project(
        id=ProjectId.from_path(project_path),
        name=name,
        path=project_path,
    )
    app_context.state.project = project
    return project_path


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

        assert len(schemas) == 5
        names = [s["name"] for s in schemas]
        assert "get_project_context" in names
        assert "list_sources" in names
        assert "read_source_content" in names
        assert "navigate_to_segment" in names
        assert "suggest_source_metadata" in names

    def test_get_tool_names(self, project_tools: ProjectTools):
        """get_tool_names returns list of tool names."""
        names = project_tools.get_tool_names()

        assert "get_project_context" in names
        assert "list_sources" in names
        assert "read_source_content" in names
        assert "navigate_to_segment" in names
        assert "suggest_source_metadata" in names


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
        app_context,
        project_tools: ProjectTools,
        tmp_path: Path,
    ):
        """Returns project info when a project is open."""
        _setup_project(app_context, tmp_path, "Test Project")

        result = project_tools.execute("get_project_context", {})

        assert isinstance(result, Success)
        context = result.unwrap()
        assert context["project_open"] is True
        assert context["project_name"] == "Test Project"
        assert "test.qda" in context["project_path"]

    def test_returns_source_count(
        self,
        app_context,
        project_tools: ProjectTools,
        sample_source: Source,
        tmp_path: Path,
    ):
        """Returns source count when project has sources."""
        _setup_project(app_context, tmp_path, "Test")

        # Add a source to state
        app_context.state.add_source(sample_source)

        result = project_tools.execute("get_project_context", {})

        assert isinstance(result, Success)
        context = result.unwrap()
        assert context["source_count"] == 1


class TestListSources:
    """Tests for listing sources."""

    def test_returns_empty_list_when_no_sources(
        self,
        app_context,
        project_tools: ProjectTools,
        tmp_path: Path,
    ):
        """Returns empty list when project has no sources."""
        _setup_project(app_context, tmp_path, "Test")

        result = project_tools.execute("list_sources", {})

        assert isinstance(result, Success)
        data = result.unwrap()
        assert data["count"] == 0
        assert data["sources"] == []

    def test_returns_sources_with_details(
        self,
        app_context,
        project_tools: ProjectTools,
        sample_source: Source,
        tmp_path: Path,
    ):
        """Returns source details."""
        _setup_project(app_context, tmp_path, "Test")
        app_context.state.add_source(sample_source)

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
        app_context,
        project_tools: ProjectTools,
        tmp_path: Path,
    ):
        """Filters sources by type."""
        _setup_project(app_context, tmp_path, "Test")

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

        app_context.state.add_source(text_source)
        app_context.state.add_source(audio_source)

        # Filter by text
        result = project_tools.execute("list_sources", {"source_type": "text"})

        assert isinstance(result, Success)
        data = result.unwrap()
        assert data["count"] == 1
        assert data["sources"][0]["type"] == "text"

    def test_returns_source_metadata(
        self,
        app_context,
        project_tools: ProjectTools,
        tmp_path: Path,
    ):
        """AC #3: Returns source metadata (memo, file_size, origin)."""
        _setup_project(app_context, tmp_path, "Test")

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
        app_context.state.add_source(source_with_metadata)

        result = project_tools.execute("list_sources", {})

        assert isinstance(result, Success)
        source = result.unwrap()["sources"][0]
        assert source["memo"] == "Important interview with participant"
        assert source["file_size"] == 1024
        assert source["origin"] == "external"

    def test_returns_coding_status(
        self,
        app_context,
        project_tools: ProjectTools,
        tmp_path: Path,
    ):
        """AC #4: Returns coding status per source (code_count, status)."""
        _setup_project(app_context, tmp_path, "Test")

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
        app_context.state.add_source(coded_source)

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
        app_context,
        project_tools: ProjectTools,
        tmp_path: Path,
    ):
        """Fails when source doesn't exist."""
        _setup_project(app_context, tmp_path, "Test")

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
        app_context,
        project_tools: ProjectTools,
        sample_source: Source,
        tmp_path: Path,
    ):
        """Successfully navigates to segment."""
        _setup_project(app_context, tmp_path, "Test")
        app_context.state.add_source(sample_source)

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
        app_context,
        project_tools: ProjectTools,
        sample_source: Source,
        tmp_path: Path,
    ):
        """Defaults highlight to True when not specified."""
        _setup_project(app_context, tmp_path, "Test")
        app_context.state.add_source(sample_source)

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
        app_context,
        project_tools: ProjectTools,
        tmp_path: Path,
    ):
        """AC #1: Agent can get text content of a source."""
        _setup_project(app_context, tmp_path, "Test")

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
        app_context.state.add_source(source)

        result = project_tools.execute("read_source_content", {"source_id": 1})

        assert isinstance(result, Success)
        data = result.unwrap()
        assert data["source_id"] == 1
        assert data["content"] == "Hello World. This is test content."
        assert data["start_pos"] == 0
        assert data["end_pos"] == 34

    def test_returns_content_range(
        self,
        app_context,
        project_tools: ProjectTools,
        tmp_path: Path,
    ):
        """AC #2: Agent can get content by position range."""
        _setup_project(app_context, tmp_path, "Test")

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
        app_context.state.add_source(source)

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
        app_context,
        project_tools: ProjectTools,
        tmp_path: Path,
    ):
        """AC #3: Agent receives content with position markers."""
        _setup_project(app_context, tmp_path, "Test")

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
        app_context.state.add_source(source)

        result = project_tools.execute("read_source_content", {"source_id": 1})

        assert isinstance(result, Success)
        data = result.unwrap()
        assert data["total_length"] == 31  # "Line one.\nLine two.\nLine three."
        assert data["start_pos"] == 0
        assert data["end_pos"] == 31

    def test_paginates_large_content(
        self,
        app_context,
        project_tools: ProjectTools,
        tmp_path: Path,
    ):
        """AC #4: Large sources are paginated."""
        _setup_project(app_context, tmp_path, "Test")

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
        app_context.state.add_source(source)

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
        app_context,
        project_tools: ProjectTools,
        tmp_path: Path,
    ):
        """Returns failure for non-existent source."""
        _setup_project(app_context, tmp_path, "Test")

        result = project_tools.execute("read_source_content", {"source_id": 999})

        assert isinstance(result, Failure)
        assert "not found" in result.failure().lower()


class TestSuggestSourceMetadata:
    """Tests for QC-027.10: Agent can suggest source metadata."""

    def test_tool_has_schema(self):
        """suggest_source_metadata tool has valid schema."""
        from src.infrastructure.mcp.project_tools import suggest_source_metadata_tool

        schema = suggest_source_metadata_tool.to_schema()

        assert schema["name"] == "suggest_source_metadata"
        props = schema["inputSchema"]["properties"]
        assert "source_id" in props
        assert "language" in props
        assert "topics" in props
        assert "organization_suggestion" in props

    def test_suggests_language(
        self,
        app_context,
        project_tools: ProjectTools,
        tmp_path: Path,
    ):
        """AC #1: Agent can detect/suggest document language."""
        _setup_project(app_context, tmp_path, "Test")

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
            fulltext="This is English text.",
        )
        app_context.state.add_source(source)

        result = project_tools.execute(
            "suggest_source_metadata",
            {
                "source_id": 1,
                "language": "en",
            },
        )

        assert isinstance(result, Success)
        data = result.unwrap()
        assert data["suggested"]["language"] == "en"

    def test_suggests_topics(
        self,
        app_context,
        project_tools: ProjectTools,
        tmp_path: Path,
    ):
        """AC #2: Agent can extract/suggest key topics."""
        _setup_project(app_context, tmp_path, "Test")

        source = Source(
            id=SourceId(value=1),
            name="interview.txt",
            source_type=SourceType.TEXT,
            status=SourceStatus.READY,
            file_path=Path("/tmp/interview.txt"),
            origin="internal",
            memo=None,
            code_count=0,
            case_ids=(),
            fulltext="Interview about healthcare and technology.",
        )
        app_context.state.add_source(source)

        result = project_tools.execute(
            "suggest_source_metadata",
            {
                "source_id": 1,
                "topics": ["healthcare", "technology", "interviews"],
            },
        )

        assert isinstance(result, Success)
        data = result.unwrap()
        assert "healthcare" in data["suggested"]["topics"]
        assert "technology" in data["suggested"]["topics"]

    def test_suggests_organization(
        self,
        app_context,
        project_tools: ProjectTools,
        tmp_path: Path,
    ):
        """AC #3: Agent can suggest source organization."""
        _setup_project(app_context, tmp_path, "Test")

        source = Source(
            id=SourceId(value=1),
            name="interview_001.txt",
            source_type=SourceType.TEXT,
            status=SourceStatus.READY,
            file_path=Path("/tmp/interview_001.txt"),
            origin="internal",
            memo=None,
            code_count=0,
            case_ids=(),
            fulltext="Interview with participant about health.",
        )
        app_context.state.add_source(source)

        result = project_tools.execute(
            "suggest_source_metadata",
            {
                "source_id": 1,
                "organization_suggestion": "Group with other health interviews",
            },
        )

        assert isinstance(result, Success)
        data = result.unwrap()
        assert "health interviews" in data["suggested"]["organization_suggestion"]

    def test_returns_pending_status(
        self,
        app_context,
        project_tools: ProjectTools,
        tmp_path: Path,
    ):
        """AC #4: Extraction results require researcher approval (pending status)."""
        _setup_project(app_context, tmp_path, "Test")

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
            fulltext="Sample document.",
        )
        app_context.state.add_source(source)

        result = project_tools.execute(
            "suggest_source_metadata",
            {
                "source_id": 1,
                "language": "en",
                "topics": ["research"],
            },
        )

        assert isinstance(result, Success)
        data = result.unwrap()
        assert data["status"] == "pending_approval"
        assert data["requires_approval"] is True

    def test_fails_for_nonexistent_source(
        self,
        app_context,
        project_tools: ProjectTools,
        tmp_path: Path,
    ):
        """Returns failure for non-existent source."""
        _setup_project(app_context, tmp_path, "Test")

        result = project_tools.execute(
            "suggest_source_metadata",
            {
                "source_id": 999,
                "language": "en",
            },
        )

        assert isinstance(result, Failure)
        assert "not found" in result.failure().lower()


class TestUnknownTool:
    """Tests for error handling."""

    def test_unknown_tool_returns_failure(self, project_tools: ProjectTools):
        """Unknown tool name returns failure."""
        result = project_tools.execute("unknown_tool", {})

        assert isinstance(result, Failure)
        assert "Unknown tool" in result.failure()
