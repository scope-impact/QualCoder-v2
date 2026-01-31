"""
Project Context: SQLAlchemy Core Repository Implementations

Implements the repository protocols using SQLAlchemy Core for clean,
type-safe database access without full ORM overhead.
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING

from sqlalchemy import delete, func, select, update

from src.domain.cases.entities import Case
from src.domain.projects.entities import (
    Source,
    SourceStatus,
    SourceType,
)
from src.domain.shared.types import CaseId, SourceId
from src.infrastructure.projects.schema import cases, project_settings, source

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

    def _row_to_source(self, row) -> Source:
        """Convert a database row to a Source entity."""
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
            created_at=datetime.fromisoformat(row.date)
            if row.date
            else datetime.now(UTC),
        )


class SQLiteProjectSettingsRepository:
    """
    Repository for project-level settings.

    Stores key-value pairs for project metadata.
    """

    def __init__(self, connection: Connection) -> None:
        self._conn = connection

    def get(self, key: str) -> str | None:
        """Get a setting value by key."""
        stmt = select(project_settings.c.value).where(project_settings.c.key == key)
        result = self._conn.execute(stmt)
        row = result.fetchone()
        return row.value if row else None

    def set(self, key: str, value: str) -> None:
        """Set a setting value."""
        exists_stmt = select(func.count()).where(project_settings.c.key == key)
        exists = self._conn.execute(exists_stmt).scalar() > 0

        if exists:
            stmt = (
                update(project_settings)
                .where(project_settings.c.key == key)
                .values(value=value, updated_at=datetime.now(UTC))
            )
        else:
            stmt = project_settings.insert().values(
                key=key,
                value=value,
                updated_at=datetime.now(UTC),
            )

        self._conn.execute(stmt)
        self._conn.commit()

    def delete(self, key: str) -> None:
        """Delete a setting."""
        stmt = delete(project_settings).where(project_settings.c.key == key)
        self._conn.execute(stmt)
        self._conn.commit()

    def get_all(self) -> dict[str, str]:
        """Get all settings as a dictionary."""
        stmt = select(project_settings)
        result = self._conn.execute(stmt)
        return {row.key: row.value for row in result}

    # Convenience methods for common settings

    def get_project_name(self) -> str | None:
        """Get the project name."""
        return self.get("project_name")

    def set_project_name(self, name: str) -> None:
        """Set the project name."""
        self.set("project_name", name)

    def get_project_memo(self) -> str | None:
        """Get the project memo."""
        return self.get("project_memo")

    def set_project_memo(self, memo: str) -> None:
        """Set the project memo."""
        self.set("project_memo", memo)


class SQLiteCaseRepository:
    """
    SQLAlchemy Core implementation of CaseRepository.

    Maps between domain Case entities and the cases table.
    """

    def __init__(self, connection: Connection) -> None:
        self._conn = connection

    def get_all(self) -> list[Case]:
        """Get all cases in the project."""
        stmt = select(cases).order_by(cases.c.name)
        result = self._conn.execute(stmt)
        return [self._row_to_case(row) for row in result]

    def get_by_id(self, case_id: CaseId) -> Case | None:
        """Get a case by its ID."""
        stmt = select(cases).where(cases.c.id == case_id.value)
        result = self._conn.execute(stmt)
        row = result.fetchone()
        return self._row_to_case(row) if row else None

    def get_by_name(self, name: str) -> Case | None:
        """Get a case by its name (case-insensitive)."""
        stmt = select(cases).where(func.lower(cases.c.name) == name.lower())
        result = self._conn.execute(stmt)
        row = result.fetchone()
        return self._row_to_case(row) if row else None

    def save(self, case: Case) -> None:
        """Save a case (insert or update)."""
        exists = self.exists(case.id)

        if exists:
            stmt = (
                update(cases)
                .where(cases.c.id == case.id.value)
                .values(
                    name=case.name,
                    description=case.description,
                    memo=case.memo,
                    updated_at=datetime.now(UTC),
                )
            )
        else:
            stmt = cases.insert().values(
                id=case.id.value,
                name=case.name,
                description=case.description,
                memo=case.memo,
                created_at=case.created_at,
                updated_at=case.updated_at,
            )

        self._conn.execute(stmt)
        self._conn.commit()

    def delete(self, case_id: CaseId) -> None:
        """Delete a case by ID."""
        stmt = delete(cases).where(cases.c.id == case_id.value)
        self._conn.execute(stmt)
        self._conn.commit()

    def exists(self, case_id: CaseId) -> bool:
        """Check if a case exists."""
        stmt = select(func.count()).where(cases.c.id == case_id.value)
        result = self._conn.execute(stmt)
        return result.scalar() > 0

    def name_exists(self, name: str, exclude_id: CaseId | None = None) -> bool:
        """Check if a case name is already taken."""
        stmt = select(func.count()).where(func.lower(cases.c.name) == name.lower())
        if exclude_id:
            stmt = stmt.where(cases.c.id != exclude_id.value)
        result = self._conn.execute(stmt)
        return result.scalar() > 0

    def count(self) -> int:
        """Get total count of cases."""
        stmt = select(func.count()).select_from(cases)
        result = self._conn.execute(stmt)
        return result.scalar()

    def _row_to_case(self, row) -> Case:
        """Convert a database row to a Case entity."""
        return Case(
            id=CaseId(value=row.id),
            name=row.name,
            description=row.description,
            memo=row.memo,
            created_at=row.created_at or datetime.now(UTC),
            updated_at=row.updated_at or datetime.now(UTC),
        )
