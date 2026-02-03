"""
Coding Context: Convex Repository Implementations

Implements the repository protocols using the Convex cloud database.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from src.contexts.coding.core.entities import (
    Category,
    Code,
    Color,
    TextPosition,
    TextSegment,
)
from src.shared.common.types import CategoryId, CodeId, SegmentId, SourceId

if TYPE_CHECKING:
    from src.shared.infra.convex import ConvexClientWrapper


class ConvexCodeRepository:
    """
    Convex implementation of CodeRepository.

    Maps between domain Code entities and Convex cod_code documents.
    """

    def __init__(self, client: ConvexClientWrapper) -> None:
        self._client = client

    def get_all(self) -> list[Code]:
        """Get all codes in the project."""
        docs = self._client.get_all_codes()
        return [self._doc_to_code(doc) for doc in docs]

    def get_by_id(self, code_id: CodeId) -> Code | None:
        """Get a code by its ID."""
        doc = self._client.get_code_by_id(code_id.value)
        return self._doc_to_code(doc) if doc else None

    def get_by_name(self, name: str) -> Code | None:
        """Get a code by its name (case-insensitive)."""
        doc = self._client.query("codes:getByName", name=name)
        return self._doc_to_code(doc) if doc else None

    def get_by_category(self, category_id: CategoryId) -> list[Code]:
        """Get all codes in a category."""
        docs = self._client.query("codes:getByCategory", categoryId=category_id.value)
        return [self._doc_to_code(doc) for doc in docs]

    def save(self, code: Code) -> None:
        """Save a code (insert or update)."""
        if self.exists(code.id):
            self._client.update_code(
                code.id.value,
                name=code.name,
                color=code.color.to_hex(),
                memo=code.memo,
                catid=code.category_id.value if code.category_id else None,
                owner=code.owner,
            )
        else:
            self._client.mutation(
                "codes:create",
                name=code.name,
                color=code.color.to_hex(),
                memo=code.memo,
                catid=code.category_id.value if code.category_id else None,
                owner=code.owner,
                date=code.created_at.isoformat(),
            )

    def delete(self, code_id: CodeId) -> None:
        """Delete a code by ID."""
        self._client.delete_code(code_id.value)

    def exists(self, code_id: CodeId) -> bool:
        """Check if a code exists."""
        return self._client.query("codes:exists", id=code_id.value)

    def name_exists(self, name: str, exclude_id: CodeId | None = None) -> bool:
        """Check if a code name is already taken."""
        return self._client.query(
            "codes:nameExists",
            name=name,
            excludeId=exclude_id.value if exclude_id else None,
        )

    def _doc_to_code(self, doc: dict[str, Any]) -> Code:
        """Map Convex document to domain Code entity."""
        return Code(
            id=CodeId(value=doc["_id"]),
            name=doc["name"],
            color=Color.from_hex(doc.get("color")) if doc.get("color") else Color(153, 153, 153),
            memo=doc.get("memo"),
            category_id=CategoryId(value=doc["catid"]) if doc.get("catid") else None,
            owner=doc.get("owner"),
            created_at=datetime.fromisoformat(doc["date"])
            if doc.get("date")
            else datetime.now(UTC),
        )


class ConvexCategoryRepository:
    """
    Convex implementation of CategoryRepository.

    Maps between domain Category entities and Convex cod_category documents.
    """

    def __init__(self, client: ConvexClientWrapper) -> None:
        self._client = client

    def get_all(self) -> list[Category]:
        """Get all categories."""
        docs = self._client.get_all_categories()
        return [self._doc_to_category(doc) for doc in docs]

    def get_by_id(self, category_id: CategoryId) -> Category | None:
        """Get a category by ID."""
        doc = self._client.get_category_by_id(category_id.value)
        return self._doc_to_category(doc) if doc else None

    def get_by_parent(self, parent_id: CategoryId | None) -> list[Category]:
        """Get child categories of a parent (None for root)."""
        docs = self._client.query(
            "categories:getByParent",
            parentId=parent_id.value if parent_id else None,
        )
        return [self._doc_to_category(doc) for doc in docs]

    def save(self, category: Category) -> None:
        """Save a category."""
        exists = self.get_by_id(category.id) is not None

        if exists:
            self._client.update_category(
                category.id.value,
                name=category.name,
                supercatid=category.parent_id.value if category.parent_id else None,
                memo=category.memo,
                owner=category.owner,
            )
        else:
            self._client.mutation(
                "categories:create",
                name=category.name,
                supercatid=category.parent_id.value if category.parent_id else None,
                memo=category.memo,
                owner=category.owner,
                date=category.created_at.isoformat(),
            )

    def delete(self, category_id: CategoryId) -> None:
        """Delete a category."""
        self._client.delete_category(category_id.value)

    def name_exists(self, name: str, exclude_id: CategoryId | None = None) -> bool:
        """Check if a category name is already taken."""
        return self._client.query(
            "categories:nameExists",
            name=name,
            excludeId=exclude_id.value if exclude_id else None,
        )

    def _doc_to_category(self, doc: dict[str, Any]) -> Category:
        """Map Convex document to domain Category entity."""
        return Category(
            id=CategoryId(value=doc["_id"]),
            name=doc["name"],
            parent_id=CategoryId(value=doc["supercatid"]) if doc.get("supercatid") else None,
            memo=doc.get("memo"),
            owner=doc.get("owner"),
            created_at=datetime.fromisoformat(doc["date"])
            if doc.get("date")
            else datetime.now(UTC),
        )


class ConvexSegmentRepository:
    """
    Convex implementation of SegmentRepository.

    Maps between domain TextSegment entities and Convex cod_segment documents.
    """

    def __init__(self, client: ConvexClientWrapper) -> None:
        self._client = client

    def get_all(self) -> list[TextSegment]:
        """Get all text segments."""
        docs = self._client.get_all_segments()
        return [self._doc_to_segment(doc) for doc in docs]

    def get_by_id(self, segment_id: SegmentId) -> TextSegment | None:
        """Get a segment by ID."""
        doc = self._client.query("segments:getById", id=segment_id.value)
        return self._doc_to_segment(doc) if doc else None

    def get_by_source(self, source_id: SourceId) -> list[TextSegment]:
        """Get all segments for a source."""
        docs = self._client.get_segments_by_source(source_id.value)
        return [self._doc_to_segment(doc) for doc in docs]

    def get_by_code(self, code_id: CodeId) -> list[TextSegment]:
        """Get all segments with a specific code."""
        docs = self._client.get_segments_by_code(code_id.value)
        return [self._doc_to_segment(doc) for doc in docs]

    def get_by_source_and_code(
        self, source_id: SourceId, code_id: CodeId
    ) -> list[TextSegment]:
        """Get segments for a source with a specific code."""
        docs = self._client.query(
            "segments:getBySourceAndCode",
            sourceId=source_id.value,
            codeId=code_id.value,
        )
        return [self._doc_to_segment(doc) for doc in docs]

    def save(self, segment: TextSegment) -> None:
        """Save a segment."""
        exists = self.get_by_id(segment.id) is not None

        if exists:
            self._client.update_segment(
                segment.id.value,
                cid=segment.code_id.value,
                fid=segment.source_id.value,
                pos0=segment.position.start,
                pos1=segment.position.end,
                seltext=segment.selected_text,
                memo=segment.memo,
                owner=segment.owner,
                important=segment.importance,
            )
        else:
            self._client.mutation(
                "segments:create",
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

    def delete(self, segment_id: SegmentId) -> None:
        """Delete a segment by ID."""
        self._client.delete_segment(segment_id.value)

    def delete_by_code(self, code_id: CodeId) -> int:
        """Delete all segments with a code, returns count deleted."""
        return self._client.mutation("segments:deleteByCode", codeId=code_id.value)

    def delete_by_source(self, source_id: SourceId) -> int:
        """Delete all segments for a source, returns count deleted."""
        return self._client.mutation("segments:deleteBySource", sourceId=source_id.value)

    def count_by_code(self, code_id: CodeId) -> int:
        """Count segments with a specific code."""
        return self._client.query("segments:countByCode", codeId=code_id.value)

    def count_by_source(self, source_id: SourceId) -> int:
        """Count segments for a specific source."""
        return self._client.query("segments:countBySource", sourceId=source_id.value)

    def reassign_code(self, from_code_id: CodeId, to_code_id: CodeId) -> int:
        """Reassign all segments from one code to another, returns count."""
        return self._client.mutation(
            "segments:reassignCode",
            fromCodeId=from_code_id.value,
            toCodeId=to_code_id.value,
        )

    def update_source_name(self, source_id: SourceId, new_name: str) -> None:
        """Update denormalized source_name for all segments of a source."""
        self._client.mutation(
            "segments:updateSourceName",
            sourceId=source_id.value,
            newName=new_name,
        )

    def _doc_to_segment(self, doc: dict[str, Any]) -> TextSegment:
        """Map Convex document to domain TextSegment entity."""
        return TextSegment(
            id=SegmentId(value=doc["_id"]),
            source_id=SourceId(value=doc["fid"]),
            code_id=CodeId(value=doc["cid"]),
            position=TextPosition(start=doc["pos0"], end=doc["pos1"]),
            selected_text=doc.get("seltext"),
            memo=doc.get("memo"),
            importance=doc.get("important") or 0,
            owner=doc.get("owner"),
            created_at=datetime.fromisoformat(doc["date"])
            if doc.get("date")
            else datetime.now(UTC),
        )
