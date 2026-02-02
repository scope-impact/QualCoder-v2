"""
Coding Context: SQLAlchemy Core Repository Implementations

Implements the repository protocols using SQLAlchemy Core for clean,
type-safe database access without full ORM overhead.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import delete, func, select, update

from src.contexts.coding.core.entities import (
    Category,
    Code,
    Color,
    TextPosition,
    TextSegment,
)
from src.contexts.coding.infra.schema import code_cat, code_name, code_text
from src.contexts.shared.core.types import CategoryId, CodeId, SegmentId, SourceId

if TYPE_CHECKING:
    from sqlalchemy import Connection


class SQLiteCodeRepository:
    """
    SQLAlchemy Core implementation of CodeRepository.

    Maps between domain Code entities and the code_name table.
    """

    def __init__(self, connection: Connection) -> None:
        self._conn = connection

    def get_all(self) -> list[Code]:
        """Get all codes in the project."""
        stmt = select(code_name).order_by(code_name.c.name)
        result = self._conn.execute(stmt)
        return [self._row_to_code(row) for row in result]

    def get_by_id(self, code_id: CodeId) -> Code | None:
        """Get a code by its ID."""
        stmt = select(code_name).where(code_name.c.cid == code_id.value)
        result = self._conn.execute(stmt)
        row = result.fetchone()
        return self._row_to_code(row) if row else None

    def get_by_name(self, name: str) -> Code | None:
        """Get a code by its name (case-insensitive)."""
        stmt = select(code_name).where(func.lower(code_name.c.name) == name.lower())
        result = self._conn.execute(stmt)
        row = result.fetchone()
        return self._row_to_code(row) if row else None

    def get_by_category(self, category_id: CategoryId) -> list[Code]:
        """Get all codes in a category."""
        stmt = (
            select(code_name)
            .where(code_name.c.catid == category_id.value)
            .order_by(code_name.c.name)
        )
        result = self._conn.execute(stmt)
        return [self._row_to_code(row) for row in result]

    def save(self, code: Code) -> None:
        """Save a code (insert or update)."""
        exists = self.exists(code.id)

        if exists:
            stmt = (
                update(code_name)
                .where(code_name.c.cid == code.id.value)
                .values(
                    name=code.name,
                    color=code.color.to_hex(),
                    memo=code.memo,
                    catid=code.category_id.value if code.category_id else None,
                    owner=code.owner,
                )
            )
        else:
            stmt = code_name.insert().values(
                cid=code.id.value,
                name=code.name,
                color=code.color.to_hex(),
                memo=code.memo,
                catid=code.category_id.value if code.category_id else None,
                owner=code.owner,
                date=code.created_at.isoformat(),
            )

        self._conn.execute(stmt)
        self._conn.commit()

    def delete(self, code_id: CodeId) -> None:
        """Delete a code by ID."""
        stmt = delete(code_name).where(code_name.c.cid == code_id.value)
        self._conn.execute(stmt)
        self._conn.commit()

    def exists(self, code_id: CodeId) -> bool:
        """Check if a code exists."""
        stmt = select(func.count()).where(code_name.c.cid == code_id.value)
        result = self._conn.execute(stmt)
        return result.scalar() > 0

    def name_exists(self, name: str, exclude_id: CodeId | None = None) -> bool:
        """Check if a code name is already taken."""
        stmt = select(func.count()).where(func.lower(code_name.c.name) == name.lower())
        if exclude_id:
            stmt = stmt.where(code_name.c.cid != exclude_id.value)
        result = self._conn.execute(stmt)
        return result.scalar() > 0

    def _row_to_code(self, row) -> Code:
        """
        Map database row to domain Code entity.

        This mapper enforces invariants via the Code constructor.
        """
        return Code(
            id=CodeId(value=row.cid),
            name=row.name,
            color=Color.from_hex(row.color) if row.color else Color(153, 153, 153),
            memo=row.memo,
            category_id=CategoryId(value=row.catid) if row.catid else None,
            owner=row.owner,
            created_at=datetime.fromisoformat(row.date)
            if row.date
            else datetime.now(UTC),
        )

    def _to_code_data(self, code: Code) -> dict:
        """
        Map domain Code entity to database format.

        Returns a dict suitable for SQLAlchemy insert/update.
        """
        return {
            "cid": code.id.value,
            "name": code.name,
            "color": code.color.to_hex(),
            "memo": code.memo,
            "catid": code.category_id.value if code.category_id else None,
            "owner": code.owner,
            "date": code.created_at.isoformat(),
        }


class SQLiteCategoryRepository:
    """
    SQLAlchemy Core implementation of CategoryRepository.

    Maps between domain Category entities and the code_cat table.
    """

    def __init__(self, connection: Connection) -> None:
        self._conn = connection

    def get_all(self) -> list[Category]:
        """Get all categories."""
        stmt = select(code_cat).order_by(code_cat.c.name)
        result = self._conn.execute(stmt)
        return [self._row_to_category(row) for row in result]

    def get_by_id(self, category_id: CategoryId) -> Category | None:
        """Get a category by ID."""
        stmt = select(code_cat).where(code_cat.c.catid == category_id.value)
        result = self._conn.execute(stmt)
        row = result.fetchone()
        return self._row_to_category(row) if row else None

    def get_by_parent(self, parent_id: CategoryId | None) -> list[Category]:
        """Get child categories of a parent (None for root)."""
        if parent_id is None:
            stmt = (
                select(code_cat)
                .where(code_cat.c.supercatid.is_(None))
                .order_by(code_cat.c.name)
            )
        else:
            stmt = (
                select(code_cat)
                .where(code_cat.c.supercatid == parent_id.value)
                .order_by(code_cat.c.name)
            )
        result = self._conn.execute(stmt)
        return [self._row_to_category(row) for row in result]

    def save(self, category: Category) -> None:
        """Save a category."""
        exists_stmt = select(func.count()).where(code_cat.c.catid == category.id.value)
        exists = self._conn.execute(exists_stmt).scalar() > 0

        if exists:
            stmt = (
                update(code_cat)
                .where(code_cat.c.catid == category.id.value)
                .values(
                    name=category.name,
                    supercatid=category.parent_id.value if category.parent_id else None,
                    memo=category.memo,
                    owner=category.owner,
                )
            )
        else:
            stmt = code_cat.insert().values(
                catid=category.id.value,
                name=category.name,
                supercatid=category.parent_id.value if category.parent_id else None,
                memo=category.memo,
                owner=category.owner,
                date=category.created_at.isoformat(),
            )

        self._conn.execute(stmt)
        self._conn.commit()

    def delete(self, category_id: CategoryId) -> None:
        """Delete a category."""
        stmt = delete(code_cat).where(code_cat.c.catid == category_id.value)
        self._conn.execute(stmt)
        self._conn.commit()

    def name_exists(self, name: str, exclude_id: CategoryId | None = None) -> bool:
        """Check if a category name is already taken."""
        stmt = select(func.count()).where(func.lower(code_cat.c.name) == name.lower())
        if exclude_id:
            stmt = stmt.where(code_cat.c.catid != exclude_id.value)
        result = self._conn.execute(stmt)
        return result.scalar() > 0

    def _row_to_category(self, row) -> Category:
        """
        Map database row to domain Category entity.

        This mapper enforces invariants via the Category constructor.
        """
        return Category(
            id=CategoryId(value=row.catid),
            name=row.name,
            parent_id=CategoryId(value=row.supercatid) if row.supercatid else None,
            memo=row.memo,
            owner=row.owner,
            created_at=datetime.fromisoformat(row.date)
            if row.date
            else datetime.now(UTC),
        )

    def _to_category_data(self, category: Category) -> dict:
        """
        Map domain Category entity to database format.

        Returns a dict suitable for SQLAlchemy insert/update.
        """
        return {
            "catid": category.id.value,
            "name": category.name,
            "supercatid": category.parent_id.value if category.parent_id else None,
            "memo": category.memo,
            "owner": category.owner,
            "date": category.created_at.isoformat(),
        }


class SQLiteSegmentRepository:
    """
    SQLAlchemy Core implementation of SegmentRepository.

    Maps between domain TextSegment entities and the code_text table.
    """

    def __init__(self, connection: Connection) -> None:
        self._conn = connection

    def get_all(self) -> list[TextSegment]:
        """Get all text segments."""
        stmt = select(code_text).order_by(code_text.c.fid, code_text.c.pos0)
        result = self._conn.execute(stmt)
        return [self._row_to_segment(row) for row in result]

    def get_by_id(self, segment_id: SegmentId) -> TextSegment | None:
        """Get a segment by ID."""
        stmt = select(code_text).where(code_text.c.ctid == segment_id.value)
        result = self._conn.execute(stmt)
        row = result.fetchone()
        return self._row_to_segment(row) if row else None

    def get_by_source(self, source_id: SourceId) -> list[TextSegment]:
        """Get all segments for a source."""
        stmt = (
            select(code_text)
            .where(code_text.c.fid == source_id.value)
            .order_by(code_text.c.pos0)
        )
        result = self._conn.execute(stmt)
        return [self._row_to_segment(row) for row in result]

    def get_by_code(self, code_id: CodeId) -> list[TextSegment]:
        """Get all segments with a specific code."""
        stmt = (
            select(code_text)
            .where(code_text.c.cid == code_id.value)
            .order_by(code_text.c.fid, code_text.c.pos0)
        )
        result = self._conn.execute(stmt)
        return [self._row_to_segment(row) for row in result]

    def get_by_source_and_code(
        self, source_id: SourceId, code_id: CodeId
    ) -> list[TextSegment]:
        """Get segments for a source with a specific code."""
        stmt = (
            select(code_text)
            .where(code_text.c.fid == source_id.value)
            .where(code_text.c.cid == code_id.value)
            .order_by(code_text.c.pos0)
        )
        result = self._conn.execute(stmt)
        return [self._row_to_segment(row) for row in result]

    def save(self, segment: TextSegment) -> None:
        """Save a segment."""
        exists_stmt = select(func.count()).where(code_text.c.ctid == segment.id.value)
        exists = self._conn.execute(exists_stmt).scalar() > 0

        if exists:
            stmt = (
                update(code_text)
                .where(code_text.c.ctid == segment.id.value)
                .values(
                    cid=segment.code_id.value,
                    fid=segment.source_id.value,
                    pos0=segment.position.start,
                    pos1=segment.position.end,
                    seltext=segment.selected_text,
                    memo=segment.memo,
                    owner=segment.owner,
                    important=segment.importance,
                )
            )
        else:
            stmt = code_text.insert().values(
                ctid=segment.id.value,
                cid=segment.code_id.value,
                fid=segment.source_id.value,
                pos0=segment.position.start,
                pos1=segment.position.end,
                seltext=segment.selected_text,
                memo=segment.memo,
                owner=segment.owner,
                date=segment.created_at.isoformat(),
                important=segment.importance,
            )

        self._conn.execute(stmt)
        self._conn.commit()

    def delete(self, segment_id: SegmentId) -> None:
        """Delete a segment by ID."""
        stmt = delete(code_text).where(code_text.c.ctid == segment_id.value)
        self._conn.execute(stmt)
        self._conn.commit()

    def delete_by_code(self, code_id: CodeId) -> int:
        """Delete all segments with a code, returns count deleted."""
        count = self.count_by_code(code_id)
        stmt = delete(code_text).where(code_text.c.cid == code_id.value)
        self._conn.execute(stmt)
        self._conn.commit()
        return count

    def delete_by_source(self, source_id: SourceId) -> int:
        """Delete all segments for a source, returns count deleted."""
        count = self.count_by_source(source_id)
        stmt = delete(code_text).where(code_text.c.fid == source_id.value)
        self._conn.execute(stmt)
        self._conn.commit()
        return count

    def count_by_code(self, code_id: CodeId) -> int:
        """Count segments with a specific code."""
        stmt = select(func.count()).where(code_text.c.cid == code_id.value)
        result = self._conn.execute(stmt)
        return result.scalar()

    def count_by_source(self, source_id: SourceId) -> int:
        """Count segments for a specific source."""
        stmt = select(func.count()).where(code_text.c.fid == source_id.value)
        result = self._conn.execute(stmt)
        return result.scalar()

    def reassign_code(self, from_code_id: CodeId, to_code_id: CodeId) -> int:
        """Reassign all segments from one code to another, returns count."""
        count = self.count_by_code(from_code_id)
        stmt = (
            update(code_text)
            .where(code_text.c.cid == from_code_id.value)
            .values(cid=to_code_id.value)
        )
        self._conn.execute(stmt)
        self._conn.commit()
        return count

    def update_source_name(self, source_id: SourceId, new_name: str) -> None:
        """
        Update denormalized source_name for all segments of a source.

        Called when a source is renamed to keep denormalized data in sync.
        """
        stmt = (
            update(code_text)
            .where(code_text.c.fid == source_id.value)
            .values(source_name=new_name)
        )
        self._conn.execute(stmt)
        self._conn.commit()

    def _row_to_segment(self, row) -> TextSegment:
        """
        Map database row to domain TextSegment entity.

        This mapper enforces invariants via the TextSegment constructor.
        """
        return TextSegment(
            id=SegmentId(value=row.ctid),
            source_id=SourceId(value=row.fid),
            code_id=CodeId(value=row.cid),
            position=TextPosition(start=row.pos0, end=row.pos1),
            selected_text=row.seltext,
            memo=row.memo,
            importance=row.important or 0,
            owner=row.owner,
            created_at=datetime.fromisoformat(row.date)
            if row.date
            else datetime.now(UTC),
        )

    def _to_segment_data(self, segment: TextSegment) -> dict:
        """
        Map domain TextSegment entity to database format.

        Returns a dict suitable for SQLAlchemy insert/update.
        """
        return {
            "ctid": segment.id.value,
            "cid": segment.code_id.value,
            "fid": segment.source_id.value,
            "pos0": segment.position.start,
            "pos1": segment.position.end,
            "seltext": segment.selected_text,
            "memo": segment.memo,
            "owner": segment.owner,
            "date": segment.created_at.isoformat(),
            "important": segment.importance,
        }
