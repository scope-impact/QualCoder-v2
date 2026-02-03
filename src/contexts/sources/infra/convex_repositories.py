"""
Sources Context: Convex Repository Implementations

Implements the repository protocols using the Convex cloud database.
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

from src.contexts.projects.core.entities import (
    Folder,
    Source,
    SourceStatus,
    SourceType,
)
from src.shared.common.types import FolderId, SourceId

if TYPE_CHECKING:
    from src.shared.infra.convex import ConvexClientWrapper


class ConvexSourceRepository:
    """
    Convex implementation of SourceRepository.

    Maps between domain Source entities and Convex src_source documents.
    """

    def __init__(self, client: ConvexClientWrapper) -> None:
        self._client = client

    def get_all(self) -> list[Source]:
        """Get all sources in the project."""
        docs = self._client.get_all_sources()
        return [self._doc_to_source(doc) for doc in docs]

    def get_by_id(self, source_id: SourceId) -> Source | None:
        """Get a source by its ID."""
        doc = self._client.get_source_by_id(source_id.value)
        return self._doc_to_source(doc) if doc else None

    def get_by_name(self, name: str) -> Source | None:
        """Get a source by its name."""
        doc = self._client.query("sources:getByName", name=name)
        return self._doc_to_source(doc) if doc else None

    def get_by_type(self, source_type: str) -> list[Source]:
        """Get all sources of a specific type."""
        docs = self._client.query("sources:getByType", sourceType=source_type)
        return [self._doc_to_source(doc) for doc in docs]

    def get_by_status(self, status: str) -> list[Source]:
        """Get all sources with a specific status."""
        docs = self._client.query("sources:getByStatus", status=status)
        return [self._doc_to_source(doc) for doc in docs]

    def get_by_folder(self, folder_id: FolderId | None) -> list[Source]:
        """Get all sources in a folder (None for root)."""
        docs = self._client.query(
            "sources:getByFolder",
            folderId=folder_id.value if folder_id else None,
        )
        return [self._doc_to_source(doc) for doc in docs]

    def save(self, source: Source) -> None:
        """Save a source (insert or update)."""
        folder_id_value = source.folder_id.value if source.folder_id else None

        if self.exists(source.id):
            self._client.update_source(
                source.id.value,
                name=source.name,
                fulltext=source.fulltext,
                source_type=source.source_type.value,
                status=source.status.value,
                memo=source.memo,
                mediapath=str(source.file_path) if source.file_path else None,
                file_size=source.file_size,
                origin=source.origin,
                folder_id=folder_id_value,
            )
        else:
            self._client.mutation(
                "sources:create",
                name=source.name,
                fulltext=source.fulltext,
                source_type=source.source_type.value,
                status=source.status.value,
                memo=source.memo,
                mediapath=str(source.file_path) if source.file_path else None,
                file_size=source.file_size,
                origin=source.origin,
                folder_id=folder_id_value,
                date=source.created_at.isoformat(),
            )

    def delete(self, source_id: SourceId) -> None:
        """Delete a source by ID."""
        self._client.delete_source(source_id.value)

    def exists(self, source_id: SourceId) -> bool:
        """Check if a source exists."""
        return self._client.query("sources:exists", id=source_id.value)

    def _doc_to_source(self, doc: dict[str, Any]) -> Source:
        """Map Convex document to domain Source entity."""
        folder_id = FolderId(value=doc["folder_id"]) if doc.get("folder_id") else None
        return Source(
            id=SourceId(value=doc["_id"]),
            name=doc["name"],
            source_type=SourceType(doc["source_type"])
            if doc.get("source_type")
            else SourceType.TEXT,
            status=SourceStatus(doc["status"])
            if doc.get("status")
            else SourceStatus.IMPORTED,
            file_path=Path(doc["mediapath"]) if doc.get("mediapath") else None,
            file_size=doc.get("file_size") or 0,
            memo=doc.get("memo"),
            origin=doc.get("origin"),
            folder_id=folder_id,
            fulltext=doc.get("fulltext"),
            created_at=datetime.fromisoformat(doc["date"])
            if doc.get("date")
            else datetime.now(UTC),
        )


class ConvexFolderRepository:
    """
    Convex implementation of FolderRepository.

    Maps between domain Folder entities and Convex src_folder documents.
    """

    def __init__(self, client: ConvexClientWrapper) -> None:
        self._client = client

    def get_all(self) -> list[Folder]:
        """Get all folders."""
        docs = self._client.get_all_folders()
        return [self._doc_to_folder(doc) for doc in docs]

    def get_by_id(self, folder_id: FolderId) -> Folder | None:
        """Get a folder by ID."""
        doc = self._client.get_folder_by_id(folder_id.value)
        return self._doc_to_folder(doc) if doc else None

    def get_children(self, parent_id: FolderId | None) -> list[Folder]:
        """Get child folders of a parent (None for root)."""
        docs = self._client.query(
            "folders:getChildren",
            parentId=parent_id.value if parent_id else None,
        )
        return [self._doc_to_folder(doc) for doc in docs]

    def get_root_folders(self) -> list[Folder]:
        """Get all root-level folders."""
        docs = self._client.query("folders:getRootFolders")
        return [self._doc_to_folder(doc) for doc in docs]

    def get_descendants(self, folder_id: FolderId) -> list[Folder]:
        """Get all descendants of a folder."""
        docs = self._client.query("folders:getDescendants", folderId=folder_id.value)
        return [self._doc_to_folder(doc) for doc in docs]

    def save(self, folder: Folder) -> None:
        """Save a folder (insert or update)."""
        exists = self.get_by_id(folder.id) is not None

        if exists:
            self._client.update_folder(
                folder.id.value,
                name=folder.name,
                parent_id=folder.parent_id.value if folder.parent_id else None,
            )
        else:
            self._client.mutation(
                "folders:create",
                name=folder.name,
                parent_id=folder.parent_id.value if folder.parent_id else None,
                created_at=folder.created_at.isoformat(),
            )

    def delete(self, folder_id: FolderId) -> None:
        """Delete a folder by ID."""
        self._client.delete_folder(folder_id.value)

    def update_parent(
        self, folder_id: FolderId, new_parent_id: FolderId | None
    ) -> None:
        """Move a folder to a new parent."""
        self._client.mutation(
            "folders:updateParent",
            folderId=folder_id.value,
            newParentId=new_parent_id.value if new_parent_id else None,
        )

    def _doc_to_folder(self, doc: dict[str, Any]) -> Folder:
        """Map Convex document to domain Folder entity."""
        parent_id = (
            FolderId(value=doc["parent_id"]) if doc.get("parent_id") else None
        )
        return Folder(
            id=FolderId(value=doc["_id"]),
            name=doc["name"],
            parent_id=parent_id,
            created_at=datetime.fromisoformat(doc["created_at"])
            if doc.get("created_at")
            else datetime.now(UTC),
        )
