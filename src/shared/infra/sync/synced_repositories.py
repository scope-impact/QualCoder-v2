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


class SyncedSourceRepository:
    """
    Source repository with sync support.

    Wraps SQLiteSourceRepository to queue changes for Convex sync.
    """

    def __init__(
        self,
        sqlite_repo: Any,
        sync_engine: SyncEngine,
    ) -> None:
        self._repo = sqlite_repo
        self._sync = sync_engine
        self._sync.on_remote_change("source", self._handle_remote_change)

    # Delegate read operations
    def get_all(self) -> list:
        return self._repo.get_all()

    def get_by_id(self, source_id: SourceId) -> Any:
        return self._repo.get_by_id(source_id)

    def get_by_name(self, name: str) -> Any:
        return self._repo.get_by_name(name)

    def get_by_type(self, source_type: str) -> list:
        return self._repo.get_by_type(source_type)

    def get_by_status(self, status: str) -> list:
        return self._repo.get_by_status(status)

    def get_by_folder(self, folder_id: Any) -> list:
        return self._repo.get_by_folder(folder_id)

    def exists(self, source_id: SourceId) -> bool:
        return self._repo.exists(source_id)

    # Write operations with sync
    def save(self, source: Any) -> None:
        is_new = not self._repo.exists(source.id)
        self._repo.save(source)

        self._sync.queue_change(
            SyncChange(
                entity_type="source",
                change_type=ChangeType.CREATE if is_new else ChangeType.UPDATE,
                entity_id=source.id.value,
                data={
                    "name": source.name,
                    "memo": getattr(source, "memo", ""),
                    "owner": getattr(source, "owner", ""),
                    "source_type": getattr(source, "source_type", ""),
                    "folder_id": source.folder_id.value if source.folder_id else None,
                },
            )
        )

    def delete(self, source_id: SourceId) -> None:
        self._repo.delete(source_id)
        self._sync.queue_change(
            SyncChange(
                entity_type="source",
                change_type=ChangeType.DELETE,
                entity_id=source_id.value,
                data={},
            )
        )

    def _handle_remote_change(self, change_type: str, data: dict) -> None:
        pass


class SyncedFolderRepository:
    """
    Folder repository with sync support.

    Wraps SQLiteFolderRepository to queue changes for Convex sync.
    """

    def __init__(
        self,
        sqlite_repo: Any,
        sync_engine: SyncEngine,
    ) -> None:
        self._repo = sqlite_repo
        self._sync = sync_engine
        self._sync.on_remote_change("folder", self._handle_remote_change)

    # Delegate read operations
    def get_all(self) -> list:
        return self._repo.get_all()

    def get_by_id(self, folder_id: Any) -> Any:
        return self._repo.get_by_id(folder_id)

    def get_children(self, parent_id: Any) -> list:
        return self._repo.get_children(parent_id)

    def get_root_folders(self) -> list:
        return self._repo.get_root_folders()

    def get_descendants(self, folder_id: Any) -> list:
        return self._repo.get_descendants(folder_id)

    # Write operations with sync
    def save(self, folder: Any) -> None:
        existing = self._repo.get_by_id(folder.id)
        is_new = existing is None
        self._repo.save(folder)

        self._sync.queue_change(
            SyncChange(
                entity_type="folder",
                change_type=ChangeType.CREATE if is_new else ChangeType.UPDATE,
                entity_id=folder.id.value,
                data={
                    "name": folder.name,
                    "parent_id": folder.parent_id.value if folder.parent_id else None,
                    "memo": getattr(folder, "memo", ""),
                },
            )
        )

    def delete(self, folder_id: Any) -> None:
        self._repo.delete(folder_id)
        self._sync.queue_change(
            SyncChange(
                entity_type="folder",
                change_type=ChangeType.DELETE,
                entity_id=folder_id.value,
                data={},
            )
        )

    def update_parent(self, folder_id: Any, new_parent_id: Any) -> None:
        self._repo.update_parent(folder_id, new_parent_id)
        self._sync.queue_change(
            SyncChange(
                entity_type="folder",
                change_type=ChangeType.UPDATE,
                entity_id=folder_id.value,
                data={"parent_id": new_parent_id.value if new_parent_id else None},
            )
        )

    def _handle_remote_change(self, change_type: str, data: dict) -> None:
        pass


class SyncedCaseRepository:
    """
    Case repository with sync support.

    Wraps SQLiteCaseRepository to queue changes for Convex sync.
    """

    def __init__(
        self,
        sqlite_repo: Any,
        sync_engine: SyncEngine,
    ) -> None:
        self._repo = sqlite_repo
        self._sync = sync_engine
        self._sync.on_remote_change("case", self._handle_remote_change)

    # Delegate read operations
    def get_all(self) -> list:
        return self._repo.get_all()

    def get_by_id(self, case_id: Any) -> Any:
        return self._repo.get_by_id(case_id)

    def get_by_name(self, name: str) -> Any:
        return self._repo.get_by_name(name)

    def get_cases_for_source(self, source_id: SourceId) -> list:
        return self._repo.get_cases_for_source(source_id)

    # Write operations with sync
    def save(self, case: Any) -> None:
        existing = self._repo.get_by_id(case.id)
        is_new = existing is None
        self._repo.save(case)

        self._sync.queue_change(
            SyncChange(
                entity_type="case",
                change_type=ChangeType.CREATE if is_new else ChangeType.UPDATE,
                entity_id=case.id.value,
                data={
                    "name": case.name,
                    "memo": getattr(case, "memo", ""),
                    "owner": getattr(case, "owner", ""),
                },
            )
        )

    def delete(self, case_id: Any) -> None:
        self._repo.delete(case_id)
        self._sync.queue_change(
            SyncChange(
                entity_type="case",
                change_type=ChangeType.DELETE,
                entity_id=case_id.value,
                data={},
            )
        )

    def link_source(
        self, case_id: Any, source_id: SourceId, source_name: str, owner: str
    ) -> None:
        self._repo.link_source(case_id, source_id, source_name, owner)
        # Case-source links are tracked as case updates
        self._sync.queue_change(
            SyncChange(
                entity_type="case",
                change_type=ChangeType.UPDATE,
                entity_id=case_id.value,
                data={"link_source": source_id.value},
            )
        )

    def unlink_source(self, case_id: Any, source_id: SourceId) -> None:
        self._repo.unlink_source(case_id, source_id)
        self._sync.queue_change(
            SyncChange(
                entity_type="case",
                change_type=ChangeType.UPDATE,
                entity_id=case_id.value,
                data={"unlink_source": source_id.value},
            )
        )

    def _handle_remote_change(self, change_type: str, data: dict) -> None:
        pass
