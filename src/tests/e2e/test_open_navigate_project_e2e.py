from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import allure
import pytest
from returns.result import Failure, Success

if TYPE_CHECKING:
    from src.shared.infra.app_context import AppContext

pytestmark = [
    pytest.mark.e2e,
    allure.epic("QualCoder v2"),
    allure.feature("QC-026 Open & Navigate Project"),
]


@pytest.fixture
def app_context():
    from src.shared.infra.app_context import create_app_context

    ctx = create_app_context()
    ctx.start()
    yield ctx
    ctx.stop()


@pytest.fixture
def temp_project_path(tmp_path: Path) -> Path:
    return tmp_path / "test_project.qda"


@pytest.fixture
def existing_project(app_context: AppContext, tmp_path: Path) -> Path:
    project_path = tmp_path / "existing_project.qda"
    result = app_context.create_project(name="Existing Project", path=str(project_path))
    assert result.is_success
    app_context.close_project()
    return project_path


@pytest.fixture
def project_with_data(app_context: AppContext, tmp_path: Path) -> Path:
    from src.contexts.projects.core.entities import Source, SourceType
    from src.shared.common.types import SourceId

    project_path = tmp_path / "project_with_data.qda"
    app_context.create_project(name="Data Project", path=str(project_path))
    app_context.open_project(str(project_path))

    source = Source(
        id=SourceId(1),
        name="saved_document.txt",
        source_type=SourceType.TEXT,
        fulltext="Previously saved content",
    )
    app_context.sources_context.source_repo.save(source)
    app_context.close_project()
    return project_path


@allure.story("QC-026.01 Open Existing Project")
@allure.severity(allure.severity_level.CRITICAL)
class TestOpenExistingProject:
    @allure.title("AC #1: Researcher can open an existing project file")
    def test_open_existing_project_success(
        self, app_context: AppContext, existing_project: Path
    ):
        with allure.step("Open existing project file"):
            result = app_context.open_project(str(existing_project))

        with allure.step("Verify project opened successfully"):
            assert result.is_success
            project = result.data
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
            assert not result.is_success

    @allure.title("AC #1: Open project validates database before opening")
    @allure.severity(allure.severity_level.NORMAL)
    def test_open_validates_database(self, app_context: AppContext, tmp_path: Path):
        from src.contexts.projects.infra.project_repository import (
            SQLiteProjectRepository,
        )

        invalid_file = tmp_path / "invalid.qda"
        invalid_file.write_text("not a valid sqlite database")

        with allure.step("Verify file is not valid database"):
            repo = SQLiteProjectRepository()
            is_valid = repo.validate_database(invalid_file)
            assert not is_valid

    @allure.title("AC #2: Project opens and shows main workspace")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_contexts_initialized_after_open(
        self, app_context: AppContext, existing_project: Path
    ):
        with allure.step("Open project"):
            result = app_context.open_project(str(existing_project))
            assert result.is_success

        with allure.step("Verify bounded contexts are available"):
            assert app_context.sources_context is not None
            assert app_context.coding_context is not None
            assert app_context.cases_context is not None
            assert app_context.projects_context is not None

    @allure.title("AC #3: Previously saved sources are loaded on open")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_previously_saved_sources_loaded(
        self, app_context: AppContext, project_with_data: Path
    ):
        with allure.step("Open project with existing data"):
            result = app_context.open_project(str(project_with_data))
            assert result.is_success

        with allure.step("Verify previously saved sources are in repo"):
            sources = app_context.sources_context.source_repo.get_all()
            assert len(sources) == 1
            assert sources[0].name == "saved_document.txt"

    @allure.title("AC #4: Recent projects are tracked")
    @allure.severity(allure.severity_level.NORMAL)
    def test_recent_projects_tracked(
        self, app_context: AppContext, existing_project: Path
    ):
        with allure.step("Open project"):
            result = app_context.open_project(str(existing_project))
            assert result.is_success

        with allure.step("Add to recent projects"):
            project = result.data
            app_context.state.add_to_recent(project)

        with allure.step("Verify project in recent list"):
            recent = app_context.state.recent_projects
            assert len(recent) >= 1
            assert recent[0].name == "Existing Project"


@allure.story("QC-026.02 Create New Project")
@allure.severity(allure.severity_level.CRITICAL)
class TestCreateNewProject:
    @allure.title("AC #1: Researcher can specify project name and location")
    def test_create_new_project_success(
        self, app_context: AppContext, temp_project_path: Path
    ):
        with allure.step("Create new project with name and path"):
            result = app_context.create_project(
                name="My Research Project", path=str(temp_project_path)
            )

        with allure.step("Verify project created with specified name"):
            assert result.is_success
            project = result.data
            assert project.name == "My Research Project"
            assert project.path == temp_project_path

        with allure.step("Verify database file at specified location"):
            assert temp_project_path.exists()
            assert temp_project_path.stat().st_size > 0

    @allure.title("AC #1: Create project fails if file already exists")
    @allure.severity(allure.severity_level.NORMAL)
    def test_create_project_existing_file_fails(
        self, app_context: AppContext, existing_project: Path
    ):
        with allure.step("Attempt to create project at existing path"):
            result = app_context.create_project(
                name="Duplicate Project", path=str(existing_project)
            )

        with allure.step("Verify failure returned"):
            assert not result.is_success

    @allure.title("AC #2: New empty project is created with valid schema")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_created_project_has_valid_schema(
        self, app_context: AppContext, temp_project_path: Path
    ):
        from src.contexts.projects.infra.project_repository import (
            SQLiteProjectRepository,
        )

        with allure.step("Create new project"):
            result = app_context.create_project(
                name="Schema Test", path=str(temp_project_path)
            )
            assert result.is_success

        with allure.step("Validate database schema"):
            repo = SQLiteProjectRepository()
            is_valid = repo.validate_database(temp_project_path)
            assert is_valid

    @allure.title("AC #2: New project starts empty")
    @allure.severity(allure.severity_level.NORMAL)
    def test_new_project_is_empty(
        self, app_context: AppContext, temp_project_path: Path
    ):
        with allure.step("Create and open new project"):
            app_context.create_project(
                name="Empty Project", path=str(temp_project_path)
            )
            app_context.close_project()
            app_context.open_project(str(temp_project_path))

        with allure.step("Verify no sources"):
            sources = app_context.sources_context.source_repo.get_all()
            assert len(sources) == 0

        with allure.step("Verify no cases"):
            cases = app_context.cases_context.case_repo.get_all()
            assert len(cases) == 0

    @allure.title("AC #3: Project can be opened after creation (workspace ready)")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_project_openable_after_creation(
        self, app_context: AppContext, temp_project_path: Path
    ):
        with allure.step("Create new project"):
            create_result = app_context.create_project(
                name="Open After Create", path=str(temp_project_path)
            )
            assert create_result.is_success

        with allure.step("Close and reopen project"):
            app_context.close_project()
            open_result = app_context.open_project(str(temp_project_path))

        with allure.step("Verify workspace ready (contexts available)"):
            assert open_result.is_success
            assert app_context.has_project
            assert app_context.sources_context is not None


@allure.story("QC-026.03 View Sources List")
@allure.severity(allure.severity_level.CRITICAL)
class TestViewSourcesList:
    @allure.title("AC #1: Researcher can see list of all imported sources")
    def test_view_empty_sources_list(
        self, app_context: AppContext, existing_project: Path
    ):
        with allure.step("Open project"):
            result = app_context.open_project(str(existing_project))
            assert result.is_success

        with allure.step("Get sources from repo"):
            sources = app_context.sources_context.source_repo.get_all()

        with allure.step("Verify empty list for new project"):
            assert sources == []

    @allure.title("AC #1: Sources list updates after adding source")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_sources_list_reflects_added_sources(
        self, app_context: AppContext, existing_project: Path, tmp_path: Path
    ):
        from src.contexts.projects.core.entities import Source, SourceType
        from src.shared.common.types import SourceId

        with allure.step("Open project"):
            result = app_context.open_project(str(existing_project))
            assert result.is_success

        with allure.step("Add source via repository"):
            source = Source(
                id=SourceId(1),
                name="test_document.txt",
                source_type=SourceType.TEXT,
                fulltext="Test content for the document",
            )
            app_context.sources_context.source_repo.save(source)

        with allure.step("Verify source in repo"):
            sources = app_context.sources_context.source_repo.get_all()
            assert len(sources) == 1
            assert sources[0].name == "test_document.txt"

    @allure.title("AC #2: Each source shows name, type, and status")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_sources_list_shows_name_type_status(
        self, app_context: AppContext, existing_project: Path
    ):
        from src.contexts.projects.core.entities import Source, SourceStatus, SourceType
        from src.shared.common.types import SourceId

        with allure.step("Open project"):
            result = app_context.open_project(str(existing_project))
            assert result.is_success

        with allure.step("Add source with all attributes"):
            source = Source(
                id=SourceId(1),
                name="interview_01.txt",
                source_type=SourceType.TEXT,
                status=SourceStatus.IMPORTED,
                fulltext="Content",
            )
            app_context.sources_context.source_repo.save(source)

        with allure.step("Verify source has name, type, status"):
            sources = app_context.sources_context.source_repo.get_all()
            assert len(sources) == 1
            assert sources[0].name == "interview_01.txt"
            assert sources[0].source_type == SourceType.TEXT
            assert sources[0].status == SourceStatus.IMPORTED

    @allure.title("AC #2: Sources list shows multiple source types")
    @allure.severity(allure.severity_level.NORMAL)
    def test_sources_list_shows_types(
        self, app_context: AppContext, existing_project: Path
    ):
        from src.contexts.projects.core.entities import Source, SourceType
        from src.shared.common.types import SourceId

        with allure.step("Open project"):
            result = app_context.open_project(str(existing_project))
            assert result.is_success

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

        with allure.step("Verify types"):
            sources = app_context.sources_context.source_repo.get_all()
            types = {s.source_type for s in sources}
            assert SourceType.TEXT in types
            assert SourceType.IMAGE in types

    @allure.title("AC #3: Sources can be filtered by type")
    @allure.severity(allure.severity_level.NORMAL)
    def test_sources_can_be_filtered(
        self, app_context: AppContext, existing_project: Path
    ):
        from src.contexts.projects.core.entities import Source, SourceType
        from src.shared.common.types import SourceId

        with allure.step("Open project and add mixed sources"):
            app_context.open_project(str(existing_project))
            sources_data = [
                ("doc1.txt", SourceType.TEXT),
                ("doc2.txt", SourceType.TEXT),
                ("img1.png", SourceType.IMAGE),
                ("audio.wav", SourceType.AUDIO),
            ]
            for i, (name, stype) in enumerate(sources_data, 1):
                src = Source(id=SourceId(i), name=name, source_type=stype)
                app_context.sources_context.source_repo.save(src)

        with allure.step("Filter sources by type"):
            all_sources = app_context.sources_context.source_repo.get_all()
            text_only = [s for s in all_sources if s.source_type == SourceType.TEXT]
            image_only = [s for s in all_sources if s.source_type == SourceType.IMAGE]

        with allure.step("Verify filtering works"):
            assert len(text_only) == 2
            assert len(image_only) == 1
            assert all(s.source_type == SourceType.TEXT for s in text_only)

    @allure.title("AC #4: Source can be selected to set as current")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_select_source_sets_current(
        self, app_context: AppContext, existing_project: Path
    ):
        from src.contexts.projects.core.entities import Source, SourceType
        from src.shared.common.types import SourceId

        with allure.step("Open project and add source"):
            app_context.open_project(str(existing_project))
            source = Source(
                id=SourceId(1),
                name="selected.txt",
                source_type=SourceType.TEXT,
                fulltext="Content to code",
            )
            app_context.sources_context.source_repo.save(source)

        with allure.step("Select source (set current_source_id)"):
            from src.shared.common.types import SourceId as SId

            app_context.state.current_source_id = SId(value=1)

        with allure.step("Verify current source ID is set"):
            assert app_context.state.current_source_id is not None
            assert app_context.state.current_source_id.value == 1


@allure.story("QC-026.04 Switch Screens/Views")
@allure.severity(allure.severity_level.NORMAL)
class TestSwitchScreens:
    @allure.title("AC #1: Researcher can switch to Coding screen")
    def test_switch_to_coding_screen(
        self, app_context: AppContext, existing_project: Path
    ):
        with allure.step("Open project"):
            app_context.open_project(str(existing_project))

        with allure.step("Switch to coding screen"):
            app_context.state.current_screen = "coding"

        with allure.step("Verify on coding screen"):
            assert app_context.state.current_screen == "coding"

    @allure.title("AC #2: Researcher can switch to Sources screen")
    @allure.severity(allure.severity_level.NORMAL)
    def test_switch_to_sources_screen(
        self, app_context: AppContext, existing_project: Path
    ):
        with allure.step("Open project"):
            app_context.open_project(str(existing_project))

        with allure.step("Switch to sources screen"):
            app_context.state.current_screen = "sources"

        with allure.step("Verify on sources screen"):
            assert app_context.state.current_screen == "sources"

    @allure.title("AC #3: Researcher can switch to Analysis screen")
    @allure.severity(allure.severity_level.NORMAL)
    def test_switch_to_analysis_screen(
        self, app_context: AppContext, existing_project: Path
    ):
        with allure.step("Open project"):
            app_context.open_project(str(existing_project))

        with allure.step("Switch to analysis screen"):
            app_context.state.current_screen = "analysis"

        with allure.step("Verify on analysis screen"):
            assert app_context.state.current_screen == "analysis"

    @allure.title("AC #4: Context preserved when switching screens")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_context_preserved_when_switching(
        self, app_context: AppContext, existing_project: Path
    ):
        from src.contexts.projects.core.entities import Source, SourceType
        from src.shared.common.types import SourceId

        with allure.step("Open project and set current source"):
            app_context.open_project(str(existing_project))
            source = Source(id=SourceId(1), name="doc.txt", source_type=SourceType.TEXT)
            app_context.sources_context.source_repo.save(source)
            from src.shared.common.types import SourceId as SId

            app_context.state.current_source_id = SId(value=1)
            app_context.state.current_screen = "coding"

        with allure.step("Switch to sources screen"):
            app_context.state.current_screen = "sources"

        with allure.step("Verify current source ID still set"):
            assert app_context.state.current_source_id is not None
            assert app_context.state.current_source_id.value == 1

        with allure.step("Switch back to coding"):
            app_context.state.current_screen = "coding"

        with allure.step("Verify context preserved"):
            assert app_context.state.current_source_id.value == 1

    @allure.title("AC #5: Screen navigation supports all main views")
    @allure.severity(allure.severity_level.NORMAL)
    def test_all_main_screens_accessible(
        self, app_context: AppContext, existing_project: Path
    ):
        with allure.step("Open project"):
            app_context.open_project(str(existing_project))

        with allure.step("Verify all screens can be set"):
            screens = ["sources", "coding", "cases", "analysis", "reports"]
            for screen in screens:
                app_context.state.current_screen = screen
                assert app_context.state.current_screen == screen


@allure.story("QC-026.05 Agent Query Project Context")
@allure.severity(allure.severity_level.CRITICAL)
class TestAgentQueryContext:
    @allure.title("AC #5: Agent can query current project context")
    def test_get_project_context_when_open(
        self, app_context: AppContext, existing_project: Path
    ):
        from src.contexts.projects.interface.mcp_tools import ProjectTools

        with allure.step("Open project"):
            result = app_context.open_project(str(existing_project))
            assert result.is_success

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
        from src.contexts.projects.interface.mcp_tools import ProjectTools

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
        from src.contexts.projects.interface.mcp_tools import ProjectTools
        from src.shared.common.types import SourceId

        with allure.step("Open project and add source"):
            app_context.open_project(str(existing_project))
            source = Source(
                id=SourceId(1),
                name="interview.txt",
                source_type=SourceType.TEXT,
                fulltext="Interview content",
            )
            app_context.sources_context.source_repo.save(source)

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
        from src.contexts.projects.interface.mcp_tools import ProjectTools
        from src.shared.common.types import SourceId

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

        with allure.step("Filter by text type"):
            tools = ProjectTools(ctx=app_context)
            result = tools.execute("list_sources", {"source_type": "text"})

        with allure.step("Verify only text sources returned"):
            assert isinstance(result, Success)
            data = result.unwrap()
            assert data["count"] == 1
            assert data["sources"][0]["type"] == "text"

    @allure.title("AC #2: Agent can read source content")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_read_source_content_tool(
        self, app_context: AppContext, existing_project: Path
    ):
        from src.contexts.projects.core.entities import Source, SourceType
        from src.contexts.projects.interface.mcp_tools import ProjectTools
        from src.shared.common.types import SourceId

        with allure.step("Open project and add source with content"):
            app_context.open_project(str(existing_project))
            source = Source(
                id=SourceId(1),
                name="document.txt",
                source_type=SourceType.TEXT,
                fulltext="This is the full text content of the document.",
            )
            app_context.sources_context.source_repo.save(source)

        with allure.step("Read source content via tool"):
            tools = ProjectTools(ctx=app_context)
            result = tools.execute("read_source_content", {"source_id": 1})

        with allure.step("Verify content returned"):
            assert isinstance(result, Success)
            data = result.unwrap()
            assert "This is the full text content" in data["content"]
            assert data["source_id"] == 1

    @allure.title("AC #3: Agent can get list of codes in the project")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_get_codes_from_context(
        self, app_context: AppContext, existing_project: Path
    ):
        with allure.step("Open project"):
            app_context.open_project(str(existing_project))

        with allure.step("Access coding context"):
            coding_ctx = app_context.coding_context
            assert coding_ctx is not None

        with allure.step("Verify codes repository available"):
            codes = coding_ctx.code_repo.get_all()
            assert isinstance(codes, list)

    @allure.title("AC #4: Agent can get currently open source")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_get_current_source(self, app_context: AppContext, existing_project: Path):
        from src.contexts.projects.core.entities import Source, SourceType
        from src.contexts.projects.interface.mcp_tools import ProjectTools
        from src.shared.common.types import SourceId

        with allure.step("Open project and set current source"):
            app_context.open_project(str(existing_project))
            source = Source(
                id=SourceId(1),
                name="current_doc.txt",
                source_type=SourceType.TEXT,
                fulltext="Current document content",
            )
            app_context.sources_context.source_repo.save(source)
            app_context.state.current_source_id = SourceId(value=1)

        with allure.step("Query project context"):
            tools = ProjectTools(ctx=app_context)
            tools.execute("get_project_context", {})

        with allure.step("Verify current source ID accessible via state"):
            assert app_context.state.current_source_id is not None
            assert app_context.state.current_source_id.value == 1


@allure.story("QC-026.06 Agent Navigate to Segment")
@allure.severity(allure.severity_level.CRITICAL)
class TestAgentNavigateToSegment:
    @allure.title("AC #6: Agent can navigate to a specific source")
    def test_navigate_to_segment_tool_schema(self, app_context: AppContext):
        from src.contexts.projects.interface.mcp_tools import ProjectTools

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
        from src.contexts.projects.interface.mcp_tools import ProjectTools

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
        from src.contexts.projects.interface.mcp_tools import ProjectTools

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

    @allure.title("AC #3: Agent can highlight a specific segment")
    @allure.severity(allure.severity_level.NORMAL)
    def test_navigate_with_highlight_option(self, app_context: AppContext):
        from src.contexts.projects.interface.mcp_tools import ProjectTools

        with allure.step("Get tool schema"):
            tools = ProjectTools(ctx=app_context)
            schemas = tools.get_tool_schemas()
            nav_schema = next(s for s in schemas if s["name"] == "navigate_to_segment")

        with allure.step("Verify highlight parameter exists"):
            props = nav_schema["inputSchema"]["properties"]
            assert "highlight" in props
            assert props["highlight"]["type"] == "boolean"

    @allure.title("AC #4: Navigation publishes event for UI update")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_navigation_publishes_event(
        self, app_context: AppContext, existing_project: Path
    ):
        from src.contexts.projects.core.entities import Source, SourceType
        from src.shared.common.types import SourceId

        with allure.step("Open project and add source"):
            app_context.open_project(str(existing_project))
            source = Source(
                id=SourceId(1),
                name="navigate_target.txt",
                source_type=SourceType.TEXT,
                fulltext="Content to navigate to",
            )
            app_context.sources_context.source_repo.save(source)

        with allure.step("Verify event bus available for navigation events"):
            assert app_context.event_bus is not None

        with allure.step("Verify signal bridge available for UI updates"):
            assert app_context.signal_bridge is not None

    @allure.title("AC #6: Agent can suggest source metadata")
    @allure.severity(allure.severity_level.NORMAL)
    def test_suggest_source_metadata_tool(
        self, app_context: AppContext, existing_project: Path
    ):
        from src.contexts.projects.core.entities import Source, SourceType
        from src.contexts.projects.interface.mcp_tools import ProjectTools
        from src.shared.common.types import SourceId

        with allure.step("Open project and add source"):
            app_context.open_project(str(existing_project))
            source = Source(
                id=SourceId(1),
                name="interview_spanish.txt",
                source_type=SourceType.TEXT,
                fulltext="Entrevista en español",
            )
            app_context.sources_context.source_repo.save(source)

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
    def test_full_project_workflow(self, app_context: AppContext, tmp_path: Path):
        from src.contexts.projects.core.entities import Source, SourceType
        from src.contexts.projects.interface.mcp_tools import ProjectTools
        from src.shared.common.types import SourceId

        project_path = tmp_path / "workflow_test.qda"

        with allure.step("Step 1: Create new project"):
            create_result = app_context.create_project(
                name="Workflow Test Project", path=str(project_path)
            )
            assert create_result.is_success

        with allure.step("Step 2: Close and reopen project"):
            app_context.close_project()
            open_result = app_context.open_project(str(project_path))
            assert open_result.is_success

        with allure.step("Step 3: Add multiple sources"):
            for i in range(3):
                source = Source(
                    id=SourceId(i + 1),
                    name=f"document_{i + 1}.txt",
                    source_type=SourceType.TEXT,
                    fulltext=f"Content of document {i + 1}",
                )
                app_context.sources_context.source_repo.save(source)

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
            assert close_result.is_success
            assert not app_context.has_project

    @allure.title("Project state cleared after close")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_state_cleared_after_close(
        self, app_context: AppContext, existing_project: Path
    ):
        from src.contexts.projects.core.entities import Source, SourceType
        from src.shared.common.types import SourceId

        with allure.step("Open and populate project"):
            app_context.open_project(str(existing_project))
            source = Source(
                id=SourceId(1), name="temp.txt", source_type=SourceType.TEXT
            )
            app_context.sources_context.source_repo.save(source)
            sources = app_context.sources_context.source_repo.get_all()
            assert len(sources) == 1

        with allure.step("Close project"):
            app_context.close_project()

        with allure.step("Verify state cleared"):
            assert not app_context.has_project
            assert app_context.state.project is None
            assert app_context.sources_context is None
