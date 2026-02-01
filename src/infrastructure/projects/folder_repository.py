"""
Folder Repository - SQLAlchemy Core Implementation.

Implements the repository for Folder entities using SQLAlchemy Core.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import delete, func, select, update

from src.domain.projects.entities import Folder
from src.domain.shared.types import FolderId
from src.infrastructure.projects.schema import folder

if TYPE_CHECKING:
    from sqlalchemy import Connection


class SQLiteFolderRepository:
    """
    SQLAlchemy Core implementation for source folder management.

    Maps between domain Folder entities and the folder table.
    """

    def __init__(self, connection: Connection) -> None:
        self._conn = connection

    def get_all(self) -> list[Folder]:
        """Get all folders in the project."""
        stmt = select(folder).order_by(folder.c.name)
        result = self._conn.execute(stmt)
        return [self._row_to_folder(row) for row in result]

    def get_by_id(self, folder_id: FolderId) -> Folder | None:
        """Get a folder by its ID."""
        stmt = select(folder).where(folder.c.id == folder_id.value)
        result = self._conn.execute(stmt)
        row = result.fetchone()
        return self._row_to_folder(row) if row else None

    def get_by_parent(self, parent_id: FolderId | None) -> list[Folder]:
        """Get all folders with a specific parent (None for root level)."""
        if parent_id is None:
            stmt = (
                select(folder)
                .where(folder.c.parent_id.is_(None))
                .order_by(folder.c.name)
            )
        else:
            stmt = (
                select(folder)
                .where(folder.c.parent_id == parent_id.value)
                .order_by(folder.c.name)
            )
        result = self._conn.execute(stmt)
        return [self._row_to_folder(row) for row in result]

    def save(self, f: Folder) -> None:
        """Save a folder (insert or update)."""
        exists = self.exists(f.id)
        parent_id_value = f.parent_id.value if f.parent_id else None

        if exists:
            stmt = (
                update(folder)
                .where(folder.c.id == f.id.value)
                .values(
                    name=f.name,
                    parent_id=parent_id_value,
                )
            )
        else:
            stmt = folder.insert().values(
                id=f.id.value,
                name=f.name,
                parent_id=parent_id_value,
                created_at=f.created_at,
            )

        self._conn.execute(stmt)
        self._conn.commit()

    def delete(self, folder_id: FolderId) -> None:
        """Delete a folder by ID."""
        stmt = delete(folder).where(folder.c.id == folder_id.value)
        self._conn.execute(stmt)
        self._conn.commit()

    def exists(self, folder_id: FolderId) -> bool:
        """Check if a folder exists."""
        stmt = select(func.count()).where(folder.c.id == folder_id.value)
        result = self._conn.execute(stmt)
        return result.scalar() > 0

    def name_exists(
        self, name: str, parent_id: FolderId | None, exclude_id: FolderId | None = None
    ) -> bool:
        """Check if a folder name already exists at the same level."""
        if parent_id is None:
            stmt = select(func.count()).where(
                func.lower(folder.c.name) == name.lower(),
                folder.c.parent_id.is_(None),
            )
        else:
            stmt = select(func.count()).where(
                func.lower(folder.c.name) == name.lower(),
                folder.c.parent_id == parent_id.value,
            )
        if exclude_id:
            stmt = stmt.where(folder.c.id != exclude_id.value)
        result = self._conn.execute(stmt)
        return result.scalar() > 0

    def _row_to_folder(self, row) -> Folder:
        """Convert a database row to a Folder entity."""
        parent_id = FolderId(value=row.parent_id) if row.parent_id else None
        return Folder(
            id=FolderId(value=row.id),
            name=row.name,
            parent_id=parent_id,
            created_at=row.created_at if row.created_at else datetime.now(UTC),
        )
