"""
Folders Context: Domain Events

Immutable event records representing state changes in the folders domain.

Event type convention: folders.{entity}_{action}
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar

from src.shared.common.types import DomainEvent, FolderId, SourceId

# ============================================================
# Folder Events
# ============================================================


@dataclass(frozen=True)
class FolderCreated(DomainEvent):
    """Event: A folder was created."""

    event_type: ClassVar[str] = "folders.folder_created"

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

    event_type: ClassVar[str] = "folders.folder_renamed"

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

    event_type: ClassVar[str] = "folders.folder_deleted"

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

    event_type: ClassVar[str] = "folders.source_moved_to_folder"

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
