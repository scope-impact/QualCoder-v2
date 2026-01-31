"""
Tests for FileManagerViewModel.

Tests the data flow from ViewModel through Controller for file management.
Following TDD: Write tests first, then implement to pass.
"""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.unit


class TestFileManagerViewModelLoadSources:
    """Tests for loading and displaying sources."""

    def test_load_sources_returns_empty_list_for_new_project(self, file_manager_vm):
        """Test that a new project has no sources."""
        sources = file_manager_vm.load_sources()

        assert sources == []

    def test_load_sources_returns_source_dtos(
        self, file_manager_vm, sample_source_file
    ):
        """Test that load_sources returns SourceDTO objects."""
        # Add a source first
        file_manager_vm.add_source(str(sample_source_file))

        sources = file_manager_vm.load_sources()

        assert len(sources) == 1
        assert sources[0].name == sample_source_file.name
        assert sources[0].source_type == "text"

    def test_load_sources_includes_all_fields(
        self, file_manager_vm, sample_source_file
    ):
        """Test that SourceDTO includes all required fields."""
        file_manager_vm.add_source(str(sample_source_file))

        sources = file_manager_vm.load_sources()
        source = sources[0]

        # Check all expected fields exist
        assert hasattr(source, "id")
        assert hasattr(source, "name")
        assert hasattr(source, "source_type")
        assert hasattr(source, "status")
        assert hasattr(source, "file_size")
        assert hasattr(source, "code_count")


class TestFileManagerViewModelSourceTypes:
    """Tests for source type detection and display."""

    def test_text_file_has_text_type(self, file_manager_vm, tmp_path):
        """Test that .txt files are detected as text type."""
        txt_file = tmp_path / "document.txt"
        txt_file.write_text("content")

        file_manager_vm.add_source(str(txt_file))
        sources = file_manager_vm.load_sources()

        assert sources[0].source_type == "text"

    def test_docx_file_has_text_type(self, file_manager_vm, tmp_path):
        """Test that .docx files are detected as text type."""
        docx_file = tmp_path / "document.docx"
        docx_file.touch()

        file_manager_vm.add_source(str(docx_file))
        sources = file_manager_vm.load_sources()

        assert sources[0].source_type == "text"

    def test_mp3_file_has_audio_type(self, file_manager_vm, tmp_path):
        """Test that .mp3 files are detected as audio type."""
        mp3_file = tmp_path / "recording.mp3"
        mp3_file.touch()

        file_manager_vm.add_source(str(mp3_file))
        sources = file_manager_vm.load_sources()

        assert sources[0].source_type == "audio"

    def test_mp4_file_has_video_type(self, file_manager_vm, tmp_path):
        """Test that .mp4 files are detected as video type."""
        mp4_file = tmp_path / "video.mp4"
        mp4_file.touch()

        file_manager_vm.add_source(str(mp4_file))
        sources = file_manager_vm.load_sources()

        assert sources[0].source_type == "video"

    def test_jpg_file_has_image_type(self, file_manager_vm, tmp_path):
        """Test that .jpg files are detected as image type."""
        jpg_file = tmp_path / "photo.jpg"
        jpg_file.touch()

        file_manager_vm.add_source(str(jpg_file))
        sources = file_manager_vm.load_sources()

        assert sources[0].source_type == "image"

    def test_pdf_file_has_pdf_type(self, file_manager_vm, tmp_path):
        """Test that .pdf files are detected as pdf type."""
        pdf_file = tmp_path / "document.pdf"
        pdf_file.touch()

        file_manager_vm.add_source(str(pdf_file))
        sources = file_manager_vm.load_sources()

        assert sources[0].source_type == "pdf"


class TestFileManagerViewModelAddSource:
    """Tests for adding sources to the project."""

    def test_add_source_returns_true_on_success(
        self, file_manager_vm, sample_source_file
    ):
        """Test that add_source returns True on success."""
        result = file_manager_vm.add_source(str(sample_source_file))

        assert result is True

    def test_add_source_returns_false_for_nonexistent(self, file_manager_vm, tmp_path):
        """Test that add_source returns False for non-existent file."""
        result = file_manager_vm.add_source(str(tmp_path / "nonexistent.txt"))

        assert result is False

    def test_add_source_returns_false_for_duplicate(
        self, file_manager_vm, sample_source_file
    ):
        """Test that add_source returns False for duplicate name."""
        file_manager_vm.add_source(str(sample_source_file))
        result = file_manager_vm.add_source(str(sample_source_file))

        assert result is False

    def test_add_source_with_origin(self, file_manager_vm, sample_source_file):
        """Test adding source with origin metadata."""
        result = file_manager_vm.add_source(
            str(sample_source_file),
            origin="Field Interview",
        )

        assert result is True
        sources = file_manager_vm.load_sources()
        assert sources[0].origin == "Field Interview"

    def test_add_source_with_memo(self, file_manager_vm, sample_source_file):
        """Test adding source with memo."""
        result = file_manager_vm.add_source(
            str(sample_source_file),
            memo="First participant interview",
        )

        assert result is True


class TestFileManagerViewModelRemoveSource:
    """Tests for removing sources from the project."""

    def test_remove_source_returns_true_on_success(
        self, file_manager_vm, sample_source_file
    ):
        """Test that remove_source returns True on success."""
        file_manager_vm.add_source(str(sample_source_file))
        sources = file_manager_vm.load_sources()
        source_id = sources[0].id

        result = file_manager_vm.remove_source(int(source_id))

        assert result is True

    def test_remove_source_removes_from_list(self, file_manager_vm, sample_source_file):
        """Test that removed source no longer appears in list."""
        file_manager_vm.add_source(str(sample_source_file))
        sources = file_manager_vm.load_sources()
        source_id = sources[0].id

        file_manager_vm.remove_source(int(source_id))
        sources = file_manager_vm.load_sources()

        assert len(sources) == 0

    def test_remove_source_returns_false_for_nonexistent(self, file_manager_vm):
        """Test that remove_source returns False for non-existent ID."""
        result = file_manager_vm.remove_source(999)

        assert result is False


class TestFileManagerViewModelOpenSource:
    """Tests for opening sources."""

    def test_open_source_returns_true_on_success(
        self, file_manager_vm, sample_source_file
    ):
        """Test that open_source returns True on success."""
        file_manager_vm.add_source(str(sample_source_file))
        sources = file_manager_vm.load_sources()
        source_id = sources[0].id

        result = file_manager_vm.open_source(int(source_id))

        assert result is True

    def test_open_source_returns_false_for_nonexistent(self, file_manager_vm):
        """Test that open_source returns False for non-existent ID."""
        result = file_manager_vm.open_source(999)

        assert result is False

    def test_get_current_source_after_open(self, file_manager_vm, sample_source_file):
        """Test that current source is set after opening."""
        file_manager_vm.add_source(str(sample_source_file))
        sources = file_manager_vm.load_sources()
        source_id = sources[0].id

        file_manager_vm.open_source(int(source_id))

        current = file_manager_vm.get_current_source()
        assert current is not None
        assert current.id == source_id


class TestFileManagerViewModelSummary:
    """Tests for project summary statistics."""

    def test_get_summary_returns_summary_dto(self, file_manager_vm):
        """Test that get_summary returns a SummaryDTO."""
        summary = file_manager_vm.get_summary()

        assert hasattr(summary, "total_sources")
        assert hasattr(summary, "text_count")
        assert hasattr(summary, "audio_count")
        assert hasattr(summary, "video_count")
        assert hasattr(summary, "image_count")
        assert hasattr(summary, "pdf_count")

    def test_get_summary_counts_types(self, file_manager_vm, tmp_path):
        """Test that summary correctly counts source types."""
        # Create files of different types
        (tmp_path / "a.txt").write_text("text")
        (tmp_path / "b.txt").write_text("text")
        (tmp_path / "c.mp3").touch()
        (tmp_path / "d.jpg").touch()

        file_manager_vm.add_source(str(tmp_path / "a.txt"))
        file_manager_vm.add_source(str(tmp_path / "b.txt"))
        file_manager_vm.add_source(str(tmp_path / "c.mp3"))
        file_manager_vm.add_source(str(tmp_path / "d.jpg"))

        summary = file_manager_vm.get_summary()

        assert summary.total_sources == 4
        assert summary.text_count == 2
        assert summary.audio_count == 1
        assert summary.image_count == 1


class TestFileManagerViewModelFiltering:
    """Tests for filtering and sorting sources."""

    def test_filter_by_type(self, file_manager_vm, tmp_path):
        """Test filtering sources by type."""
        (tmp_path / "a.txt").write_text("text")
        (tmp_path / "b.mp3").touch()

        file_manager_vm.add_source(str(tmp_path / "a.txt"))
        file_manager_vm.add_source(str(tmp_path / "b.mp3"))

        text_sources = file_manager_vm.filter_sources(source_type="text")
        audio_sources = file_manager_vm.filter_sources(source_type="audio")

        assert len(text_sources) == 1
        assert len(audio_sources) == 1
        assert text_sources[0].source_type == "text"

    def test_filter_by_status(self, file_manager_vm, sample_source_file):
        """Test filtering sources by status."""
        file_manager_vm.add_source(str(sample_source_file))

        imported = file_manager_vm.filter_sources(status="imported")
        coded = file_manager_vm.filter_sources(status="coded")

        assert len(imported) == 1
        assert len(coded) == 0

    def test_search_sources_by_name(self, file_manager_vm, tmp_path):
        """Test searching sources by name."""
        (tmp_path / "interview_01.txt").write_text("text")
        (tmp_path / "interview_02.txt").write_text("text")
        (tmp_path / "notes.txt").write_text("text")

        file_manager_vm.add_source(str(tmp_path / "interview_01.txt"))
        file_manager_vm.add_source(str(tmp_path / "interview_02.txt"))
        file_manager_vm.add_source(str(tmp_path / "notes.txt"))

        results = file_manager_vm.search_sources("interview")

        assert len(results) == 2
        assert all("interview" in s.name for s in results)


class TestFileManagerViewModelBulkOperations:
    """Tests for bulk operations on multiple sources."""

    def test_remove_multiple_sources(self, file_manager_vm, tmp_path):
        """Test removing multiple sources at once."""
        (tmp_path / "a.txt").write_text("text")
        (tmp_path / "b.txt").write_text("text")
        (tmp_path / "c.txt").write_text("text")

        file_manager_vm.add_source(str(tmp_path / "a.txt"))
        file_manager_vm.add_source(str(tmp_path / "b.txt"))
        file_manager_vm.add_source(str(tmp_path / "c.txt"))

        sources = file_manager_vm.load_sources()
        ids_to_remove = [int(s.id) for s in sources[:2]]

        result = file_manager_vm.remove_sources(ids_to_remove)

        assert result is True
        remaining = file_manager_vm.load_sources()
        assert len(remaining) == 1

    def test_get_selected_sources(self, file_manager_vm, tmp_path):
        """Test getting currently selected sources."""
        (tmp_path / "a.txt").write_text("text")
        (tmp_path / "b.txt").write_text("text")

        file_manager_vm.add_source(str(tmp_path / "a.txt"))
        file_manager_vm.add_source(str(tmp_path / "b.txt"))

        sources = file_manager_vm.load_sources()
        file_manager_vm.select_sources([int(sources[0].id)])

        selected = file_manager_vm.get_selected_sources()
        assert len(selected) == 1
