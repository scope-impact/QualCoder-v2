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
from src.contexts.folders.core.commandHandlers.get_folder import get_folder
from src.contexts.folders.core.commandHandlers.list_folders import list_folders
from src.contexts.folders.core.commandHandlers.move_source import (
    move_source_to_folder,
)
from src.contexts.folders.core.commandHandlers.rename_folder import rename_folder
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
    allure.feature("Folders Bounded Context"),
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
        id=FolderId(value=1),
        name="Test Folder",
        parent_id=None,
        created_at=datetime.now(UTC),
    )


@pytest.fixture
def sample_source() -> Source:
    """Create a sample source for testing."""
    return Source(
        id=SourceId(value=100),
        name="test_document.txt",
        source_type=SourceType.TEXT,
        status=SourceStatus.IMPORTED,
        folder_id=None,
    )


@pytest.fixture
def source_in_folder(sample_folder) -> Source:
    """Create a source that is in a folder."""
    return Source(
        id=SourceId(value=101),
        name="document_in_folder.txt",
        source_type=SourceType.TEXT,
        status=SourceStatus.IMPORTED,
        folder_id=sample_folder.id,
    )


# ============================================================
# Delete Folder Tests
# ============================================================


@allure.story("Delete Folder")
class TestDeleteFolder:
    """Tests for delete_folder command handler."""

    @allure.title("Deletes empty folder successfully")
    def test_deletes_empty_folder(self, project_state, sample_folder, event_bus):
        """Should delete an empty folder and publish FolderDeleted event."""
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

    @allure.title("Fails when no project is open")
    def test_fails_when_no_project(self, empty_state, sample_folder, event_bus):
        """Should fail with NO_PROJECT error when no project is open."""
        folder_repo = MockFolderRepository([sample_folder])
        source_repo = MockSourceRepository()

        command = DeleteFolderCommand(folder_id=sample_folder.id.value)

        result = delete_folder(
            command=command,
            state=empty_state,
            folder_repo=folder_repo,
            source_repo=source_repo,
            event_bus=event_bus,
        )

        assert result.success is False
        assert result.error_code == "FOLDER_NOT_DELETED/NO_PROJECT"
        assert "No project is currently open" in result.error
        assert len(event_bus.published_events) == 0

    @allure.title("Fails when folder not found")
    def test_fails_when_folder_not_found(self, project_state, event_bus):
        """Should fail with NOT_FOUND error when folder does not exist."""
        folder_repo = MockFolderRepository()
        source_repo = MockSourceRepository()

        command = DeleteFolderCommand(folder_id=999)

        result = delete_folder(
            command=command,
            state=project_state,
            folder_repo=folder_repo,
            source_repo=source_repo,
            event_bus=event_bus,
        )

        assert result.success is False
        assert "NOT_FOUND" in result.error_code
        assert len(event_bus.published_events) == 0

    @allure.title("Fails when folder contains sources")
    def test_fails_when_folder_not_empty(
        self, project_state, sample_folder, source_in_folder, event_bus
    ):
        """Should fail with NOT_EMPTY error when folder contains sources."""
        folder_repo = MockFolderRepository([sample_folder])
        source_repo = MockSourceRepository([source_in_folder])

        command = DeleteFolderCommand(folder_id=sample_folder.id.value)

        result = delete_folder(
            command=command,
            state=project_state,
            folder_repo=folder_repo,
            source_repo=source_repo,
            event_bus=event_bus,
        )

        assert result.success is False
        assert "NOT_EMPTY" in result.error_code
        # Error message comes from failure event type
        assert len(event_bus.published_events) == 0

    @allure.title("Removes folder from repository on success")
    def test_removes_from_repository(self, project_state, sample_folder, event_bus):
        """Should remove folder from repository after successful deletion."""
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
        assert folder_repo.get_by_id(sample_folder.id) is None


# ============================================================
# Get Folder Tests
# ============================================================


@allure.story("Get Folder")
class TestGetFolder:
    """Tests for get_folder query handler."""

    @allure.title("Returns folder details successfully")
    def test_returns_folder_details(self, project_state, sample_folder):
        """Should return folder details with source count."""
        folder_repo = MockFolderRepository([sample_folder])
        source_repo = MockSourceRepository()

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
        assert result.data["source_count"] == 0

    @allure.title("Returns correct source count")
    def test_returns_source_count(self, project_state, sample_folder, source_in_folder):
        """Should return correct count of sources in folder."""
        folder_repo = MockFolderRepository([sample_folder])
        source_repo = MockSourceRepository([source_in_folder])

        result = get_folder(
            folder_id=sample_folder.id.value,
            state=project_state,
            folder_repo=folder_repo,
            source_repo=source_repo,
        )

        assert result.success is True
        assert result.data["source_count"] == 1

    @allure.title("Fails when no project is open")
    def test_fails_when_no_project(self, empty_state, sample_folder):
        """Should fail with NO_PROJECT error when no project is open."""
        folder_repo = MockFolderRepository([sample_folder])
        source_repo = MockSourceRepository()

        result = get_folder(
            folder_id=sample_folder.id.value,
            state=empty_state,
            folder_repo=folder_repo,
            source_repo=source_repo,
        )

        assert result.success is False
        assert result.error_code == "FOLDER_NOT_FOUND/NO_PROJECT"
        assert "No project is currently open" in result.error

    @allure.title("Fails when folder not found")
    def test_fails_when_folder_not_found(self, project_state):
        """Should fail with NOT_FOUND error when folder does not exist."""
        folder_repo = MockFolderRepository()
        source_repo = MockSourceRepository()

        result = get_folder(
            folder_id=999,
            state=project_state,
            folder_repo=folder_repo,
            source_repo=source_repo,
        )

        assert result.success is False
        assert result.error_code == "FOLDER_NOT_FOUND/NOT_FOUND"
        assert "999" in result.error

    @allure.title("Returns parent_id for nested folders")
    def test_returns_parent_id_for_nested_folder(self, project_state, sample_folder):
        """Should return parent_id for nested folders."""
        parent_folder = sample_folder
        child_folder = Folder(
            id=FolderId(value=2),
            name="Child Folder",
            parent_id=parent_folder.id,
            created_at=datetime.now(UTC),
        )
        folder_repo = MockFolderRepository([parent_folder, child_folder])
        source_repo = MockSourceRepository()

        result = get_folder(
            folder_id=child_folder.id.value,
            state=project_state,
            folder_repo=folder_repo,
            source_repo=source_repo,
        )

        assert result.success is True
        assert result.data["parent_id"] == parent_folder.id.value


# ============================================================
# List Folders Tests
# ============================================================


@allure.story("List Folders")
class TestListFolders:
    """Tests for list_folders query handler."""

    @allure.title("Returns all folders successfully")
    def test_returns_all_folders(self, project_state, sample_folder):
        """Should return list of all folders with total count."""
        folder2 = Folder(
            id=FolderId(value=2),
            name="Second Folder",
            parent_id=None,
            created_at=datetime.now(UTC),
        )
        folder_repo = MockFolderRepository([sample_folder, folder2])

        result = list_folders(
            state=project_state,
            folder_repo=folder_repo,
        )

        assert result.success is True
        assert result.data["total_count"] == 2
        assert len(result.data["folders"]) == 2

    @allure.title("Returns empty list when no folders exist")
    def test_returns_empty_list(self, project_state):
        """Should return empty list when no folders exist."""
        folder_repo = MockFolderRepository()

        result = list_folders(
            state=project_state,
            folder_repo=folder_repo,
        )

        assert result.success is True
        assert result.data["total_count"] == 0
        assert result.data["folders"] == []

    @allure.title("Fails when no project is open")
    def test_fails_when_no_project(self, empty_state):
        """Should fail with NO_PROJECT error when no project is open."""
        folder_repo = MockFolderRepository()

        result = list_folders(
            state=empty_state,
            folder_repo=folder_repo,
        )

        assert result.success is False
        assert result.error_code == "FOLDERS_NOT_LISTED/NO_PROJECT"
        assert "No project is currently open" in result.error

    @allure.title("Returns folder structure details")
    def test_returns_folder_structure(self, project_state, sample_folder):
        """Should return folder_id, name, and parent_id for each folder."""
        folder_repo = MockFolderRepository([sample_folder])

        result = list_folders(
            state=project_state,
            folder_repo=folder_repo,
        )

        assert result.success is True
        folder_data = result.data["folders"][0]
        assert "folder_id" in folder_data
        assert "name" in folder_data
        assert "parent_id" in folder_data
        assert folder_data["folder_id"] == sample_folder.id.value
        assert folder_data["name"] == sample_folder.name


# ============================================================
# Move Source Tests
# ============================================================


@allure.story("Move Source to Folder")
class TestMoveSourceToFolder:
    """Tests for move_source_to_folder command handler."""

    @allure.title("Moves source to folder successfully")
    def test_moves_source_to_folder(
        self, project_state, sample_folder, sample_source, event_bus
    ):
        """Should move source to folder and publish SourceMovedToFolder event."""
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

    @allure.title("Moves source to root (no folder)")
    def test_moves_source_to_root(
        self, project_state, sample_folder, source_in_folder, event_bus
    ):
        """Should move source to root (folder_id=None)."""
        folder_repo = MockFolderRepository([sample_folder])
        source_repo = MockSourceRepository([source_in_folder])

        command = MoveSourceToFolderCommand(
            source_id=source_in_folder.id.value,
            folder_id=None,
        )

        result = move_source_to_folder(
            command=command,
            state=project_state,
            folder_repo=folder_repo,
            source_repo=source_repo,
            event_bus=event_bus,
        )

        assert result.success is True
        assert result.data.old_folder_id == sample_folder.id
        assert result.data.new_folder_id is None

    @allure.title("Provides rollback command")
    def test_provides_rollback_command(
        self, project_state, sample_folder, sample_source, event_bus
    ):
        """Should provide rollback command to restore original folder."""
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
        assert result.rollback_command is not None
        assert isinstance(result.rollback_command, MoveSourceToFolderCommand)
        # Rollback should move back to original folder (None for this source)
        assert result.rollback_command.folder_id is None

    @allure.title("Fails when no project is open")
    def test_fails_when_no_project(
        self, empty_state, sample_folder, sample_source, event_bus
    ):
        """Should fail with NO_PROJECT error when no project is open."""
        folder_repo = MockFolderRepository([sample_folder])
        source_repo = MockSourceRepository([sample_source])

        command = MoveSourceToFolderCommand(
            source_id=sample_source.id.value,
            folder_id=sample_folder.id.value,
        )

        result = move_source_to_folder(
            command=command,
            state=empty_state,
            folder_repo=folder_repo,
            source_repo=source_repo,
            event_bus=event_bus,
        )

        assert result.success is False
        assert result.error_code == "SOURCE_NOT_MOVED/NO_PROJECT"
        assert len(event_bus.published_events) == 0

    @allure.title("Fails when source not found")
    def test_fails_when_source_not_found(self, project_state, sample_folder, event_bus):
        """Should fail with SOURCE_NOT_FOUND error when source does not exist."""
        folder_repo = MockFolderRepository([sample_folder])
        source_repo = MockSourceRepository()

        command = MoveSourceToFolderCommand(
            source_id=999,
            folder_id=sample_folder.id.value,
        )

        result = move_source_to_folder(
            command=command,
            state=project_state,
            folder_repo=folder_repo,
            source_repo=source_repo,
            event_bus=event_bus,
        )

        assert result.success is False
        assert "SOURCE_NOT_FOUND" in result.error_code
        assert len(event_bus.published_events) == 0

    @allure.title("Fails when target folder not found")
    def test_fails_when_folder_not_found(self, project_state, sample_source, event_bus):
        """Should fail with FOLDER_NOT_FOUND error when folder does not exist."""
        folder_repo = MockFolderRepository()
        source_repo = MockSourceRepository([sample_source])

        command = MoveSourceToFolderCommand(
            source_id=sample_source.id.value,
            folder_id=999,
        )

        result = move_source_to_folder(
            command=command,
            state=project_state,
            folder_repo=folder_repo,
            source_repo=source_repo,
            event_bus=event_bus,
        )

        assert result.success is False
        assert "FOLDER_NOT_FOUND" in result.error_code
        assert len(event_bus.published_events) == 0

    @allure.title("Updates source in repository")
    def test_updates_source_in_repository(
        self, project_state, sample_folder, sample_source, event_bus
    ):
        """Should update source's folder_id in repository."""
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
        updated_source = source_repo.get_by_id(sample_source.id)
        assert updated_source.folder_id == sample_folder.id


# ============================================================
# Rename Folder Tests
# ============================================================


@allure.story("Rename Folder")
class TestRenameFolder:
    """Tests for rename_folder command handler."""

    @allure.title("Renames folder successfully")
    def test_renames_folder(self, project_state, sample_folder, event_bus):
        """Should rename folder and publish FolderRenamed event."""
        folder_repo = MockFolderRepository([sample_folder])
        source_repo = MockSourceRepository()

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
        assert isinstance(event_bus.published_events[0], FolderRenamed)

    @allure.title("Provides rollback command with original name")
    def test_provides_rollback_command(self, project_state, sample_folder, event_bus):
        """Should provide rollback command to restore original name."""
        folder_repo = MockFolderRepository([sample_folder])
        source_repo = MockSourceRepository()
        original_name = sample_folder.name

        command = RenameFolderCommand(
            folder_id=sample_folder.id.value,
            new_name="New Name",
        )

        result = rename_folder(
            command=command,
            state=project_state,
            folder_repo=folder_repo,
            source_repo=source_repo,
            event_bus=event_bus,
        )

        assert result.success is True
        assert result.rollback_command is not None
        assert isinstance(result.rollback_command, RenameFolderCommand)
        assert result.rollback_command.new_name == original_name

    @allure.title("Fails when no project is open")
    def test_fails_when_no_project(self, empty_state, sample_folder, event_bus):
        """Should fail with NO_PROJECT error when no project is open."""
        folder_repo = MockFolderRepository([sample_folder])
        source_repo = MockSourceRepository()

        command = RenameFolderCommand(
            folder_id=sample_folder.id.value,
            new_name="New Name",
        )

        result = rename_folder(
            command=command,
            state=empty_state,
            folder_repo=folder_repo,
            source_repo=source_repo,
            event_bus=event_bus,
        )

        assert result.success is False
        assert result.error_code == "FOLDER_NOT_RENAMED/NO_PROJECT"
        assert len(event_bus.published_events) == 0

    @allure.title("Fails when folder not found")
    def test_fails_when_folder_not_found(self, project_state, event_bus):
        """Should fail with NOT_FOUND error when folder does not exist."""
        folder_repo = MockFolderRepository()
        source_repo = MockSourceRepository()

        command = RenameFolderCommand(
            folder_id=999,
            new_name="New Name",
        )

        result = rename_folder(
            command=command,
            state=project_state,
            folder_repo=folder_repo,
            source_repo=source_repo,
            event_bus=event_bus,
        )

        assert result.success is False
        assert "NOT_FOUND" in result.error_code
        assert len(event_bus.published_events) == 0

    @allure.title("Fails with empty name")
    def test_fails_with_empty_name(self, project_state, sample_folder, event_bus):
        """Should fail with INVALID_NAME error for empty name."""
        folder_repo = MockFolderRepository([sample_folder])
        source_repo = MockSourceRepository()

        command = RenameFolderCommand(
            folder_id=sample_folder.id.value,
            new_name="",
        )

        result = rename_folder(
            command=command,
            state=project_state,
            folder_repo=folder_repo,
            source_repo=source_repo,
            event_bus=event_bus,
        )

        assert result.success is False
        assert "INVALID_NAME" in result.error_code
        assert len(event_bus.published_events) == 0

    @allure.title("Fails with whitespace-only name")
    def test_fails_with_whitespace_name(self, project_state, sample_folder, event_bus):
        """Should fail with INVALID_NAME error for whitespace-only name."""
        folder_repo = MockFolderRepository([sample_folder])
        source_repo = MockSourceRepository()

        command = RenameFolderCommand(
            folder_id=sample_folder.id.value,
            new_name="   ",
        )

        result = rename_folder(
            command=command,
            state=project_state,
            folder_repo=folder_repo,
            source_repo=source_repo,
            event_bus=event_bus,
        )

        assert result.success is False
        assert "INVALID_NAME" in result.error_code

    @allure.title("Fails when duplicate name at same level")
    def test_fails_with_duplicate_name(self, project_state, sample_folder, event_bus):
        """Should fail with DUPLICATE_NAME error when name exists at same level."""
        other_folder = Folder(
            id=FolderId(value=2),
            name="Existing Folder",
            parent_id=None,
            created_at=datetime.now(UTC),
        )
        folder_repo = MockFolderRepository([sample_folder, other_folder])
        source_repo = MockSourceRepository()

        command = RenameFolderCommand(
            folder_id=sample_folder.id.value,
            new_name="Existing Folder",
        )

        result = rename_folder(
            command=command,
            state=project_state,
            folder_repo=folder_repo,
            source_repo=source_repo,
            event_bus=event_bus,
        )

        assert result.success is False
        assert "DUPLICATE_NAME" in result.error_code

    @allure.title("Updates folder in repository")
    def test_updates_folder_in_repository(
        self, project_state, sample_folder, event_bus
    ):
        """Should update folder name in repository."""
        folder_repo = MockFolderRepository([sample_folder])
        source_repo = MockSourceRepository()

        command = RenameFolderCommand(
            folder_id=sample_folder.id.value,
            new_name="Updated Name",
        )

        result = rename_folder(
            command=command,
            state=project_state,
            folder_repo=folder_repo,
            source_repo=source_repo,
            event_bus=event_bus,
        )

        assert result.success is True
        updated_folder = folder_repo.get_by_id(sample_folder.id)
        assert updated_folder.name == "Updated Name"

    @allure.title("Publishes event with old and new names")
    def test_publishes_event_with_names(self, project_state, sample_folder, event_bus):
        """Should publish event with both old and new folder names."""
        folder_repo = MockFolderRepository([sample_folder])
        source_repo = MockSourceRepository()
        original_name = sample_folder.name

        command = RenameFolderCommand(
            folder_id=sample_folder.id.value,
            new_name="New Folder Name",
        )

        result = rename_folder(
            command=command,
            state=project_state,
            folder_repo=folder_repo,
            source_repo=source_repo,
            event_bus=event_bus,
        )

        assert result.success is True
        event = event_bus.published_events[0]
        assert event.old_name == original_name
        assert event.new_name == "New Folder Name"


# ============================================================
# Edge Cases and Integration Tests
# ============================================================


@allure.story("Edge Cases")
class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    @allure.title("Handles None folder_repo gracefully")
    def test_list_folders_with_none_repo(self, project_state):
        """Should handle None folder_repo gracefully."""
        result = list_folders(
            state=project_state,
            folder_repo=None,
        )

        assert result.success is True
        assert result.data["total_count"] == 0
        assert result.data["folders"] == []

    @allure.title("Handles None source_repo in get_folder")
    def test_get_folder_with_none_source_repo(self, project_state, sample_folder):
        """Should return 0 source_count when source_repo is None."""
        folder_repo = MockFolderRepository([sample_folder])

        result = get_folder(
            folder_id=sample_folder.id.value,
            state=project_state,
            folder_repo=folder_repo,
            source_repo=None,
        )

        assert result.success is True
        assert result.data["source_count"] == 0

    @allure.title("Handles multiple sources in folder")
    def test_get_folder_with_multiple_sources(self, project_state, sample_folder):
        """Should count multiple sources in folder correctly."""
        sources = [
            Source(
                id=SourceId(value=i),
                name=f"source_{i}.txt",
                source_type=SourceType.TEXT,
                status=SourceStatus.IMPORTED,
                folder_id=sample_folder.id,
            )
            for i in range(5)
        ]
        folder_repo = MockFolderRepository([sample_folder])
        source_repo = MockSourceRepository(sources)

        result = get_folder(
            folder_id=sample_folder.id.value,
            state=project_state,
            folder_repo=folder_repo,
            source_repo=source_repo,
        )

        assert result.success is True
        assert result.data["source_count"] == 5

    @allure.title("Allows renaming to same name (case-sensitive)")
    def test_rename_to_same_name(self, project_state, sample_folder, event_bus):
        """Should succeed when renaming folder to same name."""
        folder_repo = MockFolderRepository([sample_folder])
        source_repo = MockSourceRepository()

        command = RenameFolderCommand(
            folder_id=sample_folder.id.value,
            new_name=sample_folder.name,
        )

        result = rename_folder(
            command=command,
            state=project_state,
            folder_repo=folder_repo,
            source_repo=source_repo,
            event_bus=event_bus,
        )

        # This should succeed - renaming to same name is allowed
        assert result.success is True
