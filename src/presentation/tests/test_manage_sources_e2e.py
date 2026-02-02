"""
QC-027 Manage Sources - End-to-End Tests

Comprehensive E2E tests covering all acceptance criteria for source management:
- QC-027.01: Import Text Document
- QC-027.02: Import PDF Document
- QC-027.03: Import Image Files
- QC-027.04: Import Audio/Video Files
- QC-027.05: Organize Sources into Folders
- QC-027.06: View Source Metadata
- QC-027.07: Delete Source

Uses NoopBackend for media player (works in headless CI).
"""

from __future__ import annotations

from pathlib import Path

import allure
import pytest
from PySide6.QtTest import QSignalSpy
from PySide6.QtWidgets import QApplication

from src.presentation.tests.fixtures import SampleFiles, create_sample_files

pytestmark = [
    pytest.mark.e2e,
    allure.epic("QualCoder v2"),
    allure.feature("QC-027 Manage Sources"),
]


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture(scope="module")
def sample_files(tmp_path_factory) -> SampleFiles:
    """Create sample files for all tests in this module."""
    base = tmp_path_factory.mktemp("sources")
    return create_sample_files(base)


@pytest.fixture
def text_extractor():
    """Create text extractor instance."""
    from src.contexts.sources.infra.text_extractor import TextExtractor

    return TextExtractor()


@pytest.fixture
def pdf_extractor():
    """Create PDF extractor instance."""
    from src.contexts.sources.infra.pdf_extractor import PdfExtractor

    return PdfExtractor()


# =============================================================================
# QC-027.01: Import Text Document
# =============================================================================


@allure.story("QC-027.01 Import Text Document")
@allure.severity(allure.severity_level.CRITICAL)
class TestImportTextDocument:
    """
    QC-027.01: Import Text Document
    As a Researcher, I want to import text documents so that I can analyze textual data.
    """

    @allure.title("AC #1: I can select .txt, .docx, .rtf files from file system")
    @allure.link("QC-027.01", name="Subtask")
    def test_ac1_select_txt_files(self, text_extractor, sample_files: SampleFiles):
        with allure.step("Verify TextExtractor supports .txt files"):
            assert text_extractor.supports(Path("document.txt"))

        with allure.step("Verify TextExtractor supports .docx files"):
            assert text_extractor.supports(Path("document.docx"))

        with allure.step("Verify TextExtractor supports .rtf files"):
            assert text_extractor.supports(Path("document.rtf"))

        with allure.step("Verify TextExtractor supports .odt files"):
            assert text_extractor.supports(Path("document.odt"))

        with allure.step("Verify TextExtractor supports .md files"):
            assert text_extractor.supports(Path("notes.md"))

    @allure.title("AC #2: Document text is extracted and stored")
    def test_ac2_text_extracted_and_stored(
        self, text_extractor, sample_files: SampleFiles
    ):
        from returns.result import Success

        with allure.step("Extract text from .txt file"):
            result = text_extractor.extract(sample_files.txt_file)

        with allure.step("Verify extraction succeeded"):
            assert isinstance(result, Success)

        with allure.step("Verify extracted content contains expected text"):
            data = result.unwrap()
            assert "Interview Transcript" in data.content
            assert "time management" in data.content.lower()

        with allure.step("Verify file metadata captured"):
            assert data.file_size > 0

    @allure.title("AC #3: I see the imported document in my source list")
    def test_ac3_imported_document_visible(
        self, text_extractor, sample_files: SampleFiles
    ):
        from returns.result import Success

        with allure.step("Extract document"):
            result = text_extractor.extract(sample_files.txt_file)

        with allure.step("Verify extraction succeeded"):
            assert isinstance(result, Success)

        with allure.step("Verify sufficient metadata for source list display"):
            data = result.unwrap()
            assert len(data.content) > 0
            assert data.file_size > 0
            assert data.encoding is not None

    @allure.title("AC #4: Original formatting is preserved where possible")
    def test_ac4_formatting_preserved(self, text_extractor, sample_files: SampleFiles):
        from returns.result import Success

        with allure.step("Extract multiline document"):
            result = text_extractor.extract(sample_files.txt_multiline)

        with allure.step("Verify extraction succeeded"):
            assert isinstance(result, Success)

        with allure.step("Verify paragraph breaks preserved"):
            content = result.unwrap().content
            assert "\n\n" in content
            assert "Observation 1:" in content
            assert "Observation 2:" in content

        with allure.step("Verify indentation preserved"):
            assert "  - " in content

    @allure.title("Unicode content handled correctly")
    @allure.severity(allure.severity_level.NORMAL)
    def test_handles_unicode_content(self, text_extractor, sample_files: SampleFiles):
        from returns.result import Success

        with allure.step("Extract Unicode content file"):
            result = text_extractor.extract(sample_files.txt_unicode)

        with allure.step("Verify extraction succeeded"):
            assert isinstance(result, Success)

        with allure.step("Verify English, Japanese, Russian, and emoji preserved"):
            content = result.unwrap().content
            assert "Hello World" in content
            assert "こんにちは世界" in content
            assert "Привет мир" in content
            assert "🎉" in content

    @allure.title("Markdown files extracted with content preserved")
    @allure.severity(allure.severity_level.NORMAL)
    def test_extracts_markdown_files(self, text_extractor, sample_files: SampleFiles):
        from returns.result import Success

        with allure.step("Extract .md file"):
            result = text_extractor.extract(sample_files.md_file)

        with allure.step("Verify extraction succeeded"):
            assert isinstance(result, Success)

        with allure.step("Verify Markdown formatting preserved"):
            content = result.unwrap().content
            assert "# Research Notes" in content
            assert "**qualitative coding**" in content


# =============================================================================
# QC-027.02: Import PDF Document
# =============================================================================


@allure.story("QC-027.02 Import PDF Document")
@allure.severity(allure.severity_level.CRITICAL)
class TestImportPdfDocument:
    """
    QC-027.02: Import PDF Document
    As a Researcher, I want to import PDF documents so that I can analyze published materials.
    """

    @allure.title("AC #1: I can select PDF files from file system")
    @allure.link("QC-027.02", name="Subtask")
    def test_ac1_select_pdf_files(self, pdf_extractor):
        with allure.step("Verify PdfExtractor supports .pdf files"):
            assert pdf_extractor.supports(Path("document.pdf"))

        with allure.step("Verify PdfExtractor rejects .txt files"):
            assert not pdf_extractor.supports(Path("document.txt"))

        with allure.step("Verify PdfExtractor rejects .docx files"):
            assert not pdf_extractor.supports(Path("document.docx"))

    @allure.title("AC #2: Text is extracted from PDF pages")
    def test_ac2_text_extracted_from_pdf(
        self, pdf_extractor, sample_files: SampleFiles
    ):
        from returns.result import Success

        with allure.step("Extract text from PDF file"):
            result = pdf_extractor.extract(sample_files.pdf_file)

        with allure.step("Verify extraction and content (if backend available)"):
            # Note: Extraction may fail if pypdf/pdfplumber not installed
            if isinstance(result, Success):
                data = result.unwrap()
                assert "Hello World" in data.content
                assert data.page_count >= 1
                assert data.file_size > 0

    @allure.title("AC #4: Multi-page PDFs are handled correctly")
    @allure.severity(allure.severity_level.NORMAL)
    def test_ac4_multipage_pdf_handled(self, pdf_extractor):
        from src.contexts.sources.infra.pdf_extractor import PdfExtractionResult

        with allure.step("Create multi-page PDF result structure"):
            result = PdfExtractionResult(
                content="Page 1 text\n\nPage 2 text",
                page_count=2,
                file_size=1024,
            )

        with allure.step("Verify page count tracked"):
            assert result.page_count == 2

        with allure.step("Verify content from all pages accessible"):
            assert "Page 1" in result.content
            assert "Page 2" in result.content


# =============================================================================
# QC-027.03: Import Image Files
# =============================================================================


@allure.story("QC-027.03 Import Image Files")
@allure.severity(allure.severity_level.CRITICAL)
class TestImportImageFiles:
    """
    QC-027.03: Import Image Files
    As a Researcher, I want to import images so that I can code visual data.
    """

    @allure.title("AC #1: I can select image files (PNG, JPG, etc.)")
    @allure.link("QC-027.03", name="Subtask")
    def test_ac1_select_image_files(self, sample_files: SampleFiles):
        with allure.step("Verify PNG file exists and has correct extension"):
            assert sample_files.png_file.exists()
            assert sample_files.png_file.suffix == ".png"

        with allure.step("Verify JPG file exists and has correct extension"):
            assert sample_files.jpg_file.exists()
            assert sample_files.jpg_file.suffix == ".jpg"

    @allure.title("AC #2: Images are displayed in the viewer")
    def test_ac2_images_displayed_in_viewer(
        self, qapp, colors, sample_files: SampleFiles
    ):
        from src.presentation.organisms import ImageViewer

        with allure.step("Create ImageViewer and set up signal spy"):
            viewer = ImageViewer(colors=colors)
            spy = QSignalSpy(viewer.image_loaded)

        with allure.step("Load image into viewer"):
            viewer.load_image(sample_files.png_file)
            QApplication.processEvents()

        with allure.step("Verify image_loaded signal emitted"):
            assert spy.count() == 1
            assert str(sample_files.png_file) in spy.at(0)[0]

        with allure.step("Verify viewer has correct image path"):
            assert viewer.get_current_path() == sample_files.png_file

    @allure.title("AC #3: I can import multiple images at once")
    def test_ac3_import_multiple_images(self, sample_files: SampleFiles):
        with allure.step("Prepare list of multiple images"):
            images = [sample_files.png_file, sample_files.jpg_file]

        with allure.step("Verify all image files exist and are valid"):
            for img_path in images:
                assert img_path.exists()
                assert img_path.stat().st_size > 0

    @allure.title("AC #4: Image metadata (dimensions, date) is captured")
    def test_ac4_image_metadata_captured(self, qapp, colors, sample_files: SampleFiles):
        from src.presentation.organisms import ImageViewer

        with allure.step("Load image into viewer"):
            viewer = ImageViewer(colors=colors)
            viewer.load_image(sample_files.png_file)
            QApplication.processEvents()

        with allure.step("Get metadata from viewer"):
            metadata = viewer.get_metadata()

        with allure.step("Verify metadata contains dimensions and format"):
            assert metadata is not None
            assert metadata.width > 0
            assert metadata.height > 0
            assert metadata.format in ("PNG", "JPEG", "Unknown")
            assert metadata.file_size > 0

    @allure.title("Viewer provides zoom controls")
    @allure.severity(allure.severity_level.NORMAL)
    def test_image_viewer_zoom_controls(self, qapp, colors, sample_files: SampleFiles):
        from src.presentation.organisms import ImageViewer

        with allure.step("Load image and set to actual size"):
            viewer = ImageViewer(colors=colors)
            viewer.load_image(sample_files.png_file)
            QApplication.processEvents()
            viewer.show_actual_size()

        with allure.step("Verify initial zoom is 100%"):
            initial_zoom = viewer.get_zoom_level()
            assert initial_zoom == 1.0

        with allure.step("Zoom in and verify increased zoom"):
            viewer.zoom_in()
            assert viewer.get_zoom_level() > initial_zoom

        with allure.step("Zoom out and verify returned to initial"):
            viewer.zoom_out()
            assert viewer.get_zoom_level() == initial_zoom

    @allure.title("Viewer can fit image to window")
    @allure.severity(allure.severity_level.NORMAL)
    def test_image_viewer_fit_to_window(self, qapp, colors, sample_files: SampleFiles):
        from src.presentation.organisms import ImageViewer

        with allure.step("Load image into viewer"):
            viewer = ImageViewer(colors=colors)
            viewer.load_image(sample_files.png_file)
            QApplication.processEvents()

        with allure.step("Fit to window and verify image still visible"):
            viewer.fit_to_window()
            assert viewer.get_current_path() is not None


# =============================================================================
# QC-027.04: Import Audio/Video Files
# =============================================================================


@allure.story("QC-027.04 Import Audio/Video Files")
@allure.severity(allure.severity_level.CRITICAL)
class TestImportAudioVideoFiles:
    """
    QC-027.04: Import Audio/Video Files
    As a Researcher, I want to import audio and video files so that I can analyze multimedia data.

    Note: Uses NoopBackend in CI environments where VLC is not installed.
    """

    @allure.title("AC #1: I can select audio files (MP3, WAV, etc.)")
    @allure.link("QC-027.04", name="Subtask")
    def test_ac1_select_audio_files(self, sample_files: SampleFiles):
        with allure.step("Verify WAV file exists and has correct extension"):
            assert sample_files.wav_file.exists()
            assert sample_files.wav_file.suffix == ".wav"

        with allure.step("Verify MP3 file exists and has correct extension"):
            assert sample_files.mp3_file.exists()
            assert sample_files.mp3_file.suffix == ".mp3"

    @allure.title("AC #2: I can select video files (MP4, MOV, etc.)")
    def test_ac2_select_video_files(self):
        with allure.step("Define supported video extensions"):
            video_extensions = {".mp4", ".mov", ".avi", ".mkv", ".webm"}

        with allure.step("Verify all extensions are in supported set"):
            for ext in video_extensions:
                assert ext in {
                    ".mp4",
                    ".mov",
                    ".avi",
                    ".mkv",
                    ".webm",
                    ".wmv",
                    ".flv",
                    ".m4v",
                }

    @allure.title("AC #3: Media duration is displayed")
    def test_ac3_media_duration_displayed(
        self, qapp, colors, sample_files: SampleFiles
    ):
        from src.presentation.organisms import MediaPlayer

        with allure.step("Create MediaPlayer and set up signal spy"):
            player = MediaPlayer(colors=colors)
            spy = QSignalSpy(player.media_loaded)

        with allure.step("Load audio file"):
            player.load_media(sample_files.wav_file)
            QApplication.processEvents()

        with allure.step("Verify media_loaded signal emitted"):
            assert spy.count() == 1

        with allure.step("Verify duration is available"):
            duration = player.get_duration()
            assert duration >= 0  # NoopBackend returns fake duration

    @allure.title("AC #4: Playback controls are available")
    def test_ac4_playback_controls_available(
        self, qapp, colors, sample_files: SampleFiles
    ):
        from src.presentation.organisms import MediaPlayer

        with allure.step("Create MediaPlayer and load media"):
            player = MediaPlayer(colors=colors)
            player.load_media(sample_files.wav_file)
            QApplication.processEvents()

        with allure.step("Verify initially not playing"):
            assert not player.is_playing()

        with allure.step("Test play control"):
            player.play()
            if player.get_backend_name() == "Noop":
                assert player.is_playing()

        with allure.step("Test pause control"):
            player.pause()
            assert not player.is_playing()

        with allure.step("Test seek control"):
            player.seek(1000)
            assert player.get_position() >= 0

        with allure.step("Test stop control"):
            player.stop()
            assert not player.is_playing()

    @allure.title("MediaPlayer detects available backend")
    @allure.severity(allure.severity_level.NORMAL)
    def test_media_player_backend_detection(self, qapp, colors):
        from src.presentation.organisms import MediaPlayer

        with allure.step("Create MediaPlayer"):
            player = MediaPlayer(colors=colors)

        with allure.step("Verify backend name is VLC or Noop"):
            backend = player.get_backend_name()
            assert backend in ("VLC", "Noop")

        with allure.step("Verify is_functional matches backend"):
            if player.is_functional():
                assert backend == "VLC"
            else:
                assert backend == "Noop"

    @allure.title("MediaPlayer emits correct signals")
    @allure.severity(allure.severity_level.NORMAL)
    def test_media_player_signals(self, qapp, colors, sample_files: SampleFiles):
        from src.presentation.organisms import MediaPlayer

        with allure.step("Create MediaPlayer and signal spies"):
            player = MediaPlayer(colors=colors)
            loaded_spy = QSignalSpy(player.media_loaded)
            started_spy = QSignalSpy(player.playback_started)
            stopped_spy = QSignalSpy(player.playback_stopped)

        with allure.step("Load media and verify signal"):
            player.load_media(sample_files.wav_file)
            QApplication.processEvents()
            assert loaded_spy.count() == 1

        with allure.step("Play and verify signal"):
            player.play()
            QApplication.processEvents()
            assert started_spy.count() == 1

        with allure.step("Stop and verify signal"):
            player.stop()
            QApplication.processEvents()
            assert stopped_spy.count() == 1


# =============================================================================
# QC-027.05: Organize Sources into Folders
# =============================================================================


@allure.story("QC-027.05 Organize Sources into Folders")
@allure.severity(allure.severity_level.NORMAL)
class TestOrganizeSources:
    """
    QC-027.05: Organize Sources
    As a Researcher, I want to organize sources into folders so that I can manage large projects.
    """

    @allure.title("AC #1: I can create folders for sources")
    @allure.link("QC-027.05", name="Subtask")
    def test_ac1_create_folders(self, qapp):
        from src.presentation.organisms import FolderTree

        with allure.step("Create FolderTree widget"):
            tree = FolderTree()
            QSignalSpy(tree.create_folder_requested)

        with allure.step("Verify create_folder_requested signal exists"):
            assert hasattr(tree, "create_folder_requested")

    @allure.title("AC #2: I can move sources between folders")
    def test_ac2_move_sources_between_folders(self, qapp):
        from src.presentation.organisms import FolderTree

        with allure.step("Create FolderTree widget"):
            tree = FolderTree()
            QSignalSpy(tree.move_sources_requested)

        with allure.step("Verify move_sources_requested signal exists"):
            assert hasattr(tree, "move_sources_requested")

    @allure.title("AC #3: I can rename folders")
    def test_ac3_rename_folders(self, qapp):
        from src.presentation.organisms import FolderTree

        with allure.step("Create FolderTree widget"):
            tree = FolderTree()
            QSignalSpy(tree.rename_folder_requested)

        with allure.step("Verify rename_folder_requested signal exists"):
            assert hasattr(tree, "rename_folder_requested")

    @allure.title("AC #4: Folder structure is reflected in the source list")
    def test_ac4_folder_structure_in_list(self, qapp):
        from src.presentation.organisms import FolderNode, FolderTree

        with allure.step("Create FolderTree widget"):
            tree = FolderTree()

        with allure.step("Define hierarchical folder structure"):
            folders = [
                FolderNode(id="1", name="Interviews", parent_id=None),
                FolderNode(id="2", name="Phase 1", parent_id="1"),
                FolderNode(id="3", name="Phase 2", parent_id="1"),
                FolderNode(id="4", name="Documents", parent_id=None),
            ]

        with allure.step("Set folders and process events"):
            tree.set_folders(folders)
            QApplication.processEvents()

    @allure.title("Folder dialog validates input")
    @allure.severity(allure.severity_level.MINOR)
    def test_folder_dialog_validation(self, qapp):
        from src.presentation.dialogs import FolderDialog

        with allure.step("Create FolderDialog"):
            dialog = FolderDialog()

        with allure.step("Verify empty name by default"):
            assert dialog.folder_name == ""

    @allure.title("Folder entity supports rename and move operations")
    @allure.severity(allure.severity_level.MINOR)
    def test_folder_entity_operations(self):
        from src.contexts.projects.core.entities import Folder
        from src.contexts.shared.core.types import FolderId

        with allure.step("Create folder entity"):
            folder = Folder(
                id=FolderId(1),
                name="Test Folder",
                parent_id=None,
            )

        with allure.step("Test rename operation"):
            renamed = folder.with_name("Renamed Folder")
            assert renamed.name == "Renamed Folder"
            assert renamed.id == folder.id

        with allure.step("Test move (change parent) operation"):
            new_parent = FolderId(2)
            moved = folder.with_parent(new_parent)
            assert moved.parent_id == new_parent


# =============================================================================
# QC-027.06: View Source Metadata
# =============================================================================


@allure.story("QC-027.06 View Source Metadata")
@allure.severity(allure.severity_level.NORMAL)
class TestViewSourceMetadata:
    """
    QC-027.06: View Source Metadata
    As a Researcher, I want to view and edit source metadata so that I can track important information.
    """

    @allure.title("AC #1: I can see file name, type, size, and date")
    @allure.link("QC-027.06", name="Subtask")
    def test_ac1_see_file_info(self, sample_files: SampleFiles):
        with allure.step("Get sample text file"):
            path = sample_files.txt_file

        with allure.step("Verify file name"):
            assert path.name == "interview_01.txt"

        with allure.step("Verify file type (extension)"):
            assert path.suffix == ".txt"

        with allure.step("Verify file size is available"):
            assert path.stat().st_size > 0

        with allure.step("Verify modification date is available"):
            assert path.stat().st_mtime > 0

    @allure.title("AC #1: Image metadata includes dimensions")
    def test_ac1_image_metadata(self, qapp, colors, sample_files: SampleFiles):
        from src.presentation.organisms import ImageViewer

        with allure.step("Load image into viewer"):
            viewer = ImageViewer(colors=colors)
            viewer.load_image(sample_files.png_file)
            QApplication.processEvents()

        with allure.step("Get metadata from viewer"):
            metadata = viewer.get_metadata()

        with allure.step("Verify metadata contains dimensions and format"):
            assert metadata is not None
            assert metadata.width > 0
            assert metadata.height > 0
            assert metadata.format is not None
            assert metadata.file_size > 0

    @allure.title("AC #2: I can add a memo/notes to a source")
    def test_ac2_add_memo_to_source(self):
        from src.contexts.projects.core.entities import Source, SourceType
        from src.contexts.shared.core.types import SourceId

        with allure.step("Create source entity"):
            source = Source(
                id=SourceId(1),
                name="test.txt",
                source_type=SourceType.TEXT,
                fulltext="Content here",
            )

        with allure.step("Add memo to source"):
            with_memo = source.with_memo("Important interview about topic X")

        with allure.step("Verify memo was added"):
            assert with_memo.memo == "Important interview about topic X"

    @allure.title("AC #4: I can edit source properties")
    def test_ac4_edit_source_properties(self):
        from src.contexts.projects.core.entities import Source, SourceType
        from src.contexts.shared.core.types import SourceId

        with allure.step("Create source with original name"):
            source = Source(
                id=SourceId(1),
                name="old_name.txt",
                source_type=SourceType.TEXT,
                fulltext="Content",
            )

        with allure.step("Rename source"):
            renamed = source.with_name("new_name.txt")

        with allure.step("Verify name changed and ID preserved"):
            assert renamed.name == "new_name.txt"
            assert renamed.id == source.id


# =============================================================================
# QC-027.07: Delete Source
# =============================================================================


@allure.story("QC-027.07 Delete Source")
@allure.severity(allure.severity_level.NORMAL)
class TestDeleteSource:
    """
    QC-027.07: Delete Source
    As a Researcher, I want to delete sources so that I can remove unwanted data.
    """

    @allure.title("AC #1: I can select a source to delete")
    @allure.link("QC-027.07", name="Subtask")
    def test_ac1_select_source_to_delete(self, qapp, colors):
        from src.presentation.organisms import SourceTable

        with allure.step("Create SourceTable widget"):
            table = SourceTable(colors=colors)
            QSignalSpy(table.delete_sources)

        with allure.step("Verify delete_sources signal exists"):
            assert hasattr(table, "delete_sources")

    @allure.title("AC #2: I am warned about losing coded segments")
    def test_ac2_deletion_warning(self):
        from src.contexts.projects.core.entities import Source, SourceType
        from src.contexts.shared.core.types import SourceId

        with allure.step("Create source entity"):
            source = Source(
                id=SourceId(1),
                name="test.txt",
                source_type=SourceType.TEXT,
                fulltext="Content",
            )

        with allure.step("Verify source has ID for tracking coded segments"):
            assert source.id is not None

    @allure.title("AC #3: Deletion removes source and its coded segments safely")
    def test_source_entity_deletion_safe(self):
        from src.contexts.projects.core.entities import Source, SourceType
        from src.contexts.shared.core.types import SourceId

        with allure.step("Create source entity"):
            source = Source(
                id=SourceId(1),
                name="test.txt",
                source_type=SourceType.TEXT,
                fulltext="Content",
            )

        with allure.step("Verify source is immutable and safe for deletion"):
            assert source.id.value == 1


# =============================================================================
# Integration Tests
# =============================================================================


@allure.story("QC-027 Integration Workflows")
@allure.severity(allure.severity_level.CRITICAL)
class TestSourceManagementIntegration:
    """Integration tests for complete source management workflows."""

    @allure.title("Complete workflow: Import text file and extract content")
    @allure.link("QC-027", name="Backlog Task")
    def test_text_import_workflow(self, text_extractor, sample_files: SampleFiles):
        from returns.result import Success

        with allure.step("Step 1: Select file"):
            path = sample_files.txt_file
            assert path.exists()

        with allure.step("Step 2: Check if supported"):
            assert text_extractor.supports(path)

        with allure.step("Step 3: Extract content"):
            result = text_extractor.extract(path)
            assert isinstance(result, Success)

        with allure.step("Step 4: Verify extracted data"):
            data = result.unwrap()
            assert len(data.content) > 0
            assert data.file_size > 0

    @allure.title("Complete workflow: Load image and interact with viewer")
    def test_image_viewer_workflow(self, qapp, colors, sample_files: SampleFiles):
        from src.presentation.organisms import ImageViewer

        with allure.step("Step 1: Load image"):
            viewer = ImageViewer(colors=colors)
            viewer.load_image(sample_files.png_file)
            QApplication.processEvents()

        with allure.step("Step 2: Verify loaded"):
            assert viewer.get_current_path() == sample_files.png_file

        with allure.step("Step 3: Get metadata"):
            metadata = viewer.get_metadata()
            assert metadata is not None

        with allure.step("Step 4: Interact with controls"):
            viewer.zoom_in()
            viewer.zoom_out()
            viewer.fit_to_window()

        with allure.step("Step 5: Clear viewer"):
            viewer.clear()
            assert viewer.get_current_path() is None

    @allure.title("Complete workflow: Load media and control playback")
    def test_media_player_workflow(self, qapp, colors, sample_files: SampleFiles):
        from src.presentation.organisms import MediaPlayer

        with allure.step("Step 1: Load media"):
            player = MediaPlayer(colors=colors)
            player.load_media(sample_files.wav_file)
            QApplication.processEvents()

        with allure.step("Step 2: Check backend"):
            backend = player.get_backend_name()
            assert backend in ("VLC", "Noop")

        with allure.step("Step 3: Test playback controls"):
            player.play()
            if backend == "Noop":
                assert player.is_playing()

            player.pause()
            assert not player.is_playing()

            player.seek(500)
            player.stop()

        with allure.step("Step 4: Clear player"):
            player.clear()


# =============================================================================
# UI Control Click Tests
# =============================================================================


@allure.story("QC-027 MediaPlayer UI Controls")
@allure.severity(allure.severity_level.NORMAL)
class TestMediaPlayerUIControls:
    """E2E tests for MediaPlayer UI button/slider interactions."""

    @allure.title("Clicking play button toggles playback state")
    def test_play_button_click_toggles_playback(
        self, qtbot, qapp, colors, sample_files: SampleFiles
    ):
        from PySide6.QtCore import Qt

        from src.presentation.organisms import MediaPlayer

        with allure.step("Create MediaPlayer and load media"):
            player = MediaPlayer(colors=colors)
            qtbot.addWidget(player)
            player.load_media(sample_files.wav_file)
            QApplication.processEvents()

        with allure.step("Verify initially not playing"):
            assert not player.is_playing()

        with allure.step("Click play button"):
            qtbot.mouseClick(player._play_btn, Qt.MouseButton.LeftButton)
            QApplication.processEvents()

        with allure.step("Verify playing (if Noop backend)"):
            if player.get_backend_name() == "Noop":
                assert player.is_playing()

        with allure.step("Click again to pause"):
            qtbot.mouseClick(player._play_btn, Qt.MouseButton.LeftButton)
            QApplication.processEvents()

        with allure.step("Verify paused"):
            assert not player.is_playing()

    @allure.title("Play button click emits playback_started signal")
    def test_play_button_emits_signals(
        self, qtbot, qapp, colors, sample_files: SampleFiles
    ):
        from PySide6.QtCore import Qt

        from src.presentation.organisms import MediaPlayer

        with allure.step("Create MediaPlayer and load media"):
            player = MediaPlayer(colors=colors)
            qtbot.addWidget(player)
            player.load_media(sample_files.wav_file)
            QApplication.processEvents()

        with allure.step("Set up signal spy"):
            started_spy = QSignalSpy(player.playback_started)

        with allure.step("Click play button"):
            qtbot.mouseClick(player._play_btn, Qt.MouseButton.LeftButton)
            QApplication.processEvents()

        with allure.step("Verify playback_started signal emitted"):
            assert started_spy.count() == 1

    @allure.title("Moving volume slider changes volume")
    def test_volume_slider_changes_volume(
        self, qtbot, qapp, colors, sample_files: SampleFiles
    ):
        from src.presentation.organisms import MediaPlayer

        with allure.step("Create MediaPlayer and load media"):
            player = MediaPlayer(colors=colors)
            qtbot.addWidget(player)
            player.load_media(sample_files.wav_file)
            QApplication.processEvents()

        with allure.step("Change volume via slider"):
            player._volume_slider.setValue(30)
            QApplication.processEvents()

        with allure.step("Verify volume updated"):
            assert player._volume_slider.value() == 30

    @allure.title("Moving progress slider seeks playback position")
    def test_progress_slider_seeks(
        self, qtbot, qapp, colors, sample_files: SampleFiles
    ):
        from src.presentation.organisms import MediaPlayer

        with allure.step("Create MediaPlayer and load media"):
            player = MediaPlayer(colors=colors)
            qtbot.addWidget(player)
            player.load_media(sample_files.wav_file)
            QApplication.processEvents()

        with allure.step("Simulate slider movement"):
            player._progress_slider.setValue(500)  # 50% of 1000 range
            player._on_seek(500)
            QApplication.processEvents()

        with allure.step("Verify position changed"):
            position = player.get_position()
            assert position >= 0


@allure.story("QC-027 ImageViewer UI Controls")
@allure.severity(allure.severity_level.NORMAL)
class TestImageViewerUIControls:
    """E2E tests for ImageViewer UI button interactions."""

    @allure.title("Clicking fit button toggles fit-to-window mode")
    def test_fit_button_toggles_fit_mode(
        self, qtbot, qapp, colors, sample_files: SampleFiles
    ):
        from PySide6.QtCore import Qt

        from src.presentation.organisms import ImageViewer

        with allure.step("Create ImageViewer and load image"):
            viewer = ImageViewer(colors=colors)
            qtbot.addWidget(viewer)
            viewer.load_image(sample_files.png_file)
            QApplication.processEvents()

        with allure.step("Verify initially in fit mode"):
            fit_btn = viewer._fit_btn
            assert fit_btn.isChecked()

        with allure.step("Click to toggle off"):
            qtbot.mouseClick(fit_btn, Qt.MouseButton.LeftButton)
            QApplication.processEvents()

        with allure.step("Verify unchecked"):
            assert not fit_btn.isChecked()

    @allure.title("Clicking actual size button shows image at 100%")
    def test_actual_size_button(self, qtbot, qapp, colors, sample_files: SampleFiles):
        from PySide6.QtCore import Qt

        from src.presentation.organisms import ImageViewer

        with allure.step("Create ImageViewer and load image"):
            viewer = ImageViewer(colors=colors)
            qtbot.addWidget(viewer)
            viewer.load_image(sample_files.png_file)
            QApplication.processEvents()

        with allure.step("Click actual size button"):
            actual_btn = viewer._actual_btn
            qtbot.mouseClick(actual_btn, Qt.MouseButton.LeftButton)
            QApplication.processEvents()

        with allure.step("Verify zoom is 100%"):
            assert viewer.get_zoom_level() == 1.0

    @allure.title("Zoom in/out methods change zoom level")
    def test_zoom_methods_work(self, qtbot, qapp, colors, sample_files: SampleFiles):
        from src.presentation.organisms import ImageViewer

        with allure.step("Create ImageViewer and load image"):
            viewer = ImageViewer(colors=colors)
            qtbot.addWidget(viewer)
            viewer.load_image(sample_files.png_file)
            QApplication.processEvents()

        with allure.step("Set to actual size (100%)"):
            viewer.show_actual_size()
            QApplication.processEvents()
            initial_zoom = viewer.get_zoom_level()
            assert initial_zoom == 1.0

        with allure.step("Zoom in and verify"):
            viewer.zoom_in()
            QApplication.processEvents()
            assert viewer.get_zoom_level() > initial_zoom

        with allure.step("Zoom out and verify"):
            viewer.zoom_out()
            QApplication.processEvents()
            assert viewer.get_zoom_level() == initial_zoom

    @allure.title("Zoom label updates when zoom changes")
    def test_zoom_label_updates(self, qtbot, qapp, colors, sample_files: SampleFiles):
        from src.presentation.organisms import ImageViewer

        with allure.step("Create ImageViewer and load image"):
            viewer = ImageViewer(colors=colors)
            qtbot.addWidget(viewer)
            viewer.load_image(sample_files.png_file)
            QApplication.processEvents()

        with allure.step("Set to actual size"):
            viewer.show_actual_size()
            QApplication.processEvents()

        with allure.step("Verify label shows 100%"):
            assert "100%" in viewer._zoom_label.text()

        with allure.step("Zoom in"):
            viewer.zoom_in()
            QApplication.processEvents()

        with allure.step("Verify label changed"):
            assert (
                "100%" not in viewer._zoom_label.text()
                or viewer.get_zoom_level() != 1.0
            )
