"""
Shared state building for sources use cases.

Following DDD workshop pattern: handlers receive specific repositories,
not entire bounded contexts.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    from src.contexts.projects.core.entities import Source, SourceStatus, SourceType
    from src.shared.common.types import FolderId, SourceId


# ============================================================
# Repository Protocols (for DI)
# ============================================================


@runtime_checkable
class SourceRepository(Protocol):
    """Protocol for source repository operations needed by command handlers."""

    def get_all(self) -> list[Source]: ...
    def get_by_id(self, source_id: SourceId) -> Source | None: ...
    def get_by_name(self, name: str) -> Source | None: ...
    def get_by_type(self, source_type: SourceType) -> list[Source]: ...
    def get_by_status(self, status: SourceStatus) -> list[Source]: ...
    def get_by_folder(self, folder_id: FolderId | None) -> list[Source]: ...
    def save(self, source: Source) -> None: ...
    def delete(self, source_id: SourceId) -> None: ...
    def exists(self, source_id: SourceId) -> bool: ...
    def name_exists(self, name: str, exclude_id: SourceId | None = None) -> bool: ...


@runtime_checkable
class SegmentRepository(Protocol):
    """Protocol for segment repository operations needed for cascade deletes."""

    def delete_by_source(self, source_id: SourceId) -> int: ...
