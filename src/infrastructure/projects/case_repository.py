"""
Case Repository - SQLAlchemy Core Implementation.

Implements the repository for Case entities using SQLAlchemy Core.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import delete, func, select, update

from src.contexts.cases.core.entities import AttributeType, Case, CaseAttribute
from src.contexts.cases.infra.schema import (
    cas_attribute as case_attribute,
)
from src.contexts.cases.infra.schema import (
    cas_case as cases,
)
from src.contexts.cases.infra.schema import (
    cas_source_link as case_source,
)
from src.contexts.shared.core.types import CaseId, SourceId

if TYPE_CHECKING:
    from sqlalchemy import Connection


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
