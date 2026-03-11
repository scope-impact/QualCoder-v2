"""
Folders Context: Command Handler Tests

Unit tests for folder command handlers following DDD-workshop patterns.
Tests both success and failure scenarios using mock repositories.
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING

import allure
import pytest

from src.contexts.folders.core.commandHandlers.delete_folder import delete_folder
from src.contexts.folders.core.commandHandlers.move_source import (
    move_source_to_folder,
)
from src.contexts.folders.core.commandHandlers.rename_folder import rename_folder
from src.contexts.folders.core.queryHandlers.get_folder import get_folder
from src.contexts.folders.core.queryHandlers.list_folders import list_folders
from src.contexts.projects.core.commands import (
    DeleteFolderCommand,
    MoveSourceToFolderCommand,
    RenameFolderCommand,
)
from src.contexts.projects.core.entities import Folder, Source, SourceStatus, SourceType
from src.contexts.projects.core.events import (
    FolderDeleted,
    FolderRenamed,
    SourceMovedToFolder,
)
from src.shared.common.types import FolderId, SourceId
from src.shared.infra.state import ProjectState

if TYPE_CHECKING:
    from src.contexts.projects.core.entities import Project

pytestmark = [
    pytest.mark.unit,
    allure.epic("QualCoder v2"),
    allure.feature("QC-027 Manage Sources"),
]


# ============================================================
# Mock Repositories
# ============================================================


class MockFolderRepository:
    """Mock folder repository for testing."""

    def __init__(self, folders: list[Folder] | None = None):
        self._folders: dict[int, Folder] = {}
        if folders:
            for f in folders:
                self._folders[f.id.value] = f

    def get_all(self) -> list[Folder]:
        return list(self._folders.values())

    def get_by_id(self, folder_id: FolderId) -> Folder | None:
        return self._folders.get(folder_id.value)

    def get_by_name(
        self, name: str, parent_id: FolderId | None = None
    ) -> Folder | None:
        for folder in self._folders.values():
            if folder.name == name and folder.parent_id == parent_id:
                return folder
        return None

    def get_children(self, parent_id: FolderId | None) -> list[Folder]:
        return [f for f in self._folders.values() if f.parent_id == parent_id]

    def get_root_folders(self) -> list[Folder]:
        return [f for f in self._folders.values() if f.parent_id is None]

    def save(self, folder: Folder) -> None:
        self._folders[folder.id.value] = folder

    def delete(self, folder_id: FolderId) -> None:
        self._folders.pop(folder_id.value, None)

    def exists(self, folder_id: FolderId) -> bool:
        return folder_id.value in self._folders

    def name_exists(
        self,
        name: str,
        parent_id: FolderId | None,
        exclude_id: FolderId | None = None,
    ) -> bool:
        for folder in self._folders.values():
            if exclude_id and folder.id == exclude_id:
                continue
            if folder.name == name and folder.parent_id == parent_id:
                return True
        return False

    def get_descendants(self, folder_id: FolderId) -> list[Folder]:
        result = []
        for folder in self._folders.values():
            if folder.parent_id == folder_id:
                result.append(folder)
                result.extend(self.get_descendants(folder.id))
        return result


class MockSourceRepository:
    """Mock source repository for testing."""

    def __init__(self, sources: list[Source] | None = None):
        self._sources: dict[int, Source] = {}
        if sources:
            for s in sources:
                self._sources[s.id.value] = s

    def get_all(self) -> list[Source]:
        return list(self._sources.values())

    def get_by_id(self, source_id: SourceId) -> Source | None:
        return self._sources.get(source_id.value)

    def get_by_folder(self, folder_id: FolderId | None) -> list[Source]:
        return [s for s in self._sources.values() if s.folder_id == folder_id]

    def save(self, source: Source) -> None:
        self._sources[source.id.value] = source


class MockEventBus:
    """Mock event bus for testing."""

    def __init__(self):
        self.published_events: list = []

    def publish(self, event) -> None:
        self.published_events.append(event)


# ============================================================
# Test Fixtures
# ============================================================


@pytest.fixture
def mock_project() -> Project:
    """Create a mock project for testing."""
    from src.contexts.projects.core.entities import Project, ProjectId

    return Project(
        id=ProjectId(value="test-project"),
        name="Test Project",
        path=Path("/tmp/test.qda"),
    )


@pytest.fixture
def project_state(mock_project) -> ProjectState:
    """Create project state with a project."""
    state = ProjectState()
    state.project = mock_project
    return state


@pytest.fixture
def empty_state() -> ProjectState:
    """Create project state without a project."""
    return ProjectState()


@pytest.fixture
def event_bus() -> MockEventBus:
    """Create mock event bus."""
    return MockEventBus()


@pytest.fixture
def sample_folder() -> Folder:
    """Create a sample folder for testing."""
    return Folder(
        id=FolderId(value="1"),
        name="Test Folder",
        parent_id=None,
        created_at=datetime.now(UTC),
    )


@pytest.fixture
def sample_source() -> Source:
    """Create a sample source for testing."""
    return Source(
        id=SourceId(value="100"),
        name="test_document.txt",
        source_type=SourceType.TEXT,
        status=SourceStatus.IMPORTED,
        folder_id=None,
    )


@pytest.fixture
def source_in_folder(sample_folder) -> Source:
    """Create a source that is in a folder."""
    return Source(
        id=SourceId(value="101"),
        name="document_in_folder.txt",
        source_type=SourceType.TEXT,
        status=SourceStatus.IMPORTED,
        folder_id=sample_folder.id,
    )


# ============================================================
# Delete Folder Tests
# ============================================================


@allure.story("QC-027.13 Agent Manage Folders")
class TestDeleteFolder:
    """Tests for delete_folder command handler."""

    @allure.title("Deletes empty folder, publishes event, and removes from repo")
    def test_deletes_empty_folder_success(self, project_state, sample_folder, event_bus):
        """Should delete an empty folder, publish FolderDeleted event, and remove from repo."""
        folder_repo = MockFolderRepository([sample_folder])
        source_repo = MockSourceRepository()

        command = DeleteFolderCommand(folder_id=sample_folder.id.value)

        result = delete_folder(
            command=command,
            state=project_state,
            folder_repo=folder_repo,
            source_repo=source_repo,
            event_bus=event_bus,
        )

        assert result.success is True
        assert isinstance(result.data, FolderDeleted)
        assert result.data.folder_id == sample_folder.id
        assert result.data.name == sample_folder.name
        assert len(event_bus.published_events) == 1
        assert isinstance(event_bus.published_events[0], FolderDeleted)
        assert folder_repo.get_by_id(sample_folder.id) is None

    @pytest.mark.parametrize(
        ("scenario", "use_empty_state", "folder_exists", "has_sources", "expected_code_fragment"),
        [
            ("no_project", True, True, False, "NO_PROJECT"),
            ("not_found", False, False, False, "NOT_FOUND"),
            ("not_empty", False, True, True, "NOT_EMPTY"),
        ],
        ids=["no-project", "folder-not-found", "folder-not-empty"],
    )
    @allure.title("Fails delete under various error conditions")
    def test_delete_fails(
        self,
        scenario,
        use_empty_state,
        folder_exists,
        has_sources,
        expected_code_fragment,
        project_state,
        empty_state,
        sample_folder,
        source_in_folder,
        event_bus,
    ):
        """Should fail with appropriate error code for various invalid conditions."""
        state = empty_state if use_empty_state else project_state
        folder_repo = MockFolderRepository([sample_folder] if folder_exists else [])
        source_repo = MockSourceRepository([source_in_folder] if has_sources else [])

        command = DeleteFolderCommand(
            folder_id=sample_folder.id.value if folder_exists else "999"
        )

        result = delete_folder(
            command=command,
            state=state,
            folder_repo=folder_repo,
            source_repo=source_repo,
            event_bus=event_bus,
        )

        assert result.success is False
        assert expected_code_fragment in result.error_code
        assert len(event_bus.published_events) == 0


# ============================================================
# Get Folder Tests
# ============================================================


@allure.story("QC-027.13 Agent Manage Folders")
class TestGetFolder:
    """Tests for get_folder query handler."""

    @allure.title("Returns folder details with source count and parent info")
    def test_returns_folder_details_with_sources_and_parent(
        self, project_state, sample_folder, source_in_folder
    ):
        """Should return folder details including source count and parent_id for nested folders."""
        folder_repo = MockFolderRepository([sample_folder])
        source_repo = MockSourceRepository([source_in_folder])

        result = get_folder(
            folder_id=sample_folder.id.value,
            state=project_state,
            folder_repo=folder_repo,
            source_repo=source_repo,
        )

        assert result.success is True
        assert result.data["folder_id"] == sample_folder.id.value
        assert result.data["name"] == sample_folder.name
        assert result.data["parent_id"] is None
        assert result.data["source_count"] == 1

        # Test nested folder returns parent_id
        child_folder = Folder(
            id=FolderId(value="2"),
            name="Child Folder",
            parent_id=sample_folder.id,
            created_at=datetime.now(UTC),
        )
        folder_repo = MockFolderRepository([sample_folder, child_folder])
        source_repo = MockSourceRepository()

        result = get_folder(
            folder_id=child_folder.id.value,
            state=project_state,
            folder_repo=folder_repo,
            source_repo=source_repo,
        )

        assert result.success is True
        assert result.data["parent_id"] == sample_folder.id.value

    @pytest.mark.parametrize(
        ("use_empty_state", "folder_exists", "expected_code"),
        [
            (True, True, "FOLDER_NOT_FOUND/NO_PROJECT"),
            (False, False, "FOLDER_NOT_FOUND/NOT_FOUND"),
        ],
        ids=["no-project", "folder-not-found"],
    )
    @allure.title("Fails get_folder under various error conditions")
    def test_get_folder_fails(
        self,
        use_empty_state,
        folder_exists,
        expected_code,
        project_state,
        empty_state,
        sample_folder,
    ):
        """Should fail with appropriate error code for invalid conditions."""
        state = empty_state if use_empty_state else project_state
        folder_repo = MockFolderRepository([sample_folder] if folder_exists else [])
        source_repo = MockSourceRepository()

        result = get_folder(
            folder_id=sample_folder.id.value if folder_exists else "999",
            state=state,
            folder_repo=folder_repo,
            source_repo=source_repo,
        )

        assert result.success is False
        assert result.error_code == expected_code


# ============================================================
# List Folders Tests
# ============================================================


@allure.story("QC-027.13 Agent Manage Folders")
class TestListFolders:
    """Tests for list_folders query handler."""

    @allure.title("Returns folders list with structure details and handles empty case")
    def test_returns_folders_with_structure(self, project_state, sample_folder):
        """Should return list of folders with total count and structure, including empty case."""
        # Empty case
        folder_repo = MockFolderRepository()
        result = list_folders(state=project_state, folder_repo=folder_repo)

        assert result.success is True
        assert result.data["total_count"] == 0
        assert result.data["folders"] == []

        # Multiple folders case
        folder2 = Folder(
            id=FolderId(value="2"),
            name="Second Folder",
            parent_id=None,
            created_at=datetime.now(UTC),
        )
        folder_repo = MockFolderRepository([sample_folder, folder2])

        result = list_folders(state=project_state, folder_repo=folder_repo)

        assert result.success is True
        assert result.data["total_count"] == 2
        assert len(result.data["folders"]) == 2
        folder_data = result.data["folders"][0]
        assert "folder_id" in folder_data
        assert "name" in folder_data
        assert "parent_id" in folder_data

    @allure.title("Fails when no project is open")
    def test_fails_when_no_project(self, empty_state):
        """Should fail with NO_PROJECT error when no project is open."""
        folder_repo = MockFolderRepository()

        result = list_folders(state=empty_state, folder_repo=folder_repo)

        assert result.success is False
        assert result.error_code == "FOLDERS_NOT_LISTED/NO_PROJECT"
        assert "No project is currently open" in result.error


# ============================================================
# Move Source Tests
# ============================================================


@allure.story("QC-027.13 Agent Manage Folders")
class TestMoveSourceToFolder:
    """Tests for move_source_to_folder command handler."""

    @allure.title("Moves source to folder and to root with event and rollback")
    def test_moves_source_to_folder_and_root(
        self, project_state, sample_folder, sample_source, source_in_folder, event_bus
    ):
        """Should move source to folder and to root, publishing events and providing rollback."""
        # Move to folder
        folder_repo = MockFolderRepository([sample_folder])
        source_repo = MockSourceRepository([sample_source])

        command = MoveSourceToFolderCommand(
            source_id=sample_source.id.value,
            folder_id=sample_folder.id.value,
        )

        result = move_source_to_folder(
            command=command,
            state=project_state,
            folder_repo=folder_repo,
            source_repo=source_repo,
            event_bus=event_bus,
        )

        assert result.success is True
        assert isinstance(result.data, SourceMovedToFolder)
        assert result.data.source_id == sample_source.id
        assert result.data.new_folder_id == sample_folder.id
        assert len(event_bus.published_events) == 1
        assert result.rollback_command is not None
        assert isinstance(result.rollback_command, MoveSourceToFolderCommand)
        assert result.rollback_command.folder_id is None
        updated_source = source_repo.get_by_id(sample_source.id)
        assert updated_source.folder_id == sample_folder.id

        # Move to root
        event_bus2 = MockEventBus()
        folder_repo2 = MockFolderRepository([sample_folder])
        source_repo2 = MockSourceRepository([source_in_folder])

        command2 = MoveSourceToFolderCommand(
            source_id=source_in_folder.id.value,
            folder_id=None,
        )

        result2 = move_source_to_folder(
            command=command2,
            state=project_state,
            folder_repo=folder_repo2,
            source_repo=source_repo2,
            event_bus=event_bus2,
        )

        assert result2.success is True
        assert result2.data.old_folder_id == sample_folder.id
        assert result2.data.new_folder_id is None

    @pytest.mark.parametrize(
        ("use_empty_state", "source_exists", "folder_exists", "expected_code_fragment"),
        [
            (True, True, True, "NO_PROJECT"),
            (False, False, True, "SOURCE_NOT_FOUND"),
            (False, True, False, "FOLDER_NOT_FOUND"),
        ],
        ids=["no-project", "source-not-found", "folder-not-found"],
    )
    @allure.title("Fails move under various error conditions")
    def test_move_fails(
        self,
        use_empty_state,
        source_exists,
        folder_exists,
        expected_code_fragment,
        project_state,
        empty_state,
        sample_folder,
        sample_source,
        event_bus,
    ):
        """Should fail with appropriate error code for various invalid conditions."""
        state = empty_state if use_empty_state else project_state
        folder_repo = MockFolderRepository([sample_folder] if folder_exists else [])
        source_repo = MockSourceRepository([sample_source] if source_exists else [])

        command = MoveSourceToFolderCommand(
            source_id=sample_source.id.value if source_exists else "999",
            folder_id=sample_folder.id.value if folder_exists else "999",
        )

        result = move_source_to_folder(
            command=command,
            state=state,
            folder_repo=folder_repo,
            source_repo=source_repo,
            event_bus=event_bus,
        )

        assert result.success is False
        assert expected_code_fragment in result.error_code
        assert len(event_bus.published_events) == 0


# ============================================================
# Rename Folder Tests
# ============================================================


@allure.story("QC-027.13 Agent Manage Folders")
class TestRenameFolder:
    """Tests for rename_folder command handler."""

    @allure.title("Renames folder with event, rollback, and allows same name")
    def test_renames_folder_success(self, project_state, sample_folder, event_bus):
        """Should rename folder, publish event with old/new names, provide rollback, and allow same name."""
        folder_repo = MockFolderRepository([sample_folder])
        source_repo = MockSourceRepository()
        original_name = sample_folder.name

        command = RenameFolderCommand(
            folder_id=sample_folder.id.value,
            new_name="Renamed Folder",
        )

        result = rename_folder(
            command=command,
            state=project_state,
            folder_repo=folder_repo,
            source_repo=source_repo,
            event_bus=event_bus,
        )

        assert result.success is True
        assert isinstance(result.data, Folder)
        assert result.data.name == "Renamed Folder"
        assert len(event_bus.published_events) == 1
        event = event_bus.published_events[0]
        assert isinstance(event, FolderRenamed)
        assert event.old_name == original_name
        assert event.new_name == "Renamed Folder"
        assert result.rollback_command is not None
        assert isinstance(result.rollback_command, RenameFolderCommand)
        assert result.rollback_command.new_name == original_name
        updated_folder = folder_repo.get_by_id(sample_folder.id)
        assert updated_folder.name == "Renamed Folder"

        # Renaming to same name should also succeed
        event_bus2 = MockEventBus()
        folder_repo2 = MockFolderRepository([sample_folder])

        command2 = RenameFolderCommand(
            folder_id=sample_folder.id.value,
            new_name=sample_folder.name,
        )

        result2 = rename_folder(
            command=command2,
            state=project_state,
            folder_repo=folder_repo2,
            source_repo=source_repo,
            event_bus=event_bus2,
        )

        assert result2.success is True

    @pytest.mark.parametrize(
        ("use_empty_state", "folder_exists", "new_name", "duplicate", "expected_code_fragment"),
        [
            (True, True, "New Name", False, "NO_PROJECT"),
            (False, False, "New Name", False, "NOT_FOUND"),
            (False, True, "", False, "INVALID_NAME"),
            (False, True, "   ", False, "INVALID_NAME"),
            (False, True, "Existing Folder", True, "DUPLICATE_NAME"),
        ],
        ids=["no-project", "folder-not-found", "empty-name", "whitespace-name", "duplicate-name"],
    )
    @allure.title("Fails rename under various error conditions")
    def test_rename_fails(
        self,
        use_empty_state,
        folder_exists,
        new_name,
        duplicate,
        expected_code_fragment,
        project_state,
        empty_state,
        sample_folder,
        event_bus,
    ):
        """Should fail with appropriate error code for various invalid conditions."""
        state = empty_state if use_empty_state else project_state
        folders = [sample_folder] if folder_exists else []
        if duplicate:
            other_folder = Folder(
                id=FolderId(value="2"),
                name="Existing Folder",
                parent_id=None,
                created_at=datetime.now(UTC),
            )
            folders.append(other_folder)
        folder_repo = MockFolderRepository(folders)
        source_repo = MockSourceRepository()

        command = RenameFolderCommand(
            folder_id=sample_folder.id.value if folder_exists else "999",
            new_name=new_name,
        )

        result = rename_folder(
            command=command,
            state=state,
            folder_repo=folder_repo,
            source_repo=source_repo,
            event_bus=event_bus,
        )

        assert result.success is False
        assert expected_code_fragment in result.error_code
        assert len(event_bus.published_events) == 0
