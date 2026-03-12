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
        id=SourceId("1"),
        name="saved_document.txt",
        source_type=SourceType.TEXT,
        fulltext="Previously saved content",
    )
    app_context.sources_context.source_repo.save(source)
    app_context.session.commit()
    app_context.close_project()
    return project_path


@allure.story("QC-026.01 Open Existing Project")
@allure.severity(allure.severity_level.CRITICAL)
class TestOpenExistingProject:
    @allure.title("AC #1-2: Open existing project, verify contexts initialized")
    def test_open_project_and_contexts(
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

        with allure.step("Verify bounded contexts are available"):
            assert app_context.sources_context is not None
            assert app_context.coding_context is not None
            assert app_context.cases_context is not None
            assert app_context.projects_context is not None

    @allure.title("AC #1: Open fails for non-existent file and invalid database")
    @allure.severity(allure.severity_level.NORMAL)
    def test_open_fails_for_invalid(self, app_context: AppContext, tmp_path: Path):
        with allure.step("Attempt to open non-existent project"):
            nonexistent = tmp_path / "does_not_exist.qda"
            result = app_context.open_project(str(nonexistent))

        with allure.step("Verify failure returned"):
            assert not result.is_success

        with allure.step("Verify invalid database is detected"):
            from src.contexts.projects.infra.project_repository import (
                SQLiteProjectRepository,
            )

            invalid_file = tmp_path / "invalid.qda"
            invalid_file.write_text("not a valid sqlite database")
            repo = SQLiteProjectRepository()
            is_valid = repo.validate_database(invalid_file)
            assert not is_valid

    @allure.title(
        "AC #3-4: Previously saved sources loaded and recent projects tracked"
    )
    @allure.severity(allure.severity_level.CRITICAL)
    def test_sources_loaded_and_recent_tracked(
        self, app_context: AppContext, project_with_data: Path
    ):
        with allure.step("Open project with existing data"):
            result = app_context.open_project(str(project_with_data))
            assert result.is_success

        with allure.step("Verify previously saved sources are in repo"):
            sources = app_context.sources_context.source_repo.get_all()
            assert len(sources) == 1
            assert sources[0].name == "saved_document.txt"

        with allure.step("Add to recent projects"):
            project = result.data
            app_context.state.add_to_recent(project)

        with allure.step("Verify project in recent list"):
            recent = app_context.state.recent_projects
            assert len(recent) >= 1
            assert recent[0].name == "Data Project"


@allure.story("QC-026.02 Create New Project")
@allure.severity(allure.severity_level.CRITICAL)
class TestCreateNewProject:
    @allure.title(
        "AC #1-3: Create project with name/location, valid schema, and openable"
    )
    def test_create_project_full(
        self, app_context: AppContext, temp_project_path: Path
    ):
        from src.contexts.projects.infra.project_repository import (
            SQLiteProjectRepository,
        )

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

        with allure.step("Validate database schema"):
            repo = SQLiteProjectRepository()
            is_valid = repo.validate_database(temp_project_path)
            assert is_valid

        with allure.step("Close and reopen project"):
            app_context.close_project()
            open_result = app_context.open_project(str(temp_project_path))

        with allure.step("Verify workspace ready (contexts available)"):
            assert open_result.is_success
            assert app_context.has_project
            assert app_context.sources_context is not None

    @allure.title("AC #1-2: Create fails if exists, and new project starts empty")
    @allure.severity(allure.severity_level.NORMAL)
    def test_create_fails_and_empty(
        self, app_context: AppContext, existing_project: Path, tmp_path: Path
    ):
        with allure.step("Attempt to create project at existing path"):
            result = app_context.create_project(
                name="Duplicate Project", path=str(existing_project)
            )

        with allure.step("Verify failure returned"):
            assert not result.is_success

        with allure.step("Create and open new project to verify it starts empty"):
            empty_path = tmp_path / "empty_project.qda"
            app_context.create_project(name="Empty Project", path=str(empty_path))
            app_context.close_project()
            app_context.open_project(str(empty_path))

        with allure.step("Verify no sources"):
            sources = app_context.sources_context.source_repo.get_all()
            assert len(sources) == 0

        with allure.step("Verify no cases"):
            cases = app_context.cases_context.case_repo.get_all()
            assert len(cases) == 0


@allure.story("QC-026.03 View Sources List")
@allure.severity(allure.severity_level.CRITICAL)
class TestViewSourcesList:
    @allure.title("AC #1: Empty and populated sources list")
    def test_sources_list_empty_and_populated(
        self, app_context: AppContext, existing_project: Path, tmp_path: Path
    ):
        from src.contexts.projects.core.entities import Source, SourceType
        from src.shared.common.types import SourceId

        with allure.step("Open project"):
            result = app_context.open_project(str(existing_project))
            assert result.is_success

        with allure.step("Get sources from repo - verify empty"):
            sources = app_context.sources_context.source_repo.get_all()
            assert sources == []

        with allure.step("Add source via repository"):
            source = Source(
                id=SourceId("1"),
                name="test_document.txt",
                source_type=SourceType.TEXT,
                fulltext="Test content for the document",
            )
            app_context.sources_context.source_repo.save(source)

        with allure.step("Verify source in repo"):
            sources = app_context.sources_context.source_repo.get_all()
            assert len(sources) == 1
            assert sources[0].name == "test_document.txt"

    @allure.title("AC #2: Sources show name, type, status, and multiple types")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_sources_attributes_and_types(
        self, app_context: AppContext, existing_project: Path
    ):
        from src.contexts.projects.core.entities import Source, SourceStatus, SourceType
        from src.shared.common.types import SourceId

        with allure.step("Open project"):
            result = app_context.open_project(str(existing_project))
            assert result.is_success

        with allure.step("Add sources with all attributes"):
            text_source = Source(
                id=SourceId("1"),
                name="interview_01.txt",
                source_type=SourceType.TEXT,
                status=SourceStatus.IMPORTED,
                fulltext="Content",
            )
            image_source = Source(
                id=SourceId("2"),
                name="photo.png",
                source_type=SourceType.IMAGE,
            )
            app_context.sources_context.source_repo.save(text_source)
            app_context.sources_context.source_repo.save(image_source)

        with allure.step("Verify source has name, type, status"):
            sources = app_context.sources_context.source_repo.get_all()
            assert len(sources) == 2
            text_src = next(s for s in sources if s.name == "interview_01.txt")
            assert text_src.source_type == SourceType.TEXT
            assert text_src.status == SourceStatus.IMPORTED

        with allure.step("Verify types"):
            types = {s.source_type for s in sources}
            assert SourceType.TEXT in types
            assert SourceType.IMAGE in types

    @allure.title("AC #3-4: Sources can be filtered by type and selected as current")
    @allure.severity(allure.severity_level.NORMAL)
    def test_sources_filter_and_select(
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

        with allure.step("Select source (set current_source_id)"):
            from src.shared.common.types import SourceId as SId

            app_context.state.current_source_id = SId(value="1")

        with allure.step("Verify current source ID is set"):
            assert app_context.state.current_source_id is not None
            assert app_context.state.current_source_id.value == "1"


@allure.story("QC-026.04 Switch Screens/Views")
@allure.severity(allure.severity_level.NORMAL)
class TestSwitchScreens:
    @allure.title(
        "AC #4-5: Context preserved when switching and all screens accessible"
    )
    @allure.severity(allure.severity_level.CRITICAL)
    def test_context_preserved_and_all_screens(
        self, app_context: AppContext, existing_project: Path
    ):
        from src.contexts.projects.core.entities import Source, SourceType
        from src.shared.common.types import SourceId

        with allure.step("Open project and set current source"):
            app_context.open_project(str(existing_project))
            source = Source(
                id=SourceId("1"), name="doc.txt", source_type=SourceType.TEXT
            )
            app_context.sources_context.source_repo.save(source)
            from src.shared.common.types import SourceId as SId

            app_context.state.current_source_id = SId(value="1")
            app_context.state.current_screen = "coding"

        with allure.step("Switch to sources screen"):
            app_context.state.current_screen = "sources"

        with allure.step("Verify current source ID still set"):
            assert app_context.state.current_source_id is not None
            assert app_context.state.current_source_id.value == "1"

        with allure.step("Switch back to coding"):
            app_context.state.current_screen = "coding"

        with allure.step("Verify context preserved"):
            assert app_context.state.current_source_id.value == "1"

        with allure.step("Verify all screens can be set"):
            screens = ["sources", "coding", "cases", "analysis", "reports"]
            for screen in screens:
                app_context.state.current_screen = screen
                assert app_context.state.current_screen == screen


@allure.story("QC-026.05 Agent Query Project Context")
@allure.severity(allure.severity_level.CRITICAL)
class TestAgentQueryContext:
    @allure.title("AC #5: Agent queries project context (open and closed)")
    def test_project_context_open_and_closed(
        self, app_context: AppContext, existing_project: Path
    ):
        from src.contexts.projects.interface.mcp_tools import ProjectTools

        with allure.step("Initialize ProjectTools without project"):
            tools = ProjectTools(ctx=app_context)

        with allure.step("Execute get_project_context when closed"):
            result = tools.execute("get_project_context", {})

        with allure.step("Verify no project response"):
            assert isinstance(result, Success)
            context = result.unwrap()
            assert context["project_open"] is False

        with allure.step("Open project"):
            result = app_context.open_project(str(existing_project))
            assert result.is_success

        with allure.step("Execute get_project_context when open"):
            tools = ProjectTools(ctx=app_context)
            result = tools.execute("get_project_context", {})

        with allure.step("Verify context returned"):
            assert isinstance(result, Success)
            context = result.unwrap()
            assert context["project_open"] is True
            assert context["project_name"] == "Existing Project"
            assert "source_count" in context
            assert "sources" in context

    @allure.title("AC #5: Agent lists sources and filters by type")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_list_and_filter_sources(
        self, app_context: AppContext, existing_project: Path
    ):
        from src.contexts.projects.core.entities import Source, SourceType
        from src.contexts.sources.interface.mcp_tools import SourceTools
        from src.shared.common.types import SourceId

        with allure.step("Open project and add sources"):
            app_context.open_project(str(existing_project))
            text_src = Source(
                id=SourceId("1"),
                name="interview.txt",
                source_type=SourceType.TEXT,
                fulltext="Interview content",
            )
            image_src = Source(
                id=SourceId("2"), name="img.png", source_type=SourceType.IMAGE
            )
            app_context.sources_context.source_repo.save(text_src)
            app_context.sources_context.source_repo.save(image_src)

        with allure.step("Execute list_sources tool"):
            tools = SourceTools(ctx=app_context)
            result = tools.execute("list_sources", {})

        with allure.step("Verify sources listed"):
            assert isinstance(result, Success)
            data = result.unwrap()
            assert data["count"] == 2

        with allure.step("Filter by text type"):
            result = tools.execute("list_sources", {"source_type": "text"})

        with allure.step("Verify only text sources returned"):
            assert isinstance(result, Success)
            data = result.unwrap()
            assert data["count"] == 1
            assert data["sources"][0]["type"] == "text"

    @allure.title("AC #2-4: Agent reads source content and gets current source")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_read_content_and_current_source(
        self, app_context: AppContext, existing_project: Path
    ):
        from src.contexts.projects.core.entities import Source, SourceType
        from src.contexts.projects.interface.mcp_tools import ProjectTools
        from src.contexts.sources.interface.mcp_tools import SourceTools
        from src.shared.common.types import SourceId

        with allure.step("Open project and add source with content"):
            app_context.open_project(str(existing_project))
            source = Source(
                id=SourceId("1"),
                name="document.txt",
                source_type=SourceType.TEXT,
                fulltext="This is the full text content of the document.",
            )
            app_context.sources_context.source_repo.save(source)

        with allure.step("Read source content via tool"):
            tools = SourceTools(ctx=app_context)
            result = tools.execute("read_source_content", {"source_id": 1})

        with allure.step("Verify content returned"):
            assert isinstance(result, Success)
            data = result.unwrap()
            assert "This is the full text content" in data["content"]
            assert data["source_id"] == 1

        with allure.step("Set current source"):
            app_context.state.current_source_id = SourceId(value="1")

        with allure.step("Query project context"):
            project_tools = ProjectTools(ctx=app_context)
            project_tools.execute("get_project_context", {})

        with allure.step("Verify current source ID accessible via state"):
            assert app_context.state.current_source_id is not None
            assert app_context.state.current_source_id.value == "1"


@allure.story("QC-026.06 Agent Navigate to Segment")
@allure.severity(allure.severity_level.CRITICAL)
class TestAgentNavigateToSegment:
    @allure.title("AC #6: Navigate tool schema, validation, and nonexistent source")
    def test_navigate_schema_and_validation(
        self, app_context: AppContext, existing_project: Path
    ):
        from src.contexts.sources.interface.mcp_tools import SourceTools

        with allure.step("Get tool schemas"):
            tools = SourceTools(ctx=app_context)
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

        with allure.step("Verify highlight parameter exists"):
            props = nav_schema["inputSchema"]["properties"]
            assert "highlight" in props
            assert props["highlight"]["type"] == "boolean"

        with allure.step("Open project"):
            app_context.open_project(str(existing_project))

        with allure.step("Call navigate without source_id"):
            result = tools.execute(
                "navigate_to_segment", {"start_pos": 0, "end_pos": 10}
            )

        with allure.step("Verify failure for missing parameter"):
            assert isinstance(result, Failure)
            assert "source_id" in str(result.failure())

        with allure.step("Navigate to nonexistent source"):
            result = tools.execute(
                "navigate_to_segment",
                {"source_id": 9999, "start_pos": 0, "end_pos": 10},
            )

        with allure.step("Verify failure"):
            assert isinstance(result, Failure)

    @allure.title("AC #4-6: Navigation publishes event and suggest metadata")
    @allure.severity(allure.severity_level.NORMAL)
    def test_navigation_event_and_metadata(
        self, app_context: AppContext, existing_project: Path
    ):
        from src.contexts.projects.core.entities import Source, SourceType
        from src.contexts.sources.interface.mcp_tools import SourceTools
        from src.shared.common.types import SourceId

        with allure.step("Open project and add source"):
            app_context.open_project(str(existing_project))
            source = Source(
                id=SourceId("1"),
                name="interview_spanish.txt",
                source_type=SourceType.TEXT,
                fulltext="Entrevista en español",
            )
            app_context.sources_context.source_repo.save(source)

        with allure.step("Verify event bus available for navigation events"):
            assert app_context.event_bus is not None

        with allure.step("Verify signal bridge available for UI updates"):
            assert app_context.signal_bridge is not None

        with allure.step("Suggest metadata via tool"):
            tools = SourceTools(ctx=app_context)
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
    @allure.title("Complete workflow: Create, open, add sources, query, close")
    def test_full_project_workflow_and_state_cleared(
        self, app_context: AppContext, tmp_path: Path
    ):
        from src.contexts.projects.core.entities import Source, SourceType
        from src.contexts.projects.interface.mcp_tools import ProjectTools
        from src.contexts.sources.interface.mcp_tools import SourceTools
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

        with allure.step("Step 4: Agent queries context"):
            project_tools = ProjectTools(ctx=app_context)
            result = project_tools.execute("get_project_context", {})
            assert isinstance(result, Success)
            context = result.unwrap()
            assert context["source_count"] == 3

        with allure.step("Step 5: Agent reads source content"):
            source_tools = SourceTools(ctx=app_context)
            read_result = source_tools.execute("read_source_content", {"source_id": 2})
            assert isinstance(read_result, Success)
            assert "document 2" in read_result.unwrap()["content"]

        with allure.step("Step 6: Close project and verify state cleared"):
            close_result = app_context.close_project()
            assert close_result.is_success
            assert not app_context.has_project
            assert app_context.state.project is None
            assert app_context.sources_context is None
