"""
Synced Repository Wrappers.

These wrappers decorate SQLite repositories to:
1. Write to SQLite first (local-first)
2. Queue changes for sync to Convex
3. Handle remote updates from Convex subscriptions

Pattern:
    SQLite Repository (decorated) -> SyncedRepository -> SyncEngine -> Convex
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from src.shared.infra.sync.engine import ChangeType, SyncChange

if TYPE_CHECKING:
    from src.contexts.coding.core.entities import Category, Code, TextSegment
    from src.contexts.coding.infra.repositories import (
        SQLiteCategoryRepository,
        SQLiteCodeRepository,
        SQLiteSegmentRepository,
    )
    from src.shared.common.types import CategoryId, CodeId, SegmentId, SourceId
    from src.shared.infra.sync import SyncEngine


class SyncedCodeRepository:
    """
    Code repository with sync support.

    Wraps SQLiteCodeRepository to queue changes for Convex sync.
    """

    def __init__(
        self,
        sqlite_repo: SQLiteCodeRepository,
        sync_engine: SyncEngine,
    ) -> None:
        self._repo = sqlite_repo
        self._sync = sync_engine

        # Register for remote changes
        self._sync.on_remote_change("code", self._handle_remote_change)

    # Delegate read operations to SQLite
    def get_all(self) -> list[Code]:
        return self._repo.get_all()

    def get_by_id(self, code_id: CodeId) -> Code | None:
        return self._repo.get_by_id(code_id)

    def get_by_name(self, name: str) -> Code | None:
        return self._repo.get_by_name(name)

    def get_by_category(self, category_id: CategoryId) -> list[Code]:
        return self._repo.get_by_category(category_id)

    def exists(self, code_id: CodeId) -> bool:
        return self._repo.exists(code_id)

    def name_exists(self, name: str, exclude_id: CodeId | None = None) -> bool:
        return self._repo.name_exists(name, exclude_id)

    # Write operations: SQLite first, then queue for sync
    def save(self, code: Code) -> None:
        is_new = not self._repo.exists(code.id)
        self._repo.save(code)

        # Queue for Convex sync
        self._sync.queue_change(
            SyncChange(
                entity_type="code",
                change_type=ChangeType.CREATE if is_new else ChangeType.UPDATE,
                entity_id=code.id.value,
                data={
                    "name": code.name,
                    "color": code.color.to_hex(),
                    "memo": code.memo,
                    "catid": code.category_id.value if code.category_id else None,
                    "owner": code.owner,
                    "date": code.created_at.isoformat(),
                },
            )
        )

    def delete(self, code_id: CodeId) -> None:
        self._repo.delete(code_id)
        self._sync.queue_change(
            SyncChange(
                entity_type="code",
                change_type=ChangeType.DELETE,
                entity_id=code_id.value,
                data={},
            )
        )

    def _handle_remote_change(self, change_type: str, data: dict) -> None:
        """Handle incoming changes from Convex subscription."""
        # This would diff remote data with local and apply changes
        # For now, we'll let the sync engine handle full data refresh
        pass


class SyncedCategoryRepository:
    """
    Category repository with sync support.

    Wraps SQLiteCategoryRepository to queue changes for Convex sync.
    """

    def __init__(
        self,
        sqlite_repo: SQLiteCategoryRepository,
        sync_engine: SyncEngine,
    ) -> None:
        self._repo = sqlite_repo
        self._sync = sync_engine
        self._sync.on_remote_change("category", self._handle_remote_change)

    # Delegate read operations
    def get_all(self) -> list[Category]:
        return self._repo.get_all()

    def get_by_id(self, category_id: CategoryId) -> Category | None:
        return self._repo.get_by_id(category_id)

    def get_by_parent(self, parent_id: CategoryId | None) -> list[Category]:
        return self._repo.get_by_parent(parent_id)

    def name_exists(self, name: str, exclude_id: CategoryId | None = None) -> bool:
        return self._repo.name_exists(name, exclude_id)

    # Write operations with sync
    def save(self, category: Category) -> None:
        is_new = self._repo.get_by_id(category.id) is None
        self._repo.save(category)

        self._sync.queue_change(
            SyncChange(
                entity_type="category",
                change_type=ChangeType.CREATE if is_new else ChangeType.UPDATE,
                entity_id=category.id.value,
                data={
                    "name": category.name,
                    "memo": category.memo,
                    "supercatid": category.parent_id.value if category.parent_id else None,
                    "owner": category.owner,
                    "date": category.created_at.isoformat(),
                },
            )
        )

    def delete(self, category_id: CategoryId) -> None:
        self._repo.delete(category_id)
        self._sync.queue_change(
            SyncChange(
                entity_type="category",
                change_type=ChangeType.DELETE,
                entity_id=category_id.value,
                data={},
            )
        )

    def _handle_remote_change(self, change_type: str, data: dict) -> None:
        pass


class SyncedSegmentRepository:
    """
    Segment repository with sync support.

    Wraps SQLiteSegmentRepository to queue changes for Convex sync.
    """

    def __init__(
        self,
        sqlite_repo: SQLiteSegmentRepository,
        sync_engine: SyncEngine,
    ) -> None:
        self._repo = sqlite_repo
        self._sync = sync_engine
        self._sync.on_remote_change("segment", self._handle_remote_change)

    # Delegate read operations
    def get_all(self) -> list[TextSegment]:
        return self._repo.get_all()

    def get_by_id(self, segment_id: SegmentId) -> TextSegment | None:
        return self._repo.get_by_id(segment_id)

    def get_by_source(self, source_id: SourceId) -> list[TextSegment]:
        return self._repo.get_by_source(source_id)

    def get_by_code(self, code_id: CodeId) -> list[TextSegment]:
        return self._repo.get_by_code(code_id)

    def get_by_source_and_code(
        self, source_id: SourceId, code_id: CodeId
    ) -> list[TextSegment]:
        return self._repo.get_by_source_and_code(source_id, code_id)

    def count_by_code(self, code_id: CodeId) -> int:
        return self._repo.count_by_code(code_id)

    def count_by_source(self, source_id: SourceId) -> int:
        return self._repo.count_by_source(source_id)

    # Write operations with sync
    def save(self, segment: TextSegment) -> None:
        is_new = self._repo.get_by_id(segment.id) is None
        self._repo.save(segment)

        self._sync.queue_change(
            SyncChange(
                entity_type="segment",
                change_type=ChangeType.CREATE if is_new else ChangeType.UPDATE,
                entity_id=segment.id.value,
                data={
                    "cid": segment.code_id.value,
                    "fid": segment.source_id.value,
                    "pos0": segment.position.start,
                    "pos1": segment.position.end,
                    "seltext": segment.selected_text,
                    "memo": segment.memo,
                    "owner": segment.owner,
                    "date": segment.created_at.isoformat(),
                    "important": segment.importance,
                },
            )
        )

    def delete(self, segment_id: SegmentId) -> None:
        self._repo.delete(segment_id)
        self._sync.queue_change(
            SyncChange(
                entity_type="segment",
                change_type=ChangeType.DELETE,
                entity_id=segment_id.value,
                data={},
            )
        )

    def delete_by_code(self, code_id: CodeId) -> int:
        segments = self._repo.get_by_code(code_id)
        count = self._repo.delete_by_code(code_id)

        # Queue delete for each segment
        for segment in segments:
            self._sync.queue_change(
                SyncChange(
                    entity_type="segment",
                    change_type=ChangeType.DELETE,
                    entity_id=segment.id.value,
                    data={},
                )
            )
        return count

    def delete_by_source(self, source_id: SourceId) -> int:
        segments = self._repo.get_by_source(source_id)
        count = self._repo.delete_by_source(source_id)

        for segment in segments:
            self._sync.queue_change(
                SyncChange(
                    entity_type="segment",
                    change_type=ChangeType.DELETE,
                    entity_id=segment.id.value,
                    data={},
                )
            )
        return count

    def reassign_code(self, from_code_id: CodeId, to_code_id: CodeId) -> int:
        count = self._repo.reassign_code(from_code_id, to_code_id)
        # Note: Individual segment updates are handled by Convex-side logic
        return count

    def update_source_name(self, source_id: SourceId, new_name: str) -> None:
        self._repo.update_source_name(source_id, new_name)

    def _handle_remote_change(self, change_type: str, data: dict) -> None:
        pass
