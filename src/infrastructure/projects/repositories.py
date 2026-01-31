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

from src.domain.projects.entities import (
    Folder,
    Source,
    SourceStatus,
    SourceType,
)
from src.domain.cases.entities import AttributeType, Case, CaseAttribute
from src.domain.shared.types import CaseId, FolderId, SourceId
from src.infrastructure.projects.schema import (
    case_attribute,
    case_source,
    cases,
    folder,
    project_settings,
    source,
)

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
        """Get all cases in the project, including linked source IDs and attributes."""
        stmt = select(cases).order_by(cases.c.name)
        result = self._conn.execute(stmt)
        case_list = []
        for row in result:
            case_id = CaseId(value=row.id)
            source_ids = tuple(self.get_source_ids(case_id))
            attributes = self.get_attributes(case_id)
            case_list.append(
                self._row_to_case(row, source_ids=source_ids, attributes=attributes)
            )
        return case_list

    def get_by_id(self, case_id: CaseId) -> Case | None:
        """Get a case by its ID, including linked source IDs and attributes."""
        stmt = select(cases).where(cases.c.id == case_id.value)
        result = self._conn.execute(stmt)
        row = result.fetchone()
        if not row:
            return None

        # Fetch linked source IDs and attributes
        source_ids = tuple(self.get_source_ids(case_id))
        attributes = self.get_attributes(case_id)
        return self._row_to_case(row, source_ids=source_ids, attributes=attributes)

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
        """Delete a case by ID, including all source links and attributes."""
        # First delete all source links
        delete_links = delete(case_source).where(case_source.c.case_id == case_id.value)
        self._conn.execute(delete_links)

        # Delete all attributes
        delete_attrs = delete(case_attribute).where(
            case_attribute.c.case_id == case_id.value
        )
        self._conn.execute(delete_attrs)

        # Then delete the case
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

    # ==========================================================================
    # Source Linking Methods
    # ==========================================================================

    def link_source(self, case_id: CaseId, source_id: SourceId) -> None:
        """Link a source to a case (idempotent)."""
        # Check if link already exists
        if self.is_source_linked(case_id, source_id):
            return

        stmt = case_source.insert().values(
            case_id=case_id.value,
            source_id=source_id.value,
            date=datetime.now(UTC).isoformat(),
        )
        self._conn.execute(stmt)
        self._conn.commit()

    def unlink_source(self, case_id: CaseId, source_id: SourceId) -> None:
        """Unlink a source from a case (no-op if not linked)."""
        stmt = delete(case_source).where(
            (case_source.c.case_id == case_id.value)
            & (case_source.c.source_id == source_id.value)
        )
        self._conn.execute(stmt)
        self._conn.commit()

    def get_source_ids(self, case_id: CaseId) -> list[int]:
        """Get all source IDs linked to a case."""
        stmt = select(case_source.c.source_id).where(
            case_source.c.case_id == case_id.value
        )
        result = self._conn.execute(stmt)
        return [row.source_id for row in result]

    def is_source_linked(self, case_id: CaseId, source_id: SourceId) -> bool:
        """Check if a source is linked to a case."""
        stmt = select(func.count()).where(
            (case_source.c.case_id == case_id.value)
            & (case_source.c.source_id == source_id.value)
        )
        result = self._conn.execute(stmt)
        return result.scalar() > 0

    # ==========================================================================
    # Attribute Methods
    # ==========================================================================

    def save_attribute(self, case_id: CaseId, attr: CaseAttribute) -> None:
        """Save or update an attribute for a case."""
        # Check if attribute already exists
        exists_stmt = select(func.count()).where(
            (case_attribute.c.case_id == case_id.value)
            & (case_attribute.c.name == attr.name)
        )
        exists = self._conn.execute(exists_stmt).scalar() > 0

        # Prepare value columns based on type
        value_text = attr.value if attr.attr_type == AttributeType.TEXT else None
        value_number = (
            attr.value
            if attr.attr_type in (AttributeType.NUMBER, AttributeType.BOOLEAN)
            else None
        )
        # Convert boolean to int for storage
        if attr.attr_type == AttributeType.BOOLEAN:
            value_number = 1 if attr.value else 0
        value_date = attr.value if attr.attr_type == AttributeType.DATE else None

        if exists:
            stmt = (
                update(case_attribute)
                .where(
                    (case_attribute.c.case_id == case_id.value)
                    & (case_attribute.c.name == attr.name)
                )
                .values(
                    attr_type=attr.attr_type.value,
                    value_text=value_text,
                    value_number=value_number,
                    value_date=value_date,
                )
            )
        else:
            stmt = case_attribute.insert().values(
                case_id=case_id.value,
                name=attr.name,
                attr_type=attr.attr_type.value,
                value_text=value_text,
                value_number=value_number,
                value_date=value_date,
            )

        self._conn.execute(stmt)
        self._conn.commit()

    def delete_attribute(self, case_id: CaseId, attr_name: str) -> None:
        """Delete an attribute from a case."""
        stmt = delete(case_attribute).where(
            (case_attribute.c.case_id == case_id.value)
            & (case_attribute.c.name == attr_name)
        )
        self._conn.execute(stmt)
        self._conn.commit()

    def get_attribute(self, case_id: CaseId, attr_name: str) -> CaseAttribute | None:
        """Get a specific attribute by name."""
        stmt = select(case_attribute).where(
            (case_attribute.c.case_id == case_id.value)
            & (case_attribute.c.name == attr_name)
        )
        result = self._conn.execute(stmt)
        row = result.fetchone()
        return self._row_to_attribute(row) if row else None

    def get_attributes(self, case_id: CaseId) -> tuple[CaseAttribute, ...]:
        """Get all attributes for a case."""
        stmt = select(case_attribute).where(case_attribute.c.case_id == case_id.value)
        result = self._conn.execute(stmt)
        return tuple(self._row_to_attribute(row) for row in result)

    def _row_to_attribute(self, row) -> CaseAttribute:
        """Convert a database row to a CaseAttribute."""
        attr_type = AttributeType(row.attr_type)

        # Get value based on type
        if attr_type == AttributeType.TEXT:
            value = row.value_text
        elif attr_type == AttributeType.NUMBER:
            value = row.value_number
        elif attr_type == AttributeType.BOOLEAN:
            value = bool(row.value_number) if row.value_number is not None else False
        elif attr_type == AttributeType.DATE:
            value = row.value_date
        else:
            value = row.value_text

        return CaseAttribute(
            name=row.name,
            attr_type=attr_type,
            value=value,
        )

    def _row_to_case(
        self,
        row,
        source_ids: tuple[int, ...] | None = None,
        attributes: tuple[CaseAttribute, ...] | None = None,
    ) -> Case:
        """Convert a database row to a Case entity."""
        return Case(
            id=CaseId(value=row.id),
            name=row.name,
            description=row.description,
            memo=row.memo,
            attributes=attributes if attributes is not None else (),
            source_ids=source_ids if source_ids is not None else (),
            created_at=row.created_at or datetime.now(UTC),
            updated_at=row.updated_at or datetime.now(UTC),
        )


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
