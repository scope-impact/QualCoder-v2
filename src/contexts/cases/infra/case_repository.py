"""
Case Repository - SQLAlchemy Core Implementation for Cases Context.

Implements the repository for Case entities using the cas_* tables.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import delete, func, select, update

from src.contexts.cases.core.entities import AttributeType, Case, CaseAttribute
from src.contexts.cases.infra.schema import cas_attribute, cas_case, cas_source_link
from src.shared import CaseId, SourceId

if TYPE_CHECKING:
    from sqlalchemy import Connection


class SQLiteCaseRepository:
    """
    SQLAlchemy Core implementation of CaseRepository.

    Maps between domain Case entities and the cas_* tables.
    Uses prefixed tables from the Cases bounded context.
    """

    def __init__(self, connection: Connection) -> None:
        self._conn = connection

    def get_all(self) -> list[Case]:
        """Get all cases in the project."""
        stmt = select(cas_case).order_by(cas_case.c.name)
        result = self._conn.execute(stmt)
        return [self._row_to_case(row) for row in result]

    def get_by_id(self, case_id: CaseId) -> Case | None:
        """Get a case by its ID."""
        stmt = select(cas_case).where(cas_case.c.id == case_id.value)
        result = self._conn.execute(stmt)
        row = result.fetchone()
        return self._row_to_case(row) if row else None

    def get_by_name(self, name: str) -> Case | None:
        """Get a case by its name (case-insensitive)."""
        stmt = select(cas_case).where(func.lower(cas_case.c.name) == name.lower())
        result = self._conn.execute(stmt)
        row = result.fetchone()
        return self._row_to_case(row) if row else None

    def save(self, case: Case) -> None:
        """Save a case (insert or update)."""
        exists = self.exists(case.id)

        if exists:
            stmt = (
                update(cas_case)
                .where(cas_case.c.id == case.id.value)
                .values(
                    name=case.name,
                    description=case.description,
                    memo=case.memo,
                    updated_at=datetime.now(UTC),
                )
            )
        else:
            stmt = cas_case.insert().values(
                id=case.id.value,
                name=case.name,
                description=case.description,
                memo=case.memo,
                owner=None,
                created_at=case.created_at,
                updated_at=case.updated_at,
            )

        self._conn.execute(stmt)

        # Save attributes
        self._save_attributes(case.id, case.attributes)

        # Save source links
        self._save_source_links(case.id, case.source_ids)

        self._conn.commit()

    def delete(self, case_id: CaseId) -> None:
        """Delete a case and its attributes/links."""
        # Delete attributes first
        self._conn.execute(
            delete(cas_attribute).where(cas_attribute.c.case_id == case_id.value)
        )
        # Delete source links
        self._conn.execute(
            delete(cas_source_link).where(cas_source_link.c.case_id == case_id.value)
        )
        # Delete case
        self._conn.execute(delete(cas_case).where(cas_case.c.id == case_id.value))
        self._conn.commit()

    def exists(self, case_id: CaseId) -> bool:
        """Check if a case exists."""
        stmt = select(func.count()).where(cas_case.c.id == case_id.value)
        result = self._conn.execute(stmt)
        return result.scalar() > 0

    def name_exists(self, name: str, exclude_id: CaseId | None = None) -> bool:
        """Check if a case name is already taken."""
        stmt = select(func.count()).where(func.lower(cas_case.c.name) == name.lower())
        if exclude_id:
            stmt = stmt.where(cas_case.c.id != exclude_id.value)
        result = self._conn.execute(stmt)
        return result.scalar() > 0

    def count(self) -> int:
        """Get total count of cases."""
        stmt = select(func.count()).select_from(cas_case)
        result = self._conn.execute(stmt)
        return result.scalar()

    def get_cases_for_source(self, source_id: SourceId) -> list[Case]:
        """Get all cases linked to a source."""
        stmt = (
            select(cas_case)
            .join(cas_source_link, cas_case.c.id == cas_source_link.c.case_id)
            .where(cas_source_link.c.source_id == source_id.value)
            .order_by(cas_case.c.name)
        )
        result = self._conn.execute(stmt)
        return [self._row_to_case(row) for row in result]

    def link_source(
        self, case_id: CaseId, source_id: SourceId, source_name: str | None = None
    ) -> None:
        """Link a source to a case."""
        # Check if link exists
        stmt = select(func.count()).where(
            cas_source_link.c.case_id == case_id.value,
            cas_source_link.c.source_id == source_id.value,
        )
        if self._conn.execute(stmt).scalar() > 0:
            return  # Already linked

        self._conn.execute(
            cas_source_link.insert().values(
                case_id=case_id.value,
                source_id=source_id.value,
                source_name=source_name,
                date=datetime.now(UTC).isoformat(),
            )
        )
        self._conn.commit()

    def save_attribute(self, case_id: CaseId, attribute: CaseAttribute) -> None:
        """Save a single case attribute."""
        # Delete existing attribute with same name
        self._conn.execute(
            delete(cas_attribute).where(
                cas_attribute.c.case_id == case_id.value,
                cas_attribute.c.name == attribute.name,
            )
        )

        values = self._attribute_to_values(case_id, attribute)
        self._conn.execute(cas_attribute.insert().values(**values))
        self._conn.commit()

    def unlink_source(self, case_id: CaseId, source_id: SourceId) -> None:
        """Unlink a source from a case."""
        self._conn.execute(
            delete(cas_source_link).where(
                cas_source_link.c.case_id == case_id.value,
                cas_source_link.c.source_id == source_id.value,
            )
        )
        self._conn.commit()

    def update_source_name(self, source_id: SourceId, new_name: str) -> None:
        """
        Update denormalized source_name for all links to a source.

        Called when a source is renamed to keep denormalized data in sync.
        """
        self._conn.execute(
            update(cas_source_link)
            .where(cas_source_link.c.source_id == source_id.value)
            .values(source_name=new_name)
        )
        self._conn.commit()

    def get_source_ids(self, case_id: CaseId) -> list[int]:
        """Get list of source IDs linked to a case."""
        stmt = select(cas_source_link.c.source_id).where(
            cas_source_link.c.case_id == case_id.value
        )
        result = self._conn.execute(stmt)
        return [row[0] for row in result]

    def is_source_linked(self, case_id: CaseId, source_id: SourceId) -> bool:
        """Check if a source is linked to a case."""
        stmt = select(func.count()).where(
            cas_source_link.c.case_id == case_id.value,
            cas_source_link.c.source_id == source_id.value,
        )
        return self._conn.execute(stmt).scalar() > 0

    def get_attributes(self, case_id: CaseId) -> list[CaseAttribute]:
        """Get all attributes for a case."""
        stmt = select(cas_attribute).where(cas_attribute.c.case_id == case_id.value)
        result = self._conn.execute(stmt)
        return [self._row_to_attribute(row) for row in result]

    def get_attribute(self, case_id: CaseId, attr_name: str) -> CaseAttribute | None:
        """Get a specific attribute by name."""
        stmt = select(cas_attribute).where(
            cas_attribute.c.case_id == case_id.value,
            cas_attribute.c.name == attr_name,
        )
        result = self._conn.execute(stmt)
        row = result.fetchone()
        return self._row_to_attribute(row) if row else None

    def delete_attribute(self, case_id: CaseId, attr_name: str) -> bool:
        """Delete an attribute from a case."""
        stmt = delete(cas_attribute).where(
            cas_attribute.c.case_id == case_id.value,
            cas_attribute.c.name == attr_name,
        )
        result = self._conn.execute(stmt)
        self._conn.commit()
        return result.rowcount > 0

    def _save_attributes(
        self, case_id: CaseId, attributes: tuple[CaseAttribute, ...]
    ) -> None:
        """Save case attributes (replace all)."""
        # Delete existing attributes
        self._conn.execute(
            delete(cas_attribute).where(cas_attribute.c.case_id == case_id.value)
        )

        # Insert new attributes
        for attr in attributes:
            values = self._attribute_to_values(case_id, attr)
            self._conn.execute(cas_attribute.insert().values(**values))

    def _save_source_links(self, case_id: CaseId, source_ids: tuple[int, ...]) -> None:
        """Save source links for a case."""
        # Get existing links
        existing = {
            row[0]
            for row in self._conn.execute(
                select(cas_source_link.c.source_id).where(
                    cas_source_link.c.case_id == case_id.value
                )
            )
        }

        new_ids = set(source_ids)

        # Remove links that are no longer present
        to_remove = existing - new_ids
        if to_remove:
            self._conn.execute(
                delete(cas_source_link).where(
                    cas_source_link.c.case_id == case_id.value,
                    cas_source_link.c.source_id.in_(to_remove),
                )
            )

        # Add new links (source_name will need to be fetched separately)
        to_add = new_ids - existing
        for source_id in to_add:
            self._conn.execute(
                cas_source_link.insert().values(
                    case_id=case_id.value,
                    source_id=source_id,
                    source_name=None,  # Will be populated by sync
                    date=datetime.now(UTC).isoformat(),
                )
            )

    def _row_to_case(self, row) -> Case:
        """Convert a database row to a Case entity."""
        case_id = CaseId(value=row.id)

        # Load attributes
        attr_rows = self._conn.execute(
            select(cas_attribute).where(cas_attribute.c.case_id == case_id.value)
        )
        attributes = tuple(self._row_to_attribute(r) for r in attr_rows)

        # Load source links
        link_rows = self._conn.execute(
            select(cas_source_link.c.source_id).where(
                cas_source_link.c.case_id == case_id.value
            )
        )
        source_ids = tuple(r[0] for r in link_rows)

        return Case(
            id=case_id,
            name=row.name,
            description=row.description,
            memo=row.memo,
            attributes=attributes,
            source_ids=source_ids,
            created_at=row.created_at or datetime.now(UTC),
            updated_at=row.updated_at or datetime.now(UTC),
        )

    def _row_to_attribute(self, row) -> CaseAttribute:
        """Convert a database row to a CaseAttribute."""
        attr_type = AttributeType(row.attr_type)

        # Get value based on type
        if attr_type == AttributeType.TEXT:
            value = row.value_text
        elif attr_type == AttributeType.NUMBER:
            value = row.value_number
        elif attr_type == AttributeType.DATE:
            value = row.value_date
        elif attr_type == AttributeType.BOOLEAN:
            value = row.value_text.lower() == "true" if row.value_text else False
        else:
            value = row.value_text

        return CaseAttribute(
            name=row.name,
            attr_type=attr_type,
            value=value,
        )

    def _attribute_to_values(self, case_id: CaseId, attr: CaseAttribute) -> dict:
        """Convert a CaseAttribute to database column values."""
        values = {
            "case_id": case_id.value,
            "name": attr.name,
            "attr_type": attr.attr_type.value,
            "value_text": None,
            "value_number": None,
            "value_date": None,
        }

        # Set appropriate value column based on type
        if attr.attr_type == AttributeType.TEXT:
            values["value_text"] = str(attr.value) if attr.value else None
        elif attr.attr_type == AttributeType.NUMBER:
            values["value_number"] = int(attr.value) if attr.value else None
        elif attr.attr_type == AttributeType.DATE:
            values["value_date"] = attr.value
        elif attr.attr_type == AttributeType.BOOLEAN:
            values["value_text"] = (
                str(attr.value).lower() if attr.value is not None else None
            )

        return values
