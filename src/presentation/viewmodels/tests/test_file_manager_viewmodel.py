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


class TestFolderOperations:
    """Tests for folder management operations."""

    def test_create_folder_success(self, file_manager_vm):
        """Test creating a folder successfully."""
        result = file_manager_vm.create_folder(name="Interviews")

        assert result is True

    def test_create_folder_failure_invalid_name(self, file_manager_vm):
        """Test creating a folder with invalid name fails."""
        result = file_manager_vm.create_folder(name="")

        assert result is False

    def test_create_folder_failure_duplicate_name(self, file_manager_vm):
        """Test creating a folder with duplicate name fails."""
        file_manager_vm.create_folder(name="Interviews")
        result = file_manager_vm.create_folder(name="Interviews")

        assert result is False

    def test_create_nested_folder_success(self, file_manager_vm):
        """Test creating a nested folder successfully."""
        file_manager_vm.create_folder(name="Parent")
        folders = file_manager_vm.get_folders()
        parent_id = int(folders[0].id)

        result = file_manager_vm.create_folder(name="Child", parent_id=parent_id)

        assert result is True

    def test_rename_folder_success(self, file_manager_vm):
        """Test renaming a folder successfully."""
        file_manager_vm.create_folder(name="OldName")
        folders = file_manager_vm.get_folders()
        folder_id = int(folders[0].id)

        result = file_manager_vm.rename_folder(folder_id=folder_id, new_name="NewName")

        assert result is True

    def test_rename_folder_failure_not_found(self, file_manager_vm):
        """Test renaming a non-existent folder fails."""
        result = file_manager_vm.rename_folder(folder_id=999, new_name="NewName")

        assert result is False

    def test_rename_folder_failure_duplicate_name(self, file_manager_vm):
        """Test renaming a folder to an existing name fails."""
        file_manager_vm.create_folder(name="Folder1")
        file_manager_vm.create_folder(name="Folder2")
        folders = file_manager_vm.get_folders()
        folder_id = int(folders[0].id)

        result = file_manager_vm.rename_folder(folder_id=folder_id, new_name="Folder2")

        assert result is False

    def test_delete_folder_success(self, file_manager_vm):
        """Test deleting an empty folder successfully."""
        file_manager_vm.create_folder(name="EmptyFolder")
        folders = file_manager_vm.get_folders()
        folder_id = int(folders[0].id)

        result = file_manager_vm.delete_folder(folder_id=folder_id)

        assert result is True

    def test_delete_folder_failure_not_found(self, file_manager_vm):
        """Test deleting a non-existent folder fails."""
        result = file_manager_vm.delete_folder(folder_id=999)

        assert result is False

    def test_delete_folder_failure_has_sources(
        self, file_manager_vm, sample_source_file
    ):
        """Test deleting a folder with sources fails."""
        # Create folder
        file_manager_vm.create_folder(name="WithSources")
        folders = file_manager_vm.get_folders()
        folder_id = int(folders[0].id)

        # Add source and move to folder
        file_manager_vm.add_source(str(sample_source_file))
        sources = file_manager_vm.load_sources()
        source_id = int(sources[0].id)
        file_manager_vm.move_source_to_folder(source_id=source_id, folder_id=folder_id)

        # Try to delete folder
        result = file_manager_vm.delete_folder(folder_id=folder_id)

        assert result is False

    def test_move_source_to_folder_success(self, file_manager_vm, sample_source_file):
        """Test moving a source to a folder successfully."""
        # Create folder
        file_manager_vm.create_folder(name="Folder")
        folders = file_manager_vm.get_folders()
        folder_id = int(folders[0].id)

        # Add source
        file_manager_vm.add_source(str(sample_source_file))
        sources = file_manager_vm.load_sources()
        source_id = int(sources[0].id)

        # Move to folder
        result = file_manager_vm.move_source_to_folder(
            source_id=source_id, folder_id=folder_id
        )

        assert result is True

    def test_move_source_to_root(self, file_manager_vm, sample_source_file):
        """Test moving a source to root (None folder) successfully."""
        # Create folder and add source
        file_manager_vm.create_folder(name="Folder")
        folders = file_manager_vm.get_folders()
        folder_id = int(folders[0].id)

        file_manager_vm.add_source(str(sample_source_file))
        sources = file_manager_vm.load_sources()
        source_id = int(sources[0].id)

        # Move to folder first
        file_manager_vm.move_source_to_folder(source_id=source_id, folder_id=folder_id)

        # Move back to root
        result = file_manager_vm.move_source_to_folder(
            source_id=source_id, folder_id=None
        )

        assert result is True

    def test_move_source_failure_source_not_found(self, file_manager_vm):
        """Test moving a non-existent source fails."""
        file_manager_vm.create_folder(name="Folder")
        folders = file_manager_vm.get_folders()
        folder_id = int(folders[0].id)

        result = file_manager_vm.move_source_to_folder(
            source_id=999, folder_id=folder_id
        )

        assert result is False

    def test_move_source_failure_folder_not_found(
        self, file_manager_vm, sample_source_file
    ):
        """Test moving a source to a non-existent folder fails."""
        file_manager_vm.add_source(str(sample_source_file))
        sources = file_manager_vm.load_sources()
        source_id = int(sources[0].id)

        result = file_manager_vm.move_source_to_folder(
            source_id=source_id, folder_id=999
        )

        assert result is False

    def test_get_folders_returns_list(self, file_manager_vm):
        """Test getting all folders returns a list of FolderDTO objects."""
        file_manager_vm.create_folder(name="Folder1")
        file_manager_vm.create_folder(name="Folder2")

        folders = file_manager_vm.get_folders()

        assert len(folders) == 2
        assert all(hasattr(f, "id") for f in folders)
        assert all(hasattr(f, "name") for f in folders)
        assert folders[0].name == "Folder1"
        assert folders[1].name == "Folder2"

    def test_get_folders_empty_list(self, file_manager_vm):
        """Test getting folders returns empty list when none exist."""
        folders = file_manager_vm.get_folders()

        assert folders == []


class TestSourceDTOCases:
    """Tests for SourceDTO cases field population."""

    def test_source_dto_cases_empty_when_not_linked(
        self, file_manager_vm, sample_source_file
    ):
        """Test that source DTO has empty cases when not linked to any case."""
        file_manager_vm.add_source(str(sample_source_file))

        sources = file_manager_vm.load_sources()

        assert sources[0].cases == []

    def test_source_dto_cases_populated_when_linked(
        self, file_manager_vm, sample_source_file, coordinator
    ):
        """Test that source DTO includes case names when linked to cases."""
        from src.application.projects.commands import (
            CreateCaseCommand,
            LinkSourceToCaseCommand,
        )

        # Add source
        file_manager_vm.add_source(str(sample_source_file))
        sources = file_manager_vm.load_sources()
        source_id = int(sources[0].id)

        # Create a case
        coordinator.cases.create_case(
            CreateCaseCommand(name="Participant A", description="First participant")
        )
        cases = coordinator.cases.get_cases()
        case_id = cases[0].id.value

        # Link source to case
        coordinator.cases.link_source_to_case(
            LinkSourceToCaseCommand(source_id=source_id, case_id=case_id)
        )

        # Reload sources and check cases field
        sources = file_manager_vm.load_sources()

        assert len(sources[0].cases) == 1
        assert sources[0].cases[0] == "Participant A"

    def test_source_dto_cases_includes_multiple_cases(
        self, file_manager_vm, sample_source_file, coordinator
    ):
        """Test that source DTO includes all linked case names."""
        from src.application.projects.commands import (
            CreateCaseCommand,
            LinkSourceToCaseCommand,
        )

        # Add source
        file_manager_vm.add_source(str(sample_source_file))
        sources = file_manager_vm.load_sources()
        source_id = int(sources[0].id)

        # Create two cases
        coordinator.cases.create_case(CreateCaseCommand(name="Case Alpha"))
        coordinator.cases.create_case(CreateCaseCommand(name="Case Beta"))
        cases = coordinator.cases.get_cases()

        # Link source to both cases
        for case in cases:
            coordinator.cases.link_source_to_case(
                LinkSourceToCaseCommand(source_id=source_id, case_id=case.id.value)
            )

        # Reload sources and check cases field
        sources = file_manager_vm.load_sources()

        assert len(sources[0].cases) == 2
        assert "Case Alpha" in sources[0].cases
        assert "Case Beta" in sources[0].cases


class TestUpdateSource:
    """Tests for updating source metadata."""

    def test_update_source_memo_successfully(self, file_manager_vm, sample_source_file):
        """Test updating source memo returns True on success."""
        # Add source
        file_manager_vm.add_source(str(sample_source_file))
        sources = file_manager_vm.load_sources()
        source_id = int(sources[0].id)

        # Update memo
        result = file_manager_vm.update_source(source_id=source_id, memo="New memo")

        assert result is True

        # Verify memo was updated
        sources = file_manager_vm.load_sources()
        assert sources[0].memo == "New memo"

    def test_update_source_origin_successfully(
        self, file_manager_vm, sample_source_file
    ):
        """Test updating source origin returns True on success."""
        # Add source
        file_manager_vm.add_source(str(sample_source_file))
        sources = file_manager_vm.load_sources()
        source_id = int(sources[0].id)

        # Update origin
        result = file_manager_vm.update_source(
            source_id=source_id, origin="Field Research"
        )

        assert result is True

        # Verify origin was updated
        sources = file_manager_vm.load_sources()
        assert sources[0].origin == "Field Research"

    def test_update_source_status_successfully(
        self, file_manager_vm, sample_source_file
    ):
        """Test updating source status returns True on success."""
        # Add source
        file_manager_vm.add_source(str(sample_source_file))
        sources = file_manager_vm.load_sources()
        source_id = int(sources[0].id)

        # Update status
        result = file_manager_vm.update_source(source_id=source_id, status="coded")

        assert result is True

        # Verify status was updated
        sources = file_manager_vm.load_sources()
        assert sources[0].status == "coded"

    def test_update_source_multiple_fields(self, file_manager_vm, sample_source_file):
        """Test updating multiple source fields at once."""
        # Add source
        file_manager_vm.add_source(str(sample_source_file))
        sources = file_manager_vm.load_sources()
        source_id = int(sources[0].id)

        # Update multiple fields (using valid SourceStatus value)
        result = file_manager_vm.update_source(
            source_id=source_id,
            memo="Updated memo",
            origin="Interview",
            status="coded",
        )

        assert result is True

        # Verify all fields were updated
        sources = file_manager_vm.load_sources()
        assert sources[0].memo == "Updated memo"
        assert sources[0].origin == "Interview"
        assert sources[0].status == "coded"

    def test_update_source_returns_false_for_nonexistent(self, file_manager_vm):
        """Test updating nonexistent source returns False."""
        result = file_manager_vm.update_source(source_id=999, memo="Test")

        assert result is False


class TestSegmentCountForSource:
    """Tests for coded segment warning before delete."""

    def test_get_segment_count_returns_zero_for_new_source(
        self, file_manager_vm, sample_source_file
    ):
        """Test that a new source has zero segments."""
        file_manager_vm.add_source(str(sample_source_file))
        sources = file_manager_vm.load_sources()
        source_id = int(sources[0].id)

        count = file_manager_vm.get_segment_count_for_source(source_id)

        assert count == 0

    def test_get_segment_count_returns_correct_count(
        self, file_manager_vm, sample_source_file, coordinator
    ):
        """Test that segment count reflects actual coded segments."""
        from src.contexts.coding.core.entities import TextPosition, TextSegment
        from src.contexts.shared.core.types import CodeId, SegmentId, SourceId

        # Add source
        file_manager_vm.add_source(str(sample_source_file))
        sources = file_manager_vm.load_sources()
        source_id = int(sources[0].id)

        # Create segments directly via segment_repo
        segment_repo = coordinator.coding_context.segment_repo
        if segment_repo:
            segment1 = TextSegment(
                id=SegmentId(value=2001),
                source_id=SourceId(value=source_id),
                code_id=CodeId(value=1),
                position=TextPosition(start=0, end=10),
                selected_text="Test text",
            )
            segment2 = TextSegment(
                id=SegmentId(value=2002),
                source_id=SourceId(value=source_id),
                code_id=CodeId(value=2),
                position=TextPosition(start=15, end=25),
                selected_text="More text",
            )
            segment_repo.save(segment1)
            segment_repo.save(segment2)

            count = file_manager_vm.get_segment_count_for_source(source_id)

            assert count == 2

    def test_get_segment_count_returns_zero_for_nonexistent_source(
        self, file_manager_vm
    ):
        """Test that nonexistent source returns zero segments."""
        count = file_manager_vm.get_segment_count_for_source(999)

        assert count == 0
