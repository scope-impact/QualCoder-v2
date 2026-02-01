"""
Source Repository - SQLAlchemy Core Implementation.

Implements the repository for Source entities using SQLAlchemy Core.
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING

from sqlalchemy import delete, func, select, update

from src.domain.projects.entities import Source, SourceStatus, SourceType
from src.domain.shared.types import FolderId, SourceId
from src.infrastructure.projects.schema import source

if TYPE_CHECKING:
    from sqlalchemy import Connection


class SQLiteSourceRepository:
    """
    SQLAlchemy Core implementation of SourceRepository.

    Maps between domain Source entities and the source table.
    """

    def __init__(self, connection: Connection) -> None:
        self._conn = connection

    def get_all(self) -> list[Source]:
        """Get all sources in the project."""
        stmt = select(source).order_by(source.c.name)
        result = self._conn.execute(stmt)
        return [self._row_to_source(row) for row in result]

    def get_by_id(self, source_id: SourceId) -> Source | None:
        """Get a source by its ID."""
        stmt = select(source).where(source.c.id == source_id.value)
        result = self._conn.execute(stmt)
        row = result.fetchone()
        return self._row_to_source(row) if row else None

    def get_by_name(self, name: str) -> Source | None:
        """Get a source by its name (case-insensitive)."""
        stmt = select(source).where(func.lower(source.c.name) == name.lower())
        result = self._conn.execute(stmt)
        row = result.fetchone()
        return self._row_to_source(row) if row else None

    def get_by_type(self, source_type: SourceType) -> list[Source]:
        """Get all sources of a specific type."""
        stmt = (
            select(source)
            .where(source.c.source_type == source_type.value)
            .order_by(source.c.name)
        )
        result = self._conn.execute(stmt)
        return [self._row_to_source(row) for row in result]

    def get_by_status(self, status: SourceStatus) -> list[Source]:
        """Get all sources with a specific status."""
        stmt = (
            select(source)
            .where(source.c.status == status.value)
            .order_by(source.c.name)
        )
        result = self._conn.execute(stmt)
        return [self._row_to_source(row) for row in result]

    def save(self, src: Source) -> None:
        """Save a source (insert or update)."""
        exists = self.exists(src.id)
        folder_id_value = src.folder_id.value if src.folder_id else None

        if exists:
            stmt = (
                update(source)
                .where(source.c.id == src.id.value)
                .values(
                    name=src.name,
                    source_type=src.source_type.value,
                    status=src.status.value,
                    memo=src.memo,
                    mediapath=str(src.file_path) if src.file_path else None,
                    file_size=src.file_size,
                    origin=src.origin,
                    folder_id=folder_id_value,
                    owner=None,  # Would come from context
                )
            )
        else:
            stmt = source.insert().values(
                id=src.id.value,
                name=src.name,
                source_type=src.source_type.value,
                status=src.status.value,
                memo=src.memo,
                mediapath=str(src.file_path) if src.file_path else None,
                file_size=src.file_size,
                origin=src.origin,
                folder_id=folder_id_value,
                owner=None,
                date=src.created_at.isoformat(),
            )

        self._conn.execute(stmt)
        self._conn.commit()

    def delete(self, source_id: SourceId) -> None:
        """Delete a source by ID."""
        stmt = delete(source).where(source.c.id == source_id.value)
        self._conn.execute(stmt)
        self._conn.commit()

    def exists(self, source_id: SourceId) -> bool:
        """Check if a source exists."""
        stmt = select(func.count()).where(source.c.id == source_id.value)
        result = self._conn.execute(stmt)
        return result.scalar() > 0

    def name_exists(self, name: str, exclude_id: SourceId | None = None) -> bool:
        """Check if a source name is already taken."""
        stmt = select(func.count()).where(func.lower(source.c.name) == name.lower())
        if exclude_id:
            stmt = stmt.where(source.c.id != exclude_id.value)
        result = self._conn.execute(stmt)
        return result.scalar() > 0

    def count(self) -> int:
        """Get total count of sources."""
        stmt = select(func.count()).select_from(source)
        result = self._conn.execute(stmt)
        return result.scalar()

    def count_by_type(self, source_type: SourceType) -> int:
        """Get count of sources by type."""
        stmt = select(func.count()).where(source.c.source_type == source_type.value)
        result = self._conn.execute(stmt)
        return result.scalar()

    def update_status(self, source_id: SourceId, new_status: SourceStatus) -> None:
        """Update the status of a source."""
        stmt = (
            update(source)
            .where(source.c.id == source_id.value)
            .values(status=new_status.value)
        )
        self._conn.execute(stmt)
        self._conn.commit()

    def get_by_folder(self, folder_id: FolderId | None) -> list[Source]:
        """Get all sources in a folder (None for root level)."""
        if folder_id is None:
            stmt = (
                select(source)
                .where(source.c.folder_id.is_(None))
                .order_by(source.c.name)
            )
        else:
            stmt = (
                select(source)
                .where(source.c.folder_id == folder_id.value)
                .order_by(source.c.name)
            )
        result = self._conn.execute(stmt)
        return [self._row_to_source(row) for row in result]

    def update_folder(self, source_id: SourceId, folder_id: FolderId | None) -> None:
        """Move a source to a different folder."""
        stmt = (
            update(source)
            .where(source.c.id == source_id.value)
            .values(folder_id=folder_id.value if folder_id else None)
        )
        self._conn.execute(stmt)
        self._conn.commit()

    def _row_to_source(self, row) -> Source:
        """Convert a database row to a Source entity."""
        folder_id = FolderId(value=row.folder_id) if row.folder_id else None
        return Source(
            id=SourceId(value=row.id),
            name=row.name,
            source_type=SourceType(row.source_type)
            if row.source_type
            else SourceType.TEXT,
            status=SourceStatus(row.status) if row.status else SourceStatus.IMPORTED,
            file_path=Path(row.mediapath) if row.mediapath else None,
            file_size=row.file_size or 0,
            memo=row.memo,
            origin=row.origin,
            folder_id=folder_id,
            created_at=datetime.fromisoformat(row.date)
            if row.date
            else datetime.now(UTC),
        )
