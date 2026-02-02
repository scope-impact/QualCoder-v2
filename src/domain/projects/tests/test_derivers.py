"""
Project Context: Deriver Tests

Tests for pure functions that compose invariants and derive domain events.
Following TDD: Write tests first, then implement to pass.
"""

from __future__ import annotations

from pathlib import Path

import pytest

pytestmark = pytest.mark.unit


class TestDeriveCreateProject:
    """Tests for derive_create_project deriver."""

    def test_creates_project_with_valid_inputs(self):
        """Should create ProjectCreated event with valid inputs."""
        from src.contexts.projects.core.derivers import (
            ProjectState,
            derive_create_project,
        )
        from src.contexts.projects.core.events import ProjectCreated

        state = ProjectState(
            path_exists=lambda _: False,
            parent_writable=lambda _: True,
        )

        result = derive_create_project(
            name="My Research Study",
            path=Path("/home/user/research/study.qda"),
            memo="Initial project for PhD research",
            owner="researcher1",
            state=state,
        )

        assert isinstance(result, ProjectCreated)
        assert result.name == "My Research Study"
        assert result.path == Path("/home/user/research/study.qda")
        assert result.memo == "Initial project for PhD research"

    def test_fails_with_empty_name(self):
        """Should fail with EmptyName for empty project names."""
        from src.domain.projects.derivers import (
            ProjectState,
            derive_create_project,
        )
        from src.domain.projects.failure_events import ProjectNotCreated

        state = ProjectState(
            path_exists=lambda _: False,
            parent_writable=lambda _: True,
        )

        result = derive_create_project(
            name="",
            path=Path("/home/user/project.qda"),
            memo=None,
            owner=None,
            state=state,
        )

        assert isinstance(result, ProjectNotCreated)
        assert result.reason == "EMPTY_NAME"

    def test_fails_with_invalid_path(self):
        """Should fail with InvalidProjectPath for non-.qda paths."""
        from src.domain.projects.derivers import (
            ProjectState,
            derive_create_project,
        )
        from src.domain.projects.failure_events import ProjectNotCreated

        state = ProjectState(
            path_exists=lambda _: False,
            parent_writable=lambda _: True,
        )

        result = derive_create_project(
            name="My Project",
            path=Path("/home/user/project.txt"),  # Wrong extension
            memo=None,
            owner=None,
            state=state,
        )

        assert isinstance(result, ProjectNotCreated)
        assert result.reason == "INVALID_PATH"

    def test_fails_when_path_already_exists(self):
        """Should fail with ProjectAlreadyExists when file exists."""
        from src.domain.projects.derivers import (
            ProjectState,
            derive_create_project,
        )
        from src.domain.projects.failure_events import ProjectNotCreated

        state = ProjectState(
            path_exists=lambda _: True,  # File already exists
            parent_writable=lambda _: True,
        )

        result = derive_create_project(
            name="My Project",
            path=Path("/home/user/existing.qda"),
            memo=None,
            owner=None,
            state=state,
        )

        assert isinstance(result, ProjectNotCreated)
        assert result.reason == "ALREADY_EXISTS"

    def test_fails_when_parent_not_writable(self):
        """Should fail with ParentNotWritable for read-only directories."""
        from src.domain.projects.derivers import (
            ProjectState,
            derive_create_project,
        )
        from src.domain.projects.failure_events import ProjectNotCreated

        state = ProjectState(
            path_exists=lambda _: False,
            parent_writable=lambda _: False,  # Cannot write to parent
        )

        result = derive_create_project(
            name="My Project",
            path=Path("/readonly/project.qda"),
            memo=None,
            owner=None,
            state=state,
        )

        assert isinstance(result, ProjectNotCreated)
        assert result.reason == "PARENT_NOT_WRITABLE"


class TestDeriveOpenProject:
    """Tests for derive_open_project deriver."""

    def test_opens_existing_project(self):
        """Should create ProjectOpened event for existing project."""
        from src.domain.projects.derivers import ProjectState, derive_open_project
        from src.domain.projects.events import ProjectOpened

        state = ProjectState(
            path_exists=lambda _: True,
            parent_writable=lambda _: True,
        )

        result = derive_open_project(
            path=Path("/home/user/research/study.qda"),
            state=state,
        )

        assert isinstance(result, ProjectOpened)
        assert result.path == Path("/home/user/research/study.qda")

    def test_fails_with_nonexistent_path(self):
        """Should fail with ProjectNotFound for missing files."""
        from src.domain.projects.derivers import (
            ProjectState,
            derive_open_project,
        )
        from src.domain.projects.failure_events import ProjectNotOpened

        state = ProjectState(
            path_exists=lambda _: False,
            parent_writable=lambda _: True,
        )

        result = derive_open_project(
            path=Path("/home/user/missing.qda"),
            state=state,
        )

        assert isinstance(result, ProjectNotOpened)
        assert result.reason == "NOT_FOUND"

    def test_fails_with_invalid_extension(self):
        """Should fail with InvalidProjectPath for non-.qda files."""
        from src.domain.projects.derivers import (
            ProjectState,
            derive_open_project,
        )
        from src.domain.projects.failure_events import ProjectNotOpened

        state = ProjectState(
            path_exists=lambda _: True,
            parent_writable=lambda _: True,
        )

        result = derive_open_project(
            path=Path("/home/user/document.txt"),
            state=state,
        )

        assert isinstance(result, ProjectNotOpened)
        assert result.reason == "INVALID_PATH"


class TestDeriveAddSource:
    """Tests for derive_add_source deriver."""

    def test_adds_source_with_valid_path(self):
        """Should create SourceAdded event with valid inputs."""
        from src.domain.projects.derivers import ProjectState, derive_add_source
        from src.domain.projects.entities import SourceType
        from src.domain.projects.events import SourceAdded

        state = ProjectState(
            path_exists=lambda _: True,
            parent_writable=lambda _: True,
            existing_sources=(),
        )

        result = derive_add_source(
            source_path=Path("/home/user/data/interview.txt"),
            origin="Field Interview",
            memo="First participant interview",
            owner="researcher1",
            state=state,
        )

        assert isinstance(result, SourceAdded)
        assert result.name == "interview.txt"
        assert result.source_type == SourceType.TEXT
        assert result.origin == "Field Interview"

    def test_fails_with_nonexistent_source(self):
        """Should fail with SourceFileNotFound for missing files."""
        from src.domain.projects.derivers import (
            ProjectState,
            derive_add_source,
        )
        from src.domain.projects.failure_events import SourceNotAdded

        state = ProjectState(
            path_exists=lambda _: False,
            parent_writable=lambda _: True,
            existing_sources=(),
        )

        result = derive_add_source(
            source_path=Path("/home/user/missing.txt"),
            origin=None,
            memo=None,
            owner=None,
            state=state,
        )

        assert isinstance(result, SourceNotAdded)
        assert result.reason == "FILE_NOT_FOUND"

    def test_fails_with_duplicate_name(self):
        """Should fail with DuplicateSourceName for existing source name."""
        from src.domain.projects.derivers import (
            ProjectState,
            derive_add_source,
        )
        from src.domain.projects.entities import Source, SourceStatus, SourceType
        from src.domain.projects.failure_events import SourceNotAdded
        from src.domain.shared.types import SourceId

        existing = (
            Source(
                id=SourceId(value=1),
                name="interview.txt",
                source_type=SourceType.TEXT,
                status=SourceStatus.IMPORTED,
            ),
        )

        state = ProjectState(
            path_exists=lambda _: True,
            parent_writable=lambda _: True,
            existing_sources=existing,
        )

        result = derive_add_source(
            source_path=Path("/other/folder/interview.txt"),  # Same name
            origin=None,
            memo=None,
            owner=None,
            state=state,
        )

        assert isinstance(result, SourceNotAdded)
        assert result.reason == "DUPLICATE_NAME"

    def test_detects_correct_source_type(self):
        """Should detect source type based on file extension."""
        from src.domain.projects.derivers import ProjectState, derive_add_source
        from src.domain.projects.entities import SourceType
        from src.domain.projects.events import SourceAdded

        state = ProjectState(
            path_exists=lambda _: True,
            parent_writable=lambda _: True,
            existing_sources=(),
        )

        # Test various file types
        test_cases = [
            ("document.docx", SourceType.TEXT),
            ("recording.mp3", SourceType.AUDIO),
            ("video.mp4", SourceType.VIDEO),
            ("photo.jpg", SourceType.IMAGE),
            ("paper.pdf", SourceType.PDF),
        ]

        for filename, expected_type in test_cases:
            result = derive_add_source(
                source_path=Path(f"/data/{filename}"),
                origin=None,
                memo=None,
                owner=None,
                state=state,
            )
            assert isinstance(result, SourceAdded), f"Failed for {filename}"
            assert result.source_type == expected_type, f"Wrong type for {filename}"


class TestDeriveCreateFolder:
    """Tests for derive_create_folder deriver."""

    def test_creates_folder_with_valid_name(self):
        """Should create FolderCreated event with valid name."""
        from src.domain.projects.derivers import FolderState, derive_create_folder
        from src.domain.projects.events import FolderCreated

        state = FolderState(
            existing_folders=(),
            existing_sources=(),
        )

        result = derive_create_folder(
            name="Interviews",
            parent_id=None,
            state=state,
        )

        assert isinstance(result, FolderCreated)
        assert result.name == "Interviews"
        assert result.parent_id is None

    def test_creates_nested_folder(self):
        """Should create nested folder with valid parent."""
        from src.domain.projects.derivers import FolderState, derive_create_folder
        from src.domain.projects.entities import Folder
        from src.domain.projects.events import FolderCreated
        from src.domain.shared.types import FolderId

        parent_folder = Folder(id=FolderId(value=1), name="Documents", parent_id=None)

        state = FolderState(
            existing_folders=(parent_folder,),
            existing_sources=(),
        )

        result = derive_create_folder(
            name="Transcripts",
            parent_id=FolderId(value=1),
            state=state,
        )

        assert isinstance(result, FolderCreated)
        assert result.name == "Transcripts"
        assert result.parent_id == FolderId(value=1)

    def test_fails_with_empty_name(self):
        """Should fail with InvalidFolderName for empty folder name."""
        from src.domain.projects.derivers import (
            FolderState,
            derive_create_folder,
        )
        from src.domain.projects.failure_events import FolderNotCreated

        state = FolderState(
            existing_folders=(),
            existing_sources=(),
        )

        result = derive_create_folder(
            name="",
            parent_id=None,
            state=state,
        )

        assert isinstance(result, FolderNotCreated)
        assert result.reason == "INVALID_NAME"

    def test_fails_with_duplicate_name_at_same_level(self):
        """Should fail with DuplicateFolderName for duplicate at same parent."""
        from src.domain.projects.derivers import (
            FolderState,
            derive_create_folder,
        )
        from src.domain.projects.entities import Folder
        from src.domain.projects.failure_events import FolderNotCreated
        from src.domain.shared.types import FolderId

        existing_folder = Folder(
            id=FolderId(value=1), name="Interviews", parent_id=None
        )

        state = FolderState(
            existing_folders=(existing_folder,),
            existing_sources=(),
        )

        result = derive_create_folder(
            name="Interviews",  # Duplicate name at root
            parent_id=None,
            state=state,
        )

        assert isinstance(result, FolderNotCreated)
        assert result.reason == "DUPLICATE_NAME"

    def test_allows_same_name_in_different_parent(self):
        """Should allow same folder name in different parent folders."""
        from src.domain.projects.derivers import FolderState, derive_create_folder
        from src.domain.projects.entities import Folder
        from src.domain.projects.events import FolderCreated
        from src.domain.shared.types import FolderId

        # Parent1/Notes already exists
        existing_folder = Folder(
            id=FolderId(value=2), name="Notes", parent_id=FolderId(value=1)
        )

        state = FolderState(
            existing_folders=(existing_folder,),
            existing_sources=(),
        )

        # Create Parent2/Notes (different parent, same name)
        result = derive_create_folder(
            name="Notes",
            parent_id=FolderId(value=3),  # Different parent
            state=state,
        )

        assert isinstance(result, FolderCreated)
        assert result.name == "Notes"


class TestDeriveRenameFolder:
    """Tests for derive_rename_folder deriver."""

    def test_renames_folder_with_valid_name(self):
        """Should create FolderRenamed event with valid new name."""
        from src.domain.projects.derivers import FolderState, derive_rename_folder
        from src.domain.projects.entities import Folder
        from src.domain.projects.events import FolderRenamed
        from src.domain.shared.types import FolderId

        existing_folder = Folder(id=FolderId(value=1), name="Old Name", parent_id=None)

        state = FolderState(
            existing_folders=(existing_folder,),
            existing_sources=(),
        )

        result = derive_rename_folder(
            folder_id=FolderId(value=1),
            new_name="New Name",
            state=state,
        )

        assert isinstance(result, FolderRenamed)
        assert result.folder_id == FolderId(value=1)
        assert result.old_name == "Old Name"
        assert result.new_name == "New Name"

    def test_fails_with_folder_not_found(self):
        """Should fail with FolderNotFound for nonexistent folder."""
        from src.domain.projects.derivers import (
            FolderState,
            derive_rename_folder,
        )
        from src.domain.projects.failure_events import FolderNotRenamed
        from src.domain.shared.types import FolderId

        state = FolderState(
            existing_folders=(),
            existing_sources=(),
        )

        result = derive_rename_folder(
            folder_id=FolderId(value=999),
            new_name="New Name",
            state=state,
        )

        assert isinstance(result, FolderNotRenamed)
        assert result.reason == "NOT_FOUND"

    def test_fails_with_duplicate_name_at_same_level(self):
        """Should fail with DuplicateFolderName when renaming to existing name."""
        from src.domain.projects.derivers import (
            FolderState,
            derive_rename_folder,
        )
        from src.domain.projects.entities import Folder
        from src.domain.projects.failure_events import FolderNotRenamed
        from src.domain.shared.types import FolderId

        folder1 = Folder(id=FolderId(value=1), name="Folder1", parent_id=None)
        folder2 = Folder(id=FolderId(value=2), name="Folder2", parent_id=None)

        state = FolderState(
            existing_folders=(folder1, folder2),
            existing_sources=(),
        )

        result = derive_rename_folder(
            folder_id=FolderId(value=1),
            new_name="Folder2",  # Already exists
            state=state,
        )

        assert isinstance(result, FolderNotRenamed)
        assert result.reason == "DUPLICATE_NAME"

    def test_allows_rename_to_same_name(self):
        """Should allow renaming folder to its current name (no-op)."""
        from src.domain.projects.derivers import FolderState, derive_rename_folder
        from src.domain.projects.entities import Folder
        from src.domain.projects.events import FolderRenamed
        from src.domain.shared.types import FolderId

        existing_folder = Folder(id=FolderId(value=1), name="MyFolder", parent_id=None)

        state = FolderState(
            existing_folders=(existing_folder,),
            existing_sources=(),
        )

        result = derive_rename_folder(
            folder_id=FolderId(value=1),
            new_name="MyFolder",  # Same name
            state=state,
        )

        assert isinstance(result, FolderRenamed)


class TestDeriveDeleteFolder:
    """Tests for derive_delete_folder deriver."""

    def test_deletes_empty_folder(self):
        """Should create FolderDeleted event for empty folder."""
        from src.domain.projects.derivers import FolderState, derive_delete_folder
        from src.domain.projects.entities import Folder
        from src.domain.projects.events import FolderDeleted
        from src.domain.shared.types import FolderId

        existing_folder = Folder(
            id=FolderId(value=1), name="Empty Folder", parent_id=None
        )

        state = FolderState(
            existing_folders=(existing_folder,),
            existing_sources=(),  # No sources in the folder
        )

        result = derive_delete_folder(
            folder_id=FolderId(value=1),
            state=state,
        )

        assert isinstance(result, FolderDeleted)
        assert result.folder_id == FolderId(value=1)
        assert result.name == "Empty Folder"

    def test_fails_with_folder_not_found(self):
        """Should fail with FolderNotFound for nonexistent folder."""
        from src.domain.projects.derivers import (
            FolderState,
            derive_delete_folder,
        )
        from src.domain.projects.failure_events import FolderNotDeleted
        from src.domain.shared.types import FolderId

        state = FolderState(
            existing_folders=(),
            existing_sources=(),
        )

        result = derive_delete_folder(
            folder_id=FolderId(value=999),
            state=state,
        )

        assert isinstance(result, FolderNotDeleted)
        assert result.reason == "NOT_FOUND"

    def test_fails_when_folder_contains_sources(self):
        """Should fail with FolderNotEmpty when folder has sources."""
        from src.domain.projects.derivers import (
            FolderState,
            derive_delete_folder,
        )
        from src.domain.projects.entities import (
            Folder,
            Source,
            SourceStatus,
            SourceType,
        )
        from src.domain.projects.failure_events import FolderNotDeleted
        from src.domain.shared.types import FolderId, SourceId

        existing_folder = Folder(
            id=FolderId(value=1), name="Folder With Sources", parent_id=None
        )

        # Source in the folder
        source = Source(
            id=SourceId(value=10),
            name="document.txt",
            source_type=SourceType.TEXT,
            status=SourceStatus.IMPORTED,
            folder_id=FolderId(value=1),
        )

        state = FolderState(
            existing_folders=(existing_folder,),
            existing_sources=(source,),
        )

        result = derive_delete_folder(
            folder_id=FolderId(value=1),
            state=state,
        )

        assert isinstance(result, FolderNotDeleted)
        assert result.reason == "NOT_EMPTY"


class TestDeriveMoveSourceToFolder:
    """Tests for derive_move_source_to_folder deriver."""

    def test_moves_source_to_folder(self):
        """Should create SourceMovedToFolder event for valid move."""
        from src.domain.projects.derivers import (
            FolderState,
            derive_move_source_to_folder,
        )
        from src.domain.projects.entities import (
            Folder,
            Source,
            SourceStatus,
            SourceType,
        )
        from src.domain.projects.events import SourceMovedToFolder
        from src.domain.shared.types import FolderId, SourceId

        folder = Folder(id=FolderId(value=1), name="Interviews", parent_id=None)
        source = Source(
            id=SourceId(value=10),
            name="interview.txt",
            source_type=SourceType.TEXT,
            status=SourceStatus.IMPORTED,
            folder_id=None,  # Currently at root
        )

        state = FolderState(
            existing_folders=(folder,),
            existing_sources=(source,),
        )

        result = derive_move_source_to_folder(
            source_id=SourceId(value=10),
            folder_id=FolderId(value=1),
            state=state,
        )

        assert isinstance(result, SourceMovedToFolder)
        assert result.source_id == SourceId(value=10)
        assert result.old_folder_id is None
        assert result.new_folder_id == FolderId(value=1)

    def test_moves_source_to_root(self):
        """Should allow moving source to root (None folder_id)."""
        from src.domain.projects.derivers import (
            FolderState,
            derive_move_source_to_folder,
        )
        from src.domain.projects.entities import Source, SourceStatus, SourceType
        from src.domain.projects.events import SourceMovedToFolder
        from src.domain.shared.types import FolderId, SourceId

        source = Source(
            id=SourceId(value=10),
            name="interview.txt",
            source_type=SourceType.TEXT,
            status=SourceStatus.IMPORTED,
            folder_id=FolderId(value=1),  # Currently in a folder
        )

        state = FolderState(
            existing_folders=(),
            existing_sources=(source,),
        )

        result = derive_move_source_to_folder(
            source_id=SourceId(value=10),
            folder_id=None,  # Move to root
            state=state,
        )

        assert isinstance(result, SourceMovedToFolder)
        assert result.source_id == SourceId(value=10)
        assert result.old_folder_id == FolderId(value=1)
        assert result.new_folder_id is None

    def test_fails_with_source_not_found(self):
        """Should fail with SourceNotFound for nonexistent source."""
        from src.domain.projects.derivers import (
            FolderState,
            derive_move_source_to_folder,
        )
        from src.domain.projects.failure_events import SourceNotMoved
        from src.domain.shared.types import FolderId, SourceId

        state = FolderState(
            existing_folders=(),
            existing_sources=(),
        )

        result = derive_move_source_to_folder(
            source_id=SourceId(value=999),
            folder_id=FolderId(value=1),
            state=state,
        )

        assert isinstance(result, SourceNotMoved)
        assert result.reason == "SOURCE_NOT_FOUND"

    def test_fails_with_folder_not_found(self):
        """Should fail with FolderNotFound for nonexistent target folder."""
        from src.domain.projects.derivers import (
            FolderState,
            derive_move_source_to_folder,
        )
        from src.domain.projects.entities import Source, SourceStatus, SourceType
        from src.domain.projects.failure_events import SourceNotMoved
        from src.domain.shared.types import FolderId, SourceId

        source = Source(
            id=SourceId(value=10),
            name="interview.txt",
            source_type=SourceType.TEXT,
            status=SourceStatus.IMPORTED,
        )

        state = FolderState(
            existing_folders=(),
            existing_sources=(source,),
        )

        result = derive_move_source_to_folder(
            source_id=SourceId(value=10),
            folder_id=FolderId(value=999),  # Nonexistent folder
            state=state,
        )

        assert isinstance(result, SourceNotMoved)
        assert result.reason == "FOLDER_NOT_FOUND"
