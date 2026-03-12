"""
Folder Repository - SQLAlchemy Core Implementation for Folders Context.

Implements the repository for Folder entities using the src_folder table.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import delete, func, select, update

from src.contexts.folders.core.entities import Folder
from src.contexts.folders.infra.schema import src_folder
from src.shared.common.types import FolderId

if TYPE_CHECKING:
    from sqlalchemy import Connection

    from src.shared.infra.sync.outbox import OutboxWriter

logger = logging.getLogger("qualcoder.folders.infra")


class SQLiteFolderRepository:
    """
    SQLAlchemy Core implementation of FolderRepository.

    Maps between domain Folder entities and the src_folder table.
    """

    def __init__(
        self, connection: Connection, outbox: OutboxWriter | None = None
    ) -> None:
        self._conn = connection
        self._outbox = outbox

    def get_all(self) -> list[Folder]:
        """Get all folders in the project."""
        stmt = select(src_folder).order_by(src_folder.c.name)
        result = self._conn.execute(stmt)
        folders = [self._row_to_folder(row) for row in result]
        logger.debug("get_all: count=%d", len(folders))
        return folders

    def get_by_id(self, folder_id: FolderId) -> Folder | None:
        """Get a folder by its ID."""
        logger.debug("get_by_id: %s", folder_id.value)
        stmt = select(src_folder).where(src_folder.c.id == folder_id.value)
        result = self._conn.execute(stmt)
        row = result.fetchone()
        return self._row_to_folder(row) if row else None

    def get_by_name(
        self, name: str, parent_id: FolderId | None = None
    ) -> Folder | None:
        """Get a folder by name within a parent (case-insensitive)."""
        stmt = select(src_folder).where(func.lower(src_folder.c.name) == name.lower())
        if parent_id is None:
            stmt = stmt.where(src_folder.c.parent_id.is_(None))
        else:
            stmt = stmt.where(src_folder.c.parent_id == parent_id.value)
        result = self._conn.execute(stmt)
        row = result.fetchone()
        return self._row_to_folder(row) if row else None

    def get_children(self, parent_id: FolderId | None) -> list[Folder]:
        """Get all folders with the given parent (None for root level)."""
        parent_filter = (
            src_folder.c.parent_id.is_(None)
            if parent_id is None
            else src_folder.c.parent_id == parent_id.value
        )
        stmt = select(src_folder).where(parent_filter).order_by(src_folder.c.name)
        result = self._conn.execute(stmt)
        return [self._row_to_folder(row) for row in result]

    def get_root_folders(self) -> list[Folder]:
        """Get all root-level folders (no parent)."""
        return self.get_children(None)

    def save(self, folder: Folder) -> None:
        """Save a folder (insert or update)."""
        logger.debug("save: %s (name=%s)", folder.id.value, folder.name)
        exists = self.exists(folder.id)
        parent_id_value = folder.parent_id.value if folder.parent_id else None

        if exists:
            stmt = (
                update(src_folder)
                .where(src_folder.c.id == folder.id.value)
                .values(
                    name=folder.name,
                    parent_id=parent_id_value,
                )
            )
        else:
            stmt = src_folder.insert().values(
                id=folder.id.value,
                name=folder.name,
                parent_id=parent_id_value,
                created_at=folder.created_at,
            )

        self._conn.execute(stmt)
        if self._outbox:
            self._outbox.write_upsert(
                "folder",
                folder.id.value,
                {
                    "name": folder.name,
                    "parent_id": folder.parent_id.value if folder.parent_id else None,
                },
            )

    def delete(self, folder_id: FolderId) -> None:
        """Delete a folder by ID."""
        logger.debug("delete: %s", folder_id.value)
        stmt = delete(src_folder).where(src_folder.c.id == folder_id.value)
        self._conn.execute(stmt)
        if self._outbox:
            self._outbox.write_delete("folder", folder_id.value)

    def exists(self, folder_id: FolderId) -> bool:
        """Check if a folder exists."""
        stmt = select(func.count()).where(src_folder.c.id == folder_id.value)
        result = self._conn.execute(stmt)
        return result.scalar() > 0

    def name_exists(
        self, name: str, parent_id: FolderId | None, exclude_id: FolderId | None = None
    ) -> bool:
        """Check if a folder name already exists within a parent."""
        stmt = select(func.count()).where(func.lower(src_folder.c.name) == name.lower())
        if parent_id is None:
            stmt = stmt.where(src_folder.c.parent_id.is_(None))
        else:
            stmt = stmt.where(src_folder.c.parent_id == parent_id.value)
        if exclude_id:
            stmt = stmt.where(src_folder.c.id != exclude_id.value)
        result = self._conn.execute(stmt)
        return result.scalar() > 0

    def count(self) -> int:
        """Get total count of folders."""
        stmt = select(func.count()).select_from(src_folder)
        result = self._conn.execute(stmt)
        return result.scalar()

    def update_parent(
        self, folder_id: FolderId, new_parent_id: FolderId | None
    ) -> None:
        """Move a folder to a different parent."""
        stmt = (
            update(src_folder)
            .where(src_folder.c.id == folder_id.value)
            .values(parent_id=new_parent_id.value if new_parent_id else None)
        )
        self._conn.execute(stmt)

    def get_descendants(self, folder_id: FolderId) -> list[Folder]:
        """Get all descendant folders (recursive children)."""
        descendants = []
        children = self.get_children(folder_id)
        for child in children:
            descendants.append(child)
            descendants.extend(self.get_descendants(child.id))
        return descendants

    def _row_to_folder(self, row) -> Folder:
        """Convert a database row to a Folder entity."""
        parent_id = FolderId(value=row.parent_id) if row.parent_id else None
        return Folder(
            id=FolderId(value=row.id),
            name=row.name,
            parent_id=parent_id,
            created_at=row.created_at or datetime.now(UTC),
        )
