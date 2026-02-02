"""
Tests for Application State

Tests the ProjectState dataclass that manages in-memory cache.
"""

import pytest

from src.application.state import ProjectState
from src.contexts.cases.core.entities import Case
from src.contexts.projects.core.entities import (
    Folder,
    Project,
    ProjectId,
    Source,
    SourceStatus,
    SourceType,
)
from src.contexts.shared.core.types import CaseId, FolderId, SourceId


def make_project(tmp_path, name="Test"):
    """Create a test Project entity."""
    path = tmp_path / "test.qda"
    return Project(
        id=ProjectId.from_path(path),
        name=name,
        path=path,
    )


class TestProjectState:
    """Tests for ProjectState dataclass."""

    def test_initial_state_is_empty(self):
        """New state has no project open."""
        state = ProjectState()

        assert state.project is None
        assert state.sources == []
        assert state.cases == []
        assert state.folders == []
        assert state.current_screen is None
        assert state.current_source is None
        assert state.is_project_open is False

    def test_is_project_open_with_project(self, tmp_path):
        """is_project_open returns True when project is set."""
        state = ProjectState()
        state.project = make_project(tmp_path)

        assert state.is_project_open is True


class TestProjectStateSourceOperations:
    """Tests for source operations on ProjectState."""

    @pytest.fixture
    def state_with_sources(self, tmp_path):
        """Create state with some sources."""
        state = ProjectState()
        state.project = make_project(tmp_path)
        state.sources = [
            Source(
                id=SourceId(value=1),
                name="source1.txt",
                source_type=SourceType.TEXT,
                status=SourceStatus.IMPORTED,
                file_path=tmp_path / "source1.txt",
            ),
            Source(
                id=SourceId(value=2),
                name="source2.txt",
                source_type=SourceType.TEXT,
                status=SourceStatus.IMPORTED,
                file_path=tmp_path / "source2.txt",
            ),
        ]
        return state

    def test_add_source(self, tmp_path):
        """add_source appends a source to the list."""
        state = ProjectState()
        source = Source(
            id=SourceId(value=1),
            name="test.txt",
            source_type=SourceType.TEXT,
            status=SourceStatus.IMPORTED,
            file_path=tmp_path / "test.txt",
        )

        state.add_source(source)

        assert len(state.sources) == 1
        assert state.sources[0].name == "test.txt"

    def test_remove_source(self, state_with_sources):
        """remove_source removes source by ID."""
        state_with_sources.remove_source(1)

        assert len(state_with_sources.sources) == 1
        assert state_with_sources.sources[0].id.value == 2

    def test_get_source_found(self, state_with_sources):
        """get_source returns source when found."""
        source = state_with_sources.get_source(1)

        assert source is not None
        assert source.name == "source1.txt"

    def test_get_source_not_found(self, state_with_sources):
        """get_source returns None when not found."""
        source = state_with_sources.get_source(999)

        assert source is None

    def test_update_source(self, state_with_sources):
        """update_source replaces source with same ID."""
        updated = Source(
            id=SourceId(value=1),
            name="updated.txt",
            source_type=SourceType.TEXT,
            status=SourceStatus.IMPORTED,
            file_path=state_with_sources.sources[0].file_path,
        )

        state_with_sources.update_source(updated)

        assert state_with_sources.sources[0].name == "updated.txt"
        assert len(state_with_sources.sources) == 2


class TestProjectStateCaseOperations:
    """Tests for case operations on ProjectState."""

    @pytest.fixture
    def state_with_cases(self, tmp_path):
        """Create state with some cases."""
        state = ProjectState()
        state.project = make_project(tmp_path)
        state.cases = [
            Case(id=CaseId(value=1), name="Case 1"),
            Case(id=CaseId(value=2), name="Case 2"),
        ]
        return state

    def test_add_case(self):
        """add_case appends a case to the list."""
        state = ProjectState()
        case = Case(id=CaseId(value=1), name="Test Case")

        state.add_case(case)

        assert len(state.cases) == 1
        assert state.cases[0].name == "Test Case"

    def test_remove_case(self, state_with_cases):
        """remove_case removes case by ID."""
        state_with_cases.remove_case(1)

        assert len(state_with_cases.cases) == 1
        assert state_with_cases.cases[0].id.value == 2

    def test_get_case_found(self, state_with_cases):
        """get_case returns case when found."""
        case = state_with_cases.get_case(1)

        assert case is not None
        assert case.name == "Case 1"

    def test_get_case_not_found(self, state_with_cases):
        """get_case returns None when not found."""
        case = state_with_cases.get_case(999)

        assert case is None


class TestProjectStateFolderOperations:
    """Tests for folder operations on ProjectState."""

    @pytest.fixture
    def state_with_folders(self, tmp_path):
        """Create state with some folders."""
        state = ProjectState()
        state.project = make_project(tmp_path)
        state.folders = [
            Folder(id=FolderId(value=1), name="Folder 1"),
            Folder(id=FolderId(value=2), name="Folder 2"),
        ]
        return state

    def test_add_folder(self):
        """add_folder appends a folder to the list."""
        state = ProjectState()
        folder = Folder(id=FolderId(value=1), name="Test Folder")

        state.add_folder(folder)

        assert len(state.folders) == 1
        assert state.folders[0].name == "Test Folder"

    def test_remove_folder(self, state_with_folders):
        """remove_folder removes folder by ID."""
        state_with_folders.remove_folder(1)

        assert len(state_with_folders.folders) == 1
        assert state_with_folders.folders[0].id.value == 2


class TestProjectStateClear:
    """Tests for clearing ProjectState."""

    def test_clear_resets_all_project_data(self, tmp_path):
        """clear() resets all project-specific data."""
        state = ProjectState()
        state.project = make_project(tmp_path)
        state.sources = [
            Source(
                id=SourceId(value=1),
                name="test.txt",
                source_type=SourceType.TEXT,
                status=SourceStatus.IMPORTED,
                file_path=tmp_path / "test.txt",
            ),
        ]
        state.cases = [Case(id=CaseId(value=1), name="Case")]
        state.folders = [Folder(id=FolderId(value=1), name="Folder")]
        state.current_screen = "coding"

        state.clear()

        assert state.project is None
        assert state.sources == []
        assert state.cases == []
        assert state.folders == []
        assert state.current_screen is None
        assert state.current_source is None

    def test_clear_preserves_recent_projects(self, tmp_path):
        """clear() preserves recent_projects list."""
        state = ProjectState()
        project = make_project(tmp_path)
        state.project = project
        state.add_to_recent(project)

        state.clear()

        assert len(state.recent_projects) == 1
