"""
Shared state building for folders use cases.

Following DDD workshop pattern: handlers receive specific repositories,
not entire bounded contexts.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable

from src.contexts.projects.core.derivers import FolderState

if TYPE_CHECKING:
    from src.contexts.projects.core.entities import Folder, Source
    from src.shared.common.types import FolderId, SourceId


@runtime_checkable
class FolderRepository(Protocol):
    """Protocol for folder repository operations needed by command handlers."""

    def get_all(self) -> list[Folder]: ...
    def get_by_id(self, folder_id: FolderId) -> Folder | None: ...
    def get_by_name(
        self, name: str, parent_id: FolderId | None = None
    ) -> Folder | None: ...
    def get_children(self, parent_id: FolderId | None) -> list[Folder]: ...
    def get_root_folders(self) -> list[Folder]: ...
    def save(self, folder: Folder) -> None: ...
    def delete(self, folder_id: FolderId) -> None: ...
    def exists(self, folder_id: FolderId) -> bool: ...
    def name_exists(
        self, name: str, parent_id: FolderId | None, exclude_id: FolderId | None = None
    ) -> bool: ...
    def get_descendants(self, folder_id: FolderId) -> list[Folder]: ...


@runtime_checkable
class SourceRepository(Protocol):
    """Protocol for source repository operations needed for folder operations."""

    def get_all(self) -> list[Source]: ...
    def get_by_id(self, source_id: SourceId) -> Source | None: ...
    def get_by_folder(self, folder_id: FolderId | None) -> list[Source]: ...
    def save(self, source: Source) -> None: ...


def build_folder_state(
    folder_repo: FolderRepository | None,
    source_repo: SourceRepository | None,
) -> FolderState:
    """Build FolderState from repos (source of truth) for use with derivers."""
    existing_folders = tuple(folder_repo.get_all()) if folder_repo else ()
    existing_sources = tuple(source_repo.get_all()) if source_repo else ()
    return FolderState(
        existing_folders=existing_folders,
        existing_sources=existing_sources,
    )
