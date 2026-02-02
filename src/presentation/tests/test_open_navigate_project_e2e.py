from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import allure
import pytest
from returns.result import Failure, Success

if TYPE_CHECKING:
    from src.application.app_context import AppContext

pytestmark = [
    pytest.mark.e2e,
    allure.epic("QualCoder v2"),
    allure.feature("QC-026 Open & Navigate Project"),
]


@pytest.fixture
def app_context():
    from src.application.app_context import create_app_context, reset_app_context

    reset_app_context()
    ctx = create_app_context()
    ctx.start()
    yield ctx
    ctx.stop()
    reset_app_context()


@pytest.fixture
def temp_project_path(tmp_path: Path) -> Path:
    return tmp_path / "test_project.qda"


@pytest.fixture
def existing_project(app_context: AppContext, tmp_path: Path) -> Path:
    project_path = tmp_path / "existing_project.qda"
    result = app_context.create_project(name="Existing Project", path=str(project_path))
    assert isinstance(result, Success)
    app_context.close_project()
    return project_path


@allure.story("QC-026.01 Open Existing Project")
@allure.severity(allure.severity_level.CRITICAL)
class TestOpenExistingProject:
    @allure.title("AC #1: Researcher can open an existing project file")
    @allure.link("QC-026", name="Backlog Task")
    def test_open_existing_project_success(
        self, app_context: AppContext, existing_project: Path
    ):
        with allure.step("Open existing project file"):
            result = app_context.open_project(str(existing_project))

        with allure.step("Verify project opened successfully"):
            assert isinstance(result, Success)
            project = result.unwrap()
            assert project.name == "Existing Project"
            assert project.path == existing_project

        with allure.step("Verify app context has project"):
            assert app_context.has_project
            assert app_context.state.project is not None

    @allure.title("AC #1: Open project fails for non-existent file")
    @allure.severity(allure.severity_level.NORMAL)
    def test_open_nonexistent_project_fails(
        self, app_context: AppContext, tmp_path: Path
    ):
        nonexistent = tmp_path / "does_not_exist.qda"

        with allure.step("Attempt to open non-existent project"):
            result = app_context.open_project(str(nonexistent))

        with allure.step("Verify failure returned"):
            assert isinstance(result, Failure)

    @allure.title("AC #1: Open project validates database before opening")
    @allure.severity(allure.severity_level.NORMAL)
    def test_open_validates_database(self, app_context: AppContext, tmp_path: Path):
        from src.infrastructure.projects.project_repository import (
            SQLiteProjectRepository,
        )

        invalid_file = tmp_path / "invalid.qda"
        invalid_file.write_text("not a valid sqlite database")

        with allure.step("Verify file is not valid database"):
            repo = SQLiteProjectRepository()
            is_valid = repo.validate_database(invalid_file)
            assert not is_valid

    @allure.title("AC #1: Project contexts initialized after open")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_contexts_initialized_after_open(
        self, app_context: AppContext, existing_project: Path
    ):
        with allure.step("Open project"):
            result = app_context.open_project(str(existing_project))
            assert isinstance(result, Success)

        with allure.step("Verify bounded contexts are available"):
            assert app_context.sources_context is not None
            assert app_context.coding_context is not None
            assert app_context.cases_context is not None
            assert app_context.projects_context is not None


@allure.story("QC-026.02 Create New Project")
@allure.severity(allure.severity_level.CRITICAL)
class TestCreateNewProject:
    @allure.title("AC #2: Researcher can create a new project")
    @allure.link("QC-026", name="Backlog Task")
    def test_create_new_project_success(
        self, app_context: AppContext, temp_project_path: Path
    ):
        with allure.step("Create new project"):
            result = app_context.create_project(
                name="My Research Project", path=str(temp_project_path)
            )

        with allure.step("Verify project created successfully"):
            assert isinstance(result, Success)
            project = result.unwrap()
            assert project.name == "My Research Project"
            assert project.path == temp_project_path

        with allure.step("Verify database file exists"):
            assert temp_project_path.exists()
            assert temp_project_path.stat().st_size > 0

    @allure.title("AC #2: Create project fails if file already exists")
    @allure.severity(allure.severity_level.NORMAL)
    def test_create_project_existing_file_fails(
        self, app_context: AppContext, existing_project: Path
    ):
        with allure.step("Attempt to create project at existing path"):
            result = app_context.create_project(
                name="Duplicate Project", path=str(existing_project)
            )

        with allure.step("Verify failure returned"):
            assert isinstance(result, Failure)

    @allure.title("AC #2: Created project has valid schema")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_created_project_has_valid_schema(
        self, app_context: AppContext, temp_project_path: Path
    ):
        from src.infrastructure.projects.project_repository import (
            SQLiteProjectRepository,
        )

        with allure.step("Create new project"):
            result = app_context.create_project(
                name="Schema Test", path=str(temp_project_path)
            )
            assert isinstance(result, Success)

        with allure.step("Validate database schema"):
            repo = SQLiteProjectRepository()
            is_valid = repo.validate_database(temp_project_path)
            assert is_valid

    @allure.title("AC #2: Project can be opened after creation")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_project_openable_after_creation(
        self, app_context: AppContext, temp_project_path: Path
    ):
        with allure.step("Create new project"):
            create_result = app_context.create_project(
                name="Open After Create", path=str(temp_project_path)
            )
            assert isinstance(create_result, Success)

        with allure.step("Close and reopen project"):
            app_context.close_project()
            open_result = app_context.open_project(str(temp_project_path))

        with allure.step("Verify project opened"):
            assert isinstance(open_result, Success)
            assert app_context.has_project


@allure.story("QC-026.03 View Sources List")
@allure.severity(allure.severity_level.CRITICAL)
class TestViewSourcesList:
    @allure.title("AC #3: Researcher can see list of sources in the project")
    @allure.link("QC-026", name="Backlog Task")
    def test_view_empty_sources_list(
        self, app_context: AppContext, existing_project: Path
    ):
        with allure.step("Open project"):
            result = app_context.open_project(str(existing_project))
            assert isinstance(result, Success)

        with allure.step("Get sources from state"):
            sources = list(app_context.state.sources)

        with allure.step("Verify empty list for new project"):
            assert sources == []

    @allure.title("AC #3: Sources list updates after adding source")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_sources_list_reflects_added_sources(
        self, app_context: AppContext, existing_project: Path, tmp_path: Path
    ):
        from src.contexts.projects.core.entities import Source, SourceType
        from src.contexts.shared.core.types import SourceId

        with allure.step("Open project"):
            result = app_context.open_project(str(existing_project))
            assert isinstance(result, Success)

        with allure.step("Add source via repository and state"):
            source = Source(
                id=SourceId(1),
                name="test_document.txt",
                source_type=SourceType.TEXT,
                fulltext="Test content for the document",
            )
            app_context.sources_context.source_repo.save(source)
            app_context.state.add_source(source)

        with allure.step("Verify source in list"):
            sources = list(app_context.state.sources)
            assert len(sources) == 1
            assert sources[0].name == "test_document.txt"

    @allure.title("AC #3: Sources list shows correct source types")
    @allure.severity(allure.severity_level.NORMAL)
    def test_sources_list_shows_types(
        self, app_context: AppContext, existing_project: Path
    ):
        from src.contexts.projects.core.entities import Source, SourceType
        from src.contexts.shared.core.types import SourceId

        with allure.step("Open project"):
            result = app_context.open_project(str(existing_project))
            assert isinstance(result, Success)

        with allure.step("Add sources of different types"):
            text_source = Source(
                id=SourceId(1),
                name="document.txt",
                source_type=SourceType.TEXT,
                fulltext="Text content",
            )
            image_source = Source(
                id=SourceId(2),
                name="photo.png",
                source_type=SourceType.IMAGE,
            )
            app_context.sources_context.source_repo.save(text_source)
            app_context.sources_context.source_repo.save(image_source)
            app_context.state.add_source(text_source)
            app_context.state.add_source(image_source)

        with allure.step("Verify types"):
            sources = list(app_context.state.sources)
            types = {s.source_type for s in sources}
            assert SourceType.TEXT in types
            assert SourceType.IMAGE in types


@allure.story("QC-026.04 Switch Screens/Views")
@allure.severity(allure.severity_level.NORMAL)
class TestSwitchScreens:
    @allure.title("AC #4: Researcher can switch between different screens/views")
    @allure.link("QC-026", name="Backlog Task")
    def test_track_current_screen(
        self, app_context: AppContext, existing_project: Path
    ):
        with allure.step("Open project"):
            result = app_context.open_project(str(existing_project))
            assert isinstance(result, Success)

        with allure.step("Set screen to sources"):
            app_context.state.current_screen = "sources"
            assert app_context.state.current_screen == "sources"

        with allure.step("Switch to coding screen"):
            app_context.state.current_screen = "coding"
            assert app_context.state.current_screen == "coding"

        with allure.step("Switch to cases screen"):
            app_context.state.current_screen = "cases"
            assert app_context.state.current_screen == "cases"

    @allure.title("AC #4: Screen state persists after navigation")
    @allure.severity(allure.severity_level.NORMAL)
    def test_screen_state_persistence(
        self, app_context: AppContext, existing_project: Path
    ):
        with allure.step("Open project and set screen"):
            result = app_context.open_project(str(existing_project))
            assert isinstance(result, Success)
            app_context.state.current_screen = "analysis"

        with allure.step("Verify screen persists"):
            current = app_context.state.current_screen
            assert current == "analysis"


@allure.story("QC-026.05 Agent Query Project Context")
@allure.severity(allure.severity_level.CRITICAL)
class TestAgentQueryContext:
    @allure.title("AC #5: Agent can query current project context")
    @allure.link("QC-026", name="Backlog Task")
    def test_get_project_context_when_open(
        self, app_context: AppContext, existing_project: Path
    ):
        from src.infrastructure.mcp.project_tools import ProjectTools

        with allure.step("Open project"):
            result = app_context.open_project(str(existing_project))
            assert isinstance(result, Success)

        with allure.step("Initialize ProjectTools"):
            tools = ProjectTools(ctx=app_context)

        with allure.step("Execute get_project_context tool"):
            result = tools.execute("get_project_context", {})

        with allure.step("Verify context returned"):
            assert isinstance(result, Success)
            context = result.unwrap()
            assert context["project_open"] is True
            assert context["project_name"] == "Existing Project"
            assert "source_count" in context
            assert "sources" in context

    @allure.title("AC #5: Agent gets empty context when no project open")
    @allure.severity(allure.severity_level.NORMAL)
    def test_get_project_context_when_closed(self, app_context: AppContext):
        from src.infrastructure.mcp.project_tools import ProjectTools

        with allure.step("Initialize ProjectTools without project"):
            tools = ProjectTools(ctx=app_context)

        with allure.step("Execute get_project_context tool"):
            result = tools.execute("get_project_context", {})

        with allure.step("Verify no project response"):
            assert isinstance(result, Success)
            context = result.unwrap()
            assert context["project_open"] is False

    @allure.title("AC #5: Agent can list sources via MCP tool")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_list_sources_tool(self, app_context: AppContext, existing_project: Path):
        from src.contexts.projects.core.entities import Source, SourceType
        from src.contexts.shared.core.types import SourceId
        from src.infrastructure.mcp.project_tools import ProjectTools

        with allure.step("Open project and add source"):
            app_context.open_project(str(existing_project))
            source = Source(
                id=SourceId(1),
                name="interview.txt",
                source_type=SourceType.TEXT,
                fulltext="Interview content",
            )
            app_context.sources_context.source_repo.save(source)
            app_context.state.add_source(source)

        with allure.step("Execute list_sources tool"):
            tools = ProjectTools(ctx=app_context)
            result = tools.execute("list_sources", {})

        with allure.step("Verify sources listed"):
            assert isinstance(result, Success)
            data = result.unwrap()
            assert data["count"] == 1
            assert data["sources"][0]["name"] == "interview.txt"

    @allure.title("AC #5: Agent can filter sources by type")
    @allure.severity(allure.severity_level.NORMAL)
    def test_list_sources_filtered_by_type(
        self, app_context: AppContext, existing_project: Path
    ):
        from src.contexts.projects.core.entities import Source, SourceType
        from src.contexts.shared.core.types import SourceId
        from src.infrastructure.mcp.project_tools import ProjectTools

        with allure.step("Open project and add mixed sources"):
            app_context.open_project(str(existing_project))
            text_src = Source(
                id=SourceId(1), name="doc.txt", source_type=SourceType.TEXT
            )
            image_src = Source(
                id=SourceId(2), name="img.png", source_type=SourceType.IMAGE
            )
            app_context.sources_context.source_repo.save(text_src)
            app_context.sources_context.source_repo.save(image_src)
            app_context.state.add_source(text_src)
            app_context.state.add_source(image_src)

        with allure.step("Filter by text type"):
            tools = ProjectTools(ctx=app_context)
            result = tools.execute("list_sources", {"source_type": "text"})

        with allure.step("Verify only text sources returned"):
            assert isinstance(result, Success)
            data = result.unwrap()
            assert data["count"] == 1
            assert data["sources"][0]["type"] == "text"

    @allure.title("AC #5: Agent can read source content")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_read_source_content_tool(
        self, app_context: AppContext, existing_project: Path
    ):
        from src.contexts.projects.core.entities import Source, SourceType
        from src.contexts.shared.core.types import SourceId
        from src.infrastructure.mcp.project_tools import ProjectTools

        with allure.step("Open project and add source with content"):
            app_context.open_project(str(existing_project))
            source = Source(
                id=SourceId(1),
                name="document.txt",
                source_type=SourceType.TEXT,
                fulltext="This is the full text content of the document.",
            )
            app_context.sources_context.source_repo.save(source)
            app_context.state.add_source(source)

        with allure.step("Read source content via tool"):
            tools = ProjectTools(ctx=app_context)
            result = tools.execute("read_source_content", {"source_id": 1})

        with allure.step("Verify content returned"):
            assert isinstance(result, Success)
            data = result.unwrap()
            assert "This is the full text content" in data["content"]
            assert data["source_id"] == 1


@allure.story("QC-026.06 Agent Navigate to Segment")
@allure.severity(allure.severity_level.CRITICAL)
class TestAgentNavigateToSegment:
    @allure.title("AC #6: Agent can navigate to a specific source")
    @allure.link("QC-026", name="Backlog Task")
    def test_navigate_to_segment_tool_schema(self, app_context: AppContext):
        from src.infrastructure.mcp.project_tools import ProjectTools

        with allure.step("Get tool schemas"):
            tools = ProjectTools(ctx=app_context)
            schemas = tools.get_tool_schemas()

        with allure.step("Verify navigate_to_segment tool exists"):
            tool_names = [s["name"] for s in schemas]
            assert "navigate_to_segment" in tool_names

        with allure.step("Verify required parameters"):
            nav_schema = next(s for s in schemas if s["name"] == "navigate_to_segment")
            required = nav_schema["inputSchema"]["required"]
            assert "source_id" in required
            assert "start_pos" in required
            assert "end_pos" in required

    @allure.title("AC #6: Navigate tool validates required parameters")
    @allure.severity(allure.severity_level.NORMAL)
    def test_navigate_requires_parameters(
        self, app_context: AppContext, existing_project: Path
    ):
        from src.infrastructure.mcp.project_tools import ProjectTools

        with allure.step("Open project"):
            app_context.open_project(str(existing_project))

        with allure.step("Call navigate without source_id"):
            tools = ProjectTools(ctx=app_context)
            result = tools.execute(
                "navigate_to_segment", {"start_pos": 0, "end_pos": 10}
            )

        with allure.step("Verify failure for missing parameter"):
            assert isinstance(result, Failure)
            assert "source_id" in str(result.failure())

    @allure.title("AC #6: Navigate tool fails for nonexistent source")
    @allure.severity(allure.severity_level.NORMAL)
    def test_navigate_nonexistent_source_fails(
        self, app_context: AppContext, existing_project: Path
    ):
        from src.infrastructure.mcp.project_tools import ProjectTools

        with allure.step("Open project"):
            app_context.open_project(str(existing_project))

        with allure.step("Navigate to nonexistent source"):
            tools = ProjectTools(ctx=app_context)
            result = tools.execute(
                "navigate_to_segment",
                {"source_id": 9999, "start_pos": 0, "end_pos": 10},
            )

        with allure.step("Verify failure"):
            assert isinstance(result, Failure)

    @allure.title("AC #6: Agent can suggest source metadata")
    @allure.severity(allure.severity_level.NORMAL)
    def test_suggest_source_metadata_tool(
        self, app_context: AppContext, existing_project: Path
    ):
        from src.contexts.projects.core.entities import Source, SourceType
        from src.contexts.shared.core.types import SourceId
        from src.infrastructure.mcp.project_tools import ProjectTools

        with allure.step("Open project and add source"):
            app_context.open_project(str(existing_project))
            source = Source(
                id=SourceId(1),
                name="interview_spanish.txt",
                source_type=SourceType.TEXT,
                fulltext="Entrevista en español",
            )
            app_context.sources_context.source_repo.save(source)
            app_context.state.add_source(source)

        with allure.step("Suggest metadata via tool"):
            tools = ProjectTools(ctx=app_context)
            result = tools.execute(
                "suggest_source_metadata",
                {
                    "source_id": 1,
                    "language": "es",
                    "topics": ["interview", "qualitative"],
                },
            )

        with allure.step("Verify suggestion accepted"):
            assert isinstance(result, Success)
            data = result.unwrap()
            assert data["status"] == "pending_approval"
            assert data["suggested"]["language"] == "es"


@allure.story("QC-026 Integration")
@allure.severity(allure.severity_level.CRITICAL)
class TestProjectWorkflowIntegration:
    @allure.title("Complete workflow: Create, open, add sources, query")
    @allure.link("QC-026", name="Backlog Task")
    def test_full_project_workflow(self, app_context: AppContext, tmp_path: Path):
        from src.contexts.projects.core.entities import Source, SourceType
        from src.contexts.shared.core.types import SourceId
        from src.infrastructure.mcp.project_tools import ProjectTools

        project_path = tmp_path / "workflow_test.qda"

        with allure.step("Step 1: Create new project"):
            create_result = app_context.create_project(
                name="Workflow Test Project", path=str(project_path)
            )
            assert isinstance(create_result, Success)

        with allure.step("Step 2: Close and reopen project"):
            app_context.close_project()
            open_result = app_context.open_project(str(project_path))
            assert isinstance(open_result, Success)

        with allure.step("Step 3: Add multiple sources"):
            sources = []
            for i in range(3):
                source = Source(
                    id=SourceId(i + 1),
                    name=f"document_{i + 1}.txt",
                    source_type=SourceType.TEXT,
                    fulltext=f"Content of document {i + 1}",
                )
                app_context.sources_context.source_repo.save(source)
                sources.append(source)

        with allure.step("Step 4: Update state with sources"):
            for source in sources:
                app_context.state.add_source(source)

        with allure.step("Step 5: Agent queries context"):
            tools = ProjectTools(ctx=app_context)
            result = tools.execute("get_project_context", {})
            assert isinstance(result, Success)
            context = result.unwrap()
            assert context["source_count"] == 3

        with allure.step("Step 6: Agent reads source content"):
            read_result = tools.execute("read_source_content", {"source_id": 2})
            assert isinstance(read_result, Success)
            assert "document 2" in read_result.unwrap()["content"]

        with allure.step("Step 7: Close project"):
            close_result = app_context.close_project()
            assert isinstance(close_result, Success)
            assert not app_context.has_project

    @allure.title("Project state cleared after close")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_state_cleared_after_close(
        self, app_context: AppContext, existing_project: Path
    ):
        from src.contexts.projects.core.entities import Source, SourceType
        from src.contexts.shared.core.types import SourceId

        with allure.step("Open and populate project"):
            app_context.open_project(str(existing_project))
            source = Source(
                id=SourceId(1), name="temp.txt", source_type=SourceType.TEXT
            )
            app_context.sources_context.source_repo.save(source)
            app_context.state.add_source(source)
            assert len(list(app_context.state.sources)) == 1

        with allure.step("Close project"):
            app_context.close_project()

        with allure.step("Verify state cleared"):
            assert not app_context.has_project
            assert app_context.state.project is None
            assert app_context.sources_context is None
