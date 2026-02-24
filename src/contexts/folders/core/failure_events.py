"""
Folders Context: Failure Events

Publishable failure events for the folders bounded context.

Event naming convention: {ENTITY}_NOT_{OPERATION}/{REASON}
"""

from __future__ import annotations

from dataclasses import dataclass

from src.shared.common.failure_events import FailureEvent
from src.shared.common.types import FolderId, SourceId


@dataclass(frozen=True)
class FolderNotCreated(FailureEvent):
    """Failure event: Folder creation failed."""

    name: str | None = None
    parent_id: FolderId | None = None

    @classmethod
    def invalid_name(cls, name: str) -> FolderNotCreated:
        """Folder name is invalid."""
        return cls(
            event_id=cls._generate_id(),
            occurred_at=cls._now(),
            event_type="FOLDER_NOT_CREATED/INVALID_NAME",
            name=name,
        )

    @classmethod
    def duplicate_name(cls, name: str, parent_id: FolderId | None) -> FolderNotCreated:
        """A folder with this name already exists at this level."""
        return cls(
            event_id=cls._generate_id(),
            occurred_at=cls._now(),
            event_type="FOLDER_NOT_CREATED/DUPLICATE_NAME",
            name=name,
            parent_id=parent_id,
        )

    @property
    def message(self) -> str:
        """Human-readable error message."""
        match self.reason:
            case "INVALID_NAME":
                return f"Invalid folder name: '{self.name}'"
            case "DUPLICATE_NAME":
                return f"Folder with name '{self.name}' already exists at this level"
            case _:
                return super().message


@dataclass(frozen=True)
class FolderNotRenamed(FailureEvent):
    """Failure event: Folder rename failed."""

    folder_id: FolderId | None = None
    new_name: str | None = None

    @classmethod
    def not_found(cls, folder_id: FolderId) -> FolderNotRenamed:
        """Folder does not exist."""
        return cls(
            event_id=cls._generate_id(),
            occurred_at=cls._now(),
            event_type="FOLDER_NOT_RENAMED/NOT_FOUND",
            folder_id=folder_id,
        )

    @classmethod
    def invalid_name(cls, folder_id: FolderId, new_name: str) -> FolderNotRenamed:
        """New name is invalid."""
        return cls(
            event_id=cls._generate_id(),
            occurred_at=cls._now(),
            event_type="FOLDER_NOT_RENAMED/INVALID_NAME",
            folder_id=folder_id,
            new_name=new_name,
        )

    @classmethod
    def duplicate_name(cls, folder_id: FolderId, new_name: str) -> FolderNotRenamed:
        """A folder with this name already exists at this level."""
        return cls(
            event_id=cls._generate_id(),
            occurred_at=cls._now(),
            event_type="FOLDER_NOT_RENAMED/DUPLICATE_NAME",
            folder_id=folder_id,
            new_name=new_name,
        )

    @property
    def message(self) -> str:
        """Human-readable error message."""
        match self.reason:
            case "NOT_FOUND":
                return f"Folder not found: {self.folder_id.value if self.folder_id else 'unknown'}"
            case "INVALID_NAME":
                return f"Invalid folder name: '{self.new_name}'"
            case "DUPLICATE_NAME":
                return (
                    f"Folder with name '{self.new_name}' already exists at this level"
                )
            case _:
                return super().message


@dataclass(frozen=True)
class FolderNotDeleted(FailureEvent):
    """Failure event: Folder deletion failed."""

    folder_id: FolderId | None = None
    source_count: int = 0

    @classmethod
    def not_found(cls, folder_id: FolderId) -> FolderNotDeleted:
        """Folder does not exist."""
        return cls(
            event_id=cls._generate_id(),
            occurred_at=cls._now(),
            event_type="FOLDER_NOT_DELETED/NOT_FOUND",
            folder_id=folder_id,
        )

    @classmethod
    def not_empty(cls, folder_id: FolderId, source_count: int) -> FolderNotDeleted:
        """Cannot delete folder because it contains sources."""
        return cls(
            event_id=cls._generate_id(),
            occurred_at=cls._now(),
            event_type="FOLDER_NOT_DELETED/NOT_EMPTY",
            folder_id=folder_id,
            source_count=source_count,
        )

    @property
    def message(self) -> str:
        """Human-readable error message."""
        match self.reason:
            case "NOT_FOUND":
                return f"Folder not found: {self.folder_id.value if self.folder_id else 'unknown'}"
            case "NOT_EMPTY":
                return f"Folder contains {self.source_count} source(s) and cannot be deleted"
            case _:
                return super().message


@dataclass(frozen=True)
class SourceNotMoved(FailureEvent):
    """Failure event: Source move failed."""

    source_id: SourceId | None = None
    folder_id: FolderId | None = None

    @classmethod
    def source_not_found(cls, source_id: SourceId) -> SourceNotMoved:
        """Source does not exist."""
        return cls(
            event_id=cls._generate_id(),
            occurred_at=cls._now(),
            event_type="SOURCE_NOT_MOVED/SOURCE_NOT_FOUND",
            source_id=source_id,
        )

    @classmethod
    def folder_not_found(
        cls, source_id: SourceId, folder_id: FolderId
    ) -> SourceNotMoved:
        """Target folder does not exist."""
        return cls(
            event_id=cls._generate_id(),
            occurred_at=cls._now(),
            event_type="SOURCE_NOT_MOVED/FOLDER_NOT_FOUND",
            source_id=source_id,
            folder_id=folder_id,
        )

    @property
    def message(self) -> str:
        """Human-readable error message."""
        match self.reason:
            case "SOURCE_NOT_FOUND":
                return f"Source not found: {self.source_id.value if self.source_id else 'unknown'}"
            case "FOLDER_NOT_FOUND":
                return f"Folder not found: {self.folder_id.value if self.folder_id else 'unknown'}"
            case _:
                return super().message
