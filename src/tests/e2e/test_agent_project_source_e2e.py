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
def project_tools(app_context: AppContext):
    """Create ProjectTools instance for project lifecycle tools."""
    from src.contexts.projects.interface.mcp_tools import ProjectTools

    return ProjectTools(ctx=app_context)


@pytest.fixture
def source_tools(app_context: AppContext):
    """Create SourceTools instance for source management tools."""
    from src.contexts.sources.interface.mcp_tools import SourceTools

    return SourceTools(ctx=app_context)


@pytest.fixture
def folder_tools(app_context: AppContext):
    """Create FolderTools instance for folder management tools."""
    from src.contexts.folders.interface.mcp_tools import FolderTools

    return FolderTools(ctx=app_context)


# ============================================================
# QC-026.07: Agent Open/Close Project
# ============================================================


@allure.story("QC-026.07 Agent Open/Close Project")
@allure.severity(allure.severity_level.CRITICAL)
class TestAgentOpenCloseProject:
    @allure.title("AC #1+5: open/close project tools registered and redirect to UI")
    def test_project_tools_redirect_to_ui(
        self, project_tools, existing_project: Path
    ):
        with allure.step("Verify open_project tool schema"):
            schemas = project_tools.get_tool_schemas()
            tool_names = [s["name"] for s in schemas]
            assert "open_project" in tool_names
            assert "close_project" in tool_names
            schema = next(s for s in schemas if s["name"] == "open_project")
            assert "path" in schema["inputSchema"]["required"]

        with allure.step("Verify open_project redirects to UI"):
            result = project_tools.execute(
                "open_project", {"path": str(existing_project)}
            )
            assert isinstance(result, Success)
            data = result.unwrap()
            assert data["success"] is False
            assert "QualCoder UI" in data["message"]

        with allure.step("Verify close_project redirects to UI"):
            result = project_tools.execute("close_project", {})
            assert isinstance(result, Success)
            data = result.unwrap()
            assert data["success"] is False
            assert "QualCoder UI" in data["message"]


# ============================================================
# QC-027.12: Agent Add Text Source
# ============================================================


@allure.story("QC-027.12 Agent Add Text Source")
@allure.severity(allure.severity_level.CRITICAL)
@allure.feature("QC-027 Manage Sources")
class TestAgentAddTextSource:
    @allure.title("AC #1+2+4: Schema, add text source, persistence, and event")
    def test_schema_add_persist_and_event(
        self, app_context: AppContext, source_tools, open_project: Path
    ):
        with allure.step("Verify tool schema"):
            schemas = source_tools.get_tool_schemas()
            tool_names = [s["name"] for s in schemas]
            assert "add_text_source" in tool_names
            schema = next(s for s in schemas if s["name"] == "add_text_source")
            required = schema["inputSchema"]["required"]
            assert "name" in required
            assert "content" in required

        events_received = []
        app_context.event_bus.subscribe(
            "projects.source_added", lambda e: events_received.append(e)
        )

        with allure.step("Add text source via MCP tool"):
            result = source_tools.execute(
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

        with allure.step("Verify source in repository with content"):
            sources = app_context.sources_context.source_repo.get_all()
            names = [s.name for s in sources]
            assert "interview_01.txt" in names
            source = next(s for s in sources if s.name == "interview_01.txt")
            assert source.fulltext == "This is my interview transcript content."

        with allure.step("Verify event published"):
            assert len(events_received) >= 1

    @allure.title("AC #3+6: Duplicate names rejected and validation errors")
    def test_duplicate_and_validation(
        self, app_context: AppContext, source_tools, open_project: Path
    ):
        with allure.step("Add first source"):
            result1 = source_tools.execute(
                "add_text_source",
                {"name": "unique_doc.txt", "content": "First version"},
            )
            assert isinstance(result1, Success)

        with allure.step("Verify duplicate rejected"):
            result2 = source_tools.execute(
                "add_text_source",
                {"name": "unique_doc.txt", "content": "Second version"},
            )
            assert isinstance(result2, Failure)
            assert "already exists" in str(result2.failure())

        with allure.step("Verify empty name rejected"):
            result = source_tools.execute(
                "add_text_source", {"name": "", "content": "Some content"}
            )
            assert isinstance(result, Failure)

        with allure.step("Verify empty content rejected"):
            result = source_tools.execute(
                "add_text_source", {"name": "empty_doc.txt", "content": ""}
            )
            assert isinstance(result, Failure)


# ============================================================
# QC-027.14: Agent Remove Source
# ============================================================


@allure.story("QC-027.14 Agent Remove Source")
@allure.severity(allure.severity_level.CRITICAL)
@allure.feature("QC-027 Manage Sources")
class TestAgentRemoveSource:
    @allure.title("AC #1+3: Schema and non-existent source failure")
    def test_schema_and_not_found(self, source_tools, open_project: Path):
        with allure.step("Verify tool schema"):
            schemas = source_tools.get_tool_schemas()
            tool_names = [s["name"] for s in schemas]
            assert "remove_source" in tool_names
            schema = next(s for s in schemas if s["name"] == "remove_source")
            assert "source_id" in schema["inputSchema"]["required"]

        with allure.step("Try to remove non-existent source"):
            result = source_tools.execute(
                "remove_source", {"source_id": "9999", "confirm": True}
            )
            assert isinstance(result, Failure)
            assert "not found" in str(result.failure()).lower()

    @allure.title("AC #2+6: Preview mode and confirmed deletion")
    def test_preview_and_confirmed_delete(
        self, app_context: AppContext, source_tools, open_project: Path
    ):
        from src.contexts.projects.core.entities import Source, SourceType
        from src.shared.common.types import SourceId

        with allure.step("Add sources for testing"):
            source1 = Source(
                id=SourceId("42"),
                name="to_delete.txt",
                source_type=SourceType.TEXT,
                fulltext="Content to delete",
            )
            app_context.sources_context.source_repo.save(source1)
            source2 = Source(
                id=SourceId("43"),
                name="confirmed_delete.txt",
                source_type=SourceType.TEXT,
                fulltext="Will be deleted",
            )
            app_context.sources_context.source_repo.save(source2)
            source3 = Source(
                id=SourceId("44"), name="default.txt", source_type=SourceType.TEXT
            )
            app_context.sources_context.source_repo.save(source3)

        with allure.step("Preview deletion (confirm=false)"):
            result = source_tools.execute(
                "remove_source", {"source_id": "42", "confirm": False}
            )
            assert isinstance(result, Success)
            data = result.unwrap()
            assert data["preview"] is True
            assert data["source_name"] == "to_delete.txt"
            assert data["requires_approval"] is True
            assert "source_type" in data

        with allure.step("Default (no confirm) also returns preview"):
            result2 = source_tools.execute("remove_source", {"source_id": "44"})
            assert isinstance(result2, Success)
            assert result2.unwrap()["preview"] is True

        with allure.step("Confirm deletion"):
            result = source_tools.execute(
                "remove_source", {"source_id": "43", "confirm": True}
            )
            assert isinstance(result, Success)
            data = result.unwrap()
            assert data["success"] is True
            assert data["removed"] is True
            assert data["source_name"] == "confirmed_delete.txt"

        with allure.step("Verify source gone from repo"):
            source = app_context.sources_context.source_repo.get_by_id(SourceId("43"))
            assert source is None


# ============================================================
# QC-027.13: Agent Manage Folders
# ============================================================


@allure.story("QC-027.13 Agent Manage Folders")
@allure.severity(allure.severity_level.CRITICAL)
@allure.feature("QC-027 Manage Sources")
class TestAgentManageFolders:
    @allure.title("AC #1+2+3: List empty, create folder, reject duplicate")
    def test_list_create_and_duplicate(self, folder_tools, open_project: Path):
        with allure.step("List folders in empty project"):
            result = folder_tools.execute("list_folders", {})
            assert isinstance(result, Success)
            assert result.unwrap()["total_count"] == 0

        with allure.step("Create a folder"):
            result = folder_tools.execute("create_folder", {"name": "Interviews"})
            assert isinstance(result, Success)
            data = result.unwrap()
            assert data["success"] is True
            assert data["name"] == "Interviews"
            assert "folder_id" in data

        with allure.step("Reject duplicate"):
            folder_tools.execute("create_folder", {"name": "Duplicated"})
            result = folder_tools.execute("create_folder", {"name": "Duplicated"})
            assert isinstance(result, Failure)
            assert "duplicate" in str(result.failure()).lower()

    @allure.title("AC #4+5: Rename folder and reject delete of non-empty folder")
    def test_rename_and_delete_non_empty(
        self, app_context: AppContext, folder_tools, open_project: Path
    ):
        from src.contexts.projects.core.entities import Source, SourceType
        from src.shared.common.types import FolderId, SourceId

        with allure.step("Create and rename folder"):
            create_result = folder_tools.execute("create_folder", {"name": "Old Name"})
            assert isinstance(create_result, Success)
            folder_id = create_result.unwrap()["folder_id"]

            result = folder_tools.execute(
                "rename_folder",
                {"folder_id": folder_id, "new_name": "New Name"},
            )
            assert isinstance(result, Success)
            assert result.unwrap()["name"] == "New Name"

        with allure.step("Create non-empty folder and reject deletion"):
            create_result2 = folder_tools.execute(
                "create_folder", {"name": "Non-Empty"}
            )
            folder_id2 = create_result2.unwrap()["folder_id"]
            source = Source(
                id=SourceId("100"),
                name="in_folder.txt",
                source_type=SourceType.TEXT,
                folder_id=FolderId(value=folder_id2),
            )
            app_context.sources_context.source_repo.save(source)

            result = folder_tools.execute("delete_folder", {"folder_id": folder_id2})
            assert isinstance(result, Failure)

    @allure.title("AC #5+6: Delete empty folder and move source to folder")
    def test_delete_empty_and_move_source(
        self, app_context: AppContext, folder_tools, open_project: Path
    ):
        from src.contexts.projects.core.entities import Source, SourceType
        from src.shared.common.types import SourceId

        with allure.step("Create and delete empty folder"):
            create_result = folder_tools.execute(
                "create_folder", {"name": "To Delete"}
            )
            assert isinstance(create_result, Success)
            folder_id = create_result.unwrap()["folder_id"]

            result = folder_tools.execute("delete_folder", {"folder_id": folder_id})
            assert isinstance(result, Success)
            assert result.unwrap()["success"] is True

        with allure.step("Create folder and source, then move"):
            create_result = folder_tools.execute(
                "create_folder", {"name": "Target Folder"}
            )
            assert isinstance(create_result, Success)
            folder_id = create_result.unwrap()["folder_id"]

            source = Source(
                id=SourceId("200"),
                name="movable.txt",
                source_type=SourceType.TEXT,
            )
            app_context.sources_context.source_repo.save(source)

            result = folder_tools.execute(
                "move_source_to_folder",
                {"source_id": "200", "folder_id": folder_id},
            )
            assert isinstance(result, Success)
            data = result.unwrap()
            assert data["success"] is True
            assert data["new_folder_id"] == folder_id

    @allure.title("AC #7+1+2: Events published and create-then-list workflow")
    def test_events_and_create_list(
        self, app_context: AppContext, folder_tools, open_project: Path
    ):
        events_received = []
        app_context.event_bus.subscribe(
            "folders.folder_created", lambda e: events_received.append(e)
        )

        with allure.step("Create folder and verify event"):
            result = folder_tools.execute("create_folder", {"name": "Events Folder"})
            assert isinstance(result, Success)
            assert len(events_received) >= 1

        with allure.step("Create two more folders and list all"):
            folder_tools.execute("create_folder", {"name": "Folder A"})
            folder_tools.execute("create_folder", {"name": "Folder B"})

            result = folder_tools.execute("list_folders", {})
            assert isinstance(result, Success)
            data = result.unwrap()
            # Events Folder + Folder A + Folder B = 3
            assert data["total_count"] == 3
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
    def test_full_agent_workflow(
        self, app_context: AppContext, source_tools, folder_tools, tmp_path: Path
    ):
        with allure.step("Step 1: Create and open project via AppContext"):
            project_path = tmp_path / "agent_workflow.qda"
            app_context.create_project(
                name="Agent Workflow Project", path=str(project_path)
            )
            app_context.close_project()
            result = app_context.open_project(str(project_path))
            assert result.is_success

        with allure.step("Step 2: Add text sources"):
            r1 = source_tools.execute(
                "add_text_source",
                {"name": "interview_01.txt", "content": "First interview..."},
            )
            r2 = source_tools.execute(
                "add_text_source",
                {"name": "interview_02.txt", "content": "Second interview..."},
            )
            assert isinstance(r1, Success)
            assert isinstance(r2, Success)

        with allure.step("Step 3: Organize into folders"):
            folder_result = folder_tools.execute(
                "create_folder", {"name": "Interviews"}
            )
            assert isinstance(folder_result, Success)
            folder_id = folder_result.unwrap()["folder_id"]

            source_id_1 = r1.unwrap()["source_id"]
            move_result = folder_tools.execute(
                "move_source_to_folder",
                {"source_id": source_id_1, "folder_id": folder_id},
            )
            assert isinstance(move_result, Success)

        with allure.step("Step 4: List and verify"):
            sources = source_tools.execute("list_sources", {})
            assert isinstance(sources, Success)
            assert sources.unwrap()["count"] == 2

            folders = folder_tools.execute("list_folders", {})
            assert isinstance(folders, Success)
            assert folders.unwrap()["total_count"] == 1

        with allure.step("Step 5: Preview deletion"):
            source_id_2 = r2.unwrap()["source_id"]
            preview = source_tools.execute(
                "remove_source", {"source_id": source_id_2, "confirm": False}
            )
            assert isinstance(preview, Success)
            assert preview.unwrap()["preview"] is True

        with allure.step("Step 6: Confirm deletion"):
            remove = source_tools.execute(
                "remove_source", {"source_id": source_id_2, "confirm": True}
            )
            assert isinstance(remove, Success)

        with allure.step("Step 7: Close project via AppContext"):
            close_result = app_context.close_project()
            assert close_result.is_success


# ============================================================
# QC-027.15: Agent Import File Source
# ============================================================


@pytest.fixture
def sample_text_file(tmp_path: Path) -> Path:
    """Create a sample text file for import tests."""
    f = tmp_path / "interview.txt"
    f.write_text("This is an interview transcript.\nLine 2.")
    return f


@pytest.fixture
def sample_pdf_file(tmp_path: Path) -> Path:
    """Create a minimal PDF file for import tests."""
    f = tmp_path / "report.pdf"
    pdf_content = b"""%PDF-1.4
1 0 obj
<< /Type /Catalog /Pages 2 0 R >>
endobj
2 0 obj
<< /Type /Pages /Kids [3 0 R] /Count 1 >>
endobj
3 0 obj
<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] >>
endobj
xref
0 4
0000000000 65535 f
0000000009 00000 n
0000000058 00000 n
0000000115 00000 n
trailer
<< /Size 4 /Root 1 0 R >>
startxref
196
%%EOF"""
    f.write_bytes(pdf_content)
    return f


@pytest.fixture
def sample_image_file(tmp_path: Path) -> Path:
    """Create a minimal PNG file for import tests."""
    f = tmp_path / "photo.png"
    png_bytes = (
        b"\x89PNG\r\n\x1a\n"
        b"\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
        b"\x08\x02\x00\x00\x00\x90wS\xde"
        b"\x00\x00\x00\x0cIDATx\x9cc\xf8\x0f\x00\x00\x01\x01\x00\x05\x18\xd8N"
        b"\x00\x00\x00\x00IEND\xaeB`\x82"
    )
    f.write_bytes(png_bytes)
    return f


@pytest.fixture
def sample_audio_file(tmp_path: Path) -> Path:
    """Create a stub audio file for import tests."""
    f = tmp_path / "recording.mp3"
    f.write_bytes(b"\xff\xfb\x90\x00" + b"\x00" * 100)
    return f


@pytest.fixture
def sample_video_file(tmp_path: Path) -> Path:
    """Create a stub video file for import tests."""
    f = tmp_path / "clip.mp4"
    f.write_bytes(b"\x00\x00\x00\x1cftypisom" + b"\x00" * 100)
    return f


@allure.story("QC-027.15 Agent Import File Source")
@allure.severity(allure.severity_level.CRITICAL)
@allure.feature("QC-027 Manage Sources")
class TestAgentImportFileSource:
    @allure.title("AC #1+2+3: Schema, import text, and import PDF")
    def test_schema_text_and_pdf(
        self,
        source_tools,
        open_project: Path,
        sample_text_file: Path,
        sample_pdf_file: Path,
    ):
        with allure.step("Verify tool schema"):
            schemas = source_tools.get_tool_schemas()
            tool_names = [s["name"] for s in schemas]
            assert "import_file_source" in tool_names
            schema = next(s for s in schemas if s["name"] == "import_file_source")
            assert "file_path" in schema["inputSchema"]["required"]

        with allure.step("Import text file"):
            result = source_tools.execute(
                "import_file_source", {"file_path": str(sample_text_file)}
            )
            assert isinstance(result, Success)
            data = result.unwrap()
            assert data["success"] is True
            assert data["name"] == "interview.txt"
            assert data["type"] == "text"
            assert data["status"] == "imported"

        with allure.step("Import PDF file"):
            result = source_tools.execute(
                "import_file_source", {"file_path": str(sample_pdf_file)}
            )
            assert isinstance(result, Success)
            data = result.unwrap()
            assert data["success"] is True
            assert data["name"] == "report.pdf"
            assert data["type"] == "pdf"

    @allure.title("AC #4+5: Import image, audio, and video files")
    def test_image_audio_video(
        self,
        source_tools,
        open_project: Path,
        sample_image_file: Path,
        sample_audio_file: Path,
        sample_video_file: Path,
    ):
        with allure.step("Import image file"):
            result = source_tools.execute(
                "import_file_source", {"file_path": str(sample_image_file)}
            )
            assert isinstance(result, Success)
            data = result.unwrap()
            assert data["success"] is True
            assert data["name"] == "photo.png"
            assert data["type"] == "image"

        with allure.step("Import audio file"):
            result = source_tools.execute(
                "import_file_source", {"file_path": str(sample_audio_file)}
            )
            assert isinstance(result, Success)
            assert result.unwrap()["type"] == "audio"

        with allure.step("Import video file"):
            result = source_tools.execute(
                "import_file_source", {"file_path": str(sample_video_file)}
            )
            assert isinstance(result, Success)
            assert result.unwrap()["type"] == "video"

    @allure.title("AC #6+7: Auto-detect file type and reject non-existent files")
    def test_type_detection_and_nonexistent(
        self, source_tools, open_project: Path, tmp_path: Path
    ):
        with allure.step("Create files with various extensions"):
            jpg = tmp_path / "photo.jpg"
            jpg.write_bytes(b"\xff\xd8\xff\xe0" + b"\x00" * 50)
            wav = tmp_path / "audio.wav"
            wav.write_bytes(b"RIFF" + b"\x00" * 50)

        with allure.step("Import jpg (should be image)"):
            r1 = source_tools.execute("import_file_source", {"file_path": str(jpg)})
            assert isinstance(r1, Success)
            assert r1.unwrap()["type"] == "image"

        with allure.step("Import wav (should be audio)"):
            r2 = source_tools.execute("import_file_source", {"file_path": str(wav)})
            assert isinstance(r2, Success)
            assert r2.unwrap()["type"] == "audio"

        with allure.step("Non-existent file returns failure"):
            result = source_tools.execute(
                "import_file_source",
                {"file_path": str(tmp_path / "does_not_exist.txt")},
            )
            assert isinstance(result, Failure)
            assert "not found" in str(result.failure()).lower()

    @allure.title("AC #8+9: Unsupported extensions and duplicate names rejected")
    def test_unsupported_and_duplicate(
        self, source_tools, open_project: Path, tmp_path: Path, sample_text_file: Path
    ):
        with allure.step("Reject unsupported extension"):
            f = tmp_path / "data.xyz"
            f.write_bytes(b"some data")
            result = source_tools.execute("import_file_source", {"file_path": str(f)})
            assert isinstance(result, Failure)
            error_msg = str(result.failure())
            assert "unsupported" in error_msg.lower()
            assert ".txt" in error_msg

        with allure.step("Import file first time"):
            r1 = source_tools.execute(
                "import_file_source", {"file_path": str(sample_text_file)}
            )
            assert isinstance(r1, Success)

        with allure.step("Reject duplicate name"):
            r2 = source_tools.execute(
                "import_file_source", {"file_path": str(sample_text_file)}
            )
            assert isinstance(r2, Failure)
            assert "already exists" in str(r2.failure())

    @allure.title("AC #10+11: Name override and SourceAdded event published")
    def test_name_override_and_event(
        self,
        app_context: AppContext,
        source_tools,
        open_project: Path,
        sample_text_file: Path,
    ):
        events_received = []
        app_context.event_bus.subscribe(
            "projects.source_added", lambda e: events_received.append(e)
        )

        with allure.step("Import with custom name"):
            result = source_tools.execute(
                "import_file_source",
                {
                    "file_path": str(sample_text_file),
                    "name": "Custom Interview Name",
                },
            )
            assert isinstance(result, Success)
            assert result.unwrap()["name"] == "Custom Interview Name"

        with allure.step("Verify SourceAdded event"):
            assert len(events_received) >= 1

    @allure.title("Text content extracted and media has no fulltext")
    def test_text_content_and_media_no_fulltext(
        self,
        app_context: AppContext,
        source_tools,
        open_project: Path,
        sample_text_file: Path,
        sample_image_file: Path,
    ):
        with allure.step("Import text file and verify content"):
            result = source_tools.execute(
                "import_file_source", {"file_path": str(sample_text_file)}
            )
            assert isinstance(result, Success)
            source_id = result.unwrap()["source_id"]

            from src.shared.common.types import SourceId

            source = app_context.sources_context.source_repo.get_by_id(
                SourceId(value=source_id)
            )
            assert source is not None
            assert source.fulltext is not None
            assert "interview transcript" in source.fulltext

        with allure.step("Import image and verify no fulltext"):
            result = source_tools.execute(
                "import_file_source", {"file_path": str(sample_image_file)}
            )
            assert isinstance(result, Success)
            source_id = result.unwrap()["source_id"]

            source = app_context.sources_context.source_repo.get_by_id(
                SourceId(value=source_id)
            )
            assert source is not None
            assert source.fulltext is None

    @allure.title("Dry run validates without importing and relative path rejected")
    def test_dry_run_and_relative_path(
        self,
        app_context: AppContext,
        source_tools,
        open_project: Path,
        sample_text_file: Path,
    ):
        with allure.step("Dry run import"):
            result = source_tools.execute(
                "import_file_source",
                {"file_path": str(sample_text_file), "dry_run": True},
            )
            assert isinstance(result, Success)
            data = result.unwrap()
            assert data["dry_run"] is True
            assert data["name"] == "interview.txt"
            assert data["source_type"] == "text"
            assert data["file_size"] > 0

        with allure.step("Verify source NOT persisted"):
            sources = app_context.sources_context.source_repo.get_all()
            names = [s.name for s in sources]
            assert "interview.txt" not in names

        with allure.step("Reject relative path"):
            result = source_tools.execute(
                "import_file_source", {"file_path": "relative/path.txt"}
            )
            assert isinstance(result, Failure)
            assert "absolute" in str(result.failure()).lower()
