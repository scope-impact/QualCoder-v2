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
        from src.domain.projects.invariants import detect_source_type
        from src.domain.projects.entities import SourceType

        assert detect_source_type(Path("interview.txt")) == SourceType.TEXT
        assert detect_source_type(Path("document.docx")) == SourceType.TEXT
        assert detect_source_type(Path("notes.odt")) == SourceType.TEXT
        assert detect_source_type(Path("article.rtf")) == SourceType.TEXT

    def test_detect_audio_source_types(self):
        """Audio file extensions should be detected correctly."""
        from src.domain.projects.invariants import detect_source_type
        from src.domain.projects.entities import SourceType

        assert detect_source_type(Path("recording.mp3")) == SourceType.AUDIO
        assert detect_source_type(Path("interview.wav")) == SourceType.AUDIO
        assert detect_source_type(Path("podcast.m4a")) == SourceType.AUDIO

    def test_detect_video_source_types(self):
        """Video file extensions should be detected correctly."""
        from src.domain.projects.invariants import detect_source_type
        from src.domain.projects.entities import SourceType

        assert detect_source_type(Path("observation.mp4")) == SourceType.VIDEO
        assert detect_source_type(Path("interview.mov")) == SourceType.VIDEO
        assert detect_source_type(Path("recording.avi")) == SourceType.VIDEO

    def test_detect_image_source_types(self):
        """Image file extensions should be detected correctly."""
        from src.domain.projects.invariants import detect_source_type
        from src.domain.projects.entities import SourceType

        assert detect_source_type(Path("photo.jpg")) == SourceType.IMAGE
        assert detect_source_type(Path("diagram.png")) == SourceType.IMAGE
        assert detect_source_type(Path("scan.jpeg")) == SourceType.IMAGE

    def test_detect_pdf_source_types(self):
        """PDF file extensions should be detected correctly."""
        from src.domain.projects.invariants import detect_source_type
        from src.domain.projects.entities import SourceType

        assert detect_source_type(Path("article.pdf")) == SourceType.PDF

    def test_detect_unknown_source_types(self):
        """Unknown extensions should return UNKNOWN type."""
        from src.domain.projects.invariants import detect_source_type
        from src.domain.projects.entities import SourceType

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
        from src.domain.projects.invariants import is_source_name_unique
        from src.domain.projects.entities import Source, SourceType, SourceStatus
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
        assert can_open_project(
            Path("/home/user/project.qda"),
            path_exists=lambda _: True,
        ) is True

    def test_cannot_open_nonexistent_project(self):
        """Non-existent path should not be openable."""
        from src.domain.projects.invariants import can_open_project

        assert can_open_project(
            Path("/home/user/missing.qda"),
            path_exists=lambda _: False,
        ) is False

    def test_cannot_open_invalid_extension(self):
        """Wrong extension should not be openable even if exists."""
        from src.domain.projects.invariants import can_open_project

        assert can_open_project(
            Path("/home/user/project.txt"),
            path_exists=lambda _: True,
        ) is False


class TestCanCreateProjectInvariants:
    """Tests for project creation validation."""

    def test_can_create_project_at_valid_location(self):
        """Valid path with .qda and writable parent should be creatable."""
        from src.domain.projects.invariants import can_create_project

        assert can_create_project(
            Path("/home/user/new_project.qda"),
            path_exists=lambda _: False,
            parent_writable=lambda _: True,
        ) is True

    def test_cannot_create_project_at_existing_path(self):
        """Should not overwrite existing project."""
        from src.domain.projects.invariants import can_create_project

        assert can_create_project(
            Path("/home/user/existing.qda"),
            path_exists=lambda _: True,
            parent_writable=lambda _: True,
        ) is False

    def test_cannot_create_project_in_readonly_location(self):
        """Should not create in read-only directory."""
        from src.domain.projects.invariants import can_create_project

        assert can_create_project(
            Path("/readonly/project.qda"),
            path_exists=lambda _: False,
            parent_writable=lambda _: False,
        ) is False
