"""
References Context: Repository Implementation

SQLAlchemy Core implementation of the Reference repository.
"""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import delete, func, select, update

from src.domain.references.entities import Reference
from src.domain.shared.types import ReferenceId, SegmentId
from src.infrastructure.projects.schema import reference_segment, references


class SQLiteReferenceRepository:
    """SQLAlchemy Core implementation of ReferenceRepository."""

    def __init__(self, connection) -> None:
        """
        Initialize the repository.

        Args:
            connection: SQLAlchemy database connection
        """
        self._conn = connection

    # =========================================================================
    # Basic CRUD Operations
    # =========================================================================

    def get_all(self) -> list[Reference]:
        """Get all references."""
        stmt = select(references).order_by(references.c.title)
        result = self._conn.execute(stmt)
        return [self._row_to_reference(row) for row in result]

    def get_by_id(self, ref_id: ReferenceId) -> Reference | None:
        """Get a reference by ID."""
        stmt = select(references).where(references.c.id == ref_id.value)
        result = self._conn.execute(stmt)
        row = result.fetchone()
        if row is None:
            return None
        return self._row_to_reference(row)

    def get_by_doi(self, doi: str) -> Reference | None:
        """Get a reference by DOI."""
        stmt = select(references).where(references.c.doi == doi)
        result = self._conn.execute(stmt)
        row = result.fetchone()
        if row is None:
            return None
        return self._row_to_reference(row)

    def save(self, reference: Reference) -> None:
        """Save a reference (insert or update)."""
        exists = self.exists(reference.id)

        if exists:
            stmt = (
                update(references)
                .where(references.c.id == reference.id.value)
                .values(
                    title=reference.title,
                    authors=reference.authors,
                    year=reference.year,
                    source=reference.source,
                    doi=reference.doi,
                    url=reference.url,
                    memo=reference.memo,
                    updated_at=datetime.now(UTC),
                )
            )
        else:
            stmt = references.insert().values(
                id=reference.id.value,
                title=reference.title,
                authors=reference.authors,
                year=reference.year,
                source=reference.source,
                doi=reference.doi,
                url=reference.url,
                memo=reference.memo,
                created_at=reference.created_at,
                updated_at=reference.updated_at,
            )

        self._conn.execute(stmt)
        self._conn.commit()

    def delete(self, ref_id: ReferenceId) -> None:
        """Delete a reference and its segment links."""
        # Delete segment links first
        stmt = delete(reference_segment).where(
            reference_segment.c.reference_id == ref_id.value
        )
        self._conn.execute(stmt)

        # Delete reference
        stmt = delete(references).where(references.c.id == ref_id.value)
        self._conn.execute(stmt)
        self._conn.commit()

    def exists(self, ref_id: ReferenceId) -> bool:
        """Check if a reference exists."""
        stmt = select(func.count()).select_from(references).where(
            references.c.id == ref_id.value
        )
        result = self._conn.execute(stmt)
        return result.scalar() > 0

    # =========================================================================
    # Search Operations
    # =========================================================================

    def search_by_title(self, title_query: str) -> list[Reference]:
        """Search references by title (case-insensitive)."""
        query = f"%{title_query}%"
        stmt = (
            select(references)
            .where(references.c.title.ilike(query))
            .order_by(references.c.title)
        )
        result = self._conn.execute(stmt)
        return [self._row_to_reference(row) for row in result]

    # =========================================================================
    # Segment Linking Operations
    # =========================================================================

    def link_segment(self, ref_id: ReferenceId, segment_id: SegmentId) -> None:
        """Link a segment to a reference."""
        # Check if already linked (idempotent)
        if self.is_segment_linked(ref_id, segment_id):
            return

        stmt = reference_segment.insert().values(
            reference_id=ref_id.value,
            segment_id=segment_id.value,
            date=datetime.now(UTC).isoformat(),
        )
        self._conn.execute(stmt)
        self._conn.commit()

    def unlink_segment(self, ref_id: ReferenceId, segment_id: SegmentId) -> None:
        """Unlink a segment from a reference."""
        stmt = delete(reference_segment).where(
            (reference_segment.c.reference_id == ref_id.value)
            & (reference_segment.c.segment_id == segment_id.value)
        )
        self._conn.execute(stmt)
        self._conn.commit()

    def get_segment_ids(self, ref_id: ReferenceId) -> list[int]:
        """Get all segment IDs linked to a reference."""
        stmt = select(reference_segment.c.segment_id).where(
            reference_segment.c.reference_id == ref_id.value
        )
        result = self._conn.execute(stmt)
        return [row.segment_id for row in result]

    def is_segment_linked(self, ref_id: ReferenceId, segment_id: SegmentId) -> bool:
        """Check if a segment is linked to a reference."""
        stmt = (
            select(func.count())
            .select_from(reference_segment)
            .where(
                (reference_segment.c.reference_id == ref_id.value)
                & (reference_segment.c.segment_id == segment_id.value)
            )
        )
        result = self._conn.execute(stmt)
        return result.scalar() > 0

    # =========================================================================
    # Helper Methods
    # =========================================================================

    def _row_to_reference(self, row) -> Reference:
        """Convert a database row to a Reference entity."""
        segment_ids = self.get_segment_ids(ReferenceId(value=row.id))
        return Reference(
            id=ReferenceId(value=row.id),
            title=row.title,
            authors=row.authors,
            year=row.year,
            source=row.source,
            doi=row.doi,
            url=row.url,
            memo=row.memo,
            segment_ids=tuple(segment_ids),
            created_at=row.created_at or datetime.now(UTC),
            updated_at=row.updated_at or datetime.now(UTC),
        )
