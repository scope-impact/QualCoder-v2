"""
Coding Context: SQLAlchemy Core Repository Implementations

Implements the repository protocols using SQLAlchemy Core for clean,
type-safe database access without full ORM overhead.
"""

from __future__ import annotations

import logging
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
from src.shared.common.types import CategoryId, CodeId, SegmentId, SourceId

if TYPE_CHECKING:
    from sqlalchemy import Connection

    from src.shared.infra.sync.outbox import OutboxWriter

logger = logging.getLogger("qualcoder.coding.infra")


class SQLiteCodeRepository:
    """
    SQLAlchemy Core implementation of CodeRepository.

    Maps between domain Code entities and the code_name table.
    """

    def __init__(
        self, connection: Connection, outbox: OutboxWriter | None = None
    ) -> None:
        self._conn = connection
        self._outbox = outbox

    def get_all(self) -> list[Code]:
        """Get all codes in the project."""
        stmt = select(code_name).order_by(code_name.c.name)
        result = self._conn.execute(stmt)
        codes = [self._row_to_code(row) for row in result]
        logger.debug("get_all: count=%d", len(codes))
        return codes

    def get_by_id(self, code_id: CodeId) -> Code | None:
        """Get a code by its ID."""
        logger.debug("get_by_id: %s", code_id.value)
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
        logger.debug("save: %s (name=%s)", code.id.value, code.name)
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
        if self._outbox:
            self._outbox.write_upsert(
                "code",
                code.id.value,
                {"name": code.name, "color": code.color.to_hex(), "memo": code.memo},
            )

    def delete(self, code_id: CodeId) -> None:
        """Delete a code by ID."""
        logger.debug("delete: %s", code_id.value)
        stmt = delete(code_name).where(code_name.c.cid == code_id.value)
        self._conn.execute(stmt)
        if self._outbox:
            self._outbox.write_delete("code", code_id.value)

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


class SQLiteCategoryRepository:
    """
    SQLAlchemy Core implementation of CategoryRepository.

    Maps between domain Category entities and the code_cat table.
    """

    def __init__(
        self, connection: Connection, outbox: OutboxWriter | None = None
    ) -> None:
        self._conn = connection
        self._outbox = outbox

    def get_all(self) -> list[Category]:
        """Get all categories."""
        stmt = select(code_cat).order_by(code_cat.c.name)
        result = self._conn.execute(stmt)
        categories = [self._row_to_category(row) for row in result]
        logger.debug("get_all: count=%d", len(categories))
        return categories

    def get_by_id(self, category_id: CategoryId) -> Category | None:
        """Get a category by ID."""
        logger.debug("get_by_id: %s", category_id.value)
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
        logger.debug("save: %s (name=%s)", category.id.value, category.name)
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
        if self._outbox:
            self._outbox.write_upsert(
                "category",
                category.id.value,
                {"name": category.name, "memo": category.memo},
            )

    def delete(self, category_id: CategoryId) -> None:
        """Delete a category."""
        logger.debug("delete: %s", category_id.value)
        stmt = delete(code_cat).where(code_cat.c.catid == category_id.value)
        self._conn.execute(stmt)
        if self._outbox:
            self._outbox.write_delete("category", category_id.value)

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


class SQLiteSegmentRepository:
    """
    SQLAlchemy Core implementation of SegmentRepository.

    Maps between domain TextSegment entities and the code_text table.
    """

    def __init__(
        self, connection: Connection, outbox: OutboxWriter | None = None
    ) -> None:
        self._conn = connection
        self._outbox = outbox

    def get_all(self) -> list[TextSegment]:
        """Get all text segments."""
        stmt = select(code_text).order_by(code_text.c.fid, code_text.c.pos0)
        result = self._conn.execute(stmt)
        segments = [self._row_to_segment(row) for row in result]
        logger.debug("get_all: count=%d", len(segments))
        return segments

    def get_by_id(self, segment_id: SegmentId) -> TextSegment | None:
        """Get a segment by ID."""
        logger.debug("get_by_id: %s", segment_id.value)
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
        logger.debug(
            "save: %s (code=%s, source=%s)",
            segment.id.value,
            segment.code_id.value,
            segment.source_id.value,
        )
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
        if self._outbox:
            self._outbox.write_upsert(
                "segment",
                segment.id.value,
                {
                    "cid": segment.code_id.value,
                    "fid": segment.source_id.value,
                    "pos0": segment.position.start,
                    "pos1": segment.position.end,
                    "seltext": segment.selected_text,
                    "memo": segment.memo,
                    "owner": segment.owner,
                    "important": segment.importance,
                },
            )

    def delete(self, segment_id: SegmentId) -> None:
        """Delete a segment by ID."""
        logger.debug("delete: %s", segment_id.value)
        stmt = delete(code_text).where(code_text.c.ctid == segment_id.value)
        self._conn.execute(stmt)
        if self._outbox:
            self._outbox.write_delete("segment", segment_id.value)

    def delete_by_code(self, code_id: CodeId) -> int:
        """Delete all segments with a code, returns count deleted."""
        count = self.count_by_code(code_id)
        logger.debug("delete_by_code: %s (count=%d)", code_id.value, count)
        stmt = delete(code_text).where(code_text.c.cid == code_id.value)
        self._conn.execute(stmt)

        return count

    def delete_by_source(self, source_id: SourceId) -> int:
        """Delete all segments for a source, returns count deleted."""
        count = self.count_by_source(source_id)
        logger.debug("delete_by_source: %s (count=%d)", source_id.value, count)
        stmt = delete(code_text).where(code_text.c.fid == source_id.value)
        self._conn.execute(stmt)

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

    def count_all_by_code(self) -> dict[int, int]:
        """
        Count segments grouped by code_id in a single query.

        Returns:
            Dictionary mapping code_id to segment count
        """
        stmt = select(code_text.c.cid, func.count().label("cnt")).group_by(
            code_text.c.cid
        )
        result = self._conn.execute(stmt)
        return {row.cid: row.cnt for row in result}

    def reassign_code(self, from_code_id: CodeId, to_code_id: CodeId) -> int:
        """Reassign all segments from one code to another, returns count."""
        count = self.count_by_code(from_code_id)
        stmt = (
            update(code_text)
            .where(code_text.c.cid == from_code_id.value)
            .values(cid=to_code_id.value)
        )
        self._conn.execute(stmt)

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
