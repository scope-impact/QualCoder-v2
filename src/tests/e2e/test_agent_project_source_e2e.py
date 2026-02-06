"""
E2E tests for AI Agent MCP tools: project lifecycle and source management.

Covers:
- QC-026.07: Agent Open/Close Project
- QC-027.12: Agent Add Text Source
- QC-027.13: Agent Manage Folders
- QC-027.14: Agent Remove Source
"""

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


# ============================================================
# Fixtures
# ============================================================


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
def open_project(app_context: AppContext, existing_project: Path) -> Path:
    """Open a project and return its path."""
    result = app_context.open_project(str(existing_project))
    assert result.is_success
    return existing_project


@pytest.fixture
def tools(app_context: AppContext):
    """Create ProjectTools instance."""
    from src.contexts.projects.interface.mcp_tools import ProjectTools

    return ProjectTools(ctx=app_context)


# ============================================================
# QC-026.07: Agent Open/Close Project
# ============================================================


@allure.story("QC-026.07 Agent Open/Close Project")
@allure.severity(allure.severity_level.CRITICAL)
class TestAgentOpenCloseProject:
    @allure.title("AC #1: open_project tool is registered with path parameter")
    def test_open_project_tool_schema(self, tools):
        with allure.step("Get tool schemas"):
            schemas = tools.get_tool_schemas()

        with allure.step("Verify open_project tool exists"):
            tool_names = [s["name"] for s in schemas]
            assert "open_project" in tool_names

        with allure.step("Verify required parameters"):
            schema = next(s for s in schemas if s["name"] == "open_project")
            assert "path" in schema["inputSchema"]["required"]

    @allure.title("AC #2: Agent can open a .qda project file")
    def test_open_project_success(
        self, app_context: AppContext, tools, existing_project: Path
    ):
        with allure.step("Open project via MCP tool"):
            result = tools.execute("open_project", {"path": str(existing_project)})

        with allure.step("Verify success"):
            assert isinstance(result, Success)
            data = result.unwrap()
            assert data["success"] is True
            assert data["project_name"] == "Existing Project"

        with allure.step("Verify app context updated"):
            assert app_context.has_project

    @allure.title("AC #3: Invalid path returns clear failure message")
    def test_open_project_invalid_path(self, tools, tmp_path: Path):
        with allure.step("Attempt to open non-existent project"):
            result = tools.execute(
                "open_project", {"path": str(tmp_path / "nonexistent.qda")}
            )

        with allure.step("Verify failure"):
            assert isinstance(result, Failure)

    @allure.title("AC #4: ProjectOpened event is published")
    def test_open_project_publishes_event(
        self, app_context: AppContext, tools, existing_project: Path
    ):
        events_received = []
        app_context.event_bus.subscribe(
            "projects.project_opened", lambda e: events_received.append(e)
        )

        with allure.step("Open project"):
            result = tools.execute("open_project", {"path": str(existing_project)})
            assert isinstance(result, Success)

        with allure.step("Verify event published"):
            assert len(events_received) >= 1

    @allure.title("AC #5: close_project tool is registered")
    def test_close_project_tool_schema(self, tools):
        with allure.step("Get tool schemas"):
            schemas = tools.get_tool_schemas()

        with allure.step("Verify close_project tool exists"):
            tool_names = [s["name"] for s in schemas]
            assert "close_project" in tool_names

    @allure.title("AC #6: Agent can close the current project")
    def test_close_project_success(
        self, app_context: AppContext, tools, open_project: Path
    ):
        with allure.step("Close project via MCP tool"):
            result = tools.execute("close_project", {})

        with allure.step("Verify success"):
            assert isinstance(result, Success)
            data = result.unwrap()
            assert data["success"] is True
            assert data["closed"] is True
            assert data["project_name"] == "Existing Project"

        with allure.step("Verify project actually closed"):
            assert not app_context.has_project

    @allure.title("AC #7: Closing with no project open returns informative message")
    def test_close_project_when_none_open(self, tools):
        with allure.step("Close when no project open"):
            result = tools.execute("close_project", {})

        with allure.step("Verify informative response (not error)"):
            assert isinstance(result, Success)
            data = result.unwrap()
            assert data["success"] is True
            assert data["closed"] is False
            assert "No project" in data["message"]

    @allure.title("AC #9: Full open/close lifecycle")
    def test_open_close_lifecycle(
        self, app_context: AppContext, tools, existing_project: Path
    ):
        with allure.step("Open project"):
            open_result = tools.execute("open_project", {"path": str(existing_project)})
            assert isinstance(open_result, Success)
            assert app_context.has_project

        with allure.step("Close project"):
            close_result = tools.execute("close_project", {})
            assert isinstance(close_result, Success)
            assert not app_context.has_project

        with allure.step("Reopen project"):
            reopen_result = tools.execute(
                "open_project", {"path": str(existing_project)}
            )
            assert isinstance(reopen_result, Success)
            assert app_context.has_project


# ============================================================
# QC-027.12: Agent Add Text Source
# ============================================================


@allure.story("QC-027.12 Agent Add Text Source")
@allure.severity(allure.severity_level.CRITICAL)
@allure.feature("QC-027 Manage Sources")
class TestAgentAddTextSource:
    @allure.title("AC #1: add_text_source tool is registered with proper schema")
    def test_add_text_source_tool_schema(self, tools):
        with allure.step("Get tool schemas"):
            schemas = tools.get_tool_schemas()

        with allure.step("Verify tool exists"):
            tool_names = [s["name"] for s in schemas]
            assert "add_text_source" in tool_names

        with allure.step("Verify schema has required parameters"):
            schema = next(s for s in schemas if s["name"] == "add_text_source")
            required = schema["inputSchema"]["required"]
            assert "name" in required
            assert "content" in required

    @allure.title("AC #2: Agent can provide name, content, and optional metadata")
    def test_add_text_source_success(
        self, app_context: AppContext, tools, open_project: Path
    ):
        with allure.step("Add text source via MCP tool"):
            result = tools.execute(
                "add_text_source",
                {
                    "name": "interview_01.txt",
                    "content": "This is my interview transcript content.",
                    "memo": "First interview session",
                    "origin": "field notes",
                },
            )

        with allure.step("Verify success with source details"):
            assert isinstance(result, Success)
            data = result.unwrap()
            assert data["success"] is True
            assert data["name"] == "interview_01.txt"
            assert data["type"] == "text"
            assert data["status"] == "imported"
            assert data["file_size"] == len("This is my interview transcript content.")

    @allure.title("AC #3: Duplicate source names are rejected")
    def test_add_text_source_duplicate_name(
        self, app_context: AppContext, tools, open_project: Path
    ):
        with allure.step("Add first source"):
            result1 = tools.execute(
                "add_text_source",
                {"name": "unique_doc.txt", "content": "First version"},
            )
            assert isinstance(result1, Success)

        with allure.step("Add source with same name"):
            result2 = tools.execute(
                "add_text_source",
                {"name": "unique_doc.txt", "content": "Second version"},
            )

        with allure.step("Verify duplicate rejected"):
            assert isinstance(result2, Failure)
            assert "already exists" in str(result2.failure())

    @allure.title("AC #4: Source is persisted and SourceAdded event published")
    def test_add_text_source_persisted_and_event(
        self, app_context: AppContext, tools, open_project: Path
    ):
        events_received = []
        app_context.event_bus.subscribe(
            "projects.source_added", lambda e: events_received.append(e)
        )

        with allure.step("Add text source"):
            result = tools.execute(
                "add_text_source",
                {"name": "persisted_doc.txt", "content": "Persisted content"},
            )
            assert isinstance(result, Success)

        with allure.step("Verify source in repository"):
            sources = app_context.sources_context.source_repo.get_all()
            names = [s.name for s in sources]
            assert "persisted_doc.txt" in names

        with allure.step("Verify content stored"):
            source = next(s for s in sources if s.name == "persisted_doc.txt")
            assert source.fulltext == "Persisted content"

        with allure.step("Verify event published"):
            assert len(events_received) >= 1

    @allure.title("AC #5: Tool returns source ID, name, type, and status")
    def test_add_text_source_returns_details(self, tools, open_project: Path):
        with allure.step("Add text source"):
            result = tools.execute(
                "add_text_source",
                {"name": "detailed_doc.txt", "content": "Some content"},
            )

        with allure.step("Verify response fields"):
            assert isinstance(result, Success)
            data = result.unwrap()
            assert "source_id" in data
            assert "name" in data
            assert "type" in data
            assert "status" in data

    @allure.title("AC #6: Empty name is rejected")
    def test_add_text_source_empty_name(self, tools, open_project: Path):
        with allure.step("Add source with empty name"):
            result = tools.execute(
                "add_text_source", {"name": "", "content": "Some content"}
            )

        with allure.step("Verify rejection"):
            assert isinstance(result, Failure)

    @allure.title("AC #6: Empty content is rejected")
    def test_add_text_source_empty_content(self, tools, open_project: Path):
        with allure.step("Add source with empty content"):
            result = tools.execute(
                "add_text_source", {"name": "empty_doc.txt", "content": ""}
            )

        with allure.step("Verify rejection"):
            assert isinstance(result, Failure)

    @allure.title("AC #8: Tool schema includes optional memo and origin parameters")
    def test_add_text_source_optional_params(self, tools):
        with allure.step("Get schema"):
            schemas = tools.get_tool_schemas()
            schema = next(s for s in schemas if s["name"] == "add_text_source")
            props = schema["inputSchema"]["properties"]

        with allure.step("Verify optional params"):
            assert "memo" in props
            assert "origin" in props


# ============================================================
# QC-027.14: Agent Remove Source
# ============================================================


@allure.story("QC-027.14 Agent Remove Source")
@allure.severity(allure.severity_level.CRITICAL)
@allure.feature("QC-027 Manage Sources")
class TestAgentRemoveSource:
    @allure.title("AC #1: remove_source tool registered with source_id parameter")
    def test_remove_source_tool_schema(self, tools):
        with allure.step("Get tool schemas"):
            schemas = tools.get_tool_schemas()

        with allure.step("Verify tool exists with required params"):
            tool_names = [s["name"] for s in schemas]
            assert "remove_source" in tool_names
            schema = next(s for s in schemas if s["name"] == "remove_source")
            assert "source_id" in schema["inputSchema"]["required"]

    @allure.title("AC #3: Non-existent source returns failure")
    def test_remove_source_not_found(self, tools, open_project: Path):
        with allure.step("Try to remove non-existent source"):
            result = tools.execute(
                "remove_source", {"source_id": 9999, "confirm": True}
            )

        with allure.step("Verify failure"):
            assert isinstance(result, Failure)
            assert "not found" in str(result.failure()).lower()

    @allure.title("AC #6: Preview mode returns requires_approval flag")
    def test_remove_source_preview_mode(
        self, app_context: AppContext, tools, open_project: Path
    ):
        from src.contexts.projects.core.entities import Source, SourceType
        from src.shared.common.types import SourceId

        with allure.step("Add a source to remove"):
            source = Source(
                id=SourceId(42),
                name="to_delete.txt",
                source_type=SourceType.TEXT,
                fulltext="Content to delete",
            )
            app_context.sources_context.source_repo.save(source)

        with allure.step("Preview deletion (confirm=false)"):
            result = tools.execute("remove_source", {"source_id": 42, "confirm": False})

        with allure.step("Verify preview response"):
            assert isinstance(result, Success)
            data = result.unwrap()
            assert data["preview"] is True
            assert data["source_name"] == "to_delete.txt"
            assert data["requires_approval"] is True
            assert "source_type" in data

    @allure.title("AC #2: Agent can remove a source with confirm=true")
    def test_remove_source_confirmed(
        self, app_context: AppContext, tools, open_project: Path
    ):
        from src.contexts.projects.core.entities import Source, SourceType
        from src.shared.common.types import SourceId

        with allure.step("Add a source"):
            source = Source(
                id=SourceId(43),
                name="confirmed_delete.txt",
                source_type=SourceType.TEXT,
                fulltext="Will be deleted",
            )
            app_context.sources_context.source_repo.save(source)

        with allure.step("Confirm deletion"):
            result = tools.execute("remove_source", {"source_id": 43, "confirm": True})

        with allure.step("Verify removed"):
            assert isinstance(result, Success)
            data = result.unwrap()
            assert data["success"] is True
            assert data["removed"] is True
            assert data["source_name"] == "confirmed_delete.txt"

        with allure.step("Verify source gone from repo"):
            source = app_context.sources_context.source_repo.get_by_id(SourceId(43))
            assert source is None

    @allure.title("AC #7: Default confirm=false returns preview")
    def test_remove_source_default_preview(
        self, app_context: AppContext, tools, open_project: Path
    ):
        from src.contexts.projects.core.entities import Source, SourceType
        from src.shared.common.types import SourceId

        with allure.step("Add source"):
            source = Source(
                id=SourceId(44),
                name="default_preview.txt",
                source_type=SourceType.TEXT,
            )
            app_context.sources_context.source_repo.save(source)

        with allure.step("Call without confirm param (should default to preview)"):
            result = tools.execute("remove_source", {"source_id": 44})

        with allure.step("Verify preview mode"):
            assert isinstance(result, Success)
            data = result.unwrap()
            assert data["preview"] is True

        with allure.step("Verify source still exists"):
            source = app_context.sources_context.source_repo.get_by_id(SourceId(44))
            assert source is not None


# ============================================================
# QC-027.13: Agent Manage Folders
# ============================================================


@allure.story("QC-027.13 Agent Manage Folders")
@allure.severity(allure.severity_level.CRITICAL)
@allure.feature("QC-027 Manage Sources")
class TestAgentManageFolders:
    @allure.title("AC #1: list_folders returns all folders")
    def test_list_folders_empty(self, tools, open_project: Path):
        with allure.step("List folders in empty project"):
            result = tools.execute("list_folders", {})

        with allure.step("Verify empty list"):
            assert isinstance(result, Success)
            data = result.unwrap()
            assert data["total_count"] == 0

    @allure.title("AC #2: create_folder accepts name and returns folder ID")
    def test_create_folder_success(self, tools, open_project: Path):
        with allure.step("Create a folder"):
            result = tools.execute("create_folder", {"name": "Interviews"})

        with allure.step("Verify folder created"):
            assert isinstance(result, Success)
            data = result.unwrap()
            assert data["success"] is True
            assert data["name"] == "Interviews"
            assert "folder_id" in data

    @allure.title("AC #3: Duplicate folder names rejected")
    def test_create_folder_duplicate(self, tools, open_project: Path):
        with allure.step("Create first folder"):
            tools.execute("create_folder", {"name": "Duplicated"})

        with allure.step("Try to create duplicate"):
            result = tools.execute("create_folder", {"name": "Duplicated"})

        with allure.step("Verify rejected"):
            assert isinstance(result, Failure)
            assert "duplicate" in str(result.failure()).lower()

    @allure.title("AC #4: rename_folder accepts folder_id and new_name")
    def test_rename_folder(self, app_context: AppContext, tools, open_project: Path):
        with allure.step("Create a folder"):
            create_result = tools.execute("create_folder", {"name": "Old Name"})
            assert isinstance(create_result, Success)
            folder_id = create_result.unwrap()["folder_id"]

        with allure.step("Rename folder"):
            result = tools.execute(
                "rename_folder",
                {"folder_id": folder_id, "new_name": "New Name"},
            )

        with allure.step("Verify renamed"):
            assert isinstance(result, Success)
            data = result.unwrap()
            assert data["success"] is True
            assert data["name"] == "New Name"

    @allure.title("AC #5: delete_folder rejects non-empty folder")
    def test_delete_folder_not_empty(
        self, app_context: AppContext, tools, open_project: Path
    ):
        from src.contexts.projects.core.entities import Source, SourceType
        from src.shared.common.types import FolderId, SourceId

        with allure.step("Create folder and source in it"):
            create_result = tools.execute("create_folder", {"name": "Non-Empty"})
            assert isinstance(create_result, Success)
            folder_id = create_result.unwrap()["folder_id"]

            source = Source(
                id=SourceId(100),
                name="in_folder.txt",
                source_type=SourceType.TEXT,
                folder_id=FolderId(value=folder_id),
            )
            app_context.sources_context.source_repo.save(source)

        with allure.step("Try to delete non-empty folder"):
            result = tools.execute("delete_folder", {"folder_id": folder_id})

        with allure.step("Verify rejected"):
            assert isinstance(result, Failure)

    @allure.title("AC #5: delete_folder succeeds for empty folder")
    def test_delete_empty_folder(self, tools, open_project: Path):
        with allure.step("Create folder"):
            create_result = tools.execute("create_folder", {"name": "To Delete"})
            assert isinstance(create_result, Success)
            folder_id = create_result.unwrap()["folder_id"]

        with allure.step("Delete empty folder"):
            result = tools.execute("delete_folder", {"folder_id": folder_id})

        with allure.step("Verify deleted"):
            assert isinstance(result, Success)
            data = result.unwrap()
            assert data["success"] is True

    @allure.title("AC #6: move_source_to_folder moves source between folders")
    def test_move_source_to_folder(
        self, app_context: AppContext, tools, open_project: Path
    ):
        from src.contexts.projects.core.entities import Source, SourceType
        from src.shared.common.types import SourceId

        with allure.step("Create folder and source"):
            create_result = tools.execute("create_folder", {"name": "Target Folder"})
            assert isinstance(create_result, Success)
            folder_id = create_result.unwrap()["folder_id"]

            source = Source(
                id=SourceId(200),
                name="movable.txt",
                source_type=SourceType.TEXT,
            )
            app_context.sources_context.source_repo.save(source)

        with allure.step("Move source to folder"):
            result = tools.execute(
                "move_source_to_folder",
                {"source_id": 200, "folder_id": folder_id},
            )

        with allure.step("Verify moved"):
            assert isinstance(result, Success)
            data = result.unwrap()
            assert data["success"] is True
            assert data["new_folder_id"] == folder_id

    @allure.title("AC #7: Folder operations publish domain events")
    def test_folder_events_published(
        self, app_context: AppContext, tools, open_project: Path
    ):
        events_received = []
        app_context.event_bus.subscribe(
            "projects.folder_created", lambda e: events_received.append(e)
        )

        with allure.step("Create folder"):
            result = tools.execute("create_folder", {"name": "Events Folder"})
            assert isinstance(result, Success)

        with allure.step("Verify event published"):
            assert len(events_received) >= 1

    @allure.title("AC #1 + AC #2: Create folders and list them")
    def test_create_and_list_folders(self, tools, open_project: Path):
        with allure.step("Create two folders"):
            tools.execute("create_folder", {"name": "Folder A"})
            tools.execute("create_folder", {"name": "Folder B"})

        with allure.step("List all folders"):
            result = tools.execute("list_folders", {})

        with allure.step("Verify both returned"):
            assert isinstance(result, Success)
            data = result.unwrap()
            assert data["total_count"] == 2
            names = [f["name"] for f in data["folders"]]
            assert "Folder A" in names
            assert "Folder B" in names


# ============================================================
# Integration: Full Agent Workflow
# ============================================================


@allure.story("QC-026.07 Agent Open/Close Project")
@allure.severity(allure.severity_level.CRITICAL)
class TestAgentFullWorkflow:
    @allure.title(
        "Integration: Agent creates project, adds sources, organizes, and cleans up"
    )
    def test_full_agent_workflow(self, app_context: AppContext, tools, tmp_path: Path):
        with allure.step("Step 1: Create and open project"):
            project_path = tmp_path / "agent_workflow.qda"
            app_context.create_project(
                name="Agent Workflow Project", path=str(project_path)
            )
            app_context.close_project()
            result = tools.execute("open_project", {"path": str(project_path)})
            assert isinstance(result, Success)

        with allure.step("Step 2: Add text sources"):
            r1 = tools.execute(
                "add_text_source",
                {"name": "interview_01.txt", "content": "First interview..."},
            )
            r2 = tools.execute(
                "add_text_source",
                {"name": "interview_02.txt", "content": "Second interview..."},
            )
            assert isinstance(r1, Success)
            assert isinstance(r2, Success)

        with allure.step("Step 3: Organize into folders"):
            folder_result = tools.execute("create_folder", {"name": "Interviews"})
            assert isinstance(folder_result, Success)
            folder_id = folder_result.unwrap()["folder_id"]

            source_id_1 = r1.unwrap()["source_id"]
            move_result = tools.execute(
                "move_source_to_folder",
                {"source_id": source_id_1, "folder_id": folder_id},
            )
            assert isinstance(move_result, Success)

        with allure.step("Step 4: List and verify"):
            sources = tools.execute("list_sources", {})
            assert isinstance(sources, Success)
            assert sources.unwrap()["count"] == 2

            folders = tools.execute("list_folders", {})
            assert isinstance(folders, Success)
            assert folders.unwrap()["total_count"] == 1

        with allure.step("Step 5: Preview deletion"):
            source_id_2 = r2.unwrap()["source_id"]
            preview = tools.execute(
                "remove_source", {"source_id": source_id_2, "confirm": False}
            )
            assert isinstance(preview, Success)
            assert preview.unwrap()["preview"] is True

        with allure.step("Step 6: Confirm deletion"):
            remove = tools.execute(
                "remove_source", {"source_id": source_id_2, "confirm": True}
            )
            assert isinstance(remove, Success)

        with allure.step("Step 7: Close project"):
            close = tools.execute("close_project", {})
            assert isinstance(close, Success)
            assert close.unwrap()["closed"] is True
