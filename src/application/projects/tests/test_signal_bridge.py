"""
Tests for ProjectSignalBridge - TDD for Folder Signals

Tests written BEFORE implementation following the developer skill pattern.
"""

from __future__ import annotations

from datetime import datetime

import pytest

from src.application.projects.signal_bridge import (
    FolderPayload,
    ProjectSignalBridge,
    SourceMovedPayload,
)
from src.contexts.projects.core.events import (
    FolderCreated,
    FolderDeleted,
    FolderRenamed,
    SourceMovedToFolder,
)
from src.contexts.shared.core.types import FolderId, SourceId

# =============================================================================
# Mock Signal Class (for testing without PySide6)
# =============================================================================


class MockSignal:
    """Mock PyQt signal for testing without Qt."""

    def __init__(self) -> None:
        self.emissions: list = []

    def emit(self, payload: object) -> None:
        self.emissions.append(payload)

    def __call__(self, *args: object) -> MockSignal:
        return self


# =============================================================================
# Test Fixtures
# =============================================================================


@pytest.fixture
def mock_event_bus():
    """Provide a mock event bus for testing."""
    from src.application.signal_bridge.tests.conftest import MockEventBus

    return MockEventBus()


@pytest.fixture
def signal_bridge(mock_event_bus):
    """Create a ProjectSignalBridge with mock signals."""
    bridge = ProjectSignalBridge(mock_event_bus)

    # Replace real Qt signals with mock signals for testing
    bridge.folder_created = MockSignal()
    bridge.folder_renamed = MockSignal()
    bridge.folder_deleted = MockSignal()
    bridge.source_moved = MockSignal()

    # Rebuild signal registry with mock signals
    bridge._signals["folder_created"] = bridge.folder_created
    bridge._signals["folder_renamed"] = bridge.folder_renamed
    bridge._signals["folder_deleted"] = bridge.folder_deleted
    bridge._signals["source_moved"] = bridge.source_moved

    bridge.start()
    yield bridge
    bridge.stop()


# =============================================================================
# FolderCreated Event Tests
# =============================================================================


class TestFolderCreatedSignal:
    """Tests for FolderCreated event → folder_created signal."""

    def test_folder_created_signal_emitted(self, signal_bridge, mock_event_bus):
        """FolderCreated event should emit folder_created signal with correct payload."""
        # Arrange
        event = FolderCreated.create(
            folder_id=FolderId(value=1),
            name="Interview Transcripts",
            parent_id=None,
        )

        # Act
        mock_event_bus.publish(event)

        # Assert
        assert len(signal_bridge.folder_created.emissions) == 1
        payload = signal_bridge.folder_created.emissions[0]

        assert isinstance(payload, FolderPayload)
        assert payload.folder_id == 1
        assert payload.name == "Interview Transcripts"
        assert payload.parent_id is None
        assert payload.event_type == "projects.folder_created"
        assert isinstance(payload.timestamp, datetime)

    def test_folder_created_with_parent(self, signal_bridge, mock_event_bus):
        """FolderCreated with parent should include parent_id in payload."""
        # Arrange
        event = FolderCreated.create(
            folder_id=FolderId(value=2),
            name="Subfolder",
            parent_id=FolderId(value=1),
        )

        # Act
        mock_event_bus.publish(event)

        # Assert
        payload = signal_bridge.folder_created.emissions[0]
        assert payload.folder_id == 2
        assert payload.parent_id == 1
        assert payload.name == "Subfolder"


# =============================================================================
# FolderRenamed Event Tests
# =============================================================================


class TestFolderRenamedSignal:
    """Tests for FolderRenamed event → folder_renamed signal."""

    def test_folder_renamed_signal_emitted(self, signal_bridge, mock_event_bus):
        """FolderRenamed event should emit folder_renamed signal with new name."""
        # Arrange
        event = FolderRenamed.create(
            folder_id=FolderId(value=1),
            old_name="Old Name",
            new_name="New Name",
        )

        # Act
        mock_event_bus.publish(event)

        # Assert
        assert len(signal_bridge.folder_renamed.emissions) == 1
        payload = signal_bridge.folder_renamed.emissions[0]

        assert isinstance(payload, FolderPayload)
        assert payload.folder_id == 1
        assert payload.name == "New Name"
        assert payload.event_type == "projects.folder_renamed"

    def test_folder_renamed_preserves_parent(self, signal_bridge, mock_event_bus):
        """FolderRenamed should preserve parent_id (if available in event)."""
        # Note: Current FolderRenamed doesn't have parent_id, so it will be None
        event = FolderRenamed.create(
            folder_id=FolderId(value=2),
            old_name="Old",
            new_name="New",
        )

        mock_event_bus.publish(event)

        payload = signal_bridge.folder_renamed.emissions[0]
        assert payload.parent_id is None  # Expected since event doesn't have it


# =============================================================================
# FolderDeleted Event Tests
# =============================================================================


class TestFolderDeletedSignal:
    """Tests for FolderDeleted event → folder_deleted signal."""

    def test_folder_deleted_signal_emitted(self, signal_bridge, mock_event_bus):
        """FolderDeleted event should emit folder_deleted signal."""
        # Arrange
        event = FolderDeleted.create(
            folder_id=FolderId(value=3),
            name="Archived",
        )

        # Act
        mock_event_bus.publish(event)

        # Assert
        assert len(signal_bridge.folder_deleted.emissions) == 1
        payload = signal_bridge.folder_deleted.emissions[0]

        assert isinstance(payload, FolderPayload)
        assert payload.folder_id == 3
        assert payload.name == "Archived"
        assert payload.event_type == "projects.folder_deleted"


# =============================================================================
# SourceMovedToFolder Event Tests
# =============================================================================


class TestSourceMovedToFolderSignal:
    """Tests for SourceMovedToFolder event → source_moved signal."""

    def test_source_moved_signal_emitted(self, signal_bridge, mock_event_bus):
        """SourceMovedToFolder event should emit source_moved signal."""
        # Arrange
        event = SourceMovedToFolder.create(
            source_id=SourceId(value=100),
            old_folder_id=FolderId(value=1),
            new_folder_id=FolderId(value=2),
        )

        # Act
        mock_event_bus.publish(event)

        # Assert
        assert len(signal_bridge.source_moved.emissions) == 1
        payload = signal_bridge.source_moved.emissions[0]

        assert isinstance(payload, SourceMovedPayload)
        assert payload.source_id == 100
        assert payload.old_folder_id == 1
        assert payload.new_folder_id == 2
        assert payload.event_type == "projects.source_moved_to_folder"

    def test_source_moved_from_root(self, signal_bridge, mock_event_bus):
        """Source moved from root (no folder) should have old_folder_id=None."""
        # Arrange
        event = SourceMovedToFolder.create(
            source_id=SourceId(value=101),
            old_folder_id=None,
            new_folder_id=FolderId(value=5),
        )

        # Act
        mock_event_bus.publish(event)

        # Assert
        payload = signal_bridge.source_moved.emissions[0]
        assert payload.source_id == 101
        assert payload.old_folder_id is None
        assert payload.new_folder_id == 5

    def test_source_moved_to_root(self, signal_bridge, mock_event_bus):
        """Source moved to root (no folder) should have new_folder_id=None."""
        # Arrange
        event = SourceMovedToFolder.create(
            source_id=SourceId(value=102),
            old_folder_id=FolderId(value=3),
            new_folder_id=None,
        )

        # Act
        mock_event_bus.publish(event)

        # Assert
        payload = signal_bridge.source_moved.emissions[0]
        assert payload.source_id == 102
        assert payload.old_folder_id == 3
        assert payload.new_folder_id is None
