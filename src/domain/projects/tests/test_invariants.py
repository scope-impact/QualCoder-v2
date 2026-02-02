"""
Project Context: Invariant Tests

Tests for pure predicate functions that validate business rules.
Following TDD: Write tests first, then implement to pass.
"""

from __future__ import annotations

from pathlib import Path

import pytest

pytestmark = pytest.mark.unit


class TestProjectNameInvariants:
    """Tests for project name validation."""

    def test_valid_project_name_accepts_normal_string(self):
        """Normal alphanumeric names should be valid."""
        from src.domain.projects.invariants import is_valid_project_name

        assert is_valid_project_name("My Research Project") is True
        assert is_valid_project_name("Study-2026") is True
        assert is_valid_project_name("PhD_Thesis_Data") is True

    def test_valid_project_name_rejects_empty_string(self):
        """Empty string should be invalid."""
        from src.domain.projects.invariants import is_valid_project_name

        assert is_valid_project_name("") is False

    def test_valid_project_name_rejects_whitespace_only(self):
        """Whitespace-only strings should be invalid."""
        from src.domain.projects.invariants import is_valid_project_name

        assert is_valid_project_name("   ") is False
        assert is_valid_project_name("\t\n") is False

    def test_valid_project_name_rejects_too_long(self):
        """Names exceeding 200 characters should be invalid."""
        from src.domain.projects.invariants import is_valid_project_name

        long_name = "a" * 201
        assert is_valid_project_name(long_name) is False

    def test_valid_project_name_accepts_max_length(self):
        """Names at exactly 200 characters should be valid."""
        from src.domain.projects.invariants import is_valid_project_name

        max_name = "a" * 200
        assert is_valid_project_name(max_name) is True


class TestProjectPathInvariants:
    """Tests for project path validation."""

    def test_valid_project_path_accepts_qda_extension(self):
        """Paths with .qda extension should be valid."""
        from src.domain.projects.invariants import is_valid_project_path

        assert is_valid_project_path(Path("/home/user/my_project.qda")) is True
        assert is_valid_project_path(Path("C:/Projects/study.qda")) is True

    def test_valid_project_path_rejects_wrong_extension(self):
        """Paths without .qda extension should be invalid."""
        from src.domain.projects.invariants import is_valid_project_path

        assert is_valid_project_path(Path("/home/user/my_project.txt")) is False
        assert is_valid_project_path(Path("/home/user/my_project")) is False
        assert is_valid_project_path(Path("/home/user/my_project.qda.bak")) is False

    def test_valid_project_path_rejects_empty_name(self):
        """Paths with empty filename should be invalid."""
        from src.domain.projects.invariants import is_valid_project_path

        assert is_valid_project_path(Path("/home/user/.qda")) is False


class TestSourceTypeInvariants:
    """Tests for source file type detection."""

    def test_detect_text_source_types(self):
        """Text file extensions should be detected correctly."""
        from src.domain.projects.entities import SourceType
        from src.domain.projects.invariants import detect_source_type

        assert detect_source_type(Path("interview.txt")) == SourceType.TEXT
        assert detect_source_type(Path("document.docx")) == SourceType.TEXT
        assert detect_source_type(Path("notes.odt")) == SourceType.TEXT
        assert detect_source_type(Path("article.rtf")) == SourceType.TEXT

    def test_detect_audio_source_types(self):
        """Audio file extensions should be detected correctly."""
        from src.domain.projects.entities import SourceType
        from src.domain.projects.invariants import detect_source_type

        assert detect_source_type(Path("recording.mp3")) == SourceType.AUDIO
        assert detect_source_type(Path("interview.wav")) == SourceType.AUDIO
        assert detect_source_type(Path("podcast.m4a")) == SourceType.AUDIO

    def test_detect_video_source_types(self):
        """Video file extensions should be detected correctly."""
        from src.domain.projects.entities import SourceType
        from src.domain.projects.invariants import detect_source_type

        assert detect_source_type(Path("observation.mp4")) == SourceType.VIDEO
        assert detect_source_type(Path("interview.mov")) == SourceType.VIDEO
        assert detect_source_type(Path("recording.avi")) == SourceType.VIDEO

    def test_detect_image_source_types(self):
        """Image file extensions should be detected correctly."""
        from src.domain.projects.entities import SourceType
        from src.domain.projects.invariants import detect_source_type

        assert detect_source_type(Path("photo.jpg")) == SourceType.IMAGE
        assert detect_source_type(Path("diagram.png")) == SourceType.IMAGE
        assert detect_source_type(Path("scan.jpeg")) == SourceType.IMAGE

    def test_detect_pdf_source_types(self):
        """PDF file extensions should be detected correctly."""
        from src.domain.projects.entities import SourceType
        from src.domain.projects.invariants import detect_source_type

        assert detect_source_type(Path("article.pdf")) == SourceType.PDF

    def test_detect_unknown_source_types(self):
        """Unknown extensions should return UNKNOWN type."""
        from src.domain.projects.entities import SourceType
        from src.domain.projects.invariants import detect_source_type

        assert detect_source_type(Path("data.xyz")) == SourceType.UNKNOWN
        assert detect_source_type(Path("noextension")) == SourceType.UNKNOWN


class TestSourceNameInvariants:
    """Tests for source name uniqueness."""

    def test_source_name_unique_in_empty_project(self):
        """Any name is unique in a project with no sources."""
        from src.domain.projects.invariants import is_source_name_unique

        assert is_source_name_unique("interview.txt", []) is True

    def test_source_name_unique_detects_duplicate(self):
        """Duplicate names should be detected (case-insensitive)."""
        from src.domain.projects.entities import Source, SourceStatus, SourceType
        from src.domain.projects.invariants import is_source_name_unique
        from src.domain.shared.types import SourceId

        existing = [
            Source(
                id=SourceId(value=1),
                name="Interview.txt",
                source_type=SourceType.TEXT,
                status=SourceStatus.IMPORTED,
            )
        ]

        assert is_source_name_unique("interview.txt", existing) is False
        assert is_source_name_unique("INTERVIEW.TXT", existing) is False
        assert is_source_name_unique("other.txt", existing) is True


class TestCanOpenProjectInvariants:
    """Tests for project open validation."""

    def test_can_open_project_with_valid_path(self):
        """Valid .qda path that exists should be openable."""
        from src.domain.projects.invariants import can_open_project

        # The invariant takes a path and a function to check existence
        assert (
            can_open_project(
                Path("/home/user/project.qda"),
                path_exists=lambda _: True,
            )
            is True
        )

    def test_cannot_open_nonexistent_project(self):
        """Non-existent path should not be openable."""
        from src.domain.projects.invariants import can_open_project

        assert (
            can_open_project(
                Path("/home/user/missing.qda"),
                path_exists=lambda _: False,
            )
            is False
        )

    def test_cannot_open_invalid_extension(self):
        """Wrong extension should not be openable even if exists."""
        from src.domain.projects.invariants import can_open_project

        assert (
            can_open_project(
                Path("/home/user/project.txt"),
                path_exists=lambda _: True,
            )
            is False
        )


class TestCanCreateProjectInvariants:
    """Tests for project creation validation."""

    def test_can_create_project_at_valid_location(self):
        """Valid path with .qda and writable parent should be creatable."""
        from src.domain.projects.invariants import can_create_project

        assert (
            can_create_project(
                Path("/home/user/new_project.qda"),
                path_exists=lambda _: False,
                parent_writable=lambda _: True,
            )
            is True
        )

    def test_cannot_create_project_at_existing_path(self):
        """Should not overwrite existing project."""
        from src.domain.projects.invariants import can_create_project

        assert (
            can_create_project(
                Path("/home/user/existing.qda"),
                path_exists=lambda _: True,
                parent_writable=lambda _: True,
            )
            is False
        )

    def test_cannot_create_project_in_readonly_location(self):
        """Should not create in read-only directory."""
        from src.domain.projects.invariants import can_create_project

        assert (
            can_create_project(
                Path("/readonly/project.qda"),
                path_exists=lambda _: False,
                parent_writable=lambda _: False,
            )
            is False
        )


class TestFolderNameInvariants:
    """Tests for folder name validation."""

    def test_valid_folder_name_accepts_normal_string(self):
        """Normal alphanumeric names should be valid."""
        from src.domain.projects.invariants import is_valid_folder_name

        assert is_valid_folder_name("Interviews") is True
        assert is_valid_folder_name("Phase 1") is True
        assert is_valid_folder_name("2023-Data") is True

    def test_valid_folder_name_rejects_empty_string(self):
        """Empty string should be invalid."""
        from src.domain.projects.invariants import is_valid_folder_name

        assert is_valid_folder_name("") is False

    def test_valid_folder_name_rejects_whitespace_only(self):
        """Whitespace-only strings should be invalid."""
        from src.domain.projects.invariants import is_valid_folder_name

        assert is_valid_folder_name("   ") is False
        assert is_valid_folder_name("\t\n") is False

    def test_valid_folder_name_rejects_special_chars(self):
        """Folder names with path separators should be invalid."""
        from src.domain.projects.invariants import is_valid_folder_name

        assert is_valid_folder_name("folder/name") is False
        assert is_valid_folder_name("folder\\name") is False
        assert is_valid_folder_name("/root") is False


class TestFolderNameUniqueInvariants:
    """Tests for folder name uniqueness."""

    def test_folder_name_unique_in_empty_list(self):
        """Any name is unique when no folders exist."""
        from src.domain.projects.invariants import is_folder_name_unique

        assert is_folder_name_unique("Interviews", None, ()) is True

    def test_folder_name_unique_at_same_level(self):
        """Duplicate names at the same level should be detected."""
        from src.domain.projects.entities import Folder
        from src.domain.projects.invariants import is_folder_name_unique
        from src.domain.shared.types import FolderId

        existing = (
            Folder(id=FolderId(value=1), name="Interviews", parent_id=None),
            Folder(id=FolderId(value=2), name="Documents", parent_id=None),
        )

        assert is_folder_name_unique("Data", None, existing) is True
        assert is_folder_name_unique("Interviews", None, existing) is False
        assert is_folder_name_unique("interviews", None, existing) is False

    def test_folder_name_unique_at_different_level(self):
        """Same name at different parent level should be allowed."""
        from src.domain.projects.entities import Folder
        from src.domain.projects.invariants import is_folder_name_unique
        from src.domain.shared.types import FolderId

        parent1 = FolderId(value=1)
        parent2 = FolderId(value=2)

        existing = (
            Folder(id=FolderId(value=10), name="Data", parent_id=parent1),
            Folder(id=FolderId(value=11), name="Other", parent_id=parent2),
        )

        # "Data" already exists under parent1, should be rejected
        assert is_folder_name_unique("Data", parent1, existing) is False

        # "Data" doesn't exist under parent2, should be allowed
        assert is_folder_name_unique("Data", parent2, existing) is True


class TestFolderEmptyInvariants:
    """Tests for folder empty check."""

    def test_folder_empty_when_no_sources(self):
        """Folder with no sources should be considered empty."""
        from src.domain.projects.invariants import is_folder_empty
        from src.domain.shared.types import FolderId

        folder_id = FolderId(value=1)
        assert is_folder_empty(folder_id, ()) is True

    def test_folder_not_empty_when_has_sources(self):
        """Folder with sources should not be considered empty."""
        from src.domain.projects.entities import Source, SourceStatus, SourceType
        from src.domain.projects.invariants import is_folder_empty
        from src.domain.shared.types import FolderId, SourceId

        folder_id = FolderId(value=1)
        sources = (
            Source(
                id=SourceId(value=1),
                name="interview.txt",
                source_type=SourceType.TEXT,
                status=SourceStatus.IMPORTED,
                folder_id=folder_id,
            ),
        )

        assert is_folder_empty(folder_id, sources) is False

    def test_folder_empty_when_sources_in_other_folders(self):
        """Sources in other folders should not affect empty check."""
        from src.domain.projects.entities import Source, SourceStatus, SourceType
        from src.domain.projects.invariants import is_folder_empty
        from src.domain.shared.types import FolderId, SourceId

        folder_id = FolderId(value=1)
        other_folder = FolderId(value=2)

        sources = (
            Source(
                id=SourceId(value=1),
                name="interview.txt",
                source_type=SourceType.TEXT,
                status=SourceStatus.IMPORTED,
                folder_id=other_folder,
            ),
        )

        assert is_folder_empty(folder_id, sources) is True


class TestFolderCycleInvariants:
    """Tests for folder cycle detection."""

    def test_would_create_cycle_moving_to_unrelated_folder(self):
        """Moving folder to unrelated folder should not create cycle."""
        from src.domain.projects.entities import Folder
        from src.domain.projects.invariants import would_create_cycle
        from src.domain.shared.types import FolderId

        folder1 = FolderId(value=1)
        folder2 = FolderId(value=2)

        folders = (
            Folder(id=folder1, name="A", parent_id=None),
            Folder(id=folder2, name="B", parent_id=None),
        )

        # Moving folder1 under folder2 is safe
        assert would_create_cycle(folder1, folder2, folders) is False

    def test_would_create_cycle_moving_to_child(self):
        """Moving folder to its own child should create cycle."""
        from src.domain.projects.entities import Folder
        from src.domain.projects.invariants import would_create_cycle
        from src.domain.shared.types import FolderId

        parent = FolderId(value=1)
        child = FolderId(value=2)
        grandchild = FolderId(value=3)

        folders = (
            Folder(id=parent, name="Parent", parent_id=None),
            Folder(id=child, name="Child", parent_id=parent),
            Folder(id=grandchild, name="Grandchild", parent_id=child),
        )

        # Moving parent under child would create cycle
        assert would_create_cycle(parent, child, folders) is True

        # Moving parent under grandchild would also create cycle
        assert would_create_cycle(parent, grandchild, folders) is True

    def test_would_create_cycle_moving_to_self(self):
        """Moving folder to itself should create cycle."""
        from src.domain.projects.entities import Folder
        from src.domain.projects.invariants import would_create_cycle
        from src.domain.shared.types import FolderId

        folder_id = FolderId(value=1)

        folders = (Folder(id=folder_id, name="Folder", parent_id=None),)

        # Moving folder to itself is invalid
        assert would_create_cycle(folder_id, folder_id, folders) is True
