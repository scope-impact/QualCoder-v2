"""
Folder Repository - SQLAlchemy Core Implementation for Sources Context.

Implements the repository for Folder entities using the src_folder table.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import delete, func, select, update

from src.contexts.sources.infra.schema import src_folder
from src.domain.projects.entities import Folder
from src.domain.shared.types import FolderId

if TYPE_CHECKING:
    from sqlalchemy import Connection


class SQLiteFolderRepository:
    """
    SQLAlchemy Core implementation of FolderRepository.

    Maps between domain Folder entities and the src_folder table.
    Uses the prefixed table from the Sources bounded context.
    """

    def __init__(self, connection: Connection) -> None:
        self._conn = connection

    def get_all(self) -> list[Folder]:
        """Get all folders in the project."""
        stmt = select(src_folder).order_by(src_folder.c.name)
        result = self._conn.execute(stmt)
        return [self._row_to_folder(row) for row in result]

    def get_by_id(self, folder_id: FolderId) -> Folder | None:
        """Get a folder by its ID."""
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
        if parent_id is None:
            stmt = (
                select(src_folder)
                .where(src_folder.c.parent_id.is_(None))
                .order_by(src_folder.c.name)
            )
        else:
            stmt = (
                select(src_folder)
                .where(src_folder.c.parent_id == parent_id.value)
                .order_by(src_folder.c.name)
            )
        result = self._conn.execute(stmt)
        return [self._row_to_folder(row) for row in result]

    def get_root_folders(self) -> list[Folder]:
        """Get all root-level folders (no parent)."""
        return self.get_children(None)

    def save(self, folder: Folder) -> None:
        """Save a folder (insert or update)."""
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
        self._conn.commit()

    def delete(self, folder_id: FolderId) -> None:
        """Delete a folder by ID."""
        stmt = delete(src_folder).where(src_folder.c.id == folder_id.value)
        self._conn.execute(stmt)
        self._conn.commit()

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
        self._conn.commit()

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
