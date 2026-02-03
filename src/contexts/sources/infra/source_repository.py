"""
Source Repository - SQLAlchemy Core Implementation for Sources Context.

Implements the repository for Source entities using the src_source table.
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING

from sqlalchemy import delete, func, select, update

from src.contexts.projects.core.entities import Source, SourceStatus, SourceType
from src.contexts.sources.infra.schema import src_source
from src.shared.common.types import FolderId, SourceId

if TYPE_CHECKING:
    from sqlalchemy import Connection


class SQLiteSourceRepository:
    """
    SQLAlchemy Core implementation of SourceRepository.

    Maps between domain Source entities and the src_source table.
    Uses the prefixed table from the Sources bounded context.
    """

    def __init__(self, connection: Connection) -> None:
        self._conn = connection

    def get_all(self) -> list[Source]:
        """Get all sources in the project."""
        stmt = select(src_source).order_by(src_source.c.name)
        result = self._conn.execute(stmt)
        return [self._row_to_source(row) for row in result]

    def get_by_id(self, source_id: SourceId) -> Source | None:
        """Get a source by its ID."""
        stmt = select(src_source).where(src_source.c.id == source_id.value)
        result = self._conn.execute(stmt)
        row = result.fetchone()
        return self._row_to_source(row) if row else None

    def get_by_name(self, name: str) -> Source | None:
        """Get a source by its name (case-insensitive)."""
        stmt = select(src_source).where(func.lower(src_source.c.name) == name.lower())
        result = self._conn.execute(stmt)
        row = result.fetchone()
        return self._row_to_source(row) if row else None

    def get_by_type(self, source_type: SourceType) -> list[Source]:
        """Get all sources of a specific type."""
        stmt = (
            select(src_source)
            .where(src_source.c.source_type == source_type.value)
            .order_by(src_source.c.name)
        )
        result = self._conn.execute(stmt)
        return [self._row_to_source(row) for row in result]

    def get_by_status(self, status: SourceStatus) -> list[Source]:
        """Get all sources with a specific status."""
        stmt = (
            select(src_source)
            .where(src_source.c.status == status.value)
            .order_by(src_source.c.name)
        )
        result = self._conn.execute(stmt)
        return [self._row_to_source(row) for row in result]

    def save(self, src: Source) -> None:
        """Save a source (insert or update)."""
        exists = self.exists(src.id)
        folder_id_value = src.folder_id.value if src.folder_id else None

        if exists:
            stmt = (
                update(src_source)
                .where(src_source.c.id == src.id.value)
                .values(
                    name=src.name,
                    fulltext=src.fulltext,
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
            stmt = src_source.insert().values(
                id=src.id.value,
                name=src.name,
                fulltext=src.fulltext,
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
        stmt = delete(src_source).where(src_source.c.id == source_id.value)
        self._conn.execute(stmt)
        self._conn.commit()

    def exists(self, source_id: SourceId) -> bool:
        """Check if a source exists."""
        stmt = select(func.count()).where(src_source.c.id == source_id.value)
        result = self._conn.execute(stmt)
        return result.scalar() > 0

    def name_exists(self, name: str, exclude_id: SourceId | None = None) -> bool:
        """Check if a source name is already taken."""
        stmt = select(func.count()).where(func.lower(src_source.c.name) == name.lower())
        if exclude_id:
            stmt = stmt.where(src_source.c.id != exclude_id.value)
        result = self._conn.execute(stmt)
        return result.scalar() > 0

    def get_by_folder(self, folder_id: FolderId | None) -> list[Source]:
        """Get all sources in a folder (None for root level)."""
        if folder_id is None:
            stmt = (
                select(src_source)
                .where(src_source.c.folder_id.is_(None))
                .order_by(src_source.c.name)
            )
        else:
            stmt = (
                select(src_source)
                .where(src_source.c.folder_id == folder_id.value)
                .order_by(src_source.c.name)
            )
        result = self._conn.execute(stmt)
        return [self._row_to_source(row) for row in result]

    def _row_to_source(self, row) -> Source:
        """
        Map database row to domain Source entity.

        This mapper enforces invariants via the Source constructor.
        """
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
            fulltext=row.fulltext,
            created_at=datetime.fromisoformat(row.date)
            if row.date
            else datetime.now(UTC),
        )
