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
        from src.domain.projects.derivers import ProjectState, derive_create_project
        from src.domain.projects.events import ProjectCreated

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
            EmptyProjectName,
            ProjectState,
            derive_create_project,
        )
        from src.domain.shared.types import Failure

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

        assert isinstance(result, Failure)
        assert isinstance(result.failure(), EmptyProjectName)

    def test_fails_with_invalid_path(self):
        """Should fail with InvalidProjectPath for non-.qda paths."""
        from src.domain.projects.derivers import (
            InvalidProjectPath,
            ProjectState,
            derive_create_project,
        )
        from src.domain.shared.types import Failure

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

        assert isinstance(result, Failure)
        assert isinstance(result.failure(), InvalidProjectPath)

    def test_fails_when_path_already_exists(self):
        """Should fail with ProjectAlreadyExists when file exists."""
        from src.domain.projects.derivers import (
            ProjectAlreadyExists,
            ProjectState,
            derive_create_project,
        )
        from src.domain.shared.types import Failure

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

        assert isinstance(result, Failure)
        assert isinstance(result.failure(), ProjectAlreadyExists)

    def test_fails_when_parent_not_writable(self):
        """Should fail with ParentNotWritable for read-only directories."""
        from src.domain.projects.derivers import (
            ParentNotWritable,
            ProjectState,
            derive_create_project,
        )
        from src.domain.shared.types import Failure

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

        assert isinstance(result, Failure)
        assert isinstance(result.failure(), ParentNotWritable)


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
            ProjectNotFound,
            ProjectState,
            derive_open_project,
        )
        from src.domain.shared.types import Failure

        state = ProjectState(
            path_exists=lambda _: False,
            parent_writable=lambda _: True,
        )

        result = derive_open_project(
            path=Path("/home/user/missing.qda"),
            state=state,
        )

        assert isinstance(result, Failure)
        assert isinstance(result.failure(), ProjectNotFound)

    def test_fails_with_invalid_extension(self):
        """Should fail with InvalidProjectPath for non-.qda files."""
        from src.domain.projects.derivers import (
            InvalidProjectPath,
            ProjectState,
            derive_open_project,
        )
        from src.domain.shared.types import Failure

        state = ProjectState(
            path_exists=lambda _: True,
            parent_writable=lambda _: True,
        )

        result = derive_open_project(
            path=Path("/home/user/document.txt"),
            state=state,
        )

        assert isinstance(result, Failure)
        assert isinstance(result.failure(), InvalidProjectPath)


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
            SourceFileNotFound,
            derive_add_source,
        )
        from src.domain.shared.types import Failure

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

        assert isinstance(result, Failure)
        assert isinstance(result.failure(), SourceFileNotFound)

    def test_fails_with_duplicate_name(self):
        """Should fail with DuplicateSourceName for existing source name."""
        from src.domain.projects.derivers import (
            DuplicateSourceName,
            ProjectState,
            derive_add_source,
        )
        from src.domain.projects.entities import Source, SourceStatus, SourceType
        from src.domain.shared.types import Failure, SourceId

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

        assert isinstance(result, Failure)
        assert isinstance(result.failure(), DuplicateSourceName)

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
