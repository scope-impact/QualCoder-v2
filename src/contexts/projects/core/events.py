"""
Project Context: Domain Events

Immutable event records representing state changes in the project domain.
Events are produced by Derivers and consumed by the Application layer.
All events inherit from DomainEvent base class.

Event type convention: projects.{entity}_{action}
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import ClassVar

from src.contexts.projects.core.entities import SourceType
from src.shared.common.types import DomainEvent, FolderId, SourceId

# ============================================================
# Project Events
# ============================================================


@dataclass(frozen=True)
class ProjectCreated(DomainEvent):
    """Event: A new project was created."""

    event_type: ClassVar[str] = "projects.project_created"

    name: str
    path: Path
    memo: str | None
    owner: str | None

    @classmethod
    def create(
        cls,
        name: str,
        path: Path,
        memo: str | None = None,
        owner: str | None = None,
    ) -> ProjectCreated:
        """Factory method to create event with generated ID and timestamp."""
        return cls(
            event_id=cls._generate_id(),
            occurred_at=cls._now(),
            name=name,
            path=path,
            memo=memo,
            owner=owner,
        )


@dataclass(frozen=True)
class ProjectOpened(DomainEvent):
    """Event: An existing project was opened."""

    event_type: ClassVar[str] = "projects.project_opened"

    path: Path
    name: str | None = None  # May be resolved later from DB

    @classmethod
    def create(
        cls,
        path: Path,
        name: str | None = None,
    ) -> ProjectOpened:
        """Factory method to create event with generated ID and timestamp."""
        return cls(
            event_id=cls._generate_id(),
            occurred_at=cls._now(),
            path=path,
            name=name,
        )


@dataclass(frozen=True)
class ProjectClosed(DomainEvent):
    """Event: The current project was closed."""

    event_type: ClassVar[str] = "projects.project_closed"

    path: Path

    @classmethod
    def create(cls, path: Path) -> ProjectClosed:
        return cls(
            event_id=cls._generate_id(),
            occurred_at=cls._now(),
            path=path,
        )


@dataclass(frozen=True)
class ProjectRenamed(DomainEvent):
    """Event: Project was renamed."""

    event_type: ClassVar[str] = "projects.project_renamed"

    path: Path
    old_name: str
    new_name: str

    @classmethod
    def create(cls, path: Path, old_name: str, new_name: str) -> ProjectRenamed:
        return cls(
            event_id=cls._generate_id(),
            occurred_at=cls._now(),
            path=path,
            old_name=old_name,
            new_name=new_name,
        )


# ============================================================
# Source Events
# ============================================================


@dataclass(frozen=True)
class SourceAdded(DomainEvent):
    """Event: A source file was added to the project."""

    event_type: ClassVar[str] = "projects.source_added"

    source_id: SourceId
    name: str
    source_type: SourceType
    file_path: Path
    file_size: int
    origin: str | None
    memo: str | None
    owner: str | None

    @classmethod
    def create(
        cls,
        source_id: SourceId,
        name: str,
        source_type: SourceType,
        file_path: Path,
        file_size: int = 0,
        origin: str | None = None,
        memo: str | None = None,
        owner: str | None = None,
    ) -> SourceAdded:
        return cls(
            event_id=cls._generate_id(),
            occurred_at=cls._now(),
            source_id=source_id,
            name=name,
            source_type=source_type,
            file_path=file_path,
            file_size=file_size,
            origin=origin,
            memo=memo,
            owner=owner,
        )


@dataclass(frozen=True)
class SourceRemoved(DomainEvent):
    """Event: A source file was removed from the project."""

    event_type: ClassVar[str] = "projects.source_removed"

    source_id: SourceId
    name: str
    segments_removed: int

    @classmethod
    def create(
        cls,
        source_id: SourceId,
        name: str,
        segments_removed: int = 0,
    ) -> SourceRemoved:
        return cls(
            event_id=cls._generate_id(),
            occurred_at=cls._now(),
            source_id=source_id,
            name=name,
            segments_removed=segments_removed,
        )


@dataclass(frozen=True)
class SourceRenamed(DomainEvent):
    """Event: A source was renamed."""

    event_type: ClassVar[str] = "projects.source_renamed"

    source_id: SourceId
    old_name: str
    new_name: str

    @classmethod
    def create(
        cls,
        source_id: SourceId,
        old_name: str,
        new_name: str,
    ) -> SourceRenamed:
        return cls(
            event_id=cls._generate_id(),
            occurred_at=cls._now(),
            source_id=source_id,
            old_name=old_name,
            new_name=new_name,
        )


@dataclass(frozen=True)
class SourceOpened(DomainEvent):
    """Event: A source was opened for viewing/coding."""

    event_type: ClassVar[str] = "projects.source_opened"

    source_id: SourceId
    name: str
    source_type: SourceType

    @classmethod
    def create(
        cls,
        source_id: SourceId,
        name: str,
        source_type: SourceType,
    ) -> SourceOpened:
        return cls(
            event_id=cls._generate_id(),
            occurred_at=cls._now(),
            source_id=source_id,
            name=name,
            source_type=source_type,
        )


@dataclass(frozen=True)
class SourceStatusChanged(DomainEvent):
    """Event: Source processing status changed."""

    event_type: ClassVar[str] = "projects.source_status_changed"

    source_id: SourceId
    old_status: str
    new_status: str

    @classmethod
    def create(
        cls,
        source_id: SourceId,
        old_status: str,
        new_status: str,
    ) -> SourceStatusChanged:
        return cls(
            event_id=cls._generate_id(),
            occurred_at=cls._now(),
            source_id=source_id,
            old_status=old_status,
            new_status=new_status,
        )


@dataclass(frozen=True)
class SourceUpdated(DomainEvent):
    """Event: Source metadata was updated."""

    event_type: ClassVar[str] = "projects.source_updated"

    source_id: SourceId
    memo: str | None
    origin: str | None
    status: str | None

    @classmethod
    def create(
        cls,
        source_id: SourceId,
        memo: str | None = None,
        origin: str | None = None,
        status: str | None = None,
    ) -> SourceUpdated:
        return cls(
            event_id=cls._generate_id(),
            occurred_at=cls._now(),
            source_id=source_id,
            memo=memo,
            origin=origin,
            status=status,
        )


# ============================================================
# Folder Events
# ============================================================


@dataclass(frozen=True)
class FolderCreated(DomainEvent):
    """Event: A folder was created."""

    event_type: ClassVar[str] = "projects.folder_created"

    folder_id: FolderId
    name: str
    parent_id: FolderId | None

    @classmethod
    def create(
        cls,
        folder_id: FolderId,
        name: str,
        parent_id: FolderId | None = None,
    ) -> FolderCreated:
        return cls(
            event_id=cls._generate_id(),
            occurred_at=cls._now(),
            folder_id=folder_id,
            name=name,
            parent_id=parent_id,
        )


@dataclass(frozen=True)
class FolderRenamed(DomainEvent):
    """Event: A folder was renamed."""

    event_type: ClassVar[str] = "projects.folder_renamed"

    folder_id: FolderId
    old_name: str
    new_name: str

    @classmethod
    def create(
        cls,
        folder_id: FolderId,
        old_name: str,
        new_name: str,
    ) -> FolderRenamed:
        return cls(
            event_id=cls._generate_id(),
            occurred_at=cls._now(),
            folder_id=folder_id,
            old_name=old_name,
            new_name=new_name,
        )


@dataclass(frozen=True)
class FolderDeleted(DomainEvent):
    """Event: A folder was deleted."""

    event_type: ClassVar[str] = "projects.folder_deleted"

    folder_id: FolderId
    name: str

    @classmethod
    def create(
        cls,
        folder_id: FolderId,
        name: str,
    ) -> FolderDeleted:
        return cls(
            event_id=cls._generate_id(),
            occurred_at=cls._now(),
            folder_id=folder_id,
            name=name,
        )


@dataclass(frozen=True)
class SourceMovedToFolder(DomainEvent):
    """Event: A source was moved to a different folder."""

    event_type: ClassVar[str] = "projects.source_moved_to_folder"

    source_id: SourceId
    old_folder_id: FolderId | None
    new_folder_id: FolderId | None

    @classmethod
    def create(
        cls,
        source_id: SourceId,
        old_folder_id: FolderId | None,
        new_folder_id: FolderId | None,
    ) -> SourceMovedToFolder:
        return cls(
            event_id=cls._generate_id(),
            occurred_at=cls._now(),
            source_id=source_id,
            old_folder_id=old_folder_id,
            new_folder_id=new_folder_id,
        )


# ============================================================
# Navigation Events
# ============================================================


@dataclass(frozen=True)
class ScreenChanged(DomainEvent):
    """Event: User navigated to a different screen."""

    event_type: ClassVar[str] = "projects.screen_changed"

    from_screen: str | None
    to_screen: str

    @classmethod
    def create(
        cls,
        from_screen: str | None,
        to_screen: str,
    ) -> ScreenChanged:
        return cls(
            event_id=cls._generate_id(),
            occurred_at=cls._now(),
            from_screen=from_screen,
            to_screen=to_screen,
        )


@dataclass(frozen=True)
class NavigatedToSegment(DomainEvent):
    """Event: User/Agent navigated to a specific segment in a source."""

    event_type: ClassVar[str] = "projects.navigated_to_segment"

    source_id: SourceId
    position_start: int
    position_end: int
    highlight: bool

    @classmethod
    def create(
        cls,
        source_id: SourceId,
        position_start: int,
        position_end: int,
        highlight: bool = True,
    ) -> NavigatedToSegment:
        return cls(
            event_id=cls._generate_id(),
            occurred_at=cls._now(),
            source_id=source_id,
            position_start=position_start,
            position_end=position_end,
            highlight=highlight,
        )


# ============================================================
# Type Unions
# ============================================================

ProjectEvent = ProjectCreated | ProjectOpened | ProjectClosed | ProjectRenamed

SourceEvent = (
    SourceAdded
    | SourceRemoved
    | SourceRenamed
    | SourceOpened
    | SourceStatusChanged
    | SourceUpdated
)

FolderEvent = FolderCreated | FolderRenamed | FolderDeleted | SourceMovedToFolder

NavigationEvent = ScreenChanged | NavigatedToSegment


# ============================================================
# Exports
# ============================================================

__all__ = [
    # Project Events
    "ProjectCreated",
    "ProjectOpened",
    "ProjectClosed",
    "ProjectRenamed",
    # Source Events
    "SourceAdded",
    "SourceRemoved",
    "SourceRenamed",
    "SourceOpened",
    "SourceStatusChanged",
    "SourceUpdated",
    # Folder Events
    "FolderCreated",
    "FolderRenamed",
    "FolderDeleted",
    "SourceMovedToFolder",
    # Navigation Events
    "ScreenChanged",
    "NavigatedToSegment",
    # Type Unions
    "ProjectEvent",
    "SourceEvent",
    "FolderEvent",
    "NavigationEvent",
]
